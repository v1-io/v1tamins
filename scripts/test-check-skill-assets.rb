#!/usr/bin/env ruby
# frozen_string_literal: true

require "tmpdir"
require "fileutils"
require "open3"

checker = File.expand_path("check-skill-assets.rb", __dir__)
failures = []
cases = {
  "local asset" => ["Read [method](references/method.md).", {"references/method.md" => "Method."}, true],
  "sibling owner" => ["Read [policy](../v1-owner/references/policy.md).", {"../v1-owner/references/policy.md" => "Policy."}, true],
  "shared package resource" => ["Read [guide](../../references/guide.md).", {"../../references/guide.md" => "Guide."}, true],
  "repository fallback is absent from package" => ["Read [guide](README.md).", {"@repo/README.md" => "Maintainer guide."}, false],
  "explicit package escape" => ["Read [guide](../../../../README.md).", {"@repo/README.md" => "Maintainer guide."}, false],
  "nested missing link" => ["Read [method](references/method.md).", {"references/method.md" => "Read [contract](missing.md)."}, false],
  "reference relative link" => ["Read [method](references/method.md).", {"references/method.md" => "Read [contract](contract.md).", "references/contract.md" => "Contract."}, true],
  "prose helper path" => ["Run `scripts/missing.py`.", {}, false],
  "runtime helper path" => ['Run "$SKILL_DIR/scripts/missing.py".', {}, false],
  "external links and anchors" => ["Read [docs](https://example.com/docs) and [here](#method).", {}, true],
  "file URI is a local dependency" => ["Read [policy](file:///outside-policy.md).", {}, false],
  "fenced output example" => ["```markdown\n[proof](/absolute/output.html)\n```", {}, true],
  "symlink escapes package" => ["Read [policy](references/policy.md).", {"@symlink" => "outside"}, false]
}

cases.each do |name, (body, files, expected)|
  Dir.mktmpdir do |root|
    skills = File.join(root, "plugins", "fixture", "skills")
    skill = File.join(skills, "v1-fixture")
    FileUtils.mkdir_p(skill)
    File.write(File.join(skill, "SKILL.md"), body + "\n")
    files.each do |path, content|
      if path == "@symlink"
        outside = File.join(root, "outside.md")
        File.write(outside, content)
        FileUtils.mkdir_p(File.join(skill, "references"))
        File.symlink(outside, File.join(skill, "references", "policy.md"))
      else
        dest = path.start_with?("@repo/") ? File.join(root, path.delete_prefix("@repo/")) : File.expand_path(path, skill)
        FileUtils.mkdir_p(File.dirname(dest))
        File.write(dest, content)
      end
    end
    output, status = Open3.capture2e("ruby", checker, skills, root)
    failures << "#{name}: expected #{expected ? 'pass' : 'failure'}, got #{status.exitstatus}: #{output}" unless status.success? == expected
  end
end

abort failures.join("\n") unless failures.empty?
puts "All #{cases.length} skill asset checks passed."
