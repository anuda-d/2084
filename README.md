# 2084

2084 is an autonomous agent-based social simulation experienced primarily through one focal character's life.

The character is not a puppet waiting for constant input. The intended simulation lets them perceive a limited part of the world, form beliefs, remember imperfectly, make decisions, and live with consequences while other people and institutions continue to act. The current slice implements limited observations and structured beliefs, but not memory decay or a general model of imperfect recall. The observer follows this person closely, can inspect a readable account of their understanding, and may eventually have limited ways to redirect them.

2084 is not currently conceived as a conventional objective-driven game or as a formal study dashboard. Its intended form is a watchable, inspectable simulation. Rigorous state boundaries, append-only records, and deterministic reproduction make the current behavior trustworthy and understandable underneath the experience. Durable saves and full-run replay are not implemented yet.

## Current Direction

The setting takes substantial inspiration from the social pressures in George Orwell's *Nineteen Eighty-Four* without recreating its characters, plot, or world exactly.

The current center of gravity is a small authoritarian social world in which:

- actual events and official accounts can contradict one another;
- an institution may revise its current public record without changing the
  simulation's append-only objective history;
- surveillance is powerful but incomplete, and uncertainty can produce self-censorship;
- the focal character may privately believe, publicly say, and contextually act on different versions of reality;
- relationships, rumors, reports, status, scarcity, and institutional pressure affect behavior;
- the wider world continues beyond what the focal character sees;
- surprising outcomes should arise from interacting pressures rather than a prescribed story.

This direction remains provisional. The current slice now demonstrates one
bounded official-record rewrite and its effect on delivered agent knowledge
without attempting to reproduce an entire society.

## Repository layout

The runnable project is organized directly at the repository root:

```text
simulation/   World state, events, actions, beliefs, and the engine
policies/     Rules characters and institutions use to choose actions
scenarios/    Authored starting worlds and runnable entry points
observer/     Normal and development-facing output
tests/        Tests for the current simulation
experiments/  Older prototypes retained as historical evidence
docs/         Current documents and future plans
scripts/      Project checks
```

There is no second 2084 package inside the 2084 repository. These directories
are the current application unless explicitly described as experiments or plans.

## Current runnable slice

The repository now contains a deterministic, terminal-based first living slice.
It follows one autonomous focal character and two supporting characters through
24 ticks spanning work, travel, an allocation contradiction, public pressure,
and a physical diary. Attempted actions resolve into explicit completed or
rejected results, and the focal character retains two granted allocation units
while one need remains unmet. The normal command is intentionally filtered to
the focal character; it shows the three-packet schedule and later two-packet
schedule only after separate valid consultations. A separate inspector exposes
the hidden rewrite and complete objective development records.

Run it from the repository root:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30
```

Use the explicitly omniscient inspector:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect
```

Run all tests:

```bash
./scripts/check.sh
```

See [ARCHITECTURE.md](docs/main/ARCHITECTURE.md) for the tick order and state boundaries,
the [Lie and Doublethink architecture proposal](docs/plans/LIE_AND_DOUBLETHINK_ARCHITECTURE.md)
for the proposed next deepening,
and the [delivery report](docs/plans/first-living-slice/DELIVERY.md) for the scenario's
rules and limitations. The implementation is an engine feasibility slice, not a
claim of human realism or a complete society.

### How the current logic is divided

- `scenarios/first_day.py` assembles the authored world, agents,
  schedules, thresholds, and action durations.
- `simulation/world.py` owns objective locations, resources,
  institutional state, and the physical diary.
- `simulation/events.py` keeps objective events separate from the
  observations delivered to particular agents.
- `simulation/beliefs.py` creates source-linked structured beliefs and
  retains explicit contradictions.
- `policies/` contains deterministic decision rules. The current
  slice does not use an LLM or other AI decision model.
- `simulation/engine.py` advances time, supplies restricted policy
  views, validates attempts, resolves consequences, and produces the focal
  projection.
- `observer/terminal.py` renders only focal-character knowledge;
  `observer/inspector.py` is the separate omniscient development
  view.

The current first day is heavily authored. Policies react autonomously to
delivered evidence, but the route through work, allocation pressure, public
conformity, and the diary should not be described as an emergent story.

## Documents

Current source-of-truth documents live in `docs/main/`:

- [Core Construct](docs/main/CORE_CONSTRUCT.md) — the experience, central tensions, and current conceptual pillars.
- [Architecture](docs/main/ARCHITECTURE.md) — boundaries between world truth, knowledge, decisions, institutions, and presentation.
- [UI Architecture](docs/main/UI_ARCHITECTURE.md) — the focal-character perspective and ways to make autonomous behavior understandable.
- [Design References](docs/main/DESIGN_REFERENCES.md) — what is being taken from Orwell, the world-modeling paper, and the reference simulation.
- [Agentic Development Loop](docs/main/DEVELOPMENT_LOOP.md) — the scheduled autonomous cycle, progress gates, and escalation boundary.

Proposals and completed implementation records live in `docs/plans/`:

- [Lie and Doublethink architecture](docs/plans/LIE_AND_DOUBLETHINK_ARCHITECTURE.md) — proposed next modules; these are not implemented yet.
- [Current development objective](docs/plans/CURRENT.md) — the single owner-approved goal and verified progress.
- First living slice records — the completed [goal](docs/plans/first-living-slice/GOAL.md), [recovery baseline](docs/plans/first-living-slice/BASELINE.md), and [delivery report](docs/plans/first-living-slice/DELIVERY.md).

Other repository guidance:

- [experiments/README.md](experiments/README.md) — retained prototypes that predate the reusable engine.
- [AGENTS.md](AGENTS.md) — guidance for coding agents and future contributors.

## Working Approach

Continue through small living situations and one consequential contradiction at
a time. The proposed next slice deepens the existing allocation contradiction:
one official artifact is rewritten while objective history remains unchanged,
agents encounter versions only through valid delivery paths, and a private or
stale record can preserve an earlier account.

The slice is working if the character responds intelligibly from their own limited knowledge, the world does not grant impossible information or authority, and the observer can trace important behavior without seeing a canned plot.

Answers can remain uncertain. These documents should make uncertainty visible while preventing the project's established direction from being repeatedly rediscovered.
