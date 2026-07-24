#!/usr/bin/env bash
# Synthetic coverage for read-only installed-source verification.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERIFIER="$ROOT_DIR/scripts/verify-installed-plugin.sh"
TEST_DIR="$(mktemp -d "${TMPDIR:-/tmp}/v1-plugin-verifier-test.XXXXXX")"
CANONICAL="$TEST_DIR/canonical"
INSTALLED="$TEST_DIR/installed"
MISSING="$TEST_DIR/missing"

cleanup() {
  find "$TEST_DIR" -type f -delete 2>/dev/null || true
  find "$TEST_DIR" -depth -type d -empty -delete 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$CANONICAL" "$INSTALLED" "$MISSING"
cp -R "$ROOT_DIR/plugins/v1tamins/." "$CANONICAL/"
cp -R "$CANONICAL/." "$INSTALLED/"

json_field() {
  python3 - "$1" "$2" <<'PY'
import json
import sys
from pathlib import Path

value = json.loads(Path(sys.argv[1]).read_text())[sys.argv[2]]
print(value if isinstance(value, str) else json.dumps(value))
PY
}

"$VERIFIER" --canonical "$CANONICAL" --installed "$INSTALLED" --runtime codex > "$TEST_DIR/match.json"
[ "$(json_field "$TEST_DIR/match.json" verification_status)" = 'match' ]
[ "$(json_field "$TEST_DIR/match.json" model_catalog_status)" = 'not_requested' ]
[ "$(json_field "$TEST_DIR/match.json" model_catalog_fingerprint)" = 'null' ]
[ "$(json_field "$TEST_DIR/match.json" credential_values_exposed)" = 'false' ]
if grep -F "$TEST_DIR" "$TEST_DIR/match.json" >/dev/null; then
  printf 'verifier leaked a private absolute path\n' >&2
  exit 1
fi

# Optional catalog probe uses the installed discovery script when requested.
FAKE_CATALOG='#!/usr/bin/env python3
import json
print(json.dumps({"ok": True, "catalog_fingerprint": "synthetic-catalog"}))'
printf '%s\n' "$FAKE_CATALOG" > "$INSTALLED/skills/v1-phone-a-friend/scripts/peer_catalog.py"
chmod +x "$INSTALLED/skills/v1-phone-a-friend/scripts/peer_catalog.py"
# Tree hash changes because we replaced the installed catalog script.
if "$VERIFIER" --canonical "$CANONICAL" --installed "$INSTALLED" --runtime codex --probe-catalog > "$TEST_DIR/probe-stale.json"; then
  printf 'probe against drifted install unexpectedly matched\n' >&2
  exit 1
fi
[ "$(json_field "$TEST_DIR/probe-stale.json" verification_status)" = 'stale' ]
[ "$(json_field "$TEST_DIR/probe-stale.json" model_catalog_status)" = 'resolved' ]
[ "$(json_field "$TEST_DIR/probe-stale.json" model_catalog_fingerprint)" = 'synthetic-catalog' ]

# Restore installed tree for remaining cases.
rm -rf "$INSTALLED"
cp -R "$CANONICAL/." "$INSTALLED/"

printf '%s\n' '# synthetic installed drift' >> "$INSTALLED/skills/v1-phone-a-friend/SKILL.md"
if "$VERIFIER" --canonical "$CANONICAL" --installed "$INSTALLED" --runtime codex > "$TEST_DIR/stale.json"; then
  printf 'stale verification unexpectedly succeeded\n' >&2
  exit 1
fi
[ "$(json_field "$TEST_DIR/stale.json" verification_status)" = 'stale' ]
[ "$(json_field "$TEST_DIR/stale.json" model_catalog_status)" = 'not_requested' ]

if "$VERIFIER" --canonical "$CANONICAL" --installed "$MISSING" --runtime codex > "$TEST_DIR/missing.json"; then
  printf 'missing verification unexpectedly succeeded\n' >&2
  exit 1
fi
[ "$(json_field "$TEST_DIR/missing.json" verification_status)" = 'missing' ]

if "$VERIFIER" --canonical "$CANONICAL" --installed "$INSTALLED" --installed "$CANONICAL" --runtime codex > "$TEST_DIR/ambiguous.json"; then
  printf 'ambiguous verification unexpectedly succeeded\n' >&2
  exit 1
fi
[ "$(json_field "$TEST_DIR/ambiguous.json" verification_status)" = 'ambiguous' ]

printf 'installed plugin verifier contract passed\n'
