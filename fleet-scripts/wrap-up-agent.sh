#!/bin/bash
# wrap-up-agent.sh — Ask a target agent session to wrap up, then update the fleet map
# Usage: ./wrap-up-agent.sh <SessionRef> [fleet-map-path]
#
# Sends the wrap-up instruction to the specified session so the agent saves its episodic memory
# and concludes cleanly, then marks the fleet map entry as "completed". The platform comes from
# the ref's own shape (Claude UUID or OpenCode `ses_...`).

set -euo pipefail
source "$(dirname "$0")/fleet-common.sh"

# --- Usage ---
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <SessionRef> [fleet-map-path]"
    echo ""
    echo "  Sends the wrap-up instruction to the agent session, then marks the fleet map entry completed."
    echo ""
    echo "Examples:"
    echo "  $0 \"3f8a2b1c-9d4e-4f7a-8e2b-5c6d9a1b4e7f\""
    echo "  $0 \"ses_eac06c991ffdCKSsXMqFHrCVkb\""
    exit 1
fi

REF="$1"
FLEET_MAP=$(resolve_fleet_map "${2:-}")

if ! is_session_ref "$REF"; then
    echo -e "${RED}[wrap-up-agent] Error: Expected a session ref, got: ${REF}${NC}" >&2
    echo -e "${YELLOW}Use ask-agent.sh or delegate-agent.sh with a Name to start a new session.${NC}" >&2
    exit 1
fi

PLATFORM=$(ref_platform "$REF")

echo -e "${CYAN}[wrap-up-agent] Sending wrap-up to ${PLATFORM} session: ${REF}${NC}" >&2

# The instruction names the capability, not a command: Claude resolves /wrap-up, while a served
# memory core is reached through its procedure.
case "$PLATFORM" in
    opencode) WRAP_PROMPT="Please run your wrap-up procedure now: save your episodic memory and conclude this session cleanly." ;;
    *)        WRAP_PROMPT="Please execute /wrap-up now. Save your episodic memory and conclude this session cleanly." ;;
esac

run_agent_turn "$PLATFORM" resume "$REF" "" "$WRAP_PROMPT"

update_fleet_status "$FLEET_MAP" "$REF" "completed"

echo -e "${GREEN}[wrap-up-agent] Session ${REF} wrapped up and marked completed.${NC}" >&2
