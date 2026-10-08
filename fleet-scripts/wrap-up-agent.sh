#!/bin/bash
# wrap-up-agent.sh — Send /wrap-up to a target agent session and update fleet map
# Usage: ./wrap-up-agent.sh <UUID> [fleet-map-path]
#
# Sends the /wrap-up command to the specified session so the agent saves
# its episodic memory and concludes cleanly. Then marks the fleet map
# entry as "completed".

set -euo pipefail
source "$(dirname "$0")/fleet-common.sh"

# --- Usage ---
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <UUID> [fleet-map-path]"
    echo ""
    echo "  Sends /wrap-up to the agent session, then marks fleet map entry as completed."
    echo ""
    echo "Examples:"
    echo "  $0 \"3f8a2b1c-9d4e-4f7a-8e2b-5c6d9a1b4e7f\""
    exit 1
fi

UUID="$1"
FLEET_MAP=$(resolve_fleet_map "${2:-}")

if ! is_uuid "$UUID"; then
    echo -e "${RED}[wrap-up-agent] Error: Expected a UUID, got: ${UUID}${NC}" >&2
    echo -e "${YELLOW}Use ask-agent.sh or delegate-agent.sh with a Name to start a new session.${NC}" >&2
    exit 1
fi

echo -e "${CYAN}[wrap-up-agent] Sending /wrap-up to session: ${UUID}${NC}" >&2

claude --print --resume "$UUID" "Please execute /wrap-up now. Save your episodic memory and conclude this session cleanly."

update_fleet_status "$FLEET_MAP" "$UUID" "completed"

echo -e "${GREEN}[wrap-up-agent] Session ${UUID} wrapped up and marked completed.${NC}" >&2
