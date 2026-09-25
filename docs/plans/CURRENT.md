# Current Development

The sole owner-approved product goal is [First Consequential Choice Under Conflicting Information](first-consequential-choice/GOAL.md).
Its [implementation state](first-consequential-choice/IMPLEMENTATION_PLAN.md) records accepted behavior, authored inputs, failed live attempts, and accepted live/completion evidence.
All twelve completion criteria have accepted evidence.
The final independent whole-goal review passed; the runner owns operational completion state.

## Work selection

Follow the [goal-development skill](../../.agents/skills/goal-development/SKILL.md) and [Development Loop](../main/DEVELOPMENT_LOOP.md).
`development-loop.toml` selects the goal, context, checks, review boundaries, and daily 18:00-23:00 America/Toronto execution window.
Continue unfinished work or choose one coherent remaining responsibility; the runner owns review dispatch, operational records, staging, and commits.

Read only source, tests, and the relevant [architecture](../main/ARCHITECTURE.md) boundary for that responsibility.
Use [Core Construct](../main/CORE_CONSTRUCT.md) for product direction and reference limits, and [README](../../README.md) for commands.
Preserve limited knowledge, attempted-action authority, deterministic consequence, exact-day behavior, and the distinction between authored and live evidence.
An inconclusive experiment can expose a limitation without satisfying the goal.
Never silently reopen an exhausted experiment or omit failed samples to claim success.

## Operations and documentation

Run `python3 -m devloop status` for current state and `python3 -m devloop doctor` for setup checks.
Runtime state belongs in the runner, not manually synchronized Markdown.
The Mac runs development; the Windows PC supplies only the optional Qwen endpoint.
The retired Codex automation must remain paused.

Keep only documentation needed for current use, product direction, or development.
Condense existing files below 200 lines rather than splitting them or adding per-task logs.
Completed plans and detailed historical evidence remain recoverable from Git; the active implementation state retains the relevant conclusions and evidence anchors.
