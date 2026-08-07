# First living slice recovery baseline

This note records the implementation state recovered before work on the first
living simulation slice began.

## Recovery

- Source: GitHub pull request #3, fetched through `refs/pull/3/head`.
- Local branch: `recover-agent-loop`.
- Recovered head: `869069a0968efbbb5404119a56730e1b67ad3612`.
- Merge base with `main`: `4ab5fccd03e7b48529428627eb5b429af65a8701`.
- The recovery branch was created normally; `main` was not rewritten.

## Baseline validation

Environment: Python 3.13.7.

Command run from the repository root:

```bash
python3 -m unittest discover -s experiments/tests -p 'test_*.py'
```

Result before implementation changes: **63 tests passed in 0.109 seconds**.
There were no initial test failures. The recovered README also referred to
`./scripts/check.sh`, but that file was absent at the recovered head.

## Reusable evidence already present

- `SourceLinkedHistory` keeps append-only objective events separate from
  agent-scoped observations with stable in-run identifiers.
- Decision helpers accept filtered observations and return attempted choices
  without directly resolving them.
- Resolution helpers validate objective constraints and link attempts to
  outcomes.
- Physical diary records retain a perspective-bound immutable entry and enforce
  possession and elapsed time.
- The fixed transcript avoids displaying the raw objective history.
- Separate deterministic-transition and replay experiments establish useful
  seed, immutability, and validation-before-mutation examples.

## Fixed-script behavior to replace at the new seam

`run_provisional_focal_life_scenario()` is a 2,418-line-module composition that
calls a prescribed sequence at authored ticks. It has no reusable
`Simulation.step()` container, spatial travel graph, registry of independently
scheduled agents, completion condition, institution boundary, general action
vocabulary, or separate omniscient inspector command. Its transcript presents
the fixed evidence after the run instead of projecting each simulation step.

The recovered implementation is therefore retained and tested, not discarded.
The first living slice adds a separate reusable engine and moves the acceptance
scenario through that boundary.
