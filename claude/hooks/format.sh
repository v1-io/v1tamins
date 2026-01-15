#!/bin/bash

# Universal code formatter for Claude Code PostToolUse hook
# Automatically formats Python and TypeScript/JavaScript files after edits
# Set CLAUDE_FORMAT_DEBUG=1 to enable debug logging

# Read JSON input from stdin
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

debug_log() {
  if [[ "${CLAUDE_FORMAT_DEBUG:-0}" == "1" ]]; then
    echo "[format.sh] $1" >&2
  fi
}

# Exit early if no file path
if [[ -z "$file_path" || "$file_path" == "null" ]]; then
  debug_log "No file path provided, skipping"
  exit 0
fi

# Exit if file doesn't exist (might have been deleted)
if [[ ! -f "$file_path" ]]; then
  debug_log "File does not exist: $file_path"
  exit 0
fi

# Python formatting with black
if [[ "$file_path" =~ \.py$ ]]; then
  if command -v black &> /dev/null; then
    debug_log "Formatting Python file: $file_path"
    if [[ "${CLAUDE_FORMAT_DEBUG:-0}" == "1" ]]; then
      black --quiet "$file_path"
    else
      black --quiet "$file_path" 2>/dev/null
    fi
  else
    debug_log "black not found, skipping Python formatting"
  fi
fi

# TypeScript/JavaScript formatting with prettier
if [[ "$file_path" =~ \.(ts|tsx|js|jsx)$ ]]; then
  debug_log "Formatting TypeScript/JavaScript file: $file_path"
  # Use project's prettier if available, otherwise global npx
  if [[ -f "$CLAUDE_PROJECT_DIR/web/node_modules/.bin/prettier" ]]; then
    if [[ "${CLAUDE_FORMAT_DEBUG:-0}" == "1" ]]; then
      "$CLAUDE_PROJECT_DIR/web/node_modules/.bin/prettier" --write "$file_path"
    else
      "$CLAUDE_PROJECT_DIR/web/node_modules/.bin/prettier" --write "$file_path" 2>/dev/null >/dev/null
    fi
  elif command -v npx &> /dev/null; then
    if [[ "${CLAUDE_FORMAT_DEBUG:-0}" == "1" ]]; then
      npx prettier --write "$file_path"
    else
      npx prettier --write "$file_path" 2>/dev/null >/dev/null
    fi
  else
    debug_log "prettier not found, skipping JS/TS formatting"
  fi
fi

exit 0
