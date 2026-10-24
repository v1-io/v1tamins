# Compound-engineering dependency

Goldpan uses the public
[compound-engineering plugin](https://github.com/EveryInc/compound-engineering-plugin)
for session discovery/extraction and for the `ce-compound` documentation writer.
It is a separate installation, not a bundled v1tamins skill.

Before scouting, check that the session scripts resolve and `ce-compound` is
available in the selected runtime. The wrapper reports the exact missing
script and searches known companion layouts; `CE_SKILLS_DIR` can identify an
already installed companion's `skills` directory. Do not substitute an
unrelated file with the same basename.

If a required component is missing, report that source or queue stage as
blocked and retain useful evidence from available sources. Do not invent
session coverage, write solution documents yourself, or count an unexecuted
writer call as completed documentation. Installation or upgrade requires the
user's authorization.

For an authorized Claude Code installation:

```text
/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering@compound-engineering-plugin
```

For an authorized Codex installation:

```text
codex plugin marketplace add EveryInc/compound-engineering-plugin
```

Then install or enable `compound-engineering` in the Codex plugin UI. Follow
the companion's current installation documentation if runtime commands differ.
After installation, verify the actual script and workflow sources before
resuming the blocked stage. A marketplace entry alone does not establish that
the required component loaded.
