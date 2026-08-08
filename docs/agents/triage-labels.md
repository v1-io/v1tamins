# Triage Labels

These are the canonical triage roles and the label strings this repository uses
on GitHub Issues.

| Role | Label in this repo | Exists today |
| --- | --- | --- |
| Needs triage | `needs-triage` | no |
| Needs information | `needs-info` | no |
| Ready for agent | `ready-for-agent` | no |
| Ready for human | `ready-for-human` | no |
| Won't fix | `wontfix` | yes |

Only `wontfix` exists in the repository today. The other four are not created
yet, so a skill that tries to apply one will fail until they exist.

Create them deliberately, through the GitHub UI or `gh label create`, rather
than letting an agent create them as a side effect of triaging one issue. Label
vocabulary on a public repository is visible to everyone who reads it, so it
should be a decision rather than an accident.

The repository also carries GitHub's stock labels — `bug`, `documentation`,
`duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`,
`question`. Those describe what an issue is about. The five above describe what
should happen to it next. Keep the two sets separate; do not overload `question`
to mean `needs-info`.
