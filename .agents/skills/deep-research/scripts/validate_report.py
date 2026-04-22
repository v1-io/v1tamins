#!/usr/bin/env python3
"""
Report validator for deep-research skill.
Checks structural integrity, citation consistency, and content quality.
Zero external dependencies -- stdlib only.

Usage:
    python3 validate_report.py --report path/to/report.md
    python3 validate_report.py --report path/to/report.md --strict
"""

import argparse
import re
import sys
from pathlib import Path


def _check_executive_summary(content: str) -> list[str]:
    """Check executive summary exists and meets length requirements."""
    errors = []
    match = re.search(
        r"## Executive Summary\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
    )
    if not match:
        errors.append("ERROR: Missing '## Executive Summary' section")
        return errors

    summary = match.group(1).strip()
    word_count = len(summary.split())

    if word_count < 100:
        errors.append(
            f"ERROR: Executive summary too short ({word_count} words, minimum 100)"
        )
    elif word_count < 200:
        errors.append(
            f"WARNING: Executive summary is short ({word_count} words, target 200-400)"
        )

    # Executive summary should NOT have citations
    citations = re.findall(r"\[(\d+)\]", summary)
    if citations:
        errors.append(
            f"WARNING: Executive summary contains citations {citations} "
            "(should be standalone)"
        )

    return errors


def _check_required_sections(content: str) -> list[str]:
    """Check that all required sections exist."""
    errors = []
    required = ["Executive Summary", "Bibliography"]
    recommended = ["Limitations", "Methodology"]

    for section in required:
        if f"## {section}" not in content:
            errors.append(f"ERROR: Missing required section '## {section}'")

    for section in recommended:
        if f"## {section}" not in content:
            errors.append(f"WARNING: Missing recommended section '## {section}'")

    return errors


