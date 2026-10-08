#!/bin/bash
# delegate-agent.sh — Background agent-to-agent delegation (DEPRECATED)
# Usage: ./delegate-agent.sh <Name|UUID> "<prompt>" "<theme>" [fleet-map-path] [model]
#
# DEPRECATED: The /delegate-agent skill now calls ask-agent.sh directly via
# Bash run_in_background:true, which gives proper task-notification on completion.
# This script (which uses `claude &` internally) breaks the notification mechanism.
# Kept for standalone bash usage; do not call from skills.
#
# Name → Full 5-file awakening + prompt (new session, background)
# UUID → Resume existing session + prompt (background)
#
# Returns: UUID of the target session (stdout), agent works in background.

set -euo pipefail
source "$(dirname "$0")/fleet-common.sh"

# --- Usage ---
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <Name|UUID> \"<prompt>\" \"<theme>\" [fleet-map-path] [model]"
    echo ""
    echo "  Name  → Awakens agent with full 5-file protocol + sends prompt (background)"
    echo "  UUID  → Resumes existing session + sends prompt (background)"
    echo "  theme → Short description of the task (used in fleet map)"
    echo ""
    echo "  Returns the UUID so the caller can check status later."
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

# Resolve model: per-call arg wins; fleet default applies for name mode only
MODEL="$MODEL_ARG"
if [ -z "$MODEL" ] && ! is_uuid "$TARGET"; then
    MODEL=$(get_agent_model "$TARGET" "$FLEET_AGENTS")
fi
MODEL_FLAG=""
[ -n "$MODEL" ] && MODEL_FLAG="--model $MODEL"

if is_uuid "$TARGET"; then
    # --- UUID mode: Resume in background ---
    echo -e "${CYAN}[delegate-agent] Resuming session in background: ${TARGET}${NC}" >&2
    claude --print $MODEL_FLAG --resume "$TARGET" "$PROMPT" &
    echo "$TARGET"
else
    # --- Name mode: Awaken new session in background ---
    verify_agent_exists "$TARGET"
    UUID=$(generate_uuid)

    echo -e "${CYAN}[delegate-agent] Awakening ${TARGET} in background (UUID: ${UUID})${NC}" >&2

    FULL_PROMPT=$(build_awaken_prompt "$TARGET" "$PROMPT" "work on this delegated task autonomously. When finished, summarize what you did and what deliverables were produced:")

    add_fleet_entry "$FLEET_MAP" "$TARGET" "$UUID" "$THEME"
    echo -e "${GREEN}[delegate-agent] Registered in fleet map${NC}" >&2

    claude --print $MODEL_FLAG --session-id "$UUID" "$FULL_PROMPT" &
    echo "$UUID"
fi
