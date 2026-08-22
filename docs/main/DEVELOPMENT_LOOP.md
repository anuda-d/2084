# Agentic Development Loop

Status: current operating contract for owner-authorized continuous, scheduled,
and manual development.

The compact contract in `docs/plans/CURRENT.md` is the normal entry point. This
document expands it. As of August 22, 2026, no implementation goal is active;
the loop must therefore stop after orientation unless the owner starts a new
goal or explicitly authorizes a bounded maintenance task.

## Purpose and Boundary

The loop advances one owner-approved 2084 goal through small, independently
validated work units. One work unit selects one current gap from fresh
repository evidence, implements or reviews it, validates it, records verified
progress, and creates one coherent commit. It never creates a future task queue
or chooses the project's next goal.

An explicit owner request may authorize bounded maintenance—such as correcting
current documentation—without opening a product goal. That authority covers
only the requested maintenance and must not be used to select new behavior,
settle open product questions, or extend implementation scope.

The repository is the durable state between work units. Chat context, provider
history, scheduled triggers, and speculative plans are not sources of product
authority.

## Run Modes

### Continuous Goal

Continuous Goal mode is primary while the owner has started an active goal. One
Codex task remains active, completes one reviewed and committed work unit, then
starts the next unit from updated repository state. It stops when the goal is
complete, the owner pauses it, or a terminal condition is reached.

### Scheduled or manual one-shot

A scheduled or manual one-shot run completes at most one implementation or
alignment work unit and exits. A trigger supplies timing, not product authority.
If no active goal or explicit bounded maintenance request exists, the run makes
no repository change.

No exact schedule is part of this repository contract. Any external automation
must obey the same no-overlap, authority, validation, review, and commit rules.

### Model routing

Continuous Goal and scheduled orchestration and implementation use
`gpt-5.6-terra` with high reasoning. Fresh independent implementation review
and whole-goal alignment use `gpt-5.6-sol` with high reasoning. Luna is not used
in this loop.

These development models are not simulation characters. Mara's optional local
model boundary is separate from the development loop.

## No-Overlap Gate

Before a newly triggered Goal, scheduled run, or manual run first touches the
repository, inspect active Codex work for 2084. Ignore only the task performing
the check. If another 2084 task, loop orchestrator, or subagent is queued or
running, stop without repository work at **ACTIVE RUN EXISTS**. If task activity
cannot be inspected reliably, stop at **ACTIVE RUN STATUS UNKNOWN**.

Iterations inside the same continuous Goal are not overlap, but every work unit
must finish, wait for, or stop all of its subagents before beginning another.
An orchestrator must not disappear while a child still owns repository work.

## Sources of Authority

Read in this order:

1. `AGENTS.md` — project-wide working constraints.
2. `docs/plans/CURRENT.md` — compact current status and run boundary.
3. The active goal linked by `CURRENT.md`, when one exists.
4. That goal's shared implementation state.
5. Only enough relevant implementation and tests to select one current gap.
6. Only the detailed specification relevant to that gap.

Read the README, Core Construct, Architecture, UI Architecture, Design
References, broader proposals, completed goals, and historical experiments only
when the active specification routes there or an invariant is otherwise
unclear. A proposal is not an implementation checklist. `experiments/` remains
read-only historical evidence unless an approved goal explicitly targets it.

If authoritative sources conflict in a way that changes product direction or a
lasting architecture choice, stop at **NEEDS OWNER DECISION**.

## Authority

Within an active goal, the loop may:

- implement one coherent change that advances one unmet criterion;
- add or update tests that prove behavior or protect an affected invariant;
- update factual implementation and progress documentation;
- simplify or remove code when that is the smallest goal-aligned solution;
- delegate genuinely independent bounded work with exclusive ownership;
- mark a criterion met only after proportionate evidence and independent review;
- commit the complete work unit.

It may not:

- select, broaden, replace, or continue beyond the active goal;
- settle open product, worldbuilding, or lasting architecture questions;
- treat a completed goal, proposal, or open question as permission to build;
- modify historical experiments without explicit scope;
- push, merge, publish, discard user work, or weaken tests to obtain a pass;
- present an authored outcome as emergence or grant an agent hidden knowledge.

The owner retains product and goal authority. The main agent owns gap selection,
integration, validation, progress recording, the completion decision, and the
final report for each authorized run.

## Preconditions

Before implementation, confirm:

- an active owner-approved goal exists, or the owner explicitly authorized the
  exact bounded maintenance task;
- no other project task owns the checkout;
- the working tree contains no unrelated unfinished change that overlaps the
  task;
- the active goal and implementation state agree about current status;
- no incomplete run is recorded;
- the proposed work fits one fresh context and creates an honest evidence claim;
- baseline validation passes, or any pre-existing failure is recorded and
  demonstrably unrelated.

