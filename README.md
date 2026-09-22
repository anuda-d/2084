# 2084

Watch one autonomous person navigate conflicting experience, testimony, and official accounts.
Mara Vale acts from limited information while the world, other people, and institutions continue independently.
This is a terminal-based feasibility prototype, not a finished game or a claim to simulate human psychology.

## Run locally

Use Python 3.11 or later from the repository root.
There are no third-party runtime dependencies.

```sh
python3 -m scenarios.first_day --seed 42 --ticks 30
```

The deterministic `first_day_v3` scenario completes at tick 28.
Mara encounters a three-packet official entitlement, receives two packets, later encounters a revised entitlement, and carries the contradiction into public speech and a physical diary.
Normal output contains only her admitted perspective.
Add `--inspect` for the separately labelled omniscient causal record:

```sh
python3 -m scenarios.first_day --seed 42 --ticks 30 --inspect
```

## Accelerated day

The quiet offline composition reaches exactly `Day 1 00:00` without a model call:

```sh
python3 -m scenarios.autonomous_day --seed 42
```

The scripted comparison shows Ilan receiving transit information, telling Mara in person, and giving her an ordinary action opportunity:

```sh
python3 -m scenarios.autonomous_day --seed 42 --focal-policy scripted
```

The consequential-choice comparison adds incompatible official and personal accounts, competing work and household obligations, physical travel consequences, and a later decision:

```sh
python3 -m scenarios.autonomous_day --seed 42 --focal-policy scripted --consequential-choice
```

These scripted choices are authored evidence, not live or emergent behavior.
Add `--inspect` to either command for source-to-action causal links and final state.
The optional earlier conflict opportunity is:

```sh
python3 -m scenarios.autonomous_day --seed 42 --focal-policy scripted --consequential-choice --conflict-opportunity-timing
```

The timing option requires `--consequential-choice`.
It moves the objective service change to 07:59 and retains the 08:00 official notice.
When Ilan has the source and Mara is at the workplace, both accounts can reach her before one coalesced 08:00 decision.
It neither guarantees that access nor selects a model response.
Omitting it preserves the original consequential-choice timing.
The [active implementation state](docs/plans/first-consequential-choice/IMPLEMENTATION_PLAN.md) records authored builder options, accepted comparisons, and outstanding live evidence.

## Optional local model

Both scenarios support explicit model-backed Mara through the same restricted boundary:

```text
AgentView -> MaraHarness -> ActionAttempt -> world validation and resolution
```

The supported model is exactly `qwen3:4b-instruct` on Ollama.
Supply the server's numeric private, loopback, or link-local HTTP origin; the following address is an example:

```sh
python3 -m scenarios.autonomous_day \
  --seed 42 --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct
```

For the active goal's composition, add `--consequential-choice` and, when relevant, `--conflict-opportunity-timing`.
The first-day command accepts the same explicit provider flags.
The adapter accepts no URL path, credentials, DNS name, redirect, proxy, model pull, provider history, or automatic transport retry.
Timeouts, unavailable service, malformed responses, and invalid choices produce explicit safe waits without invoking the scripted policy.
Live choices can vary even at temperature zero.
Recorded choices reproduce world behavior without another provider call when the seed and authored configuration match.

## Private live audit

A live autonomous-day run can write to a new directory that does not already exist:

```sh
python3 -m scenarios.autonomous_day \
  --seed 42 --focal-policy ollama \
  --ollama-base-url http://192.168.1.50:11434 \
  --ollama-model qwen3:4b-instruct \
  --audit-dir /private/tmp/2084-live-audit
```

The bundle uses owner-only permissions and includes a focal-safe transcript, sanitized inspector, private decision records, measured verdict, and artifact manifest.
Its writer checks model/source identity, provider provenance, causal links, privacy, growth limits, exact-day completion, and provider-free recorded replay.
Recheck an unchanged bundle's stored evidence and integrity with:

```sh
python3 -m scenarios.autonomous_day_audit /private/tmp/2084-live-audit
```

A generic audit pass does not establish the active goal's conflict-informed choice criterion.
Preserve failed samples and the goal's bounded live-experiment authorization.

## Develop

```sh
./scripts/check.sh
python3 -m devloop status
python3 -m devloop dashboard
```

The full-screen dashboard shows live activity, Git changes, checks, and result details.
Use `h/l` or `1-4` to switch views, `j/k` to scroll, `p` to pause, `r` to resume, and `q` to close the dashboard without stopping the loop.
The Mac runs development and tests; the Windows PC supplies only the optional Ollama endpoint.
[Development Loop](docs/main/DEVELOPMENT_LOOP.md) documents installation, pause/resume, validation, and runner-owned commits.
Start agent work from [CURRENT.md](docs/plans/CURRENT.md) and [AGENTS.md](AGENTS.md).

| Location | Responsibility |
| --- | --- |
| `scenarios/` | Runnable compositions, CLIs, and private audit workflow |
| `simulation/` | Time, world state, actions, events, records, and understanding |
| `policies/`, `characters/mara/` | Deterministic policies and Mara's restricted model inputs |
| `observer/` | Focal-safe terminal view and separate development inspector |
| `devloop/`, `scripts/` | Development runner, service installation, and repository checks |
| `tests/` | Behavioral, privacy, failure, replay, and runner regressions |

[Core Construct](docs/main/CORE_CONSTRUCT.md) defines product direction and reference boundaries.
[Architecture](docs/main/ARCHITECTURE.md) records implemented contracts, limitations, and regression coverage.
There is no graphical interface, durable save system, model-backed supporting cast, or general social simulation.
