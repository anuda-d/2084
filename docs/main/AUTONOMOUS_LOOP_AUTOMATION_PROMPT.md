# Autonomous 2084 Development Loop Automation Prompt

Continue the authorized 2084 development loop in `/Users/anuda/Desktop/2084` as a liveness and recovery trigger only.

Read `AGENTS.md`, `docs/plans/CURRENT.md`, `docs/plans/AUTONOMOUS_LOOP_STATE.json`, and `docs/main/DEVELOPMENT_LOOP.md` in that order.
Run `python3 scripts/autonomous_loop_state.py validate` and inspect the exact `autonomous-2084-development-loop` automation.
Stop without repository changes when runtime state is stopped or unauthorized, the automation is paused, state is inconsistent, or an owner decision or blocker is recorded.

Do not select product work in the scheduler task.
If a valid orchestrator or writer owns the checkout, no-op.
If the recorded actor is active, idle awaiting input, non-terminal, unknown, or unreadable, no-op.
Inspect only the exact recorded owner with `read_thread` and never use `list_threads` as an ownership precondition.

Recover an actor only after its exact latest state is verified as `completed`, `failed`, or `interrupted`.
Use the observed owner identifier and claim token with `autonomous_loop_lock.py recover`, then use `autonomous_loop_state.py recover-actor` with the unchanged expected revision.
Any identity, token, scope, terminal-state, or revision mismatch fails closed.

Create one fresh orchestrator only when standing authorization exists and runtime phase is `ready` without an orchestrator or `handoff_ready` after whole-goal alignment.
The orchestrator may manage no more than three sequential accepted slices.
For each slice it freezes one completion contract, creates one fresh writer, and transfers checkout ownership to that writer.
The writer is the sole repository modifier for the slice and may use only read-only explorers and a fresh read-only reviewer.
Only frozen gates, focused and full validation, clean blocking review, and a coherent commit allow the slice to count.

Incomplete work remains the current slice and is recovered exactly.
After three accepted slices, require whole-goal alignment and a compact durable handoff to a fresh orchestrator generation.
Never create a future task queue, replace an incomplete slice, broaden a goal, push, merge, deploy, publish, or destructively clean.
