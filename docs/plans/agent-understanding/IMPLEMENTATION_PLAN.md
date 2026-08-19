# Agent Understanding Implementation State

Status: active shared state; no future tasks are planned.

## Run State

- Incomplete run: none
- Last completed run: none
- Verified implementation runs since alignment: 0
- Alignment due: after three verified implementation runs

## Goal Progress

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| AU-1 Memory traces | open | none |
| AU-2 Conflict | open | none |
| AU-3 Public stance | open | none |
| AU-4 Public action | open | none |
| AU-5 Diary record | open | none |
| AU-6 Resurfacing | open | none |
| AU-7 Recheck | open | none |
| AU-8 Boundaries | open | none |
| AU-9 Presentation | open | none |
| AU-10 Reproduction | open | none |

This table records only verified goal evidence. It is not a task backlog or an
implementation sequence.

## Per-Run Selection

Each fresh implementation run:

1. reads the goal and this verified state;
2. locates only enough relevant code and tests to find the smallest useful gap;
3. selects one bounded task that can produce new evidence for one open
   criterion in one context window;
4. records that task under `Current Run` and `Incomplete run` before changing
   implementation;
5. reads only the specification relevant to the selected task;
6. states the intended behavior and focused evidence;
7. implements, validates, obtains fresh Sol-high review, records verified
   evidence, commits, and exits.

Do not select or record a future task. Criteria order does not prescribe
implementation order. If no honest task advances the goal, make no change.

## Current Run

- Status: none
- Criterion: none
- Task: none
- Specification: none
- Expected evidence: none

## Completion Rules

- Clear `Current Run` and `Incomplete run` only after validation, independent
  review, state update, and commit preparation are complete.
- Mark a criterion met only when proportionate verified evidence satisfies it.
- Append concise observed evidence to the log below.
- Increment the alignment counter after each verified implementation run.
- If a selected task is too large, replace it with a smaller task before
  implementation; do not create a future queue.
- If owner authority is required, leave implementation unchanged and record the
  decision needed.

## Alignment

When alignment is due, a fresh Terra-high orchestrator asks a fresh Sol-high
read-only reviewer to compare all verified evidence with the goal. Resolve
blocking findings, update criterion status, record removal or simplification
recommendations, reset the counter, commit, and exit.

Alignment does not select, suggest, or record the next implementation task.

## Verified Run Log

No implementation run has been completed for this goal.
