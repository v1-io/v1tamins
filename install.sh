#!/bin/bash

# v1tamins installer
# Daily supplements for healthy code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
AGENT_SKILLS_MODE="${V1TAMINS_AGENT_SKILLS_MODE:-symlink}"
CLEAN_LEGACY_CODEX_SKILLS=1

usage() {
    cat <<'EOF'
Usage: install.sh [options]

Options:
  This script installs compatibility surfaces only. For Codex, prefer the
  v1tamins plugin package under plugins/v1tamins/.

  --agent-skills-mode symlink|copy
      Install ~/.agents/skills entries as symlinks (default) or real copied
      directories. Use copy for runtimes that reject symlink targets outside
      ~/.agents/skills.
  --copy-agent-skills
      Shortcut for --agent-skills-mode copy.
  --no-clean-legacy-codex
      Do not remove old ~/.codex/skills symlinks that point into this checkout.
  -h, --help
      Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --agent-skills-mode)
            if [ "$#" -lt 2 ]; then
                echo "Missing value for --agent-skills-mode" >&2
                exit 1
            fi
            AGENT_SKILLS_MODE="$2"
            shift 2
            ;;
        --copy-agent-skills)
            AGENT_SKILLS_MODE="copy"
            shift
            ;;
        --no-clean-legacy-codex)
            CLEAN_LEGACY_CODEX_SKILLS=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

case "$AGENT_SKILLS_MODE" in
    symlink|copy)
        ;;
    *)
        echo "Invalid --agent-skills-mode: $AGENT_SKILLS_MODE" >&2
        echo "Expected: symlink or copy" >&2
        exit 1
        ;;
esac

echo -e "${CYAN}"
echo "██╗   ██╗  ██╗ ████████╗ █████╗ ███╗   ███╗██╗███╗   ██╗███████╗"
echo "██║   ██║ ███║ ╚══██╔══╝██╔══██╗████╗ ████║██║████╗  ██║██╔════╝"
echo "██║   ██║ ╚██║    ██║   ███████║██╔████╔██║██║██╔██╗ ██║███████╗"
echo "╚██╗ ██╔╝  ██║    ██║   ██╔══██║██║╚██╔╝██║██║██║╚██╗██║╚════██║"
echo " ╚████╔╝   ██║    ██║   ██║  ██║██║ ╚═╝ ██║██║██║ ╚████║███████║"
echo "  ╚═══╝    ╚═╝    ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝"
echo -e "${NC}"
echo "         Daily supplements for healthy code"
echo ""

# Create directories if they don't exist
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p ~/.agents
mkdir -p ~/.claude
mkdir -p ~/.cursor

# Backup existing configs
backup_if_exists() {
    if [ -e "$1" ] && [ ! -L "$1" ]; then
        echo -e "${YELLOW}Backing up existing $1 to $1.backup${NC}"
        mv "$1" "$1.backup"
    elif [ -L "$1" ]; then
        echo -e "${YELLOW}Removing existing symlink $1${NC}"
        rm "$1"
    fi
}

