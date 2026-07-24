#!/usr/bin/env bash
# Run one peer with an explicit credential policy.
#
# subscription_native removes known user-supplied API-key variables before the
# child is exec'd. It intentionally leaves provider-native OAuth variables and
# host login state untouched. api_explicit keeps only the selected provider's
# known API-key variables and still scrubs every other provider's keys.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLICY_PY="$SCRIPT_DIR/peer_policy.py"

die() {
  printf 'peer-env: %s\n' "$1" >&2
  exit "${2:-2}"
}

provider=""
auth_mode="subscription_native"
command_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --provider)
      provider="${2:-}"
      shift 2 || die "--provider needs a value"
      ;;
    --auth-mode)
      auth_mode="${2:-}"
      shift 2 || die "--auth-mode needs a value"
      ;;
    --)
      shift
      command_args=("$@")
      break
      ;;
    *)
      die "unexpected argument: $1"
      ;;
  esac
done

[ -n "$provider" ] || die "--provider is required"
python3 "$POLICY_PY" --require-provider "$provider" >/dev/null \
  || die "unsupported provider: $provider"

case "$auth_mode" in
  subscription_native|api_explicit) ;;
  *) die "unsupported auth mode: $auth_mode" ;;
esac

[ "${#command_args[@]}" -gt 0 ] || die "a command is required after --"

# Names only; never print their values. Source of truth is peer_policy.py.
if [ "$auth_mode" = "subscription_native" ]; then
  eval "$(python3 "$POLICY_PY" --emit-shell-unset)"
else
  eval "$(python3 "$POLICY_PY" --emit-shell-unset-except-provider "$provider")"
fi

# Keep the provider wrapper safe even when a caller forgets the redirection;
# peer processes are prompt-as-argument runs, never interactive stdin runs.
exec "${command_args[@]}" </dev/null
