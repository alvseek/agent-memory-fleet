#!/bin/bash
# fleet-common.sh — Shared functions for fleet agent scripts
# Source this file: source "$(dirname "$0")/fleet-common.sh"
#
# Two platforms are supported, and only the spawn line differs. Everything else — project,
# roster, fleet map, structured prompt — is platform-neutral, so the platform surface is one
# case statement: how the command is built, and what a session ref looks like.

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Agent memory path ---
# [AGENT-MEMORY-PATH] is a placeholder in the instructions, and a shell has no instructions
# file to read it from, so it is an env var with the historical Claude path as the fallback.
# The fallback keeps existing installs working; a machine that keeps its store elsewhere sets
# AGENT_MEMORY_PATH.
resolve_agent_memory_path() {
    if [ -n "${AGENT_MEMORY_PATH:-}" ]; then
        echo "$AGENT_MEMORY_PATH"
        return
    fi
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) echo "/c/Users/$(whoami)/.claude/@agent-memory" ;;
        Darwin)               echo "/Users/$(whoami)/.claude/@agent-memory" ;;
        *)                    echo "/home/$(whoami)/.claude/@agent-memory" ;;
    esac
}
AGENT_MEMORY_PATH=$(resolve_agent_memory_path)

# --- Platform resolution ---
# Detection reads the environment the calling harness gives its shell, not a config file:
# OpenCode sets OPENCODE=1 and AI_AGENT=opencode, Claude Code sets CLAUDECODE=1. FLEET_PLATFORM
# overrides both, which is what a harness that sets neither uses.
detect_platform() {
    if [ -n "${FLEET_PLATFORM:-}" ]; then
        echo "$FLEET_PLATFORM"
        return
    fi
    if [ "${AI_AGENT:-}" = "opencode" ] || [ "${OPENCODE:-}" = "1" ]; then
        echo "opencode"
        return
    fi
    echo "claude"
}
PLATFORM=$(detect_platform)

# --- Declarations from the platform's global instructions file ---
# [PROJECT-ACCESS] and its URL are declared in the instructions file, not the environment, so a
# script that has to honour the layer's delivery form reads the same text the agent reads.
instructions_file() {
    case "$PLATFORM" in
        opencode) echo "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/AGENTS.md" ;;
        *)        echo "$HOME/.claude/CLAUDE.md" ;;
    esac
}

# read_declaration KEY — the backticked value of `**[KEY]** = ...` in the instructions file.
read_declaration() {
    local file value
    file=$(instructions_file)
    if [ ! -f "$file" ]; then
        return 0
    fi
    value=$(grep -F "**[$1]**" "$file" 2>/dev/null | head -n 1 | sed 's/.*= `//; s/`.*//')
    echo "$value"
}

# --- Session refs ---
# A ref is whatever the platform calls a session: a UUID on Claude Code, `ses_...` on OpenCode.
is_uuid() {
    [[ "$1" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]
}

is_session_ref() {
    is_uuid "$1" || [[ "$1" =~ ^ses_ ]]
}

ref_platform() {
    if is_uuid "$1"; then
        echo "claude"
    elif [[ "$1" =~ ^ses_ ]]; then
        echo "opencode"
    fi
}

generate_uuid() {
    local uuid
    uuid=$(cat /proc/sys/kernel/random/uuid 2>/dev/null \
        || python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null \
        || powershell -c "[guid]::NewGuid().ToString()" 2>/dev/null)
    if [ -z "$uuid" ]; then
        echo -e "${RED}Error: Could not generate UUID${NC}" >&2
        exit 1
    fi
    echo "$uuid"
}

# new_session_ref PLATFORM — a ref the platform will accept and create on first use.
new_session_ref() {
    case "$1" in
        opencode) echo "ses_$(generate_uuid | tr -d '-')" ;;
        *)        generate_uuid ;;
    esac
}

