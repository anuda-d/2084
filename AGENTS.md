# Agent Guidance

These are flexible working principles for coding agents and future contributors. They are not permanent project rules and should change as 2084 becomes more defined.

## Before Working

- Start with `docs/plans/CURRENT.md`; it is the compact operational index.
- Read the linked active goal, implementation plan, and only the specification
  linked by the active task.
- Locate relevant implementation and tests just in time with repository search.
- Read `README.md`, `docs/main/CORE_CONSTRUCT.md`, or
  `docs/main/ARCHITECTURE.md` only when the active specification routes there or
  an invariant is unclear.
- Use `docs/plans/LIE_AND_DOUBLETHINK_ARCHITECTURE.md` only as optional broader
  context; it is not an implementation checklist.
- Read `docs/main/DESIGN_REFERENCES.md` only before borrowing from a reference.
- Treat unanswered questions as open design space rather than silently deciding them.
- Distinguish a temporary exploration from a lasting architectural choice.

## While Exploring

- Prefer small experiments that clarify one concept.
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
- Validate work in proportion to its maturity; early conceptual experiments need clarity more than production ceremony.

## Communicating Results

- Describe what happened without overstating what it proves.
- Separate observed behavior from interpretation.
- Call out forced outcomes, special cases, and unresolved assumptions.
- Be willing to recommend removing a system when it obscures the central question.
- Update these documents when the project’s direction genuinely changes.

## Current Bias

For now, favor one autonomous focal life, a small living world, understandable agents, limited knowledge, and inspectable consequences over scale, conventional game systems, visual polish, or elaborate AI behavior.

## Autonomous Development Loop

- Use the compact run contract in `docs/plans/CURRENT.md`; consult
  `docs/main/DEVELOPMENT_LOOP.md` when the full operating contract is needed.
- Each scheduled or manual Codex task completes at most one current
  implementation-plan task, commits it, and exits. A separate alignment run
  plans the next small batch from verified goal evidence.
- A later standalone task loads fresh context from repository state.
- Before a scheduled run touches the repository, it must confirm that no
  other 2084 task, loop orchestrator, or subagent thread is still active. Any
  active project task makes the new trigger a no-op.
- Manual runs follow the same one-task, authority, validation, review, and
  no-overlap rules.
- The active goal, not the trigger or task, defines authorized product and
  implementation scope.
- The main agent owns gap selection, implementation, integration, validation,
  progress recording, commits, and the final report. It may partition genuinely
  independent implementation work between subagents with exclusive ownership,
  and must use a fresh read-only subagent for independent review of an
  implementation task, as described by the loop contract.
- Treat `experiments/` as read-only historical evidence unless an approved goal
  explicitly targets it.
- Do not select, broaden, or replace the active goal. Stop when the active goal
  is complete or when continuing requires an owner decision.
