#!/usr/bin/env bash
# Characterization tests for the bounded, stdin-safe peer runner.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$ROOT_DIR/plugins/v1tamins/skills/v1-phone-a-friend/scripts/peer-run.sh"
TEST_DIR="$(mktemp -d "${TMPDIR:-/tmp}/v1-peer-run-test.XXXXXX")"

cleanup() {
  if [ -n "${UNRELATED_PID:-}" ] && kill -0 "$UNRELATED_PID" 2>/dev/null; then
    kill "$UNRELATED_PID" 2>/dev/null || true
    wait "$UNRELATED_PID" 2>/dev/null || true
  fi
  find "$TEST_DIR" -type f -delete 2>/dev/null || true
  find "$TEST_DIR" -depth -type d -empty -delete 2>/dev/null || true
}
trap cleanup EXIT

FAKE_OUTPUT="$TEST_DIR/fake-output.sh"
FAKE_EMPTY="$TEST_DIR/fake-empty.sh"
FAKE_HANG="$TEST_DIR/fake-hang.sh"
FAKE_ENV="$TEST_DIR/fake-env.sh"

printf '%s\n' '#!/usr/bin/env bash' 'if IFS= read -r -t 1 _; then printf "stdin-was-open\n"; exit 9; fi' 'printf "substantive synthetic peer output\n"' 'exit 7' > "$FAKE_OUTPUT"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' > "$FAKE_EMPTY"
printf '%s\n' '#!/usr/bin/env bash' 'while :; do sleep 1; done' > "$FAKE_HANG"
printf '%s\n' '#!/usr/bin/env bash' 'if [ -n "${OPENAI_API_KEY:-}" ] || [ -n "${ANTHROPIC_API_KEY:-}" ] || [ -n "${CURSOR_API_KEY:-}" ]; then printf "key-present\n"; else printf "keys-scrubbed\n"; fi' 'if IFS= read -r -t 1 _; then printf "stdin-open\n"; else printf "stdin-closed\n"; fi' > "$FAKE_ENV"
chmod +x "$FAKE_OUTPUT" "$FAKE_EMPTY" "$FAKE_HANG" "$FAKE_ENV"

ENV_WRAPPER="$ROOT_DIR/plugins/v1tamins/skills/v1-phone-a-friend/scripts/peer-env.sh"
OPENAI_API_KEY=synthetic ANTHROPIC_API_KEY=synthetic CURSOR_API_KEY=synthetic \
  "$ENV_WRAPPER" --provider codex --auth-mode subscription_native -- "$FAKE_ENV" > "$TEST_DIR/env.txt"
grep -qx 'keys-scrubbed' "$TEST_DIR/env.txt"
grep -qx 'stdin-closed' "$TEST_DIR/env.txt"
OPENAI_API_KEY=synthetic "$ENV_WRAPPER" --provider codex --auth-mode api_explicit -- "$FAKE_ENV" > "$TEST_DIR/api-env.txt"
grep -qx 'key-present' "$TEST_DIR/api-env.txt"
grep -qx 'stdin-closed' "$TEST_DIR/api-env.txt"

json_field() {
  local file="$1"
  local field="$2"
  python3 - "$file" "$field" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text())
value = payload[sys.argv[2]]
print(value if isinstance(value, str) else json.dumps(value))
PY
}

poll_verdict() {
  local dir="$1"
  local slug="$2"
  local output="$3"
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12; do
    "$RUNNER" verdict --dir "$dir" --slug "$slug" --json > "$output"
    case "$(json_field "$output" state)" in
      running) sleep 0.1 ;;
      *) return 0 ;;
    esac
  done
  printf 'peer did not reach a terminal state: %s\n' "$slug" >&2
  return 1
}

# Nonzero provider exit plus substantive output is complete, and stdin is
# closed at the actual child boundary.
OUTPUT_DIR="$TEST_DIR/output"
"$RUNNER" launch --dir "$TEST_DIR" --slug output --deadline-seconds 5 -- "$FAKE_OUTPUT" >/dev/null
poll_verdict "$TEST_DIR" output "$OUTPUT_DIR.json"
[ "$(json_field "$OUTPUT_DIR.json" state)" = 'complete' ]
[ "$(json_field "$OUTPUT_DIR.json" exit_code)" = '7' ]
if grep -q 'stdin-was-open' "$TEST_DIR/output/peer.stdout"; then
  printf 'stdin was not closed\n' >&2
  exit 1
fi

# A clean empty exit is a typed empty_output, not success by exit code.
"$RUNNER" launch --dir "$TEST_DIR" --slug empty --deadline-seconds 5 -- "$FAKE_EMPTY" >/dev/null
poll_verdict "$TEST_DIR" empty "$TEST_DIR/empty.json"
[ "$(json_field "$TEST_DIR/empty.json" state)" = 'empty_output' ]

# A hung peer reaches timed_out and the runner terminates only its recorded
# process group. The unrelated process must remain alive.
sleep 4 &
UNRELATED_PID=$!
"$RUNNER" launch --dir "$TEST_DIR" --slug hang --deadline-seconds 1 -- "$FAKE_HANG" >/dev/null
if [ "$(cat "$TEST_DIR/hang/peer.session")" = '1' ]; then
  recorded_pid="$(cat "$TEST_DIR/hang/peer.pid")"
  recorded_pgid="$(ps -o pgid= -p "$recorded_pid" | tr -d ' ' | head -1)"
  [ "$recorded_pid" = "$recorded_pgid" ] || {
    printf 'runner recorded the launcher PID instead of the session leader\n' >&2
    exit 1
  }
fi
sleep 2
"$RUNNER" verdict --dir "$TEST_DIR" --slug hang --json > "$TEST_DIR/hang.json"
[ "$(json_field "$TEST_DIR/hang.json" state)" = 'timed_out' ]
kill -0 "$UNRELATED_PID" 2>/dev/null

printf 'peer-run contract passed\n'
