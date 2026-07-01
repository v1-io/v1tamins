#!/usr/bin/env ruby
# frozen_string_literal: true

require "date"
require "json"
require "yaml"

VALID_INVOCATION_POSTURES = %w[implicit selective_implicit explicit_only].freeze
VALID_SIDE_EFFECTS = %w[
  browser_capture
  external_write
  git_remote
  peer_launch
].freeze

def usage
  warn "Usage: scripts/check-skill-metadata.rb [--side-effect-skills-json] <skills-dir> <repo-root> <verbose>"
  exit 2
end

side_effect_json = false
if ARGV.first == "--side-effect-skills-json"
  side_effect_json = true
  ARGV.shift
end

usage unless ARGV.length == 3

skills_dir = ARGV.fetch(0)
repo_root = ARGV.fetch(1)
verbose = ARGV.fetch(2) == "true"

def rel(path, root)
  path.delete_prefix("#{root}/")
end

def yaml_load(content, path)
  begin
    YAML.safe_load(content, permitted_classes: [Date, Time], aliases: false, filename: path)
  rescue ArgumentError
    YAML.safe_load(content, [Date, Time], [], false, path)
  end
end

def safe_yaml_load(content, path, failures, repo_root)
  yaml_load(content, path) || {}
rescue Psych::Exception => e
  failures << "#{rel(path, repo_root)}: invalid YAML: #{e.message}"
  nil
end

warnings = []
failures = []
descriptions = []
side_effect_skills = []

Dir.glob(File.join(skills_dir, "v1-*", "SKILL.md")).sort.each do |skill_path|
  skill_name = File.basename(File.dirname(skill_path))
  content = File.read(skill_path)
  frontmatter = content[/\A---\s*\n(.*?)\n---\s*\n/m, 1]
  next unless frontmatter

  data = safe_yaml_load(frontmatter, skill_path, failures, repo_root)
  next unless data
  unless data.is_a?(Hash)
    failures << "#{rel(skill_path, repo_root)}: frontmatter must be a mapping"
    next
  end

  description = data.fetch("description", "").to_s.strip
  descriptions << [skill_name, description.length]

  first_clause = description.split(/[.;]/, 2).first.to_s.strip

  if description.length > 350
    warnings << "#{rel(skill_path, repo_root)}: description is #{description.length} chars; target <= 350 for budget resilience"
  end

  unless description.match?(/\A(Use when|Conducts?|Create|Convert|Extract|Commit|Autonomous)\b/i)
    warnings << "#{rel(skill_path, repo_root)}: description should front-load the trigger condition"
  end

  unless description.match?(/\b(Use when|Triggers? on|trigger|review|debug|test|PR|prompt|skill|research|customer|prototype|HTML|chart|glossary|changelog|refactor|simplify|proof|Google Doc)\b/i)
    warnings << "#{rel(skill_path, repo_root)}: description may not include natural trigger terms"
  end

  if first_clause.length > 140
    warnings << "#{rel(skill_path, repo_root)}: first clause is #{first_clause.length} chars; key trigger may be truncated"
  end

  openai_path = File.join(File.dirname(skill_path), "agents", "openai.yaml")
  unless File.file?(openai_path)
    failures << "#{rel(openai_path, repo_root)}: missing Codex metadata"
    next
  end

  openai = safe_yaml_load(File.read(openai_path), openai_path, failures, repo_root)
  next unless openai
  unless openai.is_a?(Hash)
    failures << "#{rel(openai_path, repo_root)}: metadata must be a mapping"
    next
  end

  policy = openai.fetch("policy", {}) || {}
  unless policy.is_a?(Hash)
    failures << "#{rel(openai_path, repo_root)}: policy must be a mapping"
    next
  end

  allow_implicit = policy["allow_implicit_invocation"]
  invocation_posture = policy.fetch("invocation_posture", "implicit").to_s
  side_effects = Array(policy["side_effects"]).map(&:to_s).reject(&:empty?)
  claude_disabled = data["disable-model-invocation"] == true
  side_effect_skills << skill_name if side_effects.any?

  unless VALID_INVOCATION_POSTURES.include?(invocation_posture)
    failures << "#{rel(openai_path, repo_root)}: policy.invocation_posture must be one of #{VALID_INVOCATION_POSTURES.join(', ')}"
  end

  unknown_side_effects = side_effects - VALID_SIDE_EFFECTS
  unless unknown_side_effects.empty?
    failures << "#{rel(openai_path, repo_root)}: unknown policy.side_effects value(s): #{unknown_side_effects.join(', ')}"
  end

  if side_effects.any? && invocation_posture == "implicit"
    failures << "#{rel(openai_path, repo_root)}: side-effectful skills must use selective_implicit or explicit_only invocation posture"
  end

  case invocation_posture
  when "explicit_only"
    if allow_implicit != false
      failures << "#{rel(openai_path, repo_root)}: explicit_only skills must set policy.allow_implicit_invocation: false"
    end
    unless claude_disabled
      failures << "#{rel(skill_path, repo_root)}: explicit_only skills must set disable-model-invocation: true"
    end
  when "selective_implicit"
    if allow_implicit != true
      failures << "#{rel(openai_path, repo_root)}: selective_implicit skills must set policy.allow_implicit_invocation: true"
    end
    if claude_disabled
      failures << "#{rel(skill_path, repo_root)}: selective_implicit skills should not set disable-model-invocation: true"
    end
  else
    if claude_disabled
      failures << "#{rel(skill_path, repo_root)}: disable-model-invocation requires policy.invocation_posture: explicit_only"
    end
  end
end

if side_effect_json
  failures.each { |failure| warn "ERROR: #{failure}" }
  exit 1 unless failures.empty?

  puts JSON.generate(side_effect_skills.sort)
  exit 0
end

total = descriptions.sum { |_name, length| length }
largest = descriptions.max_by(5) { |_name, length| length }

if verbose
  puts "ok: total skill description chars: #{total}"
  largest.each do |name, length|
    puts "ok: description budget contributor #{name}: #{length} chars"
  end
end

failures.each { |failure| puts "ERROR: #{failure}" }
warnings.each { |warning| puts "WARNING: #{warning}" }
exit failures.empty? ? 0 : 1
