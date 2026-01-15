#!/bin/bash
# Wrapper script for analyze_tool_errors.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ANALYZER_SCRIPT="$PROJECT_ROOT/services/analyst/scripts/analyze_tool_errors.py"

# Check if script exists
if [[ ! -f "$ANALYZER_SCRIPT" ]]; then
    echo "Error: Analyzer script not found at $ANALYZER_SCRIPT"
    exit 1
fi

# Check for LANGSMITH_API_KEY
if [[ -z "$LANGSMITH_API_KEY" ]]; then
    # Try to load from .env
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        # Safely extract LANGSMITH_API_KEY without eval/xargs (avoids command injection)
        LANGSMITH_API_KEY=$(grep -E '^LANGSMITH_API_KEY=' "$PROJECT_ROOT/.env" | cut -d'=' -f2-)
        export LANGSMITH_API_KEY
    fi
fi

if [[ -z "$LANGSMITH_API_KEY" ]]; then
    echo "Error: LANGSMITH_API_KEY not found in environment"
    exit 1
fi

# Activate virtual environment if available
if [[ -d "$PROJECT_ROOT/.venv" ]]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Run the analyzer with all passed arguments
python "$ANALYZER_SCRIPT" "$@"
