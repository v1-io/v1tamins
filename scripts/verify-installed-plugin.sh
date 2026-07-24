#!/usr/bin/env bash
# Read-only comparison of the canonical plugin root with one installed root.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/verify-installed-plugin.sh \
  --canonical <plugin-root> --installed <plugin-root> --runtime <codex|claude>

Repeat --installed only to receive a fail-closed ambiguous result.
The command never edits a source, cache, credential, or installed target.
EOF
}

canonical=""
runtime=""
installed_roots=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --canonical)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      canonical="$2"
      shift 2
      ;;
    --installed)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      installed_roots+=("$2")
      shift 2
      ;;
    --runtime)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      runtime="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'verify-installed-plugin: unexpected argument: %s\n' "$1" >&2
      usage
      exit 2
      ;;
  esac
done

if [ -z "$canonical" ] || [ -z "$runtime" ]; then
  usage
  exit 2
fi
case "$runtime" in
  codex) manifest_relpath=".codex-plugin/plugin.json" ;;
  claude) manifest_relpath=".claude-plugin/plugin.json" ;;
  *) printf 'verify-installed-plugin: runtime must be codex or claude\n' >&2; exit 2 ;;
esac

status_json() {
  local status="$1"
  local message="$2"
  python3 - "$runtime" "$status" "$message" <<'PY'
import json
import sys

runtime, status, message = sys.argv[1:]
print(json.dumps({
    "schema": "v1-installed-plugin-verification/v1",
    "runtime": runtime,
    "verification_status": status,
    "action_status": "not_requested",
    "credential_values_exposed": False,
    "message": message,
}, sort_keys=True))
PY
}

if [ "${#installed_roots[@]}" -eq 0 ]; then
  status_json missing "no installed root supplied"
  exit 1
fi
if [ "${#installed_roots[@]}" -ne 1 ]; then
  status_json ambiguous "more than one installed root supplied"
  exit 1
fi

installed="${installed_roots[0]}"
if [ ! -d "$canonical" ] || [ ! -f "$canonical/$manifest_relpath" ]; then
  status_json missing "canonical plugin root is missing the selected runtime manifest"
  exit 1
fi
if [ ! -d "$installed" ] || [ ! -f "$installed/$manifest_relpath" ]; then
  status_json missing "installed plugin root is missing the selected runtime manifest"
  exit 1
fi

required_relpaths=(
  "skills/v1-phone-a-friend/SKILL.md"
  "skills/v1-review-board/SKILL.md"
  "skills/v1-phone-a-friend/scripts/peer_catalog.py"
  "skills/v1-phone-a-friend/scripts/peer_catalog_support.py"
)
for relpath in "${required_relpaths[@]}"; do
  if [ ! -f "$canonical/$relpath" ] || [ ! -f "$installed/$relpath" ]; then
    status_json missing "required peer skill resource is missing"
    exit 1
  fi
done

json_field() {
  local file="$1"
  local field="$2"
  python3 - "$file" "$field" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        payload = json.load(handle)
except (OSError, json.JSONDecodeError):
    print("__INVALID__")
    raise SystemExit
value = payload.get(sys.argv[2])
print(value if isinstance(value, str) else "__MISSING__")
PY
}

tree_hash() {
  python3 - "$1" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
digest = hashlib.sha256()
for current, directories, files in os.walk(root, followlinks=False):
    directories.sort()
    for name in sorted(files):
        path = Path(current) / name
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative)
        digest.update(b"\0")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
print(digest.hexdigest())
PY
}

skill_hash() {
  python3 - "$1" "$2" <<'PY'
import hashlib
import os
import sys
from pathlib import Path

digest = hashlib.sha256()
for root_arg in sys.argv[1:]:
    root = Path(root_arg).resolve()
    for current, directories, files in os.walk(root, followlinks=False):
        directories.sort()
        for name in sorted(files):
            path = Path(current) / name
            if not path.is_file():
                continue
            relative = f"{root.name}/{path.relative_to(root).as_posix()}".encode()
            digest.update(relative)
            digest.update(b"\0")
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
print(digest.hexdigest())
PY
}

canonical_version="$(json_field "$canonical/$manifest_relpath" version)"
installed_version="$(json_field "$installed/$manifest_relpath" version)"
if [ "$canonical_version" = "__INVALID__" ] || [ "$installed_version" = "__INVALID__" ]; then
  status_json missing "runtime manifest is not valid JSON"
  exit 1
fi

canonical_source_hash="$(tree_hash "$canonical")"
installed_source_hash="$(tree_hash "$installed")"
canonical_skill_hash="$(skill_hash "$canonical/skills/v1-phone-a-friend" "$canonical/skills/v1-review-board")"
installed_skill_hash="$(skill_hash "$installed/skills/v1-phone-a-friend" "$installed/skills/v1-review-board")"

catalog_status="unavailable"
catalog_fingerprint=""
catalog_tmp="$(mktemp -d "${TMPDIR:-/tmp}/v1-plugin-catalog.XXXXXX")"
cleanup() {
  find "$catalog_tmp" -type f -delete 2>/dev/null || true
  find "$catalog_tmp" -depth -type d -empty -delete 2>/dev/null || true
}
trap cleanup EXIT

catalog_script="$installed/skills/v1-phone-a-friend/scripts/peer_catalog.py"
if python3 "$catalog_script" --profile fast --auth-mode subscription_native > "$catalog_tmp/catalog.json" 2>/dev/null; then
  catalog_fingerprint="$(json_field "$catalog_tmp/catalog.json" catalog_fingerprint)"
  if [ "$catalog_fingerprint" != "__INVALID__" ] && [ "$catalog_fingerprint" != "__MISSING__" ]; then
    catalog_status="resolved"
  else
    catalog_fingerprint=""
    catalog_status="invalid"
  fi
fi

verification_status="match"
if [ "$canonical_version" = "__MISSING__" ] || [ "$installed_version" = "__MISSING__" ]; then
  verification_status="missing"
elif [ "$canonical_version" != "$installed_version" ] || [ "$canonical_source_hash" != "$installed_source_hash" ] || [ "$canonical_skill_hash" != "$installed_skill_hash" ]; then
  verification_status="stale"
fi

python3 - "$runtime" "$verification_status" "$canonical_version" "$installed_version" \
  "$canonical_source_hash" "$installed_source_hash" "$canonical_skill_hash" "$installed_skill_hash" \
  "$catalog_status" "$catalog_fingerprint" <<'PY'
import json
import sys

(runtime, status, canonical_version, installed_version, canonical_source,
 installed_source, canonical_skill, installed_skill, catalog_status,
 catalog_fingerprint) = sys.argv[1:]
print(json.dumps({
    "schema": "v1-installed-plugin-verification/v1",
    "runtime": runtime,
    "verification_status": status,
    "action_status": "not_requested",
    "canonical_version": None if canonical_version.startswith("__") else canonical_version,
    "installed_version": None if installed_version.startswith("__") else installed_version,
    "canonical_source_sha256": canonical_source,
    "installed_source_sha256": installed_source,
    "canonical_peer_skills_sha256": canonical_skill,
    "installed_peer_skills_sha256": installed_skill,
    "model_catalog_status": catalog_status,
    "model_catalog_fingerprint": catalog_fingerprint or None,
    "credential_values_exposed": False,
}, sort_keys=True))
PY

if [ "$verification_status" = "match" ]; then
  exit 0
fi
exit 1
