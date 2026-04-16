#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/.agents/skills"
CLAUDE_DIR="$ROOT_DIR/claude/skills"
WRITE=0

usage() {
  cat <<'USAGE'
Usage: scripts/sync-skill-hosts.sh [--write]

Checks shared skills for:
  - SKILL.md frontmatter name/description
  - directory name matching frontmatter name, allowing legacy leading underscore directories
  - Claude compatibility symlink targets
  - required agents/openai.yaml fields when metadata exists

With --write, creates missing Claude symlinks and missing agents/openai.yaml files.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ "${1:-}" == "--write" ]]; then
  WRITE=1
elif [[ $# -gt 0 ]]; then
  usage >&2
  exit 2
fi

extract_scalar() {
  local key="$1"
  local file="$2"

  awk -v key="$key" '
    $0 == "---" { fence++; next }
    fence == 1 && $0 ~ "^" key ":[[:space:]]*" {
      sub("^" key ":[[:space:]]*", "")
      print
      exit
    }
    fence == 2 { exit }
  ' "$file" | sed 's/^["'\'']//; s/["'\'']$//'
}

extract_description() {
  local file="$1"

  awk '
    $0 == "---" {
      if (in_block) {
        print description
        exit
      }
      fence++
      next
    }

    fence != 1 { next }

    in_block && $0 ~ /^[A-Za-z0-9_-]+:[[:space:]]*/ {
      print description
      exit
    }

    in_block {
      sub(/^[[:space:]]+/, "")
      description = description (description == "" ? "" : " ") $0
      next
    }

    $0 ~ /^description:[[:space:]]*[>|]/ {
      in_block = 1
      next
    }

    $0 ~ /^description:[[:space:]]*/ {
      sub(/^description:[[:space:]]*/, "")
      print
      exit
    }
  ' "$file" | tr -s ' ' | sed 's/^ *//; s/ *$//; s/^["'\'']//; s/["'\'']$//'
}

yaml_quote() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/^/"/; s/$/"/'
}

titleize() {
  printf '%s\n' "$1" |
    tr '_-' '  ' |
    awk '{ for (i = 1; i <= NF; i++) $i = toupper(substr($i, 1, 1)) substr($i, 2); print }'
}

short_description() {
  local description="$1"
  description="${description#Use when }"
  description="${description%%. Triggers on*}"
  description="${description%% Triggers on*}"
  printf '%s' "$description" | cut -c 1-120
}

expected_openai_yaml() {
  local skill_name="$1"
  local description="$2"
  local display_name short

  display_name="$(titleize "$skill_name")"
  short="$(short_description "$description")"

  cat <<YAML
interface:
  display_name: $(yaml_quote "$display_name")
  short_description: $(yaml_quote "$short")
  default_prompt: $(yaml_quote "Use \$$skill_name for this task.")

policy:
  allow_implicit_invocation: true
YAML
}

failures=0

while IFS= read -r skill_md; do
  skill_dir="$(dirname "$skill_md")"
  skill_dir_name="$(basename "$skill_dir")"
  frontmatter_name="$(extract_scalar name "$skill_md")"
  description="$(extract_description "$skill_md")"

  if [[ -z "$frontmatter_name" || -z "$description" ]]; then
    printf 'Missing name or description: %s\n' "${skill_md#$ROOT_DIR/}" >&2
    failures=1
    continue
  fi

  if [[ "$frontmatter_name" != "$skill_dir_name" && "$frontmatter_name" != "${skill_dir_name#_}" ]]; then
    printf 'Name mismatch: %s declares %s\n' "${skill_md#$ROOT_DIR/}" "$frontmatter_name" >&2
    failures=1
  fi

  if [[ ! "$frontmatter_name" =~ ^[a-z0-9][a-z0-9-]{0,63}$ ]]; then
    printf 'Invalid skill name: %s\n' "$frontmatter_name" >&2
    failures=1
  fi

  if (( ${#description} > 1024 )); then
    printf 'Description too long: %s (%s chars)\n' "$frontmatter_name" "${#description}" >&2
    failures=1
  fi

  claude_link="$CLAUDE_DIR/$skill_dir_name"
  claude_target="../../.agents/skills/$skill_dir_name"
  if [[ ! -L "$claude_link" || "$(readlink "$claude_link" 2>/dev/null)" != "$claude_target" ]]; then
    if (( WRITE )); then
      mkdir -p "$CLAUDE_DIR"
      if [[ -e "$claude_link" && ! -L "$claude_link" ]]; then
        printf 'Refusing to replace non-symlink Claude entry: %s\n' "${claude_link#$ROOT_DIR/}" >&2
        failures=1
        continue
      fi
      rm -rf "$claude_link"
      ln -s "$claude_target" "$claude_link"
      printf 'Wrote Claude symlink: %s\n' "${claude_link#$ROOT_DIR/}"
    else
      printf 'Missing or stale Claude symlink: %s\n' "${claude_link#$ROOT_DIR/}" >&2
      failures=1
    fi
  fi

  openai_yaml="$skill_dir/agents/openai.yaml"
  if [[ -f "$openai_yaml" ]]; then
    for required_field in "display_name:" "short_description:" "default_prompt:" "allow_implicit_invocation:"; do
      if ! grep -q "$required_field" "$openai_yaml"; then
        printf 'OpenAI metadata missing %s %s\n' "$required_field" "${openai_yaml#$ROOT_DIR/}" >&2
        failures=1
      fi
    done
  elif (( WRITE )); then
    mkdir -p "$skill_dir/agents"
    expected_openai_yaml "$frontmatter_name" "$description" > "$openai_yaml"
    printf 'Wrote OpenAI metadata: %s\n' "${openai_yaml#$ROOT_DIR/}"
  fi
done < <(find "$SKILLS_DIR" -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort)

if (( failures )); then
  exit 1
fi

printf 'Skill host checks passed.\n'
