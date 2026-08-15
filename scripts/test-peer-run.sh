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
if "$ENV_WRAPPER" --provider gemini --auth-mode subscription_native -- "$FAKE_EMPTY" >/dev/null 2>&1; then
  printf 'legacy gemini provider was accepted\n' >&2
  exit 1
fi
if "$ENV_WRAPPER" --provider oracle --auth-mode subscription_native -- "$FAKE_EMPTY" >/dev/null 2>&1; then
  printf 'oracle provider was accepted by peer-env allowlist\n' >&2
  exit 1
fi
OPENAI_API_KEY=synthetic ANTHROPIC_API_KEY=synthetic CURSOR_API_KEY=synthetic \
  "$ENV_WRAPPER" --provider codex --auth-mode subscription_native -- "$FAKE_ENV" > "$TEST_DIR/env.txt"
grep -qx 'keys-scrubbed' "$TEST_DIR/env.txt"
grep -qx 'stdin-closed' "$TEST_DIR/env.txt"
OPENAI_API_KEY=synthetic ANTHROPIC_API_KEY=synthetic CURSOR_API_KEY=synthetic \
  "$ENV_WRAPPER" --provider codex --auth-mode api_explicit -- "$FAKE_ENV" > "$TEST_DIR/api-env.txt"
grep -qx 'key-present' "$TEST_DIR/api-env.txt"
grep -qx 'stdin-closed' "$TEST_DIR/api-env.txt"
# api_explicit for codex must keep OpenAI keys but scrub Anthropic/Cursor keys.
printf '%s\n' '#!/usr/bin/env bash' \
  'printf "openai=%s\n" "${OPENAI_API_KEY:-absent}"' \
  'printf "anthropic=%s\n" "${ANTHROPIC_API_KEY:-absent}"' \
  'printf "cursor=%s\n" "${CURSOR_API_KEY:-absent}"' > "$TEST_DIR/fake-scoped-env.sh"
chmod +x "$TEST_DIR/fake-scoped-env.sh"
OPENAI_API_KEY=synthetic ANTHROPIC_API_KEY=synthetic CURSOR_API_KEY=synthetic \
  "$ENV_WRAPPER" --provider codex --auth-mode api_explicit -- "$TEST_DIR/fake-scoped-env.sh" > "$TEST_DIR/scoped-env.txt"
grep -qx 'openai=synthetic' "$TEST_DIR/scoped-env.txt"
grep -qx 'anthropic=absent' "$TEST_DIR/scoped-env.txt"
grep -qx 'cursor=absent' "$TEST_DIR/scoped-env.txt"

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

# A hung peer reaches timed_out via the watchdog. status/verdict must not kill.
# Teardown owns mutation after observation. The unrelated process must remain.
# Keep the sentinel alive past launch + deadline grace + observation sleeps.
while :; do sleep 1; done &
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
# Wait past deadline + watchdog grace without calling status/verdict mutation.
sleep 3
"$RUNNER" status --dir "$TEST_DIR" --slug hang > "$TEST_DIR/hang-status.txt" || true
[ "$(cat "$TEST_DIR/hang-status.txt")" = 'timed_out' ]
"$RUNNER" verdict --dir "$TEST_DIR" --slug hang --json > "$TEST_DIR/hang.json"
[ "$(json_field "$TEST_DIR/hang.json" state)" = 'timed_out' ]
kill -0 "$UNRELATED_PID" 2>/dev/null
"$RUNNER" teardown --dir "$TEST_DIR" --slug hang >/dev/null
kill -0 "$UNRELATED_PID" 2>/dev/null

# Reusing a slug must tear down the prior watchdog before overwriting sentinels.
"$RUNNER" launch --dir "$TEST_DIR" --slug reuse --deadline-seconds 30 -- "$FAKE_HANG" >/dev/null
old_watchdog="$(cat "$TEST_DIR/reuse/peer.watchdog.pid")"
kill -0 "$old_watchdog" 2>/dev/null
"$RUNNER" launch --dir "$TEST_DIR" --slug reuse --deadline-seconds 5 -- "$FAKE_OUTPUT" >/dev/null
if kill -0 "$old_watchdog" 2>/dev/null; then
  printf 'stale watchdog survived slug reuse\n' >&2
  exit 1
fi
poll_verdict "$TEST_DIR" reuse "$TEST_DIR/reuse.json"
[ "$(json_field "$TEST_DIR/reuse.json" state)" = 'complete' ]
"$RUNNER" teardown --dir "$TEST_DIR" --slug reuse >/dev/null

