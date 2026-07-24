#!/usr/bin/env bash
# Deadline watchdog for a recorded peer. Honors peer.session for PGID kill.
# Args: seconds donefile pidfile childpidfile sessfile

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=peer-run-lib.sh
. "$SCRIPT_DIR/peer-run-lib.sh"

seconds="$1"
donefile="$2"
pidfile="$3"
childpidfile="$4"
sessfile="$5"

sleep "$seconds"
[ -f "$donefile" ] && exit 0

terminate_peer_processes "$pidfile" "$childpidfile" "$sessfile" 10 >/dev/null
