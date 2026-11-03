# Triage Labels

These are the canonical triage roles and the label strings this repository uses
on GitHub Issues.

| Role | Label in this repo |
| --- | --- |
| Needs triage | `needs-triage` |
| Needs information | `needs-info` |
| Ready for agent | `ready-for-agent` |
| Ready for human | `ready-for-human` |
| Won't fix | `wontfix` |

All five labels exist. They apply to GitHub intake issues while they wait for
triage; accepted work moves to Linear as described in
[issue-tracker.md](issue-tracker.md).

Change this label vocabulary deliberately, through the GitHub UI or
`gh label create`, rather than as a side effect of triaging one issue. Labels
on a public repository are visible to everyone who reads it.

The repository also carries GitHub's stock labels — `bug`, `documentation`,
`duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`,
`question`. Those describe what an issue is about. The five above describe what
should happen to it next. Keep the two sets separate; do not overload `question`
to mean `needs-info`.
