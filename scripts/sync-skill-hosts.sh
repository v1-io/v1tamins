#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/sync-skill-hosts.sh [--write] [--verbose]

Validate canonical shared skills and their host surfaces.

Checks:
  - every .agents/skills/<skill>/SKILL.md has parseable YAML frontmatter
  - required frontmatter keys are present: name, description
  - optional .agents/skills/<skill>/agents/openai.yaml files parse as YAML
  - every canonical skill has a claude/skills/<skill> host entry
  - Claude host symlinks point back to ../../.agents/skills/<skill>

Options:
  --write   create missing Claude host symlinks and repair wrong symlinks
  --verbose print each successful check
  -h, --help
EOF
}

write=false
verbose=false

for arg in "$@"; do
  case "$arg" in
    --write)
      write=true
      ;;
    --verbose)
      verbose=true
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
agent_skills_dir="$repo_root/.agents/skills"
claude_skills_dir="$repo_root/claude/skills"

failures=0
warnings=0

relpath() {
  local path="$1"
  printf '%s' "${path#"$repo_root"/}"
}

ok() {
  if [ "$verbose" = true ]; then
    printf 'ok: %s\n' "$1"
  fi
}

warn() {
  warnings=$((warnings + 1))
  printf 'WARN: %s\n' "$1" >&2
}

fail() {
  failures=$((failures + 1))
  printf 'ERROR: %s\n' "$1" >&2
}

require_dir() {
  local dir="$1"
  if [ ! -d "$dir" ]; then
    fail "missing directory: $(relpath "$dir")"
    return 1
  fi
}

validate_skill_frontmatter() {
  local file="$1"

  if ! command -v ruby >/dev/null 2>&1; then
    fail "ruby is required to parse YAML frontmatter"
    return 1
  fi

  if ruby -ryaml -rdate - "$file" <<'RUBY'
path = ARGV.fetch(0)
content = File.read(path)

unless content.match?(/\A---\s*\n/)
  warn "#{path}: missing opening YAML frontmatter delimiter"
  exit 1
end

match = content.match(/\A---\s*\n(.*?)\n---\s*\n/m)
unless match
  warn "#{path}: missing closing YAML frontmatter delimiter"
  exit 1
end

frontmatter = match[1]

begin
  begin
    data = YAML.safe_load(frontmatter, permitted_classes: [Date, Time], aliases: false, filename: path)
  rescue ArgumentError
    data = YAML.safe_load(frontmatter, [Date, Time], [], false, path)
  end
rescue Psych::Exception => e
  warn "#{path}: invalid YAML frontmatter: #{e.message}"
  exit 1
end

unless data.is_a?(Hash)
  warn "#{path}: YAML frontmatter must be a mapping"
  exit 1
end

missing = %w[name description].select do |key|
  value = data[key]
  value.nil? || value.to_s.strip.empty?
end

unless missing.empty?
  warn "#{path}: missing required frontmatter key(s): #{missing.join(', ')}"
  exit 1
end
RUBY
  then
    ok "$(relpath "$file") frontmatter"
  else
    fail "$(relpath "$file") frontmatter validation failed"
  fi
}

validate_yaml_file() {
  local file="$1"

  if ! command -v ruby >/dev/null 2>&1; then
    fail "ruby is required to parse YAML files"
    return 1
  fi

  if ruby -ryaml -rdate - "$file" <<'RUBY'
path = ARGV.fetch(0)

begin
  content = File.read(path)
  begin
    YAML.safe_load(content, permitted_classes: [Date, Time], aliases: false, filename: path)
  rescue ArgumentError
    YAML.safe_load(content, [Date, Time], [], false, path)
  end
rescue Psych::Exception => e
  warn "#{path}: invalid YAML: #{e.message}"
  exit 1
end
RUBY
  then
    ok "$(relpath "$file") YAML"
  else
    fail "$(relpath "$file") YAML validation failed"
  fi
}

sync_claude_host_entry() {
  local skill_dir="$1"
  local skill_name
  local host_entry
  local expected_target

  skill_name="$(basename "$skill_dir")"
  host_entry="$claude_skills_dir/$skill_name"
  expected_target="../../.agents/skills/$skill_name"

  if [ -L "$host_entry" ]; then
    local actual_target
    actual_target="$(readlink "$host_entry")"

    if [ "$actual_target" = "$expected_target" ]; then
      ok "claude/skills/$skill_name symlink"
    elif [ "$write" = true ]; then
      ln -sfn "$expected_target" "$host_entry"
      ok "repaired claude/skills/$skill_name symlink"
    else
      fail "claude/skills/$skill_name points to $actual_target; expected $expected_target"
    fi
  elif [ -e "$host_entry" ]; then
    if [ -f "$host_entry/SKILL.md" ]; then
      warn "claude/skills/$skill_name is a directory mirror; leaving it untouched"
    else
      fail "claude/skills/$skill_name exists but is not a symlink or skill mirror"
    fi
  elif [ "$write" = true ]; then
    mkdir -p "$claude_skills_dir"
    ln -s "$expected_target" "$host_entry"
    ok "created claude/skills/$skill_name symlink"
  else
    fail "missing Claude host entry: claude/skills/$skill_name"
  fi
}

check_for_stale_claude_entries() {
  local entry
  local skill_name

  if [ ! -d "$claude_skills_dir" ]; then
    return
  fi

  while IFS= read -r entry; do
    skill_name="$(basename "$entry")"
    if [ ! -d "$agent_skills_dir/$skill_name" ]; then
      fail "stale Claude host entry without canonical skill: claude/skills/$skill_name"
    fi
  done < <(find "$claude_skills_dir" -mindepth 1 -maxdepth 1 ! -name '.DS_Store' -print | sort)
}

main() {
  require_dir "$agent_skills_dir"
  require_dir "$claude_skills_dir"

  if [ "$failures" -ne 0 ]; then
    exit 1
  fi

  while IFS= read -r skill_dir; do
    local skill_md="$skill_dir/SKILL.md"
    local openai_yaml="$skill_dir/agents/openai.yaml"

    if [ -f "$skill_md" ]; then
      validate_skill_frontmatter "$skill_md"
    else
      fail "missing SKILL.md: $(relpath "$skill_md")"
    fi

    if [ -f "$openai_yaml" ]; then
      validate_yaml_file "$openai_yaml"
    fi

    sync_claude_host_entry "$skill_dir"
  done < <(find "$agent_skills_dir" -mindepth 1 -maxdepth 1 -type d -print | sort)

  check_for_stale_claude_entries

  if [ "$failures" -ne 0 ]; then
    printf '\n%d validation error(s), %d warning(s)\n' "$failures" "$warnings" >&2
    if [ "$write" != true ]; then
      printf 'Run scripts/sync-skill-hosts.sh --write to create missing symlinks or repair wrong symlinks.\n' >&2
    fi
    exit 1
  fi

  printf '\nSkill host sync checks passed'
  if [ "$warnings" -ne 0 ]; then
    printf ' with %d warning(s)' "$warnings"
  fi
  printf '.\n'
}

main "$@"
