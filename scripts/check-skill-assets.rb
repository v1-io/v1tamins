#!/usr/bin/env ruby
# frozen_string_literal: true

# Bounded source/package check, not a Markdown parser or runtime loading test.
# Markdown links resolve from their containing file. Prose references/scripts
# paths and SKILL_ROOT/SKILL_DIR substitutions resolve from the owning skill.
require "pathname"

abort "Usage: check-skill-assets.rb <skills-dir> <repo-root>" unless ARGV.length == 2
skills_dir = File.realpath(ARGV.fetch(0))
repo_root = File.realpath(ARGV.fetch(1))
plugin_dir = File.dirname(skills_dir)
failures = []

def asset_error(base, target, plugin_dir)
  return nil if target.empty? || target.start_with?("#")
  return "use a package-relative path instead of file URI #{target}" if target.match?(/\Afile:/i)
  return nil if target.match?(%r{\A[a-z][a-z0-9+.-]*:}i)

  candidate = File.expand_path(target, base)
  return "asset escapes plugin package #{target}" unless candidate.start_with?(plugin_dir + File::SEPARATOR)
  return "missing bundled asset #{target}" unless File.exist?(candidate)

  resolved = File.realpath(candidate)
  return "asset resolves outside plugin package #{target}" unless resolved.start_with?(plugin_dir + File::SEPARATOR)
  nil
rescue SystemCallError => e
  "unreadable bundled asset #{target} (#{e.class})"
end

Dir.glob(File.join(skills_dir, "v1-*", "**", "*.md")).sort.each do |path|
  next if path.split(File::SEPARATOR).any? { |part| part.start_with?("v1-_") }
  next unless File.file?(path)

  skill_dir = File.join(skills_dir, Pathname.new(path).relative_path_from(Pathname.new(skills_dir)).each_filename.first)
  relative = path.delete_prefix(repo_root + File::SEPARATOR)
  path_error = asset_error(File.dirname(path), File.basename(path), plugin_dir)
  if path_error
    failures << "#{relative}: #{path_error}"
    next
  end
  fence = nil
  File.readlines(path, encoding: "UTF-8").each_with_index do |line, index|
    if (marker = line.match(/^\s{0,3}(`{3,}|~{3,})/))
      if fence.nil?
        fence = marker[1]
      elsif marker[1][0] == fence[0] && marker[1].length >= fence.length
        fence = nil
      end
      next
    end

    targets = []
    unless fence
      line.scan(/\[[^\]]+\]\(([^)]+)\)/) do |match|
        target = match.fetch(0).sub(/\s+['"].*\z/, "").delete_prefix("<").delete_suffix(">")
        targets << [File.dirname(path), target.split("#", 2).first.to_s]
      end
      if line.match?(/\b(read|run|use|follow|following|helper|starting point)\b/i)
        line.scan(/`((?:references?|scripts)\/[^`\s]+)`/) do |match|
          targets << [skill_dir, match.fetch(0)]
        end
      end
    end
    line.scan(%r{\$\{?SKILL_(?:ROOT|DIR)\}?/((?:references?|scripts)/[A-Za-z0-9._/-]+)}) do |match|
      targets << [skill_dir, match.fetch(0)]
    end
    targets.uniq.each do |base, target|
      error = asset_error(base, target, plugin_dir)
      failures << "#{relative}:#{index + 1}: #{error}" if error
    end
  end
end

warn failures.join("\n") unless failures.empty?
exit failures.empty? ? 0 : 1
