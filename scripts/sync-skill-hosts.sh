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
  - every public canonical skill has a plugins/v1tamins/skills/v1-<skill> mirror
  - plugin mirrors have v1-prefixed frontmatter names and no stale entries
  - the Codex plugin manifest, Codex marketplace manifest, Claude Code plugin
    manifest, and Claude Code marketplace manifest all parse as JSON

Options:
  --write   create missing Claude host symlinks, repair wrong symlinks, and refresh plugin mirrors
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
plugin_dir="$repo_root/plugins/v1tamins"
plugin_skills_dir="$plugin_dir/skills"
plugin_manifest="$plugin_dir/.codex-plugin/plugin.json"
marketplace_manifest="$repo_root/.agents/plugins/marketplace.json"
claude_plugin_manifest="$plugin_dir/.claude-plugin/plugin.json"
claude_marketplace_manifest="$repo_root/.claude-plugin/marketplace.json"

failures=0
warnings=0
runtime_names_file="$(mktemp "${TMPDIR:-/tmp}/v1tamins-runtime-names.XXXXXX")"
trap 'rm -f "$runtime_names_file"' EXIT

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

print_failure_summary() {
  printf '\n%d validation error(s), %d warning(s)\n' "$failures" "$warnings" >&2
}

require_dir() {
  local dir="$1"
  if [ ! -d "$dir" ]; then
    fail "missing directory: $(relpath "$dir")"
  fi
}

validate_skill_frontmatter() {
  local file="$1"
  local expected_name="$2"

  if ! command -v ruby >/dev/null 2>&1; then
    fail "ruby is required to parse YAML frontmatter"
    return 1
  fi

  if ruby -ryaml -rdate - "$file" "$expected_name" <<'RUBY'
path = ARGV.fetch(0)
expected_name = ARGV.fetch(1)
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

actual_name = data["name"].to_s.strip
unless actual_name == expected_name
  warn "#{path}: frontmatter name #{actual_name.inspect} must match directory #{expected_name.inspect}"
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

validate_json_file() {
  local file="$1"

  if ! command -v jq >/dev/null 2>&1; then
    fail "jq is required to parse JSON files"
    return 1
  fi

  if jq empty "$file" >/dev/null; then
    ok "$(relpath "$file") JSON"
  else
    fail "$(relpath "$file") JSON validation failed"
  fi
}

skill_frontmatter_name() {
  local file="$1"

  ruby -ryaml -rdate - "$file" <<'RUBY'
path = ARGV.fetch(0)
content = File.read(path)
match = content.match(/\A---\s*\n(.*?)\n---\s*\n/m)
exit 1 unless match

begin
  begin
    data = YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: false, filename: path)
  rescue ArgumentError
    data = YAML.safe_load(match[1], [Date, Time], [], false, path)
  end
rescue Psych::Exception
  exit 1
end

name = data.is_a?(Hash) ? data["name"].to_s.strip : ""
exit 1 if name.empty?
puts name
RUBY
}

refresh_runtime_names() {
  local skill_dir
  local skill_md
  local runtime_name

  : > "$runtime_names_file"

  while IFS= read -r skill_dir; do
    skill_md="$skill_dir/SKILL.md"
    runtime_name="$(skill_frontmatter_name "$skill_md" 2>/dev/null || true)"
    [ -n "$runtime_name" ] && printf '%s\n' "$runtime_name" >> "$runtime_names_file"
  done < <(find "$agent_skills_dir" -mindepth 1 -maxdepth 1 -type d ! -name '_*' ! -name '.*' -print | sort)

  sort -u "$runtime_names_file" -o "$runtime_names_file"
}

canonical_skill_exists_by_name() {
  local expected_name="$1"

  case "$expected_name" in
    _*|.*) return 1 ;;
  esac

  [ -d "$agent_skills_dir/$expected_name" ]
}