prepare_managed_directory() {
    local dir="$1"
    local backup_entry
    local backup_root

    if [ -L "$dir" ]; then
        echo -e "${YELLOW}Replacing directory symlink $dir with a real directory${NC}"
        rm "$dir"
    elif [ -e "$dir" ] && [ ! -d "$dir" ]; then
        echo -e "${YELLOW}Backing up existing $dir to $dir.backup${NC}"
        mv "$dir" "$dir.backup"
    fi

    mkdir -p "$dir"

    backup_root="$dir.backups/$(date +%Y%m%d%H%M%S)"
    for backup_entry in "$dir"/*.backup.*; do
        [ -e "$backup_entry" ] || continue
        mkdir -p "$backup_root"
        echo -e "${YELLOW}Moving nested backup $backup_entry to $backup_root/$(basename "$backup_entry")${NC}"
        mv "$backup_entry" "$backup_root/$(basename "$backup_entry")"
    done
}

backup_managed_entry() {
    local target_dir="$1"
    local name="$2"
    local label="$3"
    local target="$target_dir/$name"
    local backup_root="$target_dir.backups/$(date +%Y%m%d%H%M%S)"
    local backup="$backup_root/$name"

    mkdir -p "$backup_root"
    echo -e "${YELLOW}Backing up existing $label entry $target to $backup${NC}"
    mv "$target" "$backup"
}

cleanup_legacy_codex_skill_links() {
    local codex_skills_dir="$HOME/.codex/skills"
    local target
    local removed=0
    local entry

    [ "$CLEAN_LEGACY_CODEX_SKILLS" -eq 1 ] || return 0
    [ -d "$codex_skills_dir" ] || return 0

    echo -e "\n${CYAN}Cleaning legacy Codex skill links...${NC}"

    for entry in "$codex_skills_dir"/*; do
        [ -L "$entry" ] || continue

        target="$(readlink "$entry")"
        case "$target" in
            "$SCRIPT_DIR/.agents/skills"/*)
                echo -e "${YELLOW}Removing legacy Codex skill link $entry${NC}"
                rm "$entry"
                removed=$((removed + 1))
                ;;
        esac
    done

    if [ "$removed" -eq 0 ]; then
        echo -e "${GREEN}✓ No legacy v1tamins Codex skill links found${NC}"
    else
        echo -e "${GREEN}✓ Removed $removed legacy v1tamins Codex skill links${NC}"
    fi
}

cleanup_stale_agent_skill_entries() {
    local target_dir="$1"
    local entry
    local name
    local target
    local removed=0

    [ -d "$target_dir" ] || return 0

    echo -e "\n${CYAN}Cleaning stale managed agent skills...${NC}"

    for entry in "$target_dir"/*; do
        [ -e "$entry" ] || continue
        name="$(basename "$entry")"

        if [ -e "$SCRIPT_DIR/.agents/skills/$name" ]; then
            continue
        fi

        if [ -L "$entry" ]; then
            target="$(readlink "$entry")"
            case "$target" in
                "$SCRIPT_DIR/.agents/skills"/*)
                    echo -e "${YELLOW}Removing stale agent skill link $entry${NC}"
                    rm "$entry"
                    removed=$((removed + 1))
                    ;;
            esac
        elif [ -d "$entry" ] && [ -f "$entry/.v1tamins-managed-copy" ]; then
            echo -e "${YELLOW}Removing stale managed agent skill copy $entry${NC}"
            rm -rf "$entry"
            removed=$((removed + 1))
        fi
    done

    if [ "$removed" -eq 0 ]; then
        echo -e "${GREEN}✓ No stale managed agent skills found${NC}"
    else
        echo -e "${GREEN}✓ Removed $removed stale managed agent skill entries${NC}"
    fi
}

link_managed_entries() {
    local source_dir="$1"
    local target_dir="$2"
    local label="$3"
    local entry
    local name
    local target

    prepare_managed_directory "$target_dir"

    for entry in "$source_dir"/*; do
        [ -e "$entry" ] || continue

        name="$(basename "$entry")"
        target="$target_dir/$name"

        if [ -L "$target" ]; then
            rm "$target"
        elif [ -e "$target" ]; then
            backup_managed_entry "$target_dir" "$name" "$label"
        fi

        ln -s "$entry" "$target"
    done
}

copy_managed_entries() {
    local source_dir="$1"
    local target_dir="$2"
    local label="$3"
    local entry
    local name
    local target

    prepare_managed_directory "$target_dir"

    for entry in "$source_dir"/*; do
        [ -e "$entry" ] || continue

        name="$(basename "$entry")"
        target="$target_dir/$name"

        if [ -L "$target" ]; then
            rm "$target"
        elif [ -e "$target" ]; then
            if [ -f "$target/.v1tamins-managed-copy" ]; then
                rm -rf "$target"
            else
                backup_managed_entry "$target_dir" "$name" "$label"
            fi
        fi

        mkdir -p "$target"
        cp -R "$entry"/. "$target"/
        touch "$target/.v1tamins-managed-copy"
    done
}

# Shared agent / Codex skills setup
cleanup_legacy_codex_skill_links
echo -e "\n${CYAN}Setting up shared agent skills...${NC}"
cleanup_stale_agent_skill_entries ~/.agents/skills
if [ "$AGENT_SKILLS_MODE" = "copy" ]; then
    copy_managed_entries "$SCRIPT_DIR/.agents/skills" ~/.agents/skills "agent skill"
    echo -e "${GREEN}✓ Shared agent skills copied individually${NC}"
else
    link_managed_entries "$SCRIPT_DIR/.agents/skills" ~/.agents/skills "agent skill"
    echo -e "${GREEN}✓ Shared agent skills linked individually${NC}"
fi

# Claude Code setup
echo -e "\n${CYAN}Setting up Claude Code...${NC}"
backup_if_exists ~/.claude/hooks
link_managed_entries "$SCRIPT_DIR/claude/skills" ~/.claude/skills "Claude skill"
ln -sf "$SCRIPT_DIR/claude/hooks" ~/.claude/hooks
echo -e "${GREEN}✓ Claude skills linked individually${NC}"
echo -e "${GREEN}✓ Claude hooks linked${NC}"

# Cursor setup
echo -e "\n${CYAN}Setting up Cursor...${NC}"
backup_if_exists ~/.cursor/commands
backup_if_exists ~/.cursor/rules
ln -sf "$SCRIPT_DIR/cursor/commands" ~/.cursor/commands
ln -sf "$SCRIPT_DIR/cursor/rules" ~/.cursor/rules
echo -e "${GREEN}✓ Cursor commands linked${NC}"
echo -e "${GREEN}✓ Cursor rules linked${NC}"

# MCP config
echo -e "\n${CYAN}MCP Configuration...${NC}"
if [ -f ~/.cursor/mcp.json ]; then
    echo -e "${YELLOW}Existing mcp.json found at ~/.cursor/mcp.json${NC}"
    echo "You may want to manually merge: $SCRIPT_DIR/mcp/mcp.json"
else
    cp "$SCRIPT_DIR/mcp/mcp.json" ~/.cursor/mcp.json
    echo -e "${GREEN}✓ MCP config copied${NC}"
fi

echo -e "\n${GREEN}Installation complete!${NC}"
echo ""
echo "What's installed:"
echo "  ~/.agents/skills  → $(ls ~/.agents/skills | wc -l | tr -d ' ') skills ($AGENT_SKILLS_MODE mode)"
echo "  ~/.claude/skills  → $(ls ~/.claude/skills | wc -l | tr -d ' ') skills"
echo "  ~/.claude/hooks   → $(ls ~/.claude/hooks | wc -l | tr -d ' ') hooks"
echo "  ~/.cursor/commands → $(ls ~/.cursor/commands | wc -l | tr -d ' ') commands"
echo "  ~/.cursor/rules   → $(ls ~/.cursor/rules | wc -l | tr -d ' ') rules"
echo ""
echo -e "${YELLOW}Note: Restart Codex, Claude Code, and Cursor to load the new configs.${NC}"
echo ""
echo "Required environment variables for MCP servers:"
echo "  LANGSMITH_API_KEY  - for LangSmith integration"
echo "  POSTMAN_API_KEY    - for Postman integration"
echo "  BRAVE_API_KEY      - for Brave Search integration"