# resolve_model PLATFORM MODEL
# Claude takes an alias (haiku/sonnet/opus). OpenCode takes provider/model#variant, so a bare
# alias is looked up in FLEET_MODEL_<ALIAS> (e.g. FLEET_MODEL_SONNET=provider/model) rather than
# inventing a provider here. An unresolved alias yields no model flag, so the platform default
# applies instead of a guessed one.
resolve_model() {
    local platform="$1" model="$2" var mapped
    if [ -z "$model" ]; then
        echo ""
        return
    fi
    if [ "$platform" = "opencode" ] && [[ "$model" != */* ]]; then
        var="FLEET_MODEL_$(echo "$model" | tr '[:lower:]-' '[:upper:]_')"
        mapped="${!var:-}"
        if [ -n "$mapped" ]; then
            echo "$mapped"
        else
            echo -e "${YELLOW}No OpenCode mapping for '${model}' (set ${var}=provider/model); using the platform default.${NC}" >&2
            echo ""
        fi
        return
    fi
    echo "$model"
}

# --- Project + fleet map ---
get_project_name() {
    local name
    name=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || basename "$(pwd)")
    echo "$name"
}

# upgrade an earlier map in place: the platform and the ref are now separate facts.
ensure_map_schema() {
    local fleet_map="$1" header tmp
    if [ ! -f "$fleet_map" ]; then
        return 0
    fi
    header=$(head -n 1 "$fleet_map")
    if [ "$header" != "agent_domain,uuid,awakened,task_theme,status" ]; then
        return 0
    fi
    tmp="${fleet_map}.tmp"
    {
        echo "agent_domain,session_ref,platform,awakened,task_theme,status"
        tail -n +2 "$fleet_map" \
            | awk -F',' 'BEGIN{OFS=","} NF>=5{print $1,$2,"claude",$3,$4,$5; next} {print}'
    } > "$tmp" && mv "$tmp" "$fleet_map"
    echo -e "${YELLOW}Migrated fleet map to the platform-aware schema: ${fleet_map}${NC}" >&2
}

resolve_fleet_map() {
    local fleet_map="${1:-}"
    if [ -z "$fleet_map" ]; then
        local project_name
        project_name=$(get_project_name)
        fleet_map="${AGENT_MEMORY_PATH}/shared-memory/${project_name}/fleet-map.csv"
    fi
    if [ ! -f "$fleet_map" ]; then
        local dir
        dir=$(dirname "$fleet_map")
        mkdir -p "$dir"
        local template="$(dirname "$0")/../templates/fleet-map-template.csv"
        if [ -f "$template" ]; then
            cp "$template" "$fleet_map"
        else
            echo "agent_domain,session_ref,platform,awakened,task_theme,status" > "$fleet_map"
        fi
        echo -e "${GREEN}Created fleet map: ${fleet_map}${NC}" >&2
    else
        ensure_map_schema "$fleet_map"
    fi
    echo "$fleet_map"
}

add_fleet_entry() {
    local fleet_map="$1"
    local domain="$2"
    local ref="$3"
    local task_theme="$4"
    local platform="$5"
    local date
    date=$(date '+%Y-%m-%d %H:%M')
    echo "${domain},${ref},${platform},${date},${task_theme},active" >> "$fleet_map"
}

update_fleet_status() {
    local fleet_map="$1"
    local ref="$2"
    local new_status="$3"

    if [ -f "$fleet_map" ]; then
        awk -F',' -v id="$ref" -v status="$new_status" 'BEGIN{OFS=","} $2==id{$6=status} {print}' "$fleet_map" > "${fleet_map}.tmp" && mv "${fleet_map}.tmp" "$fleet_map"
        echo -e "${GREEN}Fleet map updated: ${ref} → ${new_status}${NC}" >&2
    else
        echo -e "${YELLOW}Warning: Fleet map not found at ${fleet_map}${NC}" >&2
    fi
}

resolve_fleet_agents() {
    local fleet_map="${1:-}"
    if [ -n "$fleet_map" ]; then
        echo "$(dirname "$fleet_map")/fleet-agents.md"
    else
        local project_name
        project_name=$(get_project_name)
        echo "${AGENT_MEMORY_PATH}/shared-memory/${project_name}/fleet-agents.md"
    fi
}

get_agent_model() {
    local domain="$1"
    local fleet_agents="$2"
    [ -f "$fleet_agents" ] || { echo ""; return; }
    awk -F'|' -v domain="$domain" '
        {
            col2 = $2; gsub(/^[[:space:]]+|[[:space:]]+$/, "", col2)
            col5 = $5; gsub(/^[[:space:]]+|[[:space:]]+$/, "", col5)
            if (col2 == domain && col5 != "" && col5 !~ /^[-*]/) { print col5; exit }
        }
    ' "$fleet_agents"
}

agent_in_roster() {
    local domain="$1"
    local fleet_agents="$2"
    awk -F'|' -v domain="$domain" '
        { col2 = $2; gsub(/^[[:space:]]+|[[:space:]]+$/, "", col2)
          if (tolower(col2) == tolower(domain)) { found = 1 } }
        END { exit(found ? 0 : 1) }
    ' "$fleet_agents"
}

domain_to_folder() {
    # "Backend Django" → "backend-django"
    echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-'
}

verify_agent_exists() {
    local domain="$1"
    local fleet_agents="${2:-}"
    local folder
    folder=$(domain_to_folder "$domain")
    local agent_dir="${AGENT_MEMORY_PATH}/agent-${folder}"

    if [ -d "$agent_dir" ]; then
        return
    fi
    # A team member defined in the project's roster is a legitimate target even when its store
    # folder is not on this machine (the memory may be served rather than checked out).
    if [ -n "$fleet_agents" ] && [ -f "$fleet_agents" ] && agent_in_roster "$domain" "$fleet_agents"; then
        return
    fi

    echo -e "${RED}Error: Agent folder not found: ${agent_dir}${NC}" >&2
    echo -e "${YELLOW}Available agents:${NC}" >&2
    ls -d "${AGENT_MEMORY_PATH}"/agent-*/ 2>/dev/null | while read -r d; do
        basename "$d" | sed 's/^agent-/  /'
    done >&2
    exit 1
}

# --- The awakening sentence ---
# The capability is the same on every harness; the wording is not. Claude has slash commands,
# OpenCode has model-invoked skills, and a served layer is addressed by its MCP endpoint.
project_access() {
    local declared
    declared=$(read_declaration "PROJECT-ACCESS")
    if [ -z "$declared" ]; then
        declared=$(read_declaration "CODING-ACCESS")
    fi
    echo "${PROJECT_ACCESS:-${declared:-markdown}}"
}

project_mcp_url() {
    local declared
    declared=$(read_declaration "PROJECT-MCP-URL")
    if [ -z "$declared" ]; then
        declared=$(read_declaration "CODING-MCP-URL")
    fi
    echo "${PROJECT_MCP_URL:-${declared:-}}"
}

build_awaken_prompt() {
    local domain="$1"
    local user_prompt="$2"
    local after_awakening_instruction="${3:-respond to this request:}"
    local platform="${4:-$PLATFORM}"
    local folder
    folder=$(domain_to_folder "$domain")

    local access url open_line
    access=$(project_access)
    url=$(project_mcp_url)

    if [ "$access" = "mcp" ]; then
        if [ -n "$url" ]; then
            open_line="Awaken as the ${folder} agent: fetch the awaken-coder procedure from the served coding overlay (${url}) and follow it."
        else
            open_line="Awaken as the ${folder} agent: fetch the awaken-coder procedure from the served coding overlay and follow it."
        fi
    else
        case "$platform" in
            opencode) open_line="Awaken as the ${folder} agent: use the awaken-coder skill and follow it." ;;
            *)        open_line="Execute /awaken-coder ${folder}" ;;
        esac
    fi

    cat <<EOF
${open_line}

After awakening, ${after_awakening_instruction}

---
${user_prompt}
---
EOF
}

