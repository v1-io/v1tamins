#!/usr/bin/env python3
"""Reject personal dependencies and operator paths in shared instructions/code.

Historical changelog entries are deliberately outside this scope.
This is a bounded regression guard, not a complete dependency/privacy audit.
"""
import re
import subprocess
import sys
from pathlib import Path

# Public optional companion; installation and availability policy: README.md.
EXTERNAL_SKILLS = {"ce-work"}
SKILL_ROUTES = re.compile(
    r"`([a-z][a-z0-9-]+)`\s+skill\b|\bskill\s+`([a-z][a-z0-9-]+)`"
    r"|\b(?:use|load|invoke|run)\s+`\$([a-z][a-z0-9-]+)`", re.I
)
PERSONAL_DEPENDENCIES = re.compile(
    r"(?<![A-Za-z0-9_-])(?:taskit|tool-native-operations)(?![A-Za-z0-9_-])"
    r"|(?:/|\\)lint-pr\.sh\b", re.I
)
CHECKER_FIXTURES = {
    "scripts/check-shared-portability.py",
    "scripts/test-check-shared-portability.py",
}
USER_HOME = re.compile(r"(?:/Users/|/home/)[A-Za-z0-9][A-Za-z0-9._-]*/|[A-Za-z]:\\Users\\[A-Za-z0-9][A-Za-z0-9._-]*\\")


def active_guidance(path: str) -> bool:
    p = Path(path)
    if path in CHECKER_FIXTURES:
        return False
    code = p.suffix.lower() in {".py", ".sh", ".rb", ".js", ".ts", ".json", ".toml", ".yaml", ".yml"}
    if code and (path.startswith("scripts/") or path.startswith("plugins/v1tamins/scripts/")
                 or path.startswith(".github/workflows/")):
        return True
    return p.suffix.lower() in {".md", ".yaml", ".yml", ".py", ".sh", ".rb", ".js", ".ts", ".json", ".toml"} and (
        path in {"AGENTS.md", "CLAUDE.md", "README.md"}
        or path.startswith("docs/agents/")
        or path.startswith(".agents/skills/")
        or path.startswith("plugins/v1tamins/skills/")
    )


def check(root: Path) -> list[str]:
    paths = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"], text=True
    ).split("\0")
    declared = {
        Path(path).parent.name for path in paths
        if path.endswith("/SKILL.md") and (root / path).is_file()
    } | EXTERNAL_SKILLS
    failures = []
    for path in paths:
        if not active_guidance(path) or not (root / path).is_file():
            continue
        try:
            lines = (root / path).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            failures.append(f"{path}: active guidance must be UTF-8")
            continue
        for number, line in enumerate(lines, 1):
            if PERSONAL_DEPENDENCIES.search(line):
                failures.append(f"{path}:{number}: replace personal dependency with a packaged helper or documented public interface")
            if USER_HOME.search(line):
                failures.append(f"{path}:{number}: replace operator home path with a portable root")
            for match in SKILL_ROUTES.finditer(line):
                name = next(value for value in match.groups() if value).lower()
                if name not in declared:
                    failures.append(f"{path}:{number}: undeclared skill route {name}; use a packaged skill or document a public dependency")
    return failures


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    failures = check(root)
    if failures:
        print("\n".join(failures), file=sys.stderr)
    sys.exit(bool(failures))
