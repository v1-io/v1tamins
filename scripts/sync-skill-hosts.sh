#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/sync-skill-hosts.sh [--write] [--verbose]

Validate the v1tamins plugin package.

Checks:
  - plugin and marketplace manifests parse as JSON
  - plugins/v1tamins/skills/v1-*/SKILL.md files have parseable YAML frontmatter
  - each skill frontmatter name matches its v1-* directory
  - optional agents/openai.yaml files parse as YAML
  - plugin-distributed skills use the v1- prefix
  - plugin skills do not reference known v1tamins skills by legacy bare names
  - root SKILL.md local links and required bundled asset references resolve
  - distributed helper snippets avoid checkout-only executable paths and host-specific plugin cache paths
  - legacy tracked .agents/skills mirrors are absent

Options:
  --write   accepted for backward compatibility; validation only
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
legacy_agent_skills_dir="$repo_root/.agents/skills"
plugin_dir="$repo_root/plugins/v1tamins"
plugin_skills_dir="$plugin_dir/skills"
plugin_manifest="$plugin_dir/.codex-plugin/plugin.json"
marketplace_manifest="$repo_root/.agents/plugins/marketplace.json"
claude_plugin_manifest="$plugin_dir/.claude-plugin/plugin.json"
claude_marketplace_manifest="$repo_root/.claude-plugin/marketplace.json"

failures=0

relpath() {
  local path="$1"
  printf '%s' "${path#"$repo_root"/}"
}

ok() {
  if [ "$verbose" = true ]; then
    printf 'ok: %s\n' "$1"
  fi
}

fail() {
  failures=$((failures + 1))
  printf 'ERROR: %s\n' "$1" >&2
}

