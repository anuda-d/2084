# 2084

2084 is an autonomous agent-based social simulation experienced primarily through one focal character's life.

The character is not a puppet waiting for constant input. They perceive a limited part of the world, form beliefs, remember imperfectly, make decisions, and live with consequences while other people and institutions continue to act. The observer follows this person closely, can inspect a readable account of their understanding, and may eventually have limited ways to redirect them.

2084 is not currently conceived as a conventional objective-driven game or as a formal study dashboard. Its intended form is a watchable, inspectable simulation. Rigorous state boundaries, records, and replay exist to make the behavior trustworthy and understandable underneath the experience.

## Current Direction

The setting takes substantial inspiration from the social pressures in George Orwell's *Nineteen Eighty-Four* without recreating its characters, plot, or world exactly.

The current center of gravity is a small authoritarian social world in which:

- actual events and official accounts can contradict one another;
- surveillance is powerful but incomplete, and uncertainty can produce self-censorship;
- the focal character may privately believe, publicly say, and contextually act on different versions of reality;
- relationships, rumors, reports, status, scarcity, and institutional pressure affect behavior;
- the wider world continues beyond what the focal character sees;
- surprising outcomes should arise from interacting pressures rather than a prescribed story.

This direction remains provisional. The first implementation should clarify it rather than attempt to reproduce an entire society.

## Current runnable slice

The repository now contains a deterministic, terminal-based first living slice.
It follows one autonomous focal character and two supporting characters through
24 ticks spanning work, travel, an allocation contradiction, public pressure,
and a physical diary. The normal command is intentionally filtered to the focal
character; a separate inspector exposes objective development records.

Run it from the repository root:

```bash
python3 -m experiments.scenarios.first_day --seed 42 --ticks 30
```

Use the explicitly omniscient inspector:

```bash
python3 -m experiments.scenarios.first_day --seed 42 --ticks 30 --inspect
```

Run all tests:

```bash
./scripts/check.sh
```

See [experiments/README.md](experiments/README.md) for the tick order, state
boundaries, scenario rules, and limitations. The implementation is an engine
feasibility slice, not a claim of human realism or a complete society.

## Documents

- [CORE_CONSTRUCT.md](CORE_CONSTRUCT.md) — the experience, central tensions, and current conceptual pillars.
- [ARCHITECTURE.md](ARCHITECTURE.md) — boundaries between world truth, knowledge, decisions, institutions, and presentation.
- [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md) — the focal-character perspective and ways to make autonomous behavior understandable.
- [DESIGN_REFERENCES.md](DESIGN_REFERENCES.md) — what is being taken from Orwell, the world-modeling paper, and the reference simulation.
- [AGENTS.md](AGENTS.md) — guidance for coding agents and future contributors.

## Working Approach

Begin with one small living situation and one consequential contradiction. A useful early slice might follow a focal character through an ordinary day in which their experience, an official announcement, and another person's account do not agree.

The slice is working if the character responds intelligibly from their own limited knowledge, the world does not grant impossible information or authority, and the observer can trace important behavior without seeing a canned plot.

Answers can remain uncertain. These documents should make uncertainty visible while preventing the project's established direction from being repeatedly rediscovered.
