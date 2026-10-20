#!/bin/bash
# delegate-agent.sh — Background agent-to-agent delegation (DEPRECATED)
# Usage: ./delegate-agent.sh <Name|SessionRef> "<prompt>" "<theme>" [fleet-map-path] [model]
#
# DEPRECATED: the /delegate-agent skill starts ask-agent.sh through the harness's own background
# facility, which gives a completion notification. This script backgrounds the turn itself
# (`&`), which breaks that notification, so keep it for standalone shell use only.
#
# Name       → Awaken a new session on the detected platform and work in the background.
# SessionRef → Resume that session in the background.
#
# Returns: the session ref on stdout; the agent keeps working after the script exits.

set -euo pipefail
source "$(dirname "$0")/fleet-common.sh"

# --- Usage ---
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <Name|SessionRef> \"<prompt>\" \"<theme>\" [fleet-map-path] [model]"
    echo ""
    echo "  Name       → Awakens agent with full ceremony + prompt (background)"
    echo "  SessionRef → Resumes existing session + prompt (background)"
    echo "  theme      → Short description of the task (used in fleet map)"
    echo ""
    echo "  Returns the session ref so the caller can check status later."
    echo ""
    echo "Examples:"
    echo "  $0 \"Backend Django\" \"Implement user auth middleware per the spec...\" \"user auth middleware\""
    echo "  $0 \"3f8a2b1c-...\" \"Continue with the next step\""
    exit 1
fi

TARGET="$1"
PROMPT="$2"
THEME="${3:-}"
FLEET_MAP=$(resolve_fleet_map "${4:-}")
MODEL_ARG="${5:-}"
FLEET_AGENTS=$(resolve_fleet_agents "$FLEET_MAP")

if is_session_ref "$TARGET"; then
    MODE="resume"
    PLATFORM=$(ref_platform "$TARGET")
    REF="$TARGET"
else
    MODE="new"
    PLATFORM=$(detect_platform)
    REF=$(new_session_ref "$PLATFORM")
fi

# Resolve model: per-call arg wins; the roster default applies on a new awakening
MODEL="$MODEL_ARG"
if [ -z "$MODEL" ] && [ "$MODE" = "new" ]; then
    MODEL=$(get_agent_model "$TARGET" "$FLEET_AGENTS")
fi
MODEL=$(resolve_model "$PLATFORM" "$MODEL")

if [ "$MODE" = "resume" ]; then
    # --- Resume in the background ---
    echo -e "${CYAN}[delegate-agent] Resuming ${PLATFORM} session in background: ${REF}${NC}" >&2
    run_agent_turn "$PLATFORM" resume "$REF" "$MODEL" "$PROMPT" &
    echo "$REF"
else
    # --- Awaken in the background ---
    verify_agent_exists "$TARGET" "$FLEET_AGENTS"

    echo -e "${CYAN}[delegate-agent] Awakening ${TARGET} on ${PLATFORM} in background (${REF})${NC}" >&2

    FULL_PROMPT=$(build_awaken_prompt "$TARGET" "$PROMPT" "work on this delegated task autonomously. When finished, summarize what you did and what deliverables were produced:" "$PLATFORM")

    add_fleet_entry "$FLEET_MAP" "$TARGET" "$REF" "$THEME" "$PLATFORM"
    echo -e "${GREEN}[delegate-agent] Registered in fleet map${NC}" >&2

    run_agent_turn "$PLATFORM" new "$REF" "$MODEL" "$FULL_PROMPT" &
    echo "$REF"
fi