print_failure_summary() {
  printf '\n%d validation error(s)\n' "$failures" >&2
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

unless actual_name.start_with?("v1-")
  warn "#{path}: plugin-distributed skill names must use the v1- prefix"
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

validate_plugin_manifest() {
  if validate_json_file "$plugin_manifest"; then
    local skills_path
    skills_path="$(jq -r '.skills // empty' "$plugin_manifest")"
    if [ "$skills_path" != "./skills/" ]; then
      fail "$(relpath "$plugin_manifest") must set skills to ./skills/"
    fi
  fi
}

validate_marketplace_manifest() {
  if validate_json_file "$marketplace_manifest"; then
    if ! jq -e '.plugins[] | select(.name == "v1tamins" and .source.path == "./plugins/v1tamins")' "$marketplace_manifest" >/dev/null; then
      fail "$(relpath "$marketplace_manifest") must expose v1tamins from ./plugins/v1tamins"
    fi
  fi

  if validate_json_file "$claude_marketplace_manifest"; then
    if ! jq -e '.plugins[] | select(.name == "v1tamins" and .source == "./plugins/v1tamins")' "$claude_marketplace_manifest" >/dev/null; then
      fail "$(relpath "$claude_marketplace_manifest") must expose v1tamins from ./plugins/v1tamins"
    fi
  fi
}

validate_no_legacy_agent_skills() {
  local tracked_legacy

  tracked_legacy="$(git -C "$repo_root" ls-files -- .agents/skills 2>/dev/null || true)"
  if [ -n "$tracked_legacy" ]; then
    fail "legacy tracked skill mirror exists under $(relpath "$legacy_agent_skills_dir")"
  else
    ok "legacy tracked .agents/skills mirror absent"
  fi
}

validate_skill_references() {
  if ! command -v ruby >/dev/null 2>&1; then
    fail "ruby is required to validate skill references"
    return 1
  fi

  if ruby - "$plugin_skills_dir" "$repo_root" <<'RUBY'
skills_dir = ARGV.fetch(0)
repo_root = ARGV.fetch(1)
skill_names = Dir.glob(File.join(skills_dir, "v1-*"))
  .select { |path| File.directory?(path) }
  .map { |path| File.basename(path).delete_prefix("v1-") }
  .reject { |name| name.start_with?("_") }
  .sort_by { |name| -name.length }

name_pattern = Regexp.union(skill_names)
failures = []

def rel(path, root)
  path.delete_prefix("#{root}/")
end

Dir.glob(File.join(skills_dir, "v1-*", "**", "*.{md,yaml}")).sort.each do |path|
  next unless File.file?(path)
  next if path.split(File::SEPARATOR).any? { |part| part.start_with?("v1-_") }

  File.readlines(path).each_with_index do |line, index|
    line_no = index + 1

    line.scan(%r{(?<![\w/-])/(#{name_pattern})(?![\w/-])}) do |match|
      bare_name = match.fetch(0)
      failures << "#{rel(path, repo_root)}:#{line_no}: use /v1-#{bare_name} instead of /#{bare_name}"
    end

    line.scan(/(?<![\w-])\$(#{name_pattern})(?![\w-])/) do |match|
      bare_name = match.fetch(0)
      failures << "#{rel(path, repo_root)}:#{line_no}: use $v1-#{bare_name} instead of $#{bare_name}"
    end

    next unless line.match?(/\b(invoke|recommend|recommended|fall back|fallback|chains? to|run|use|using)\b/i)

    line.scan(/`(#{name_pattern})`/) do |match|
      bare_name = match.fetch(0)
      failures << "#{rel(path, repo_root)}:#{line_no}: use `v1-#{bare_name}` instead of `#{bare_name}`"
    end
  end
end

if failures.any?
  warn failures.join("\n")
  exit 1
end
RUBY
  then
    ok "plugin skill references"
  else
    fail "plugin skill reference validation failed"
  fi
}

validate_skill_assets() {
  if ! command -v ruby >/dev/null 2>&1; then
    fail "ruby is required to validate skill asset references"
    return 1
  fi

  if ruby - "$plugin_skills_dir" "$repo_root" <<'RUBY'
skills_dir = ARGV.fetch(0)
repo_root = ARGV.fetch(1)
failures = []

def rel(path, root)
  path.delete_prefix("#{root}/")
end

def existing_path?(skill_dir, repo_root, target)
  return true if target.empty? || target.start_with?("#")
  return true if target.match?(%r{\A[a-z][a-z0-9+.-]*:}i)

  [File.expand_path(target, skill_dir), File.expand_path(target, repo_root)].any? do |candidate|
    File.exist?(candidate)
  end
end

Dir.glob(File.join(skills_dir, "v1-*", "SKILL.md")).sort.each do |path|
  next if path.split(File::SEPARATOR).any? { |part| part.start_with?("v1-_") }

  skill_dir = File.dirname(path)
  in_fence = false

  File.readlines(path).each_with_index do |line, index|
    line_no = index + 1

    if line.start_with?("```")
      in_fence = !in_fence
      next
    end

    unless in_fence
      line.scan(/\[[^\]]+\]\(([^)]+)\)/) do |match|
        target = match.fetch(0).split("#", 2).first
        unless existing_path?(skill_dir, repo_root, target)
          failures << "#{rel(path, repo_root)}:#{line_no}: missing linked asset #{target}"
        end
      end

      if line.match?(/\b(read|run|use|follow|following|helper|starting point)\b/i)
        line.scan(/`((?:references?|scripts)\/[^`\s]+)`/) do |match|
          target = match.fetch(0)
          unless existing_path?(skill_dir, repo_root, target)
            failures << "#{rel(path, repo_root)}:#{line_no}: missing referenced asset #{target}"
          end
        end
      end
    end

    line.scan(%r{\$SKILL_(?:ROOT|DIR)/((?:references?|scripts)/[A-Za-z0-9._/-]+)}) do |match|
      target = match.fetch(0)
      unless existing_path?(skill_dir, repo_root, target)
        failures << "#{rel(path, repo_root)}:#{line_no}: missing bundled asset #{target}"
      end
    end
  end
end

if failures.any?
  warn failures.join("\n")
  exit 1
end
RUBY
  then
    ok "plugin skill asset references"
  else
    fail "plugin skill asset validation failed"
  fi
}

validate_portable_host_paths() {
  if ! command -v ruby >/dev/null 2>&1; then
    fail "ruby is required to validate portable host paths"
    return 1
  fi

  if ruby - "$plugin_skills_dir" "$repo_root" <<'RUBY'
skills_dir = ARGV.fetch(0)
repo_root = ARGV.fetch(1)
failures = []

def rel(path, root)
  path.delete_prefix("#{root}/")
end

patterns = [
  [
    /\A\s*plugins\/v1tamins\/skills\/v1-[^\s`]+\/[^\s`]+\.(?:sh|py)(?:\s|$)/,
    "resolve skill helper paths from the current skill directory instead of hardcoding a repo-relative executable path"
  ],
  [
    /(?:\$HOME|~)\/\.claude\/plugins\/marketplaces\/every-marketplace\/plugins\/compound-engineering/,
    "resolve compound-engineering plugin helpers dynamically instead of hardcoding the Claude marketplace cache"
  ],
  [
    /\.claude\/session-notes/,
    "write reusable skill artifacts to a host-neutral project path instead of .claude/session-notes"
  ]
]

Dir.glob(File.join(skills_dir, "v1-*", "**", "*.{md,yaml,yml,sh,py}")).sort.each do |path|
  next unless File.file?(path)
  next if path.split(File::SEPARATOR).any? { |part| part.start_with?("v1-_") }

  File.readlines(path).each_with_index do |line, index|
    patterns.each do |pattern, message|
      next unless line.match?(pattern)

      failures << "#{rel(path, repo_root)}:#{index + 1}: #{message}"
    end
  end
end

if failures.any?
  warn failures.join("\n")
  exit 1
end
RUBY
  then
    ok "portable host paths"
  else
    fail "portable host path validation failed"
  fi
}

validate_plugin_skills() {
  local skill_dir
  local skill_name
  local skill_md
  local openai_yaml
  local found=false

  require_dir "$plugin_skills_dir"

  while IFS= read -r skill_dir; do
    found=true
    skill_name="$(basename "$skill_dir")"
    skill_md="$skill_dir/SKILL.md"
    openai_yaml="$skill_dir/agents/openai.yaml"

    case "$skill_name" in
      v1-*) ;;
      *)
        fail "plugin skill directory must use v1- prefix: $(relpath "$skill_dir")"
        continue
        ;;
    esac

    if [ -f "$skill_md" ]; then
      validate_skill_frontmatter "$skill_md" "$skill_name"
    else
      fail "missing SKILL.md: $(relpath "$skill_md")"
    fi

    if [ -f "$openai_yaml" ]; then
      validate_yaml_file "$openai_yaml"
    fi
  done < <(find "$plugin_skills_dir" -mindepth 1 -maxdepth 1 -type d ! -name '.*' ! -name 'v1-_*' -print 2>/dev/null | sort)

  if [ "$found" = false ]; then
    fail "no plugin skills found in $(relpath "$plugin_skills_dir")"
  fi
}

main() {
  if [ "$write" = true ] && [ "$verbose" = true ]; then
    printf 'note: --write is a compatibility no-op; plugin skills are canonical now.\n'
  fi

  require_dir "$plugin_dir"

  validate_plugin_manifest
  validate_json_file "$claude_plugin_manifest"
  validate_marketplace_manifest

  if [ "$failures" -ne 0 ]; then
    print_failure_summary
    exit 1
  fi

  validate_no_legacy_agent_skills
  validate_plugin_skills
  validate_skill_references
  validate_skill_assets
  validate_portable_host_paths

  if [ "$failures" -ne 0 ]; then
    print_failure_summary
    exit 1
  fi

  printf '\nSkill host sync checks passed.\n'
}

main "$@"
