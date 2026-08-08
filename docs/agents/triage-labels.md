# Triage Labels

These are the canonical triage roles and how they map onto Linear.

| Role | Label | Linear mapping |
| --- | --- | --- |
| Needs triage | `needs-triage` | Triage state, or Backlog when untriaged |
| Needs information | `needs-info` | Blocked, with the open question in a comment |
| Ready for agent | `ready-for-agent` | Todo, fully specified, agent may pick up |
| Ready for human | `ready-for-human` | Todo, requires human implementation |
| Won't fix | `wontfix` | Cancelled |

Linear workflow state is the source of truth. Apply a label only when the
workspace already defines it — create labels through the Linear UI, not through
an agent, so the vocabulary stays under human control.

When a skill names a role, map it to the state in this table rather than
inventing a new label.
