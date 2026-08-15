#!/usr/bin/env python3
"""Classify peer stdout: is there a terminal answer, and in which envelope?

Providers frame a headless run differently. Some end with a plain string
payload, some nest the answer one or more levels below the terminal event, and
all of them interleave framing, progress, reasoning, and tool events that are
not answers. This module reads shapes, never provider names, so a provider that
changes its envelope stays classifiable without a code edit here.

Exit status of ``answer`` is the runner contract: 0 when a terminal answer is
present, 1 when the output is framing, reasoning, tool traffic, or an error
only.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Bounded descent keeps a hostile or pathological payload from costing more
# than a fixed amount of work.
MAX_DEPTH = 6

# Keys that can carry a provider's final answer payload.
ANSWER_KEYS = ("result", "message", "content", "text", "output", "response")

# Content blocks that are never an answer on their own.
NON_ANSWER_BLOCK_TYPES = frozenset(
    {
        "thinking",
        "redacted_thinking",
        "reasoning",
        "tool_use",
        "tool_result",
        "tool_call",
        "function_call",
    }
)

# Envelopes that frame or narrate a run rather than terminate it.
FRAMING_TYPES = frozenset(
    {
        "system",
        "status",
        "progress",
        "ping",
        "heartbeat",
        "tool_progress",
        "user",
        "rate_limit_event",
    }
)

# Envelope type -> reported family. An empty type is a bare JSON document.
TYPE_FAMILY = {
    "": "json_object",
    "result": "result_text",
    "message": "assistant_message",
    "assistant": "assistant_message",
    "agent_message": "assistant_message",
    "response": "assistant_message",
    "item.completed": "item_completed",
    "agent.completed": "item_completed",
}

ERROR_SUBTYPES = frozenset({"error", "failure", "failed"})
ERROR_STATUSES = frozenset({"error", "failed", "failure"})

# Families reported when no terminal answer was found.
EMPTY_FAMILY = "empty"
UNKNOWN_FAMILY = "unknown"
PLAIN_TEXT_FAMILY = "plain_text"


@dataclass(frozen=True)
class Verdict:
    """One classification of a peer's stdout."""

    answer: bool
    envelope_family: str

    def to_dict(self) -> dict[str, Any]:
        return {"answer": self.answer, "envelope_family": self.envelope_family}


def is_error_object(obj: dict[str, Any]) -> bool:
    """Reject error envelopes before reading any text out of them."""

    if obj.get("is_error") is True:
        return True
    if str(obj.get("subtype") or "").strip().lower() in ERROR_SUBTYPES:
        return True
    status = obj.get("status")
    if isinstance(status, str) and status.strip().lower() in ERROR_STATUSES:
        return True
    return False


def terminal_text(value: Any, depth: int = 0) -> bool:
    """True when value carries answer text, not framing, reasoning, or tools."""

    if depth > MAX_DEPTH:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(terminal_text(item, depth + 1) for item in value)
    if isinstance(value, dict):
        if is_error_object(value):
            return False
        if str(value.get("type") or "").strip().lower() in NON_ANSWER_BLOCK_TYPES:
            return False
        for key in ANSWER_KEYS:
            if key in value and terminal_text(value[key], depth + 1):
                return True
    return False


def envelope_type(obj: dict[str, Any]) -> str:
    return str(obj.get("type") or obj.get("event") or "").strip().lower()


def object_answer_family(obj: Any) -> str | None:
    """Return the envelope family when obj terminates a run with an answer."""

    if not isinstance(obj, dict):
        return None
    if is_error_object(obj):
        return None
    typ = envelope_type(obj)
    if typ in FRAMING_TYPES:
        return None

    item_completed = typ.startswith("item.") and "completed" in typ
    if typ not in TYPE_FAMILY and not item_completed:
        return None

    # A terminal result event may hold the answer directly or nest it below.
    if typ == "result":
        payload = obj.get("result")
        if isinstance(payload, str):
            return "result_text" if payload.strip() else None
        if terminal_text(payload):
            return "result_event_nested"

    for key in ANSWER_KEYS:
        if key in obj and terminal_text(obj[key]):
            if item_completed:
                return "item_completed"
            return TYPE_FAMILY[typ]
    return None


def first_answer_family(objects: list[Any]) -> str | None:
    for obj in objects:
        family = object_answer_family(obj)
        if family is not None:
            return family
    return None


def classify_text(text: str) -> Verdict:
    """Classify one peer's whole stdout capture."""

    stripped = text.strip()
    if not stripped:
        return Verdict(False, EMPTY_FAMILY)

    objects: list[Any] = []
    json_lines = 0
    nonempty = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        nonempty += 1
        try:
            objects.append(json.loads(line))
            json_lines += 1
        except json.JSONDecodeError:
            objects.append(None)

    # Every non-empty line parsed: this is a stream of events, not a document.
    if nonempty and json_lines == nonempty:
        family = first_answer_family(objects)
        return Verdict(family is not None, family or UNKNOWN_FAMILY)

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        # Plain text with non-whitespace content is its own answer.
        return Verdict(True, PLAIN_TEXT_FAMILY)

    if isinstance(payload, list):
        family = first_answer_family(payload)
        return Verdict(family is not None, family or UNKNOWN_FAMILY)
    family = object_answer_family(payload)
    return Verdict(family is not None, family or UNKNOWN_FAMILY)


def classify_path(path: Path) -> Verdict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return Verdict(False, EMPTY_FAMILY)
    return classify_text(text)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("answer", "exit 0 when stdout holds a terminal answer, else 1"),
        ("classify", "print the typed classification as JSON"),
        ("family", "print the envelope family token only"),
    ):
        subcommand = subcommands.add_parser(name, help=help_text)
        subcommand.add_argument("path", help="captured peer stdout file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    verdict = classify_path(Path(args.path))
    if args.command == "answer":
        return 0 if verdict.answer else 1
    if args.command == "family":
        print(verdict.envelope_family)
        return 0
    print(json.dumps(verdict.to_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