Never discard, stage, or commit unrelated user changes. If they prevent safe
work, stop at **BASELINE BLOCKED** and report the exact paths.

## One Work Unit

### 1. Orient

Read the compact index and applicable authority. If alignment is due, perform a
read-only whole-goal review without selecting implementation. Otherwise inspect
only enough code and tests to identify the smallest useful current gap.

### 2. State the evidence claim

Before editing, state:

> This work advances criterion X by producing behavior Y, verified by evidence
> Z.

For owner-directed maintenance, replace the criterion with the exact requested
outcome. If no honest claim can be made, make no change.

Record only the current work unit in shared state when an active goal requires
it. Do not record later tasks or a preferred sequence.

### 3. Partition carefully

The main agent may delegate bounded investigation or implementation only when
the work is genuinely independent. Give every writer exclusive files or
modules, agreed interfaces, relevant constraints, and a concise return format.
Do not use concurrent writers on a shared schema, registry, central coordinator,
or the same tests.

Skip delegation when coordination costs more than it saves. The main agent may
not delegate goal selection, the evidence claim, integration, or completion.

### 4. Implement one coherent change

Make the smallest change that can satisfy the evidence claim. Do not add
speculative extension points. Infrastructure work is justified only when it is
necessary for a named criterion and has an immediate behavioral use.

Preserve these invariants:

- `EventLog` is append-only objective evidence;
- official-record changes do not rewrite history or automatically deliver an
  observation;
- agents act only from information and access actually available to them;
- public expression remains an attempted action;
- model output is not automatically truth, memory, or consequence;
- normal presentation and the omniscient inspector remain separate;
- the focal character remains autonomous rather than a player puppet.

### 5. Validate proportionately

Run focused checks first, then `./scripts/check.sh`. When observable simulation
behavior changes, also run the normal scenario and inspector. Review the diff
for:

- impossible knowledge or authority;
- accidental history mutation or observation delivery;
- forced outcomes described as emergence;
- tests changed beyond the intended behavior;
- normal-view privacy leaks;
- complexity that does not improve the active question;
- stale or contradictory documentation.

Always run `git diff --check`. Validate documentation links when documentation
changes.

### 6. Obtain independent review

After implementation and local validation, use a fresh read-only
`gpt-5.6-sol` high-reasoning reviewer. Provide the applicable authority, final
diff, and validation results, but do not ask it to confirm the implementer's
reasoning. The reviewer looks for goal mismatch, factual errors, hidden
authority, broken invariants, missing evidence, test gaps, privacy leaks, and
unnecessary complexity.

Resolve every material finding and repeat independent review after material
corrections. Documentation-only implementation and whole-goal alignment still
require fresh independent review.

### 7. Record and commit

Update shared implementation state only with verified facts. Mark a criterion
met only when its evidence is proportionate. Clear the current-run record during
commit preparation and never record a future task.

Review the final diff, then create one coherent commit containing the change,
its tests where applicable, and factual progress documentation. Do not include
unrelated files. Never commit a known failing or partial result as complete.

In continuous Goal mode, begin another unit only after the commit and from the
updated repository state. A one-shot run exits after the commit.

## Alignment and Saturation

- A criterion with verified evidence is closed unless a regression or affected
  invariant justifies reopening it.
- After at most three implementation work units, perform a separate whole-goal
  alignment before another implementation unit.
- Alignment reviews evidence, complexity, removals, and completion; it does not
  choose later work.
- Two infrastructure-only units must not occur without focused behavioral
  evidence.
- A no-change result is valid when no justified change advances the goal.

## Terminal States

- **TASK COMPLETE** — one implementation or maintenance unit is validated,
  reviewed, recorded where applicable, and committed.
- **ALIGNMENT COMPLETE** — verified goal evidence was reviewed and recorded;
  no implementation task was selected.
- **ACTIVE RUN EXISTS** — another project task or agent owns the checkout.
- **ACTIVE RUN STATUS UNKNOWN** — overlap could not be ruled out safely.
- **NEEDS OWNER DECISION** — continuing requires authority or a material choice
  outside the active goal.
- **GOAL COMPLETE** — every criterion is verified; mark the goal complete,
  commit that state, and stop before selecting another goal.
- **NO ACTIVE GOAL** — no implementation goal or bounded maintenance authority
  exists.
- **NO JUSTIFIED CHANGE** — no change would honestly advance the authorized
  outcome.
- **BASELINE BLOCKED** — existing repository state prevents safe work.

For a completed unit, report the authorized outcome, observed result, changed
files, validation, review findings, commit, forced or special cases, and any
remaining owner decision. Keep observation separate from interpretation and do
not imply that passing a bounded test proves a broader simulation claim.
