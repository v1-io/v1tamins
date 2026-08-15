#!/usr/bin/env python3
"""Turn an approved peer selection into an argv list the installed CLI accepts.

Prose wrappers fail deterministically and locally: a streaming output mode that
needs a companion verbosity flag, a variadic option that swallows the prompt
placed after it, an effort value synthesized into a model argument the provider
never advertised. Those are wrapper defects, not peer failures, so they belong
in tested code with typed refusals rather than in a template a human retypes.

Discovery still never launches: this module builds and validates commands, and
``peer-run.sh`` remains the only thing that starts a process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from peer_adapters import effort_suffix  # noqa: E402
from peer_policy import API_KEY_ENV_VARS, PROVIDERS, subscription_environment  # noqa: E402

SCHEMA = "v1-peer-launch/v1"

PermissionMode = Literal["readonly", "local-verify", "isolated-delegate"]
LaunchErrorCode = Literal["launch_recipe_unresolved", "wrapper_validation_failed"]

PERMISSION_MODES = ("readonly", "local-verify", "isolated-delegate")

# The prompt is passed to the wrapper through this shell variable in every
# documented example. Recipes carry the real text instead.
PROMPT_SENTINEL = "$PHONE_A_FRIEND_PROMPT"

# Read-only tool sets for providers that take an explicit allow/deny list.
READ_ONLY_TOOLS = "Read,Grep,Glob"
WRITE_TOOLS = "Edit,Write,Bash,mcp__*"

DEFAULT_PRINT_TIMEOUT = "5m"
DEFAULT_PROBE_TIMEOUT_SECONDS = 10.0

# Options that accept more than one value. Their value is attached with `=` so
# the parser cannot keep consuming tokens and eat the prompt.
VARIADIC_FLAGS: dict[str, frozenset[str]] = {
    "claude": frozenset({"--tools", "--allowedTools", "--disallowedTools", "--add-dir"}),
    "codex": frozenset(),
    "cursor-agent": frozenset(),
    "agy": frozenset({"--add-dir"}),
}

# Provider entry points. The subcommand is probed together with the binary so a
# syntax probe reads the help surface that actually parses these flags.
BINARIES: dict[str, tuple[str, ...]] = {
    "claude": ("claude",),
    "codex": ("codex", "exec"),
    "cursor-agent": ("cursor-agent",),
    "agy": ("agy",),
}


@dataclass(frozen=True)
class LaunchContext:
    """Run-specific values the wrapper needs but selection does not own."""

    repo: str | None = None
    worktree: str | None = None
    print_timeout: str = DEFAULT_PRINT_TIMEOUT


@dataclass(frozen=True)
class LaunchError:
    """A wrapper defect found before any provider process starts."""

    code: LaunchErrorCode
    detail: str
    missing_flags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "schema": SCHEMA,
            "code": self.code,
            "detail": self.detail,
            "missing_flags": list(self.missing_flags),
            # Nothing was dispatched, so the repair boundary stays open.
            "dispatch_state": "pre_dispatch_failed",
        }


@dataclass(frozen=True)
class LaunchRecipe:
    """One validated launch command, minus the credential-policy prefix."""

    cli: str
    argv: tuple[str, ...]
    permission: PermissionMode
    auth_mode: str
    prompt_digest: str
    launch_model_argument: str | None = None
    reasoning_argument: str | None = None
    provider_version_fingerprint: str | None = None
    catalog_fingerprint: str | None = None
    env_overrides: dict[str, str] = field(default_factory=dict)
    prompt_placement: str = "final_positional"
    syntax_validation: str = "unverified"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "schema": SCHEMA,
            "cli": self.cli,
            "argv": list(self.argv),
            "permission": self.permission,
            "auth_mode": self.auth_mode,
            "prompt_digest": self.prompt_digest,
            "launch_model_argument": self.launch_model_argument,
            "reasoning_argument": self.reasoning_argument,
            "provider_version_fingerprint": self.provider_version_fingerprint,
            "catalog_fingerprint": self.catalog_fingerprint,
            "env_overrides": dict(self.env_overrides),
            "prompt_placement": self.prompt_placement,
            "syntax_validation": self.syntax_validation,
        }


def unresolved(cli: str, detail: str, missing: tuple[str, ...] = ()) -> LaunchError:
    return LaunchError("launch_recipe_unresolved", f"{cli}: {detail}", missing)


def option(cli: str, name: str, value: str) -> list[str]:
    """Emit one option, attaching the value when the option is variadic."""

    if name in VARIADIC_FLAGS.get(cli, frozenset()):
        return [f"{name}={value}"]
    return [name, value]


def finalize(cli: str, argv: list[str], prompt: str) -> list[str] | LaunchError:
    """Append the prompt last and refuse when it could be swallowed."""

    if argv and argv[-1] in VARIADIC_FLAGS.get(cli, frozenset()):
        return unresolved(
            cli,
            f"prompt would be consumed by the variadic option {argv[-1]}",
            (argv[-1],),
        )
    return [*argv, prompt]


def reasoning_encoded_in_model(model: str | None, reasoning: str | None) -> bool:
    """True when the model argument already carries the requested level."""

    if reasoning is None:
        return True
    if model is None:
        return False
    return effort_suffix(model) == reasoning


def build_claude(
    permission: PermissionMode,
    model: str | None,
    reasoning: str | None,
    context: LaunchContext,
) -> list[str] | LaunchError:
    argv = ["claude", "-p"]
    if permission == "readonly":
        argv += option("claude", "--tools", READ_ONLY_TOOLS)
        argv += option("claude", "--allowedTools", READ_ONLY_TOOLS)
        argv += option("claude", "--disallowedTools", WRITE_TOOLS)
        argv += ["--strict-mcp-config"]
    else:
        argv += ["--permission-mode", "bypassPermissions"]
    argv += ["--output-format", "stream-json"]
    # Streaming JSON is only accepted alongside the verbose flag.
    argv += ["--verbose"]
    if model:
        argv += ["--model", model]
    if reasoning:
        argv += ["--effort", reasoning]
    return argv


def build_codex(
    permission: PermissionMode,
    model: str | None,
    reasoning: str | None,
    context: LaunchContext,
) -> list[str] | LaunchError:
    if context.repo is None:
        return unresolved("codex", "needs an explicit working directory (--repo)")
    if not reasoning_encoded_in_model(model, reasoning):
        return unresolved(
            "codex",
            f"reasoning level {reasoning!r} has no validated launch argument",
        )
    sandbox = (
        ["--sandbox", "read-only"]
        if permission == "readonly"
        else ["--dangerously-bypass-approvals-and-sandbox"]
    )
    argv = ["codex", "exec", *sandbox, "--cd", context.repo, "--json"]
    if model:
        argv += ["--model", model]
    return argv


def build_cursor(
    permission: PermissionMode,
    model: str | None,
    reasoning: str | None,
    context: LaunchContext,
) -> list[str] | LaunchError:
    # The catalog ID is the only accepted model argument. Never synthesize an
    # effort-parameterized form the provider did not advertise.
    if not reasoning_encoded_in_model(model, reasoning):
        return unresolved(
            "cursor-agent",
            f"reasoning level {reasoning!r} is not part of the validated model argument",
        )
    argv = ["cursor-agent", "-p"]
    if permission == "readonly":
        argv += ["--mode", "plan", "--trust"]
    else:
        if context.worktree is None:
            return unresolved(
                "cursor-agent", "elevated permission needs an explicit --worktree name"
            )
        argv += ["--worktree", context.worktree]
    argv += ["--output-format", "stream-json"]
    if model:
        argv += ["--model", model]
    if permission != "readonly":
        argv += ["--force"]
    return argv


def build_agy(
    permission: PermissionMode,
    model: str | None,
    reasoning: str | None,
    context: LaunchContext,
) -> list[str] | LaunchError:
    argv = ["agy"]
    argv += ["--sandbox"] if permission == "readonly" else ["--dangerously-skip-permissions"]
    argv += ["--print-timeout", context.print_timeout]
    if model:
        argv += ["--model", model]
    if reasoning:
        argv += ["--effort", reasoning]
    # --print takes the prompt, so it must stay the final option.
    argv += ["--print"]
    return argv


BUILDERS = {
    "claude": build_claude,
    "codex": build_codex,
    "cursor-agent": build_cursor,
    "agy": build_agy,
}


def build_recipe(
    cli: str,
    *,
    permission: PermissionMode,
    prompt: str,
    model: str | None = None,
    reasoning: str | None = None,
    auth_mode: str = "subscription_native",
    context: LaunchContext | None = None,
    version_fingerprint: str | None = None,
    catalog_fingerprint: str | None = None,
) -> LaunchRecipe | LaunchError:
    if cli not in BUILDERS:
        return unresolved(cli, "unsupported provider")
    if permission not in PERMISSION_MODES:
        return unresolved(cli, f"unsupported permission mode: {permission}")

    built = BUILDERS[cli](permission, model, reasoning, context or LaunchContext())
    if isinstance(built, LaunchError):
        return built
    completed = finalize(cli, built, prompt)
    if isinstance(completed, LaunchError):
        return completed

    reasoning_argument = reasoning if reasoning and "--effort" in completed else None
    return LaunchRecipe(
        cli=cli,
        argv=tuple(completed),
        permission=permission,
        auth_mode=auth_mode,
        prompt_digest=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        launch_model_argument=model,
        reasoning_argument=reasoning_argument,
        provider_version_fingerprint=version_fingerprint,
        catalog_fingerprint=catalog_fingerprint,
    )


def recipe_flags(recipe: LaunchRecipe) -> list[str]:
    """Long option names used by a recipe, without their attached values."""

    names: list[str] = []
    for token in recipe.argv:
        if not token.startswith("--"):
            continue
        name = token.split("=", 1)[0]
        if name not in names:
            names.append(name)
    return names


def help_surface(cli: str, auth_mode: str, timeout_seconds: float) -> str | None:
    """Read the installed CLI's own help text. No model request is made."""

    entry = BINARIES[cli]
    executable = shutil.which(entry[0])
    if executable is None:
        return None
    try:
        completed = subprocess.run(
            [executable, *entry[1:], "--help"],
            check=False,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            errors="replace",
            env=subscription_environment(auth_mode, cli),
            timeout=timeout_seconds,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    text = f"{completed.stdout}\n{completed.stderr}"
    return text if text.strip() else None


def validate_syntax(
    recipe: LaunchRecipe, timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS
) -> LaunchRecipe | LaunchError:
    """Check every option against the installed CLI's help surface.

    Help text is the only surface a CLI offers for this, so the check reads it
    directly. It is deliberately one-sided: a help surface that cannot be read
    leaves the recipe `unverified`, and only a readable surface that omits an
    option is a failure. This never repairs a recipe.
    """

    text = help_surface(recipe.cli, recipe.auth_mode, timeout_seconds)
    if text is None:
        return recipe
    missing = tuple(
        name
        for name in recipe_flags(recipe)
        if not re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text)
    )
    if missing:
        return LaunchError(
            "wrapper_validation_failed",
            f"{recipe.cli}: installed help surface does not document "
            + ", ".join(missing),
            missing,
        )
    return LaunchRecipe(**{**recipe.__dict__, "syntax_validation": "verified"})


SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_@%+=:,./-]+$")


def shell_token(value: str) -> str:
    """Render one argv token as shell source that lexes back to itself."""

    if value == PROMPT_SENTINEL:
        return f'"{PROMPT_SENTINEL}"'
    if SAFE_TOKEN.match(value):
        return value
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
    )
    return f'"{escaped}"'


def render_example(recipe: LaunchRecipe) -> str:
    """Render the documented shell form of one recipe."""

    entry = BINARIES[recipe.cli]
    head = len(entry)
    # Keep a leading short switch such as -p on the invocation line.
    while head < len(recipe.argv) and re.match(r"^-[A-Za-z]$", recipe.argv[head]):
        head += 1
    prefix = (
        f'"$PEER_ENV" --provider {recipe.cli} '
        f"--auth-mode {recipe.auth_mode} -- {' '.join(recipe.argv[:head])}"
    )
    body = list(recipe.argv[head:])
    prompt = body.pop()
    # Options that take the prompt as their value stay on the prompt's line.
    trailing = [body.pop()] if body and body[-1] == "--print" else []

    lines = [prefix]
    index = 0
    while index < len(body):
        token = body[index]
        takes_value = (
            token.startswith("-")
            and "=" not in token
            and index + 1 < len(body)
            and not body[index + 1].startswith("-")
        )
        if takes_value:
            lines.append(f"{shell_token(token)} {shell_token(body[index + 1])}")
            index += 2
        else:
            lines.append(shell_token(token))
            index += 1
    tail = " ".join(shell_token(token) for token in [*trailing, prompt])
    lines.append(f"{tail} < /dev/null")
    return " \\\n  ".join(lines)