mirror_skill_to_plugin() {
  local skill_dir="$1"
  local skill_name
  local plugin_skill_name
  local target_dir
  local runtime_names=()
  local runtime_name

  skill_name="$(skill_frontmatter_name "$skill_dir/SKILL.md")"
  plugin_skill_name="v1-$skill_name"
  target_dir="$plugin_skills_dir/$plugin_skill_name"

  rm -rf "$target_dir"
  mkdir -p "$target_dir"
  cp -R "$skill_dir"/. "$target_dir"/
  find "$target_dir" -name '.DS_Store' -delete
  find "$target_dir" -type d -name '__pycache__' -prune -exec rm -rf {} +
  find "$target_dir" -type f -name '*.pyc' -delete

  while IFS= read -r runtime_name; do
    [ -n "$runtime_name" ] && runtime_names+=("$runtime_name")
  done < "$runtime_names_file"

  ruby - "$target_dir/SKILL.md" "$skill_name" "${runtime_names[@]}" <<'RUBY'
path = ARGV.fetch(0)
skill_name = ARGV.fetch(1)
runtime_names = ARGV.drop(2).uniq.sort_by { |name| -name.length }
plugin_skill_name = "v1-#{skill_name}"
content = File.read(path)

match = content.match(/\A---\s*\n(.*?)\n---\s*\n/m)
abort "#{path}: missing YAML frontmatter" unless match

frontmatter = match[1]
body = content[match[0].length..] || ""
frontmatter = frontmatter.sub(/^name:\s*#{Regexp.escape(skill_name)}\s*$/m, "name: #{plugin_skill_name}")

runtime_names.each do |name|
  prefixed = "v1-#{name}"
  frontmatter = frontmatter.gsub(%r{(?<![\w/-])/#{Regexp.escape(name)}(?![\w/-])}, "/#{prefixed}")
  frontmatter = frontmatter.gsub(%r{(?<![\w/-])\$#{Regexp.escape(name)}(?![\w/-])}, "$#{prefixed}")
  body = body.gsub(%r{(?<![\w/-])/#{Regexp.escape(name)}(?![\w/-])}, "/#{prefixed}")
  body = body.gsub(%r{(?<![\w/-])\$#{Regexp.escape(name)}(?![\w/-])}, "$#{prefixed}")
  body = body.gsub("invoke `#{name}`", "invoke `#{prefixed}`")
  body = body.gsub("invoke #{name}", "invoke #{prefixed}")
end

File.write(path, "---\n#{frontmatter}\n---\n#{body}")
RUBY

  if [ -f "$target_dir/agents/openai.yaml" ]; then
    ruby - "$target_dir/agents/openai.yaml" "${runtime_names[@]}" <<'RUBY'
path = ARGV.fetch(0)
runtime_names = ARGV.drop(1).uniq.sort_by { |name| -name.length }
content = File.read(path)

runtime_names.each do |name|
  prefixed = "v1-#{name}"
  content = content.gsub(%r{(?<![\w/-])/#{Regexp.escape(name)}(?![\w/-])}, "/#{prefixed}")
  content = content.gsub(%r{(?<![\w/-])\$#{Regexp.escape(name)}(?![\w/-])}, "$#{prefixed}")
  content = content.gsub("invoke `#{name}`", "invoke `#{prefixed}`")
  content = content.gsub("invoke #{name}", "invoke #{prefixed}")
end

File.write(path, content)
RUBY
  fi

  ok "plugins/v1tamins/skills/$plugin_skill_name mirror"
}

sync_plugin_mirror() {
  local skill_dir="$1"
  local skill_name
  local plugin_skill_name
  local plugin_skill_dir
  local skill_md

  if ! skill_name="$(skill_frontmatter_name "$skill_dir/SKILL.md")"; then
    fail "cannot determine skill name from $(relpath "$skill_dir/SKILL.md")"
    return
  fi

  plugin_skill_name="v1-$skill_name"
  plugin_skill_dir="$plugin_skills_dir/$plugin_skill_name"
  skill_md="$plugin_skill_dir/SKILL.md"

  if [ "$write" = true ]; then
    mirror_skill_to_plugin "$skill_dir"
  fi

  if [ ! -f "$skill_md" ]; then
    fail "missing Codex plugin skill mirror: plugins/v1tamins/skills/$plugin_skill_name"
    return
  fi

  validate_skill_frontmatter "$skill_md" "$plugin_skill_name"

  if [ -f "$plugin_skill_dir/agents/openai.yaml" ]; then
    validate_yaml_file "$plugin_skill_dir/agents/openai.yaml"
  fi
}

check_for_stale_plugin_entries() {
  local entry
  local plugin_skill_name
  local skill_name

  if [ ! -d "$plugin_skills_dir" ]; then
    return
  fi

  while IFS= read -r entry; do
    plugin_skill_name="$(basename "$entry")"
    case "$plugin_skill_name" in
      v1-*)
        skill_name="${plugin_skill_name#v1-}"
        ;;
      *)
        fail "Codex plugin skill mirror must use v1- prefix: plugins/v1tamins/skills/$plugin_skill_name"
        continue
        ;;
    esac

    if ! canonical_skill_exists_by_name "$skill_name"; then
      if [ "$write" = true ]; then
        rm -rf "$entry"
        ok "removed stale Codex plugin skill mirror plugins/v1tamins/skills/$plugin_skill_name"
      else
        fail "stale Codex plugin skill mirror without canonical skill: plugins/v1tamins/skills/$plugin_skill_name"
      fi
    fi
  done < <(find "$plugin_skills_dir" -mindepth 1 -maxdepth 1 -type d ! -name '.*' -print 2>/dev/null | sort)
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
  done < <(find "$claude_skills_dir" -mindepth 1 -maxdepth 1 ! -name '.DS_Store' ! -name '_*' ! -name '.*' -print | sort)
}

main() {
  require_dir "$agent_skills_dir"
  require_dir "$claude_skills_dir"

  if [ -f "$plugin_manifest" ]; then
    validate_json_file "$plugin_manifest"
  else
    fail "missing Codex plugin manifest: plugins/v1tamins/.codex-plugin/plugin.json"
  fi

  if [ -f "$marketplace_manifest" ]; then
    validate_json_file "$marketplace_manifest"
  else
    fail "missing Codex marketplace manifest: .agents/plugins/marketplace.json"
  fi

  if [ -f "$claude_plugin_manifest" ]; then
    validate_json_file "$claude_plugin_manifest"
  else
    fail "missing Claude Code plugin manifest: plugins/v1tamins/.claude-plugin/plugin.json"
  fi

  if [ -f "$claude_marketplace_manifest" ]; then
    validate_json_file "$claude_marketplace_manifest"
  else
    fail "missing Claude Code marketplace manifest: .claude-plugin/marketplace.json"
  fi

  if [ "$failures" -ne 0 ]; then
    print_failure_summary
    exit 1
  fi

  refresh_runtime_names

  while IFS= read -r skill_dir; do
    local skill_md="$skill_dir/SKILL.md"
    local openai_yaml="$skill_dir/agents/openai.yaml"

    if [ -f "$skill_md" ]; then
      validate_skill_frontmatter "$skill_md" "$(basename "$skill_dir")"
    else
      fail "missing SKILL.md: $(relpath "$skill_md")"
    fi

    if [ -f "$openai_yaml" ]; then
      validate_yaml_file "$openai_yaml"
    fi

    sync_claude_host_entry "$skill_dir"
  done < <(find "$agent_skills_dir" -mindepth 1 -maxdepth 1 -type d ! -name '_*' ! -name '.*' -print | sort)

  while IFS= read -r skill_dir; do
    sync_plugin_mirror "$skill_dir"
  done < <(find "$agent_skills_dir" -mindepth 1 -maxdepth 1 -type d ! -name '_*' ! -name '.*' -print | sort)

  check_for_stale_claude_entries
  check_for_stale_plugin_entries

  if [ "$failures" -ne 0 ]; then
    print_failure_summary
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
