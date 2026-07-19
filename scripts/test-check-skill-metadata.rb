#!/usr/bin/env ruby
# frozen_string_literal: true

# False-positive and false-negative tests for the fenced-block mutation
# detection in check-skill-metadata.rb. Black-box: builds throwaway skill
# fixtures and asserts on the undeclared-side_effects failure message.

require "tmpdir"
require "open3"

CHECKER = File.expand_path("check-skill-metadata.rb", __dir__)
MUTATION_MESSAGE = "mutation commands but policy.side_effects is empty"

def write_skill(skills_dir, name, body)
  skill_dir = File.join(skills_dir, name)
  Dir.mkdir(skill_dir)
  Dir.mkdir(File.join(skill_dir, "agents"))
  File.write(File.join(skill_dir, "SKILL.md"), <<~MARKDOWN)
    ---
    name: #{name}
    description: Use when testing metadata checks. Triggers on "test".
    ---
    # #{name}

    #{body}
  MARKDOWN
  File.write(File.join(skill_dir, "agents", "openai.yaml"), <<~YAML)
    interface:
      display_name: "#{name}"
      short_description: "Fixture skill"
      default_prompt: "Use $#{name}."

    policy:
      allow_implicit_invocation: true
  YAML
end

def checker_output(body)
  Dir.mktmpdir do |skills_dir|
    write_skill(skills_dir, "v1-fixture", body)
    output, = Open3.capture2e("ruby", CHECKER, skills_dir, skills_dir, "false")
    return output
  end
end

MUTATION_BODIES = {
  "gh pr review" => "```bash\ngh pr review 12 --request-changes -b \"findings\"\n```",
  "gh pr edit embedded" => "```bash\ncd repo && gh pr edit 12 --title \"t\"\n```",
  "git push" => "```sh\ngit push origin HEAD\n```",
  "gh api explicit method" => "```bash\ngh api repos/{owner}/{repo}/issues -X POST -f title=t\n```",
  "gh api --method=DELETE" => "```bash\ngh api repos/{owner}/{repo}/labels/bug --method=DELETE\n```",
  "gh api body flag defaults to POST" =>
    "```bash\ngh api repos/{owner}/{repo}/pulls/1/comments/2/replies -f body=\"Fixed\"\n```",
  "gh api graphql mutation" =>
    "```bash\ngh api graphql -f query='mutation { resolveReviewThread(input: {threadId: \"x\"}) { thread { id } } }'\n```"
}.freeze

READ_ONLY_BODIES = {
  "gh api read" => "```bash\ngh api repos/{owner}/{repo}/issues/1/comments --paginate | jq -r '.[].body'\n```",
  "gh api explicit GET with params" => "```bash\ngh api repos/{owner}/{repo}/issues -X GET -f state=open\n```",
  "gh api graphql query" =>
    "```bash\ngh api graphql -f query='query { repository(owner: \"o\", name: \"r\") { id } }'\n```",
  "read-only gh and git" => "```bash\ngh pr view 12 --comments\ngit log --oneline\n```",
  "mutation named only in prose" => "Never run gh pr edit from this skill.",
  "commented-out mutation" => "```bash\n# gh pr merge 12\ngh pr diff 12\n```"
}.freeze

failures = []

MUTATION_BODIES.each do |label, body|
  output = checker_output(body)
  unless output.include?(MUTATION_MESSAGE)
    failures << "false negative: #{label} was not flagged as a mutation"
  end
end

READ_ONLY_BODIES.each do |label, body|
  output = checker_output(body)
  if output.include?(MUTATION_MESSAGE)
    failures << "false positive: #{label} was flagged as a mutation"
  end
end

if failures.empty?
  puts "ok: #{MUTATION_BODIES.size + READ_ONLY_BODIES.size} mutation-detection cases"
  exit 0
end

failures.each { |failure| puts "ERROR: #{failure}" }
exit 1
