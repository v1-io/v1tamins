#!/usr/bin/env bash
# Read-only comparison of the canonical plugin root with one installed root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_PY="$SCRIPT_DIR/installed_plugin_verify.py"

usage() {
  cat >&2 <<'EOF'
Usage: scripts/verify-installed-plugin.sh \
  --canonical <plugin-root> --installed <plugin-root> --runtime <codex|claude> \
  [--probe-catalog]

Repeat --installed only to receive a fail-closed ambiguous result.
The command never edits a source, cache, credential, or installed target.
By default model catalog probing is skipped (model_catalog_status=not_requested).
With --probe-catalog, probing runs only after the install hash matches.
EOF
}

canonical=""
runtime=""
installed_roots=()
probe_catalog=false

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
    --probe-catalog)
      probe_catalog=true
      shift
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

args=(
  --canonical "$canonical"
  --runtime "$runtime"
)
for root in "${installed_roots[@]+"${installed_roots[@]}"}"; do
  args+=(--installed "$root")
done
if [ "$probe_catalog" = true ]; then
  args+=(--probe-catalog)
fi

exec python3 "$VERIFY_PY" "${args[@]}"