def _check_citations(content: str) -> list[str]:
    """Check citation consistency between body and bibliography."""
    errors = []

    # Find all inline citations [N]
    inline_citations = set(int(n) for n in re.findall(r"\[(\d+)\]", content))

    # Find bibliography entries [N]
    bib_match = re.search(r"## Bibliography\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not bib_match:
        if inline_citations:
            errors.append(
                f"ERROR: {len(inline_citations)} inline citations but no bibliography"
            )
        return errors

    bib_text = bib_match.group(1)
    bib_entries = set(int(n) for n in re.findall(r"^\[(\d+)\]", bib_text, re.MULTILINE))

    # Citations in body but not in bibliography
    missing_bib = inline_citations - bib_entries
    if missing_bib:
        errors.append(
            f"ERROR: Citations {sorted(missing_bib)} used in text but missing "
            "from bibliography"
        )

    # Bibliography entries never cited
    uncited = bib_entries - inline_citations
    if uncited:
        errors.append(
            f"WARNING: Bibliography entries {sorted(uncited)} never cited in text"
        )

    # Check for URL in each bibliography entry
    for line in bib_text.strip().split("\n"):
        line = line.strip()
        if not line or not re.match(r"\[\d+\]", line):
            continue
        if "http" not in line:
            entry_num = re.match(r"\[(\d+)\]", line)
            if entry_num:
                errors.append(
                    f"WARNING: Bibliography entry [{entry_num.group(1)}] has no URL"
                )

    return errors


def _check_bibliography_truncation(content: str) -> list[str]:
    """Detect bibliography truncation patterns."""
    errors = []
    truncation_patterns = [
        (r"\[\d+-\d+\]", "citation range (e.g., [8-75])"),
        (r"additional\s+citations", "'additional citations'"),
        (r"further\s+references", "'further references'"),
        (r"\[(?:N|n)\]\s*(?:etc|\.\.\.)", "etc/ellipsis in bibliography"),
        (r"see\s+above", "'see above' in bibliography"),
        (r"similar\s+to\s+\[\d+\]", "'similar to [N]' in bibliography"),
    ]

    bib_match = re.search(r"## Bibliography\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not bib_match:
        return errors

    bib_text = bib_match.group(1).lower()
    for pattern, description in truncation_patterns:
        if re.search(pattern, bib_text, re.IGNORECASE):
            errors.append(f"ERROR: Bibliography truncation detected -- {description}")

    return errors


def _check_placeholders(content: str) -> list[str]:
    """Detect placeholder text that should have been replaced."""
    errors = []
    placeholders = [
        (r"\bTBD\b", "TBD"),
        (r"\bTODO\b", "TODO"),
        (r"\bFIXME\b", "FIXME"),
        (r"\bXXX\b", "XXX"),
        (r"to be determined", "to be determined"),
        (r"\[insert\b", "[insert...]"),
        (r"\[add\b", "[add...]"),
        (r"\{\{.*?\}\}", "template placeholder {{...}}"),
    ]

    for pattern, description in placeholders:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            errors.append(
                f"ERROR: Placeholder text detected -- {description} "
                f"({len(matches)} occurrence(s))"
            )

    return errors


def _check_content_truncation(content: str) -> list[str]:
    """Detect anti-patterns indicating the model truncated or got lazy."""
    errors = []
    truncation_patterns = [
        (r"content continues", "'Content continues...'"),
        (r"due to (?:length|space) (?:constraints|limitations)", "length excuse"),
        (r"\[sections? \d+.*?follow", "'[Sections X-Y follow...]'"),
        (r"and many more", "'and many more'"),
        (r"similar analysis (?:applies|follows)", "'similar analysis applies'"),
        (r"as (?:discussed|mentioned|noted) (?:above|earlier|previously),?\s*$",
         "back-reference without new info (end of paragraph)"),
    ]

    # Check body content only (exclude bibliography)
    body = content
    bib_start = content.find("## Bibliography")
    if bib_start > 0:
        body = content[:bib_start]

    for pattern, description in truncation_patterns:
        if re.search(pattern, body, re.IGNORECASE | re.MULTILINE):
            errors.append(f"ERROR: Content truncation detected -- {description}")

    return errors


def _check_word_count(content: str, mode: str = "standard") -> list[str]:
    """Check total word count against mode targets."""
    errors = []
    targets = {
        "quick": (1500, 5000),
        "standard": (3000, 10000),
        "deep": (6000, 20000),
    }

    min_words, max_words = targets.get(mode, targets["standard"])
    word_count = len(content.split())

    if word_count < min_words:
        errors.append(
            f"WARNING: Report is short for {mode} mode "
            f"({word_count} words, target {min_words}-{max_words})"
        )

    return errors


def _check_source_count(content: str, mode: str = "standard") -> list[str]:
    """Check that enough sources are cited."""
    errors = []
    targets = {"quick": 5, "standard": 10, "deep": 20}

    bib_match = re.search(r"## Bibliography\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not bib_match:
        return errors  # Already caught in required sections check

    bib_entries = re.findall(r"^\[(\d+)\]", bib_match.group(1), re.MULTILINE)
    source_count = len(bib_entries)
    target = targets.get(mode, targets["standard"])

    if source_count < target:
        errors.append(
            f"WARNING: Only {source_count} sources for {mode} mode (target: {target}+)"
        )

    return errors


def validate(report_path: str, mode: str = "standard", strict: bool = False) -> bool:
    """Run all validation checks. Returns True if report passes."""
    path = Path(report_path)
    if not path.exists():
        print(f"ERROR: Report not found at {report_path}")
        return False

    content = path.read_text()

    all_issues = []
    all_issues.extend(_check_executive_summary(content))
    all_issues.extend(_check_required_sections(content))
    all_issues.extend(_check_citations(content))
    all_issues.extend(_check_bibliography_truncation(content))
    all_issues.extend(_check_placeholders(content))
    all_issues.extend(_check_content_truncation(content))
    all_issues.extend(_check_word_count(content, mode))
    all_issues.extend(_check_source_count(content, mode))

    errors = [i for i in all_issues if i.startswith("ERROR")]
    warnings = [i for i in all_issues if i.startswith("WARNING")]

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  {w}")

    if not errors and not warnings:
        print("PASS: All checks passed")
        return True

    if not errors:
        if strict:
            print("\nFAIL: Warnings treated as errors in strict mode")
            return False
        print("\nPASS: No errors (warnings only)")
        return True

    print(f"\nFAIL: {len(errors)} error(s) must be fixed")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a deep-research report")
    parser.add_argument("--report", required=True, help="Path to the report markdown")
    parser.add_argument(
        "--mode",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Research mode (affects word/source count targets)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    args = parser.parse_args()

    success = validate(args.report, args.mode, args.strict)
    sys.exit(0 if success else 1)
