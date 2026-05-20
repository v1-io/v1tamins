#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
args=()

for arg in "$@"; do
  case "$arg" in
    --write)
      printf 'note: --write is ignored; plugin skills are canonical now. Use scripts/validate-plugin.sh.\n' >&2
      ;;
    *)
      args+=("$arg")
      ;;
  esac
done

exec "$script_dir/validate-plugin.sh" "${args[@]}"
