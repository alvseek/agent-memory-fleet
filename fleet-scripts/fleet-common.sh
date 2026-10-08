#!/bin/bash
# fleet-common.sh — Shared functions for fleet agent scripts
# Source this file: source "$(dirname "$0")/fleet-common.sh"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Resolve Agent Memory Path (cross-platform, forward slashes for bash) ---
resolve_agent_memory_path() {
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) echo "/c/Users/$(whoami)/.claude/@agent-memory" ;;
        Darwin)               echo "/Users/$(whoami)/.claude/@agent-memory" ;;
        *)                    echo "/home/$(whoami)/.claude/@agent-memory" ;;
    esac
}

AGENT_MEMORY_PATH=$(resolve_agent_memory_path)

# --- Shared Functions ---

is_uuid() {
    [[ "$1" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]
}

get_project_name() {
    local name
    name=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || basename "$(pwd)")
    echo "$name"
}

resolve_fleet_map() {
    local fleet_map="${1:-}"
    if [ -z "$fleet_map" ]; then
        local project_name
        project_name=$(get_project_name)
        fleet_map="${AGENT_MEMORY_PATH}/shared-memory/${project_name}/fleet-map.csv"
    fi
    # Create fleet map from template if it doesn't exist
    if [ ! -f "$fleet_map" ]; then
        local dir
        dir=$(dirname "$fleet_map")
        mkdir -p "$dir"
        local template="$(dirname "$0")/../templates/fleet-map-template.csv"
        if [ -f "$template" ]; then
            cp "$template" "$fleet_map"
        else
            echo "agent_domain,uuid,awakened,task_theme,status" > "$fleet_map"
        fi
        echo -e "${GREEN}Created fleet map: ${fleet_map}${NC}" >&2
    fi
    echo "$fleet_map"
}

add_fleet_entry() {
    local fleet_map="$1"
    local domain="$2"
    local uuid="$3"
    local task_theme="$4"
    local date
    date=$(date '+%Y-%m-%d %H:%M')
    echo "${domain},${uuid},${date},${task_theme},active" >> "$fleet_map"
}

update_fleet_status() {
    local fleet_map="$1"
    local uuid="$2"
    local new_status="$3"

    if [ -f "$fleet_map" ]; then
        awk -F',' -v id="$uuid" -v status="$new_status" 'BEGIN{OFS=","} $2==id{$5=status} {print}' "$fleet_map" > "${fleet_map}.tmp" && mv "${fleet_map}.tmp" "$fleet_map"
        echo -e "${GREEN}Fleet map updated: ${uuid} → ${new_status}${NC}" >&2
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

domain_to_folder() {
    # "Backend Django" → "backend-django"
    echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' ' '-'
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

verify_agent_exists() {
    local domain="$1"
    local folder
    folder=$(domain_to_folder "$domain")
    local agent_dir="${AGENT_MEMORY_PATH}/agent-${folder}"

    if [ ! -d "$agent_dir" ]; then
        echo -e "${RED}Error: Agent folder not found: ${agent_dir}${NC}" >&2
        echo -e "${YELLOW}Available agents:${NC}" >&2
        ls -d "${AGENT_MEMORY_PATH}"/agent-*/ 2>/dev/null | while read -r d; do
            basename "$d" | sed 's/^agent-/  /'
        done >&2
        exit 1
    fi
}

build_awaken_prompt() {
    local domain="$1"
    local user_prompt="$2"
    local after_awakening_instruction="${3:-respond to this request:}"
    local folder
    folder=$(domain_to_folder "$domain")

    # Reaching the coding overlay resolves through its access declaration, which the caller reads
    # ([CODING-ACCESS] / [CODING-MCP-URL]). The shell has no instructions file, so it reads the
    # same env var the overlay's installer writes; an absent value means `markdown`.
    local coding_access="${CODING_ACCESS:-markdown}"
    local open_line
    if [ "$coding_access" = "mcp" ]; then
        open_line="Fetch the awaken-coder procedure from the served coding overlay ([CODING-MCP-URL]) and follow it for ${folder}"
    else
        open_line="Execute /awaken-coder ${folder}"
    fi

    cat <<EOF
${open_line}

After awakening, ${after_awakening_instruction}

---
${user_prompt}
---
EOF
}
