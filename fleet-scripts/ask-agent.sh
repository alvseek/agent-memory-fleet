#!/bin/bash
# ask-agent.sh — Blocking agent-to-agent communication
# Usage: ./ask-agent.sh <Name|SessionRef> "<prompt>" "<theme>" [fleet-map-path] [model]
#
# Name      → Awaken a new session on the detected platform, then send the prompt.
# SessionRef → Resume that session (a Claude UUID, or an OpenCode `ses_...`).
#
# The platform is detected from the caller's environment (OpenCode or Claude Code) and can be
# forced with FLEET_PLATFORM. The ref's own shape decides which platform a resume goes to.
#
# Returns: Agent's response (stdout), blocks until complete.

set -euo pipefail
source "$(dirname "$0")/fleet-common.sh"

# --- Usage ---
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <Name|SessionRef> \"<prompt>\" \"<theme>\" [fleet-map-path] [model]"
    echo ""
    echo "  Name       → Awakens agent with full ceremony + sends prompt (blocking)"
    echo "  SessionRef → Resumes existing session + sends prompt (blocking)"
    echo "  theme      → Short description of the task (used in fleet map)"
    echo ""
    echo "Examples:"
    echo "  $0 \"Backend Django\" \"What is the best model pattern for user auth?\" \"user auth patterns\""
    echo "  $0 \"3f8a2b1c-9d4e-4f7a-8e2b-5c6d9a1b4e7f\" \"Status update?\""
    echo "  $0 \"ses_eac06c991ffdCKSsXMqFHrCVkb\" \"Status update?\""
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
    # --- Resume an existing session ---
    echo -e "${CYAN}[ask-agent] Resuming ${PLATFORM} session: ${REF}${NC}" >&2
    run_agent_turn "$PLATFORM" resume "$REF" "$MODEL" "$PROMPT"
else
    # --- Awaken a new session ---
    verify_agent_exists "$TARGET" "$FLEET_AGENTS"

    echo -e "${CYAN}[ask-agent] Awakening ${TARGET} on ${PLATFORM} (${REF})${NC}" >&2

    FULL_PROMPT=$(build_awaken_prompt "$TARGET" "$PROMPT" "respond to this request:" "$PLATFORM")

    add_fleet_entry "$FLEET_MAP" "$TARGET" "$REF" "$THEME" "$PLATFORM"
    echo -e "${GREEN}[ask-agent] Registered in fleet map${NC}" >&2

    # Print the ref as the first stdout line so callers using a background shell can capture it
    echo "$REF"
    run_agent_turn "$PLATFORM" new "$REF" "$MODEL" "$FULL_PROMPT"
fi