# --- The two adapters ---
# run_agent_turn PLATFORM new|resume REF MODEL PROMPT
# One blocking turn. These two arms are the entire platform-specific surface: the flags, the
# approval switch that makes the call non-interactive, and (on Claude) create and resume being
# different flags. Everything above this line is shared.
run_agent_turn() {
    local platform="$1"
    local mode="$2"
    local ref="$3"
    local model="$4"
    local prompt="$5"
    local -a args

    case "$platform" in
        opencode)
            # --auto is what makes a non-interactive run possible: a permission prompt has no
            # one to answer it, so anything not explicitly denied is approved.
            args=(opencode run --session "$ref" --auto)
            if [ -n "$model" ]; then
                args+=(--model "$model")
            fi
            args+=("$prompt")
            ;;
        claude)
            args=(claude --print)
            if [ "$mode" = "new" ]; then
                args+=(--session-id "$ref")
            else
                args+=(--resume "$ref")
            fi
            if [ -n "$model" ]; then
                args+=(--model "$model")
            fi
            args+=("$prompt")
            ;;
        *)
            echo -e "${RED}Error: unknown platform '${platform}' (FLEET_PLATFORM=claude|opencode)${NC}" >&2
            return 1
            ;;
    esac

    # A dry run prints the argv instead of executing it, which is how the branch is tested
    # without spawning an agent.
    if [ "${FLEET_DRY_RUN:-}" = "1" ]; then
        printf '%q ' "${args[@]}"
        echo
        return 0
    fi

    "${args[@]}"
}