# JSON / stream-json framing without a terminal answer is empty_output, not complete.
FAKE_JSON_FRAME="$TEST_DIR/fake-json-frame.sh"
printf '%s\n' '#!/usr/bin/env bash' \
  'printf "%s\n" "{\"type\":\"system\",\"subtype\":\"init\"}"' \
  'printf "%s\n" "{\"type\":\"result\",\"subtype\":\"success\",\"result\":\"\",\"is_error\":false}"' \
  'exit 0' > "$FAKE_JSON_FRAME"
chmod +x "$FAKE_JSON_FRAME"
"$RUNNER" launch --dir "$TEST_DIR" --slug json-frame --deadline-seconds 5 -- "$FAKE_JSON_FRAME" >/dev/null
poll_verdict "$TEST_DIR" json-frame "$TEST_DIR/json-frame.json"
[ "$(json_field "$TEST_DIR/json-frame.json" state)" = 'empty_output' ]

FAKE_JSON_ANSWER="$TEST_DIR/fake-json-answer.sh"
printf '%s\n' '#!/usr/bin/env bash' \
  'printf "%s\n" "{\"type\":\"system\",\"subtype\":\"init\"}"' \
  'printf "%s\n" "{\"type\":\"result\",\"subtype\":\"success\",\"result\":\"peer answer\",\"is_error\":false}"' \
  'exit 0' > "$FAKE_JSON_ANSWER"
chmod +x "$FAKE_JSON_ANSWER"
"$RUNNER" launch --dir "$TEST_DIR" --slug json-answer --deadline-seconds 5 -- "$FAKE_JSON_ANSWER" >/dev/null
poll_verdict "$TEST_DIR" json-answer "$TEST_DIR/json-answer.json"
[ "$(json_field "$TEST_DIR/json-answer.json" state)" = 'complete' ]
[ "$(json_field "$TEST_DIR/json-answer.json" envelope_family)" = 'result_text' ]

# A terminal answer nested below the result event is complete, not empty_output.
FAKE_NESTED_ANSWER="$TEST_DIR/fake-nested-answer.sh"
cat > "$FAKE_NESTED_ANSWER" <<'PEER'
#!/usr/bin/env bash
cat <<'STREAM'
{"event":"start","session_id":"synthetic"}
{"event":"result","result":{"status":"SUCCESS","response":"nested peer answer"}}
STREAM
exit 0
PEER
chmod +x "$FAKE_NESTED_ANSWER"
"$RUNNER" launch --dir "$TEST_DIR" --slug nested --deadline-seconds 5 -- "$FAKE_NESTED_ANSWER" >/dev/null
poll_verdict "$TEST_DIR" nested "$TEST_DIR/nested.json"
[ "$(json_field "$TEST_DIR/nested.json" state)" = 'complete' ]
[ "$(json_field "$TEST_DIR/nested.json" envelope_family)" = 'result_event_nested' ]

# A nested terminal envelope reporting failure is empty_output, not complete.
FAKE_NESTED_ERROR="$TEST_DIR/fake-nested-error.sh"
cat > "$FAKE_NESTED_ERROR" <<'PEER'
#!/usr/bin/env bash
cat <<'STREAM'
{"event":"start","session_id":"synthetic"}
{"event":"result","result":{"status":"FAILED","response":"upstream refused"}}
STREAM
exit 0
PEER
chmod +x "$FAKE_NESTED_ERROR"
"$RUNNER" launch --dir "$TEST_DIR" --slug nested-error --deadline-seconds 5 -- "$FAKE_NESTED_ERROR" >/dev/null
poll_verdict "$TEST_DIR" nested-error "$TEST_DIR/nested-error.json"
[ "$(json_field "$TEST_DIR/nested-error.json" state)" = 'empty_output' ]

# Reasoning and tool traffic without an answer block is empty_output.
FAKE_THINKING="$TEST_DIR/fake-thinking.sh"
cat > "$FAKE_THINKING" <<'PEER'
#!/usr/bin/env bash
cat <<'STREAM'
{"type":"system","subtype":"init"}
{"type":"assistant","message":{"content":[{"type":"thinking","thinking":"deliberating"}]}}
STREAM
exit 0
PEER
chmod +x "$FAKE_THINKING"
"$RUNNER" launch --dir "$TEST_DIR" --slug thinking --deadline-seconds 5 -- "$FAKE_THINKING" >/dev/null
poll_verdict "$TEST_DIR" thinking "$TEST_DIR/thinking.json"
[ "$(json_field "$TEST_DIR/thinking.json" state)" = 'empty_output' ]

printf 'peer-run contract passed\n'
