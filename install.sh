#!/bin/bash

# v1tamins installer
# Daily supplements for healthy code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Claude Code setup
echo -e "\n${CYAN}Setting up Claude Code...${NC}"
backup_if_exists ~/.claude/skills
backup_if_exists ~/.claude/hooks
ln -sf "$SCRIPT_DIR/claude/skills" ~/.claude/skills
ln -sf "$SCRIPT_DIR/claude/hooks" ~/.claude/hooks
echo -e "${GREEN}✓ Claude skills linked${NC}"
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
echo "  ~/.claude/skills  → $(ls ~/.claude/skills | wc -l | tr -d ' ') skills"
echo "  ~/.claude/hooks   → $(ls ~/.claude/hooks | wc -l | tr -d ' ') hooks"
echo "  ~/.cursor/commands → $(ls ~/.cursor/commands | wc -l | tr -d ' ') commands"
echo "  ~/.cursor/rules   → $(ls ~/.cursor/rules | wc -l | tr -d ' ') rules"
echo ""
echo -e "${YELLOW}Note: Restart Claude Code and Cursor to load the new configs.${NC}"
echo ""
echo "Required environment variables for MCP servers:"
echo "  LANGSMITH_API_KEY  - for LangSmith integration"
echo "  POSTMAN_API_KEY    - for Postman integration"
echo "  BRAVE_API_KEY      - for Brave Search integration"
