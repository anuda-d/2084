# First living slice delivery report

> Historical delivery record. The later
> [Lie and Doublethink architecture proposal](../LIE_AND_DOUBLETHINK_ARCHITECTURE.md)
> identifies proposed next modules and preserves the implementation described
> here as the factual baseline; those modules were not part of this delivery.

## 1. Implemented simulation

The delivered slice is a standard-library Python simulation with a reusable
`Simulation.step()` and `Simulation.run()` boundary. One focal character and two
supporting characters act autonomously for 24 ticks across home, workplace, and
allocation office. The run includes scheduled work, time-consuming travel, a
direct resource observation, incompatible official claims, an objectively
constrained allocation, delayed observations, public pressure, private/public
belief divergence, and a physical perspective-bound diary.

The behavior comes from configured initial state, the travel graph, institutional
claim schedule, supporting schedules, deterministic policy priorities, action
validation, a hidden objective commitment, pressure 0.8, a conformity threshold
of 0.7, and fixed action durations. It is not claimed to model consciousness,
human fidelity, or unconstrained emergence.

The hardened action boundary records immutable completed or rejected results.
Policies advance from those results instead of assuming an attempt succeeded,
and malformed actions fail without consequential mutation. The two-unit
handover becomes a simple focal-character holding when delivered, leaving one
household unit explicitly unmet.

## 2. Recovered starting point

- Delivery branch: `codex/first-living-slice`
- Recovered branch: `recover-agent-loop`
- Recovered PR #3 head: `869069a0968efbbb5404119a56730e1b67ad3612`
- Merge base with `main`: `4ab5fccd03e7b48529428627eb5b429af65a8701`
- Baseline: 63 tests passed before implementation changes; no initial failures.

PR #3 was fetched through `refs/pull/3/head` onto a normal local branch. `main`
was not overwritten or force-pushed. Details are in
[`BASELINE.md`](BASELINE.md).

## 3. Architectural changes

- Added a run-scoped world, configuration, seed, tick, agent registry, action
  queue, completion condition, and deterministic event/observation identifiers.
- Added immutable attempted actions and separate linked outcomes or rejections.
- Added actor-safe terminal action results to restricted policy views and replay
  records; rejected attempts no longer satisfy policy progress checks.
- Added centralized per-action parameter, provenance, access, and belief
  validation with safe linked rejections for malformed attempts.
- Added simple per-agent resource holdings and remaining-need presentation at
  the delayed handover boundary.
- Added three-location travel constraints and tick-based work, travel, diary
  write, and diary read durations.
- Added structured sourced beliefs with confidence, context, explicit conflict
  links, and serializable transition evidence.
- Added restricted `AgentView` and `InstitutionView` policy inputs. Policy
  selection is pure and cannot inspect objective resources or history.
- Added one bounded institution with scheduled official claims and no automatic
  access to diary or private agent state.
- Added independently scheduled and reactive supporting policies.
- Added a filtered snapshot-only terminal observer and a separately labelled
  omniscient inspector.
- Added JSON-compatible complete history data and same-seed replay checks.
- Preserved all recovered experiments and tests while promoting the reusable
  engine to the top-level simulation code.

## 4. Exact commands

Normal observer:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30
```

Development inspector:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect
```

All tests:

```bash
./scripts/check.sh
```

Equivalent direct test command:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m unittest discover -s experiments/tests -p 'test_*.py'
```

No package installation is required.

## 5. Test results

The recovered baseline was 63 passing tests. The hardened suite contains **101
passing tests** with no failures. It covers step order, spatial and temporal
constraints, knowledge boundaries, action/resolution separation, contradictions
and pressure thresholds, supporting autonomy, diary authorization and
immutability, malformed-action rejection, resolved-action knowledge, resource
holdings, presentation privacy, CLI execution, completion, JSON compatibility,
and deterministic replay.

The suite passed both in the working tree and in an isolated clean copy without
Git metadata, caches, or environment-specific files. In that clean copy,
`./scripts/check.sh` ran 101 tests in 0.243 seconds; both documented simulation
commands also exited successfully.

Two seed-42 executions separated by unrelated global-random activity produced
identical JSON history with SHA-256
`971aed2e50101508e9779957e3fee2ec0ee90e814285b4f97fdff56afbf901d0`.

## 6. Short example transcript

```text
Tick 07 | Allocation Office
Action: wait for the allocation briefing
Observed: directly saw 3 allocation units.
Private belief: 3 units (90% confidence).

Tick 08 | Allocation Office
Action: request 3 allocation units
Observed: official broadcast claimed 5 allocation units.

Tick 09 | Allocation Office
Allocation outcome: 2 granted and 1 unfilled.
Household allocation: 2 held; 1 still needed.

Tick 10 | Allocation Office
Action: repeat the official 5-unit claim publicly
Public pressure: the allocation clerk repeated the official 5-unit claim.

Tick 18 | Home
Diary read returned the earlier 3-unit perspective.
```

The normal transcript intentionally omits the one-unit commitment, complete
event stream, institution identifier, NPC-private records, and resolver inputs.

## 7. Known limitations

- Scenario vocabulary, quantities, claim times, pressure, threshold, schedules,
  and durations are provisional.
- Resource possession is an integer holding per agent, not a physical inventory
  or model of transfer, storage, use, and consumption.
- The default run uses deterministic rules and currently makes no random choice,
  although it owns and records a run-scoped seeded generator.
- Belief updates cover one structured proposition with two confidence rules;
  there is no broad memory, emotion, personality, or theory-of-mind model.
- Institution behavior is limited to bounded records and scheduled public claims.
- Replay data is in memory and JSON-compatible, not a durable save/checkpoint.
- The terminal output is a read-only observer, not a game UI or study dashboard.

## 8. Decisions for owner review

- Mara Vale, Ilan Reed, Sena Orr, and “Civic Allocation Office” are provisional
  names, not settled worldbuilding.
- Direct sight currently reports the three units physically present, while one
  unit is already committed and therefore unavailable during resolution. This
  distinction is useful for the slice but may need different product vocabulary.
- Public conformity occurs at pressure 0.8 against threshold 0.7. Those values
  demonstrate an inspectable condition and are not a general psychology model.
- The observer shows a readable summary of Mara's private beliefs and confidence.
  The institution and supporting characters do not receive that summary.
- The claim schedule is authored at ticks 8 and 16. Policies decide responses
  from delivered evidence; the schedule itself is not emergent.
- The engine records a seed even though the acceptance path has no random choice.
  A future stochastic rule should justify why it improves behavior before using
  the generator.

## 9. Intentionally excluded follow-ups

- Graphical map, animation, game engine, web application, API, or deployment.
- LLM decisions or generated dialogue, vector/semantic memory, or AI-defined
  world consequences.
- Large populations, full economy, political system, surveillance network, or
  language-control system.
- Multiplayer, observer intervention, direct character control, or always-on
  simulation time.
- Diary concealment, discovery, confiscation, evidence, sharing, or editing.
- Durable saves, background workers, distributed execution, or real-time clocks.
