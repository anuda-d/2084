# Agent Guidance

These are flexible working principles for coding agents and future contributors. They are not permanent project rules and should change as 2084 becomes more defined.

## Before Working

- Start with `docs/plans/CURRENT.md`; it is the compact operational index.
- Read-only work does not require checkout ownership.
- Use a dedicated loop checkout; the runner owns exclusive execution and Git commits.
- For manual administrative work, pause the runner and confirm it has stopped before editing that checkout.
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

- The owner-approved goal defines what work is authorized.
- Follow `.agents/skills/goal-development/SKILL.md` for work selection and implementation quality.
- `development-loop.toml` selects the goal, context, daily window, checks, and review boundaries.
- `python3 -m devloop status` is the operational source of truth; do not transcribe runtime state into documents.
- The runner continuously advances eligible work inside 18:00-23:00 America/Toronto, including after mid-window restarts.
- One working agent chooses and implements a coherent responsibility; the same session continues across changes.
- The runner performs repository checks, invokes independent review when warranted, and commits the exact validated result.
- Report semantic review risks that automatic path checks may miss.
- The runner owns staging, commits, retries, and runtime records; agents must not manipulate them.
- Stop for missing product direction, exhausted repairs, an owner pause, or goal completion.
- Do not create task contracts, orchestrator generations, future task queues, or per-task ledgers.
- Preserve incomplete work across the end of the daily window; do not claim it is complete.
- Never push, merge, deploy, broaden the goal, or modify the runner without explicit owner direction.
- The retired Codex automation must remain paused; it is superseded by the Mac runner.
