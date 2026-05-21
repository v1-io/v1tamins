#!/usr/bin/env bash
# Human-in-the-loop reproduction loop.
# Copy this file, edit the prompts below, and run the copy.
# The agent runs the script; the user follows prompts in their terminal.
#
# Usage:
#   bash hitl-loop.template.sh
#
# Helpers:
#   step "instruction"          show instruction, wait for Enter
#   capture VAR "question"      read an answer into VAR
#
# Captured values are printed as KEY=VALUE for the agent to parse.

set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p " [Enter when done] " _
}

capture() {
  local var="$1"
  local question="$2"
  local answer

  printf '\n>>> %s\n' "$question"
  read -r -p " > " answer
  printf -v "$var" '%s' "$answer"
}

# --- edit below ---------------------------------------------------------

step "Open the application or command path that reproduces the issue."
capture REPRODUCED "Did the issue reproduce? (y/n)"
capture SYMPTOM "Paste the exact error message, wrong output, timing, or visible symptom:"

# --- edit above ---------------------------------------------------------

printf '\n--- Captured ---\n'
printf 'REPRODUCED=%s\n' "$REPRODUCED"
printf 'SYMPTOM=%s\n' "$SYMPTOM"
