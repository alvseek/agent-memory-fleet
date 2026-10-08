#!/bin/bash
# ask-agent.sh — Blocking agent-to-agent communication
# Usage: ./ask-agent.sh <Name|UUID> "<prompt>" "<theme>" [fleet-map-path] [model]
#
# Name → Full 5-file awakening + prompt (new session, registered in fleet map)
# UUID → Resume existing session + prompt (continuation)
#
# Returns: Agent's response (stdout), blocks until complete.

set -euo pipefail
source "$(dirname "$0")/fleet-common.sh"

# --- Usage ---
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <Name|UUID> \"<prompt>\" \"<theme>\" [fleet-map-path] [model]"
    echo ""
    echo "  Name  → Awakens agent with full 5-file protocol + sends prompt (blocking)"
    echo "  UUID  → Resumes existing session + sends prompt (blocking)"
    echo "  theme → Short description of the task (used in fleet map)"
    echo ""
    echo "Examples:"
    echo "  $0 \"Backend Django\" \"What is the best model pattern for user auth?\" \"user auth patterns\""
    echo "  $0 \"3f8a2b1c-9d4e-4f7a-8e2b-5c6d9a1b4e7f\" \"Status update?\""
    exit 1
fi

TARGET="$1"
PROMPT="$2"
THEME="${3:-}"
FLEET_MAP=$(resolve_fleet_map "${4:-}")
MODEL_ARG="${5:-}"
FLEET_AGENTS=$(resolve_fleet_agents "$FLEET_MAP")

# Resolve model: per-call arg wins; fleet default applies for name mode only
MODEL="$MODEL_ARG"
if [ -z "$MODEL" ] && ! is_uuid "$TARGET"; then
    MODEL=$(get_agent_model "$TARGET" "$FLEET_AGENTS")
fi
MODEL_FLAG=""
[ -n "$MODEL" ] && MODEL_FLAG="--model $MODEL"

if is_uuid "$TARGET"; then
    # --- UUID mode: Resume existing session ---
    echo -e "${CYAN}[ask-agent] Resuming session: ${TARGET}${NC}" >&2
    claude --print $MODEL_FLAG --resume "$TARGET" "$PROMPT"
else
    # --- Name mode: Awaken new session ---
    verify_agent_exists "$TARGET"
    UUID=$(generate_uuid)

    echo -e "${CYAN}[ask-agent] Awakening ${TARGET} (UUID: ${UUID})${NC}" >&2

    FULL_PROMPT=$(build_awaken_prompt "$TARGET" "$PROMPT" "respond to this request:")

    add_fleet_entry "$FLEET_MAP" "$TARGET" "$UUID" "$THEME"
    echo -e "${GREEN}[ask-agent] Registered in fleet map${NC}" >&2

    # Print UUID as first stdout line so callers using run_in_background can capture it
    echo "$UUID"
    claude --print $MODEL_FLAG --session-id "$UUID" "$FULL_PROMPT"
fi
