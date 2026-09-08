# Agent Guidance

These are flexible working principles for coding agents and future contributors. They are not permanent project rules and should change as 2084 becomes more defined.

## Before Working

- Start with `docs/plans/CURRENT.md`; it is the compact operational index.
- Read-only work does not require checkout ownership.
- Immediately before the first repository write, follow the no-overlap gate in
  `docs/main/DEVELOPMENT_LOOP.md` and claim checkout ownership with
  `python3 scripts/autonomous_loop_lock.py acquire`.
- The ownership command uses `CODEX_THREAD_ID` automatically.
  Assert ownership after any resumed turn and immediately before commit.
  Release ownership at completion, at any other terminal state, or
  immediately before a relay handoff.
- For implementation, confirm that exactly one owner-approved goal is active
  with standing authorization.
- If no goal is active, stop before implementation unless the owner explicitly
  requested a bounded administrative change.
- Read the linked active goal and implementation state, then locate only enough
  relevant implementation and tests to select one smallest useful goal gap.
- Read only the specification relevant to that selected task.
- Read `README.md`, `docs/main/CORE_CONSTRUCT.md`, or
  `docs/main/ARCHITECTURE.md` only when the active specification routes there or
  an invariant is unclear.
- Use `docs/plans/LIE_AND_DOUBLETHINK_ARCHITECTURE.md` only as optional broader
  context; it is not an implementation checklist.
- Read `docs/main/DESIGN_REFERENCES.md` only before borrowing from a reference.
- Treat unanswered questions as open design space rather than silently deciding them.
- Distinguish a temporary exploration from a lasting architectural choice.

## While Exploring

- Prefer small probes that clarify one concept.
- Explain assumptions that materially affect behavior.
- Keep worldbuilding ideas separate from general simulation mechanisms where practical.
- Avoid hardcoding a desired story and then describing it as emergence.
- Avoid treating AI output as automatically true, human, or internally consistent.
- Consider whether a simpler rule-based approach could answer the same question.
- Keep true world state, agent knowledge, and observer presentation conceptually distinct.
- Preserve `EventLog` as append-only objective evidence. Official Record may
  change a current public projection but must never rewrite objective history.
- Do not treat an official-record change as automatic observation delivery.
  Agents learn a version only through a channel they can actually access.
- Do not add complexity only to imitate the full real world.
- Treat the focal character as an autonomous participant, not a player puppet or privileged source of truth.
- Keep the normal experience centered on watchable agency rather than conventional game objectives or a formal-study dashboard.
- Use the reference simulation for transferable concepts, not as code, scenario, or interface to copy wholesale.
- Model doublethink-inspired behavior through source-linked memory, explicit
  contradictions, confidence, contextual stance, accessibility, inspectable
  inhibition or resurfacing, and public/private divergence. Do not erase source
  evidence on conflict or claim to simulate human consciousness.
- Keep public expression as an attempted action rather than silently equating it
  with an agent's private or contextual understanding.
- Keep the diary's initial scope physical and basic. Add discovery, concealment, or other consequences only when they create a necessary interaction.

## When Making Changes

- Say what question or uncertainty the change explores.
- Identify which behavior would show that the idea is working.
- Check whether the change grants an agent hidden knowledge or impossible authority.
- Keep consequential actions connected to understandable world responses.
- Preserve enough information to explain surprising behavior.
- Validate work in proportion to its maturity; early conceptual prototypes need clarity more than production ceremony.

## Communicating Results

- Describe what happened without overstating what it proves.
- Separate observed behavior from interpretation.
- Call out forced outcomes, special cases, and unresolved assumptions.
- Be willing to recommend removing a system when it obscures the central question.
- Update these documents when the project’s direction genuinely changes.

## Current Bias

For now, favor one autonomous focal life, a small living world, understandable agents, limited knowledge, and inspectable consequences over scale, conventional game systems, visual polish, or elaborate AI behavior.

## Autonomous Development Loop

- Use `docs/main/DEVELOPMENT_LOOP.md` as the complete operating contract.
- Treat `docs/plans/AUTONOMOUS_LOOP_STATE.json` as the authoritative runtime state and `docs/plans/CURRENT.md` as its human-readable index.
- The current runtime state is stopped and unauthorized.
  Historical goal documents do not reactivate it.
- Standing authorization exists only when the runtime state names one owner-approved goal, records `authorization.status` as `standing`, and the exact `autonomous-2084-development-loop` automation is active.
- The scheduler is only a liveness and recovery trigger.
  It never selects product work and must no-op when a valid orchestrator or writer owns the loop.
- One orchestrator generation manages at most three sequential accepted slices, then performs whole-goal alignment and hands off to a fresh orchestrator.
- Each slice has one fresh writer that is the sole repository modifier for the slice.
  The writer may use read-only explorers and must use a fresh read-only reviewer.
- Freeze the slice completion contract before transferring checkout ownership to the writer.
  A slice counts only after every frozen gate, focused and full validation, and blocking review have passed.
- Keep an incomplete slice active or recover it exactly.
  Never replace it silently or count it as accepted.
- Use the guarded state CLI and durable checkout lock for every lifecycle transition.
  Revision mismatches, unknown ownership, and illegal transitions fail closed.
- The unscoped Codex task listing is not an ownership precondition.
  Do not call `list_threads` as part of the no-overlap gate.
- If acquisition reports another owner, inspect only that exact task with `read_thread`.
  Recover the stale lock only when the exact owner has a terminal latest turn, using `recover --expected-task-id` and the observed claim token with that verified terminal state, then rebind the exact recorded actor in runtime state.
  Active, unknown, or idle owners awaiting input continue to block recovery.
- Run focused checks and `./scripts/check.sh` before recording evidence.
- Resolve blocking findings with the same writer and repeat validation and fresh review after material correction.
- The active goal, not the trigger or task, defines authorized product and implementation scope.
- Repository state and the guarded runtime state are authoritative.
  Temporary handoffs are compact context only and never authority or a future task queue.
- Do not select, broaden, or replace the active goal.
  Stop when the active goal is complete or when continuing requires an owner decision.
