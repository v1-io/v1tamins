# Public-Safe Extraction

Use this reference when converting a private project lesson into a reusable shared skill.

## Keep

- General workflow shape
- Failure modes that apply across repositories
- Validation patterns that can run in any compatible repo
- Placeholder examples such as `<repo>`, `<service>`, `<org-id>`, and `<incident-id>`

## Remove Or Generalize

- Private project, customer, organization, or person names
- Internal domains, dashboards, trace URLs, Slack channels, and ticket URLs
- Absolute user or company filesystem paths
- Proprietary architecture details that are not needed to apply the pattern
- Incident-specific timelines, thread IDs, org IDs, account IDs, secrets, or tokens
- Host-specific path casing unless the shared repo explicitly supports it
- OS-specific commands such as BSD-only date flags when a portable Python snippet would work

## Scan

Run a privacy and portability scan before recommending or publishing a shared-skill change:

```bash
rg -n "(/Users/|/home/|[A-Za-z]:\\\\|https?://|slack|customer|secret|token|date -v)" plugins/v1tamins/skills/v1-<skill-name>
```

Review every hit. Keep intentional public references, but rewrite private or host-specific details. If the skill genuinely needs project-specific facts, keep it in that project's local skill directory instead of v1tamins.
