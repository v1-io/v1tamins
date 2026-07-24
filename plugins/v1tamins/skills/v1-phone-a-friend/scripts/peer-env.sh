#!/usr/bin/env bash
# Run one peer with an explicit credential policy.
#
# subscription_native removes known user-supplied API-key variables before the
# child is exec'd. It intentionally leaves provider-native OAuth variables and
# host login state untouched. api_explicit is the only mode that preserves
# ambient API-key variables; selecting it is a deliberate per-run choice.

set -euo pipefail

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
case "$provider" in
  claude|codex|cursor-agent|agy|oracle) ;;
  *) die "unsupported provider: $provider" ;;
esac

case "$auth_mode" in
  subscription_native|api_explicit) ;;
  *) die "unsupported auth mode: $auth_mode" ;;
esac

[ "${#command_args[@]}" -gt 0 ] || die "a command is required after --"

if [ "$auth_mode" = "subscription_native" ]; then
  # Names only; never print their values. Keep this list aligned with
  # peer_catalog.py and the deterministic contract tests.
  unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN CLAUDE_API_KEY
  unset OPENAI_API_KEY OPENAI_AUTH_TOKEN CODEX_API_KEY
  unset CURSOR_API_KEY GEMINI_API_KEY GOOGLE_API_KEY GOOGLE_GENAI_API_KEY
fi

# Keep the provider wrapper safe even when a caller forgets the redirection;
# peer processes are prompt-as-argument runs, never interactive stdin runs.
exec "${command_args[@]}" </dev/null
