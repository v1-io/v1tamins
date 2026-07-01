#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/validate-plugin.sh [--verbose]

Validate the v1tamins plugin package.

Checks:
  - plugin and marketplace manifests parse as JSON
  - plugins/v1tamins/skills/v1-*/SKILL.md files have parseable YAML frontmatter
  - each skill frontmatter name matches its v1-* directory
  - optional agents/openai.yaml files parse as YAML
  - each distributed skill has Codex metadata
  - routing evals and trigger inventory cover distributed skills
  - live routing eval schema parses as JSON
  - skill descriptions are checked for trigger-oriented, budget-resilient metadata
  - plugin-distributed skills use the v1- prefix
  - plugin skills do not reference known v1tamins skills by legacy bare names
  - root SKILL.md local links and required bundled asset references resolve
  - distributed helper snippets avoid checkout-only executable paths and host-specific plugin cache paths
  - runtime plugin content changes bump both runtime plugin versions
  - legacy tracked .agents/skills mirrors are absent

Options:
  --verbose print each successful check
  -h, --help
EOF
}

verbose=false

for arg in "$@"; do
  case "$arg" in
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
live_routing_schema="$plugin_dir/evals/live-routing-output.schema.json"

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

fail() {
  failures=$((failures + 1))
  printf 'ERROR: %s\n' "$1" >&2
}

warn_validation() {
  warnings=$((warnings + 1))
  printf 'WARNING: %s\n' "$1" >&2
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

version_gt() {
  local current="$1"
  local previous="$2"

  awk -v current="$current" -v previous="$previous" '
    BEGIN {
      split(current, c, ".")
      split(previous, p, ".")
      for (i = 1; i <= 3; i++) {
        cn = c[i] + 0
        pn = p[i] + 0
        if (cn > pn) {
          exit 0
        }
        if (cn < pn) {
          exit 1
        }
      }
      exit 1
    }
  '
}

resolve_version_base() {
  if [ -n "${GITHUB_BASE_REF:-}" ]; then
    local github_base="origin/$GITHUB_BASE_REF"
    if git -C "$repo_root" rev-parse --verify "$github_base" >/dev/null 2>&1; then
      printf '%s\n' "$github_base"
      return 0
    fi
  fi

  if git -C "$repo_root" rev-parse --verify origin/main >/dev/null 2>&1; then
    printf '%s\n' "origin/main"
    return 0
  fi

  if git -C "$repo_root" rev-parse --verify HEAD~1 >/dev/null 2>&1; then
    printf '%s\n' "HEAD~1"
    return 0
  fi

  return 1
}

validate_plugin_version_bump() {
  local base_ref diff_base changed_files runtime_changed=0
  local current_codex current_claude
  local base_codex base_claude changed_file

  if ! git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ok "plugin version bump skipped outside git worktree"
    return 0
  fi

  if ! base_ref="$(resolve_version_base)"; then
    ok "plugin version bump skipped without base ref"
    return 0
  fi

  diff_base="$(git -C "$repo_root" merge-base "$base_ref" HEAD 2>/dev/null || printf '%s\n' "$base_ref")"
  changed_files="$(
    {
      git -C "$repo_root" diff --name-only "$diff_base" HEAD || true
      git -C "$repo_root" diff --name-only "$diff_base" || true
      git -C "$repo_root" ls-files --others --exclude-standard || true
    } | sort -u
  )"

  while IFS= read -r changed_file; do
    case "$changed_file" in
      plugins/v1tamins/skills/* | plugins/v1tamins/.codex-plugin/plugin.json | plugins/v1tamins/.claude-plugin/plugin.json)
        runtime_changed=1
        break
        ;;
    esac
  done <<< "$changed_files"

  current_codex="$(jq -r '.version' "$plugin_manifest")"
  current_claude="$(jq -r '.version' "$claude_plugin_manifest")"

  if [ "$current_codex" != "$current_claude" ]; then
    fail "runtime plugin versions must match: $current_codex != $current_claude"
    return 0
  fi

  if [ "$runtime_changed" -eq 0 ]; then
    ok "plugin version bump not required"
    return 0
  fi

  base_codex="$(git -C "$repo_root" show "$base_ref:plugins/v1tamins/.codex-plugin/plugin.json" 2>/dev/null | jq -r '.version' || true)"
  base_claude="$(git -C "$repo_root" show "$base_ref:plugins/v1tamins/.claude-plugin/plugin.json" 2>/dev/null | jq -r '.version' || true)"

  if [ -z "$base_codex" ] || [ -z "$base_claude" ]; then
    ok "plugin version bump skipped because manifests are absent at $base_ref"
    return 0
  fi

  if [ "$base_codex" != "$base_claude" ]; then
    fail "base runtime plugin versions differ at $base_ref: $base_codex != $base_claude"
    return 0
  fi

  if version_gt "$current_codex" "$base_codex"; then
    ok "plugin version bumped $base_codex -> $current_codex"
  else
    fail "runtime plugin content changed but version was not bumped above $base_codex"
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
    else
      fail "missing Codex metadata: $(relpath "$openai_yaml")"
    fi
  done < <(find "$plugin_skills_dir" -mindepth 1 -maxdepth 1 -type d ! -name '.*' ! -name 'v1-_*' -print 2>/dev/null | sort)

  if [ "$found" = false ]; then
    fail "no plugin skills found in $(relpath "$plugin_skills_dir")"
  fi
}

validate_skill_routing_fixture() {
  local args=("--repo-root" "$repo_root")

  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 is required to validate skill routing fixture"
    return 0
  fi

  if [ "$verbose" = true ]; then
    args+=("--verbose")
  fi

  if python3 "$repo_root/scripts/check-skill-routing-fixture.py" "${args[@]}"; then
    ok "skill routing fixture"
  else
    fail "skill routing fixture validation failed"
  fi
}

validate_metadata_hygiene() {
  if ! command -v ruby >/dev/null 2>&1; then
    fail "ruby is required to validate metadata hygiene"
    return 0
  fi

  local output
  local status
  if output="$(
    ruby "$repo_root/scripts/check-skill-metadata.rb" "$plugin_skills_dir" "$repo_root" "$verbose"
  )"; then
    status=0
  else
    status=$?
  fi

  if [ -n "$output" ]; then
    while IFS= read -r line; do
      case "$line" in
        ERROR:*)
          fail "${line#ERROR: }"
          ;;
        WARNING:*)
          warn_validation "${line#WARNING: }"
          ;;
        *)
          printf '%s\n' "$line"
          ;;
      esac
    done <<< "$output"
  fi

  if [ "$status" -eq 0 ]; then
    ok "skill metadata hygiene"
  else
    fail "skill metadata hygiene validation failed"
  fi
}

main() {
  require_dir "$plugin_dir"

  validate_plugin_manifest
  validate_json_file "$claude_plugin_manifest"
  validate_marketplace_manifest
  validate_plugin_version_bump

  if [ "$failures" -ne 0 ]; then
    print_failure_summary
    exit 1
  fi

  validate_no_legacy_agent_skills
  validate_plugin_skills
  validate_json_file "$live_routing_schema"
  validate_skill_routing_fixture
  validate_metadata_hygiene
  validate_skill_references
  validate_skill_assets
  validate_portable_host_paths

  if [ "$failures" -ne 0 ]; then
    print_failure_summary
    exit 1
  fi

  printf '\nPlugin validation checks passed.\n'
  if [ "$warnings" -ne 0 ]; then
    printf '%d validation warning(s)\n' "$warnings" >&2
  fi
}

main "$@"