# Placeholders the documented examples use in place of runtime values.
DOC_MODEL = "<current-model-from-catalog>"
DOC_REASONING = "<current-reasoning-level>"


def doc_examples() -> list[dict[str, str]]:
    """Every wrapper the command templates document, rendered from the adapter."""

    plans: list[tuple[str, PermissionMode, LaunchContext, str | None]] = [
        ("claude", "readonly", LaunchContext(), DOC_REASONING),
        ("claude", "isolated-delegate", LaunchContext(), DOC_REASONING),
        ("codex", "readonly", LaunchContext(repo="<repo>"), None),
        (
            "codex",
            "isolated-delegate",
            LaunchContext(repo="<trusted-or-isolated-repo>"),
            None,
        ),
        ("cursor-agent", "readonly", LaunchContext(), None),
        ("cursor-agent", "isolated-delegate", LaunchContext(worktree="<name>"), None),
        ("agy", "readonly", LaunchContext(), DOC_REASONING),
        ("agy", "isolated-delegate", LaunchContext(), DOC_REASONING),
    ]
    examples: list[dict[str, str]] = []
    for cli, permission, context, reasoning in plans:
        recipe = build_recipe(
            cli,
            permission=permission,
            prompt=PROMPT_SENTINEL,
            model=DOC_MODEL,
            reasoning=reasoning,
            context=context,
        )
        if isinstance(recipe, LaunchError):
            raise SystemExit(f"doc example is unbuildable: {recipe.detail}")
        examples.append(
            {
                "cli": cli,
                "permission": permission,
                "block": render_example(recipe),
            }
        )
    return examples


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", choices=tuple(PROVIDERS))
    parser.add_argument("--permission", choices=PERMISSION_MODES, default="readonly")
    parser.add_argument("--prompt-file", help="file holding the approved prompt")
    parser.add_argument("--model")
    parser.add_argument("--reasoning")
    parser.add_argument(
        "--auth-mode",
        choices=("subscription_native", "api_explicit"),
        default="subscription_native",
    )
    parser.add_argument("--repo")
    parser.add_argument("--worktree")
    parser.add_argument("--print-timeout", default=DEFAULT_PRINT_TIMEOUT)
    parser.add_argument("--version-fingerprint")
    parser.add_argument("--catalog-fingerprint")
    parser.add_argument(
        "--probe-syntax",
        action="store_true",
        help="check options against the installed CLI help surface",
    )
    parser.add_argument(
        "--probe-timeout-seconds", type=float, default=DEFAULT_PROBE_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--emit-doc-examples",
        action="store_true",
        help="print the documented wrapper examples this adapter produces",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.emit_doc_examples:
        print(json.dumps({"schema": SCHEMA, "examples": doc_examples()}, indent=2))
        return 0
    if not args.cli or not args.prompt_file:
        print(
            json.dumps(
                LaunchError(
                    "launch_recipe_unresolved",
                    "--cli and --prompt-file are required",
                ).to_dict(),
                sort_keys=True,
            )
        )
        return 2

    try:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    except OSError as exc:
        print(
            json.dumps(
                LaunchError(
                    "launch_recipe_unresolved", f"unreadable prompt file: {exc}"
                ).to_dict(),
                sort_keys=True,
            )
        )
        return 2

    outcome = build_recipe(
        args.cli,
        permission=args.permission,
        prompt=prompt,
        model=args.model,
        reasoning=args.reasoning,
        auth_mode=args.auth_mode,
        context=LaunchContext(
            repo=args.repo, worktree=args.worktree, print_timeout=args.print_timeout
        ),
        version_fingerprint=args.version_fingerprint,
        catalog_fingerprint=args.catalog_fingerprint,
    )
    if isinstance(outcome, LaunchRecipe) and args.probe_syntax:
        outcome = validate_syntax(outcome, args.probe_timeout_seconds)
    print(json.dumps(outcome.to_dict(), sort_keys=True))
    return 2 if isinstance(outcome, LaunchError) else 0


if __name__ == "__main__":
    sys.exit(main())
