# 2084

2084 is an early, terminal-based social simulation about following one
autonomous person through a world they can only partly understand.

The long-term idea is to watch a life unfold inside a small society shaped by
scarcity, institutions, relationships, limited information, and pressure. The
focal character is not a player-controlled puppet and does not know everything
the simulation knows. Other people and institutions continue acting while the
observer sees the world mainly through that character's experience.

The project takes thematic inspiration from George Orwell's *Nineteen
Eighty-Four*, especially the gap between lived experience, public behavior, and
official accounts. It is not an adaptation of Orwell's plot, characters, or
setting.

## What exists today

The repository contains one deterministic prototype scenario, `first_day_v3`.
It follows Mara Vale and two supporting characters through a 28-tick workday.
Mara:

- travels between home, work, and a civic allocation office;
- sees three allocation units but physically receives only two;
- consults an official schedule that initially promises three packets;
- experiences public pressure, encounters the revised two-packet schedule, and
  repeats that revised entitlement publicly while retaining separate evidence;
- writes the earlier three-packet schedule claim into a physical diary;
- reads that entry later and makes one ordinary trip to recheck the public
  schedule; and
- finishes the day with one household unit still unmet.

The route is heavily authored, but the characters are not moved directly by a
player. Transparent rule-based policies choose attempted actions from limited
information. The simulation then checks whether each attempt is valid and
records what actually happens.

The current prototype also preserves an important separation:

- **Objective history** records what happened and is append-only.
- **Official records** can gain a new current version without rewriting that
  objective history.
- **Observations** determine what a particular character actually encounters
  and when. Publishing or revising a record does not automatically tell every
  character about it.
- **Agent state** can contain source-linked beliefs and memory traces derived
  from delivered observations.
- **Presentation** keeps the normal view focused on Mara, while a separate
  development inspector can reveal the complete underlying record.

This is a feasibility prototype, not a finished game or a claim to model human
psychology.

## Run the simulation

The project uses Python's standard library and has no third-party runtime
dependencies. From the repository root, run:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30
```

The normal output shows only information deliberately admitted to Mara's view.
The scenario completes at tick 28; `--ticks 30` simply gives it enough room to
reach that completion condition.

To see the explicitly omniscient development record, run:

```bash
python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect
```

The inspector is intentionally verbose. It includes objective events,
agent-specific observations, action outcomes, official-record versions,
physical state, beliefs, and the new Agent Understanding evidence.

Useful options:

```text
--seed N       Choose the deterministic random seed.
--ticks N      Limit how many ticks may run.
--inspect      Show the omniscient development view.
```

Run the complete test suite with:

```bash
./scripts/check.sh
```

That command checks both the current engine and the older prototypes retained
under `experiments/`.

## Current development status

The bounded **Agent Understanding** experiment now demonstrates that Mara can
retain two delivered official versions, link their conflict, use the revised
version as a public working stance under pressure, and later resurface the
earlier version through a physical diary strongly enough to prompt one ordinary
public-schedule recheck.

The evidence remains deliberately inspectable and limited:

- only delivered observations create source-linked memory traces and claims;
- the public and diary stances retain their exact sources and transition
  history;
- supporting characters and institutions receive no focal-private diary
  understanding;
- the normal transcript explains the encountered behavior without omniscient
  identifiers; and
- the development inspector exposes the detached causal record.

The older narrow belief model still supplies the “Private belief” line visible
in the terminal output. It represents Mara's direct sight of three physical
allocation units. It remains separate from the official-version conflict and
stance system.

## Known limits

- The scenario uses deterministic hand-written policies, not an LLM or other AI
  decision model. The approved architectural direction is to begin with one
  model-backed focal character whose structured choices become attempted
  actions, while the simulation retains authority over knowledge boundaries and
  consequences; this is not implemented yet.
- The first-day route, institutional rewrite timing, public pressure, and diary
  opportunity are authored inputs. The result is bounded evidence, not an
  emergent story.
- Memory decay, forgetting, general language understanding, emotion,
  personality, relationships, surveillance, punishment, and a broader living
  society are not implemented.
- There is no graphical interface, durable save system, executable replay, or
  player intervention.
- The inspector is a development tool, not the intended final experience.

These limits are deliberate. The project is testing small, inspectable
mechanisms before adding scale or less predictable behavior.

## Repository guide

```text
scenarios/    Authored worlds and runnable entry points
simulation/   Time, world state, actions, events, records, and understanding
policies/     Deterministic character and institution decision rules
observer/     The filtered terminal view and omniscient inspector
tests/        Tests for the current engine and scenario
experiments/  Older prototypes kept as historical evidence
docs/         Product direction, architecture, goals, and verified progress
scripts/      Repository checks
```

The most useful documents are:

- [Core Construct](docs/main/CORE_CONSTRUCT.md) — the intended experience and
  thematic direction.
- [Architecture](docs/main/ARCHITECTURE.md) — the boundaries between world
  truth, observations, decisions, institutions, and presentation.
- [Current Development Index](docs/plans/CURRENT.md) — the active development
  entry point.
- [Model-Backed Focal Character Goal](docs/plans/model-backed-focal-character/GOAL.md)
  — the active bounded Phase 3B goal.
- [Model-Backed Focal Character Implementation State](docs/plans/model-backed-focal-character/IMPLEMENTATION_PLAN.md)
  — verified progress for the active goal.
- [Agent Understanding Goal](docs/plans/agent-understanding/GOAL.md) — the
  completed Phase 3A foundation.
- [Verified Implementation State](docs/plans/agent-understanding/IMPLEMENTATION_PLAN.md)
  — evidence retained from the completed Agent Understanding goal.

For coding agents and contributors, [AGENTS.md](AGENTS.md) describes the working
agreements and the one-slice development loop.
