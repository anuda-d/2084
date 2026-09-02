# Agentic Development Loop

Status: current operating contract for owner-authorized continuous, scheduled,
and manual development.

The compact contract in `docs/plans/CURRENT.md` is the normal entry point. This
document expands it. As of August 23, 2026, First Autonomous 24-Hour Living Day
is the active owner-approved implementation goal.

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

Continuous Goal mode is primary while the owner has started an active goal.
It is a real app-level Goal created through `create_goal`, not the repository's owner-approved product goal and not a mode an agent may activate by saying it is active.
The repository goal defines product authority; the app Goal provides durable execution across turns.

When the owner explicitly asks to start the continuous implementation loop, first call `get_goal` before repository work.
If it reports no Goal or a completed Goal, call `create_goal` with the owner-approved objective, boundaries, validation expectations, and verifiable stop condition, then call `get_goal` again.
Continue only when `get_goal` reports `status: active` and the objective covers the requested work.
Perform this verification before task listing or lock acquisition.
If the Goal is paused, blocked, otherwise non-active, or has a different objective, stop at **GOAL MODE NOT ACTIVE** and ask the owner to resume, clear, or resolve it.
Never claim Continuous Goal mode from commentary, repository state, or an earlier turn alone.
Continuous Goal does not use `create_thread`; that tool belongs only to scheduled relay.

One Codex task remains active, completes one reviewed and committed work unit, then starts the next unit from updated repository state.
Every automatically continued turn calls `get_goal` before repository work and then asserts that the same task still owns the repository lock.
A normal Goal turn boundary is not a terminal state while the app Goal status remains active, so the lock remains with that task for automatic continuation.
If a continued turn observes any non-active Goal status, it performs no repository work except releasing a lock it owns, then stops at **GOAL MODE NOT ACTIVE**.
When the objective is genuinely complete, the task commits the verified completion state, releases the lock, and calls `update_goal` with `status: complete`.

### Scheduled relay or manual one-shot

Each scheduled task and manual one-shot completes at most one implementation or
alignment work unit. A trigger supplies timing, not product authority. If no
active goal or explicit bounded maintenance request exists, the task makes no
repository change.

During an owner-authorized scheduled relay window, `TASK COMPLETE` or
`ALIGNMENT COMPLETE` may hand off to exactly one fresh Codex task. The current
task first finishes validation and independent review, records verified state,
commits, stops every subagent, and resolves its own task ID. Before the local
cutoff it verifies the exact saved project through the project listing, then
creates one successor in that project's local checkout with the scheduled
implementation model and reasoning level. If either ID is unavailable or
ambiguous, it reports the handoff failure and creates no task. The successor
prompt names the exact predecessor task ID and directs the successor to reread
`AGENTS.md` and `docs/plans/CURRENT.md`. The predecessor does no more repository
work after creating the successor. It uses one bounded successor progress wait
to confirm dispatch or surface that the child needs attention, does not create a
second successor if the result is missing or unclear, and then exits.

A successor starts no work at or after the cutoff. The cutoff prevents another
cycle from starting; it does not interrupt or abandon a work unit already in
progress. That task finishes its validation, review, recording, and commit, but
creates no successor. A task ending in any other terminal state also creates no
successor. External scheduled triggers remain recovery starts: they no-op when
a task already owns the checkout and can start the relay again when no task
does. A manual one-shot never relays.

The current external automation uses an 18:00 through 23:00
`America/Toronto` relay window, with recovery triggers at 18:00, 19:00, 20:00,
21:00, and 22:00. Exact schedules remain external configuration rather than
product authority. Any external automation must obey the same no-overlap,
authority, validation, review, and commit rules.

### Model routing

Continuous Goal and scheduled orchestration and implementation use
`gpt-5.6-terra` with high reasoning. Fresh independent implementation review
and whole-goal alignment use `gpt-5.6-sol` with high reasoning. Luna is not used
in this loop.

These development models are not simulation characters. Mara's optional local
model boundary is separate from the development loop.

## No-Overlap Gate

Before a newly triggered Goal first touches the repository, confirm its app-level Goal state through `get_goal` as required above.
This Goal-state proof precedes task listing and lock acquisition.
Before that verified Goal, a scheduled task, or a manual run first touches the
repository, inspect active Codex work for 2084. Ignore only the task performing
the check. A scheduled relay successor may also ignore the one exact
predecessor task ID embedded in its creation prompt, because the relay protocol
requires that predecessor to have committed, stopped all subagents, and ended
repository work before creating the successor. The exception does not apply to
a matching title, summary, or inferred predecessor. Inspect every returned
pinned and non-pinned task. If any other visible 2084 task, loop orchestrator,
or subagent is queued or running, stop without repository work at **ACTIVE RUN
EXISTS**. If task activity otherwise cannot be inspected reliably, stop at
**ACTIVE RUN STATUS UNKNOWN**.

A full task-list page is not itself terminal because the app exposes no reliable
continuation. After the visible activity screen and before repository work,
resolve the current task ID and run
`python3 scripts/autonomous_loop_lock.py acquire --task-id <current-id>`. This
durable local record is the checkout-ownership proof. If it reports another
owner, inspect that exact task ID with `read_thread`; takeover is allowed only
when it reports `idle` or `notLoaded` and its latest turn is terminal
(`completed`, `failed`, or `interrupted`). Every other result, including an uninspectable owner,
blocks the new task. Only then may a new task use `takeover
--expected-task-id <owner-id> --verified-inactive`. Before every subsequent
repository-working turn or resumed work unit, the owner must run
`assert-owner --task-id <current-id>` and stop on a mismatch. This makes a task
that resumes after handoff observe that it lost ownership before it resumes
repository work. A task releases its own record on a non-relaying terminal
state, or immediately before it dispatches its successor and becomes
handoff-only. The lock utility rejects simultaneous claims, wrong-owner release,
stale-owner assertions, and recovery without the explicit terminal-owner
verification.

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
- Continuous Goal runs have a verified unfinished app-level Goal established
  through `get_goal` and, when activation was required, `create_goal`;
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

For an implementation work unit, explicitly invoke the installed `$unlazy`
skill in Solo mode after selecting the current gap and before editing. Write one
root `GATES.md` containing only observable gates for this work unit, with
focused checks, the full repository check, and `git diff --check` represented
as runnable gates where applicable. The file is run-scoped and ignored by Git;
verified result counts and decisive evidence belong in shared implementation
state.

Before replacing a prior run's ledger, confirm it contains no unmet gate. If a
stale ledger has unmet gates that do not agree with shared run state, stop at
**BASELINE BLOCKED** rather than erasing the discrepancy. Approve only commands
the main agent has read and understands. Do not install the optional Claude
Code stop hook for this loop.

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

Re-run the current work unit's approved runnable gates with the skill's
`--reverify` path after implementation and after any material review fix. An
unmet gate prevents completion even when another check passed. Any deliberately
abandoned gate must retain its non-empty reason and be surfaced in the run
report and shared evidence.

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
updated repository state. A successful scheduled relay task may create one
fresh successor under the relay contract, then exits. A manual one-shot exits
after the commit.

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
- **GOAL MODE NOT ACTIVE** - Continuous Goal activation is absent, paused,
  blocked, otherwise non-active, mismatched, or unverifiable; do no repository
  work except releasing a lock owned by the current task.

For a completed unit, report the authorized outcome, observed result, changed
files, validation, review findings, commit, forced or special cases, and any
remaining owner decision. Include exact met, unmet, and abandoned `unlazy` gate
counts. Keep observation separate from interpretation and do not imply that
passing a bounded test proves a broader simulation claim.
