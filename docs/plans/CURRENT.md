# Current development index

The owner-approved product goal is [First Consequential Choice Under Conflicting Information](first-consequential-choice/GOAL.md).
Its [implementation evidence](first-consequential-choice/IMPLEMENTATION_PLAN.md) records accepted behavior and remaining criteria.
CC-4, CC-11, and CC-12 still require completion evidence; neither the preserved prerequisite repairs nor the conflict-opportunity timing establishes a successful live model day.

## Development

Use the shared [goal-development skill](../../.agents/skills/goal-development/SKILL.md) and [continuous development loop](../main/DEVELOPMENT_LOOP.md).
`development-loop.toml` selects the approved goal and project-specific validation and review rules.
Execution is allowed daily from 18:00 to 23:00 America/Toronto, with continuous work throughout the window.
The working agent chooses and completes a meaningful remaining responsibility; the runner handles operational records and commits.

Read only source, tests, and specifications relevant to the selected gap.
Preserve information access, attempted-action boundaries, deterministic world consequences, exact-day behavior, and the distinction between authored and live evidence.
An inconclusive experiment can identify a limitation without satisfying the goal.
Never silently reopen an exhausted historical experiment or discard failed attempts to claim success.

## Operational state

Run `python3 -m devloop status` for current state and `python3 -m devloop doctor` for local setup checks.
Do not copy scheduler status, task identities, counters, or commit hashes into this index.
The retired Codex automation remains paused.
The replacement runs on the Mac; the Windows PC supplies only the Qwen endpoint.
Resume execution after installation and verification when the loop should start working.
The [historical loop snapshot](../archive/development-loop-20260916.md) and [original runtime record](../archive/development-loop-20260916.json) preserve prior evidence without controlling current execution.
