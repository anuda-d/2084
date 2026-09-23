# First Consequential Choice Implementation State

Status: active; nine criteria are accepted, while CC-4, CC-11, and CC-12 remain unverified.
This records product evidence for the [approved goal](GOAL.md), not operational state or a task queue.
Use `python3 -m devloop status` for execution state and [Development Loop](../../main/DEVELOPMENT_LOOP.md) for runner ownership.

## Goal progress

| Criterion | Status | Evidence or remaining requirement |
| --- | --- | --- |
| CC-1 Shared referent/conflict | accepted | Delivered official and social claims retain sources, the same interval, and reciprocal conflict links. |
| CC-2 Legitimate access | accepted | Publication, Ilan's source ownership, and physical testimony delivery remain separate; missing access blocks downstream knowledge. |
| CC-3 Feasible tradeoff | accepted | Restricted input exposes authored obligations and ordinary work/home alternatives with different outcomes. |
| CC-4 Autonomous choice | unverified | The live model must select a documented competing-obligation alternative through the conflict-informed restricted boundary. |
| CC-5 Physical transit effect | accepted | Equivalent action paths under different actual service conditions cross the household deadline and change its outcome. |
| CC-6 Obligation outcomes | accepted | Required location, completed activity, and explicit deadlines govern fulfillment or failure. |
| CC-7 Follow-through | accepted | Mara receives an attributable missed-obligation result and a later decision opportunity retaining the conflict. |
| CC-8 Causal comparisons | accepted | Information, action, and physical-condition comparisons isolate their respective effects. |
| CC-9 Offline watchability | accepted | The authored command presents accounts, choice, consequence, follow-through, and quiet spans through a focal-safe surface. |
| CC-10 Inspection/replay | accepted | Ordered causal inspection and recorded playback reconstruct the chain without another provider call. |
| CC-11 Reviewed live day | unverified | An audited exact day must include the valid conflict-informed choice, obligation consequence, and follow-up. |
| CC-12 Integration/completion | unverified | Current regressions, full checks, and final independent whole-goal review must pass. |

## Authored configuration and accepted behavior

[README](../../../README.md) gives the runnable `--consequential-choice` commands.
`build_autonomous_day(...)` exposes the following opt-in inputs; option-absent completed scenarios remain regressions.
The authored options are retained for recorded replay.

| Builder option | Meaning |
| --- | --- |
| `include_conflicting_transit_accounts=True` | Official normal-status notice at minute 480 and incompatible source-linked Ilan testimony for the same workplace-home interval. |
| `include_ilan_transit_source_delivery=False` | Withholds Ilan's source while retaining objective transit and the official-account path. |
| `include_deadline_governed_obligation_outcomes=True` | Base profile uses 10:31 workplace and 10:30 household deadlines. |
| `include_obligation_outcome_delivery=True` | Delivers Mara's own missed result through her personal schedule; requests a later decision only when she is idle. |
| `include_consequential_choice_tradeoff_timing=True` | Requires deadline outcomes and sets both deadlines to 10:32, disclosed through Mara's own schedule. |
| `include_service_dependent_travel=True` | Samples actual normal/reduced service when travel is accepted, using 30/60-minute duration. |
| `homeward_travel_service_recovery_minute` | Optional objective recovery after the source observation; does not automatically inform Mara or retime pending travel. |
| `include_conflict_opportunity_timing=True` | Requires conflicting accounts and the tradeoff profile; moves the objective change from minute 510 to 479 while retaining the minute-480 notice. |

Publication alone grants no knowledge; Mara needs workplace notice-board access.
Under original timing, Ilan receives the service source at 510 and valid testimony reaches Mara at 511.
Under the earlier timing, legitimate source access and workplace co-location allow both accounts and understanding updates before one coalesced minute-480 decision.
Source withholding or missing physical access prevents the corresponding testimony/conflict.
Earlier departure can still remove the opportunity; the option guarantees neither presence nor a live choice.

Actual completed activity at the required location governs obligations; arrival alone is insufficient, and completion exactly at the deadline is missed.
Restricted input exposes only Mara's own obligations, required activity/location, and deadlines, never actual service or predicted success.
An undelivered missed outcome stays inspector-only.
Delivered outcomes and retained conflict enter a later legitimate decision without interrupting pending work.

Deterministic comparisons separately change information with the world fixed, action with information/world fixed, and actual service with information/action path fixed.
Withholding Ilan's source removes only downstream statement, testimony, and conflict effects.
Normal versus reduced travel crosses the household deadline and changes its fulfilled/missed status under comparable activity choices.
The work-versus-home choice produces different obligation outcomes under the same circumstances.
These are authored causal proofs, not live-model success.

## Accepted prerequisites on 2026-09-16

Commit `bc25194725b7ea32f05b711e1faf29ffc50b1f4e` preserves two repairs exposed by failed live samples.
The adapter copies its response schema per request and constrains scalar strings to disclosed affordance options without constraining numeric parameters or mutating caller state.
The world rejects otherwise available duration-bearing actions that would complete after minute 1440 before creating pending work.
The provider-free seed-44 reproduction reaches the endpoint and links its minute-1410 rejection to an actor-safe result and private decision record.

Commit `ab11c5570f1c2ade6604c946359259706b1bff1d` adds the earlier access-gated timing described above.
Separate deterministic clients selected workplace work and homeward travel from the same conflict-informed minute-480 input.
Negative source/access cases, option-absent presentation, and replay were preserved.
Both prerequisites passed focused/full checks and independent review when accepted.
Neither made a real Ollama call or satisfied CC-4 or CC-11.

## Exhausted live attempts on 2026-09-11

The first bounded attempt allowed three samples through the concrete Ollama adapter and exact `qwen3:4b-instruct`, after immediate service/model preflights.
Its historical contract digest was `272b4be03dd11fc8c8538f92bf015d8ca20f974a1bfe830368e44a2276c10f78`.
The record identifies owner-only bundles under `/private/tmp/2084-cc11-20260911`; their present availability has not been reverified by this cleanup.

| Seed | Observed result | Why it failed CC-11 |
| --- | --- | --- |
| 42 | Exact day; generic audit/replay passed; five decisions/calls, four selected responses, one provider failure. | Conflict-informed minute-511 travel targeted Mara's current workplace and was rejected; neither competing alternative was accepted. |
| 43 | Reproduced seed 42, including decision/call counts and generic audit success. | The same conflict-informed same-location travel was rejected. |
| 44 | Nineteen decisions/calls, eighteen selected responses, one provider failure; terminal `ValueError` at minute 1410. | Mara left at minute 480 before testimony, then late travel exceeded the day boundary. |

Seeds 42-43 exposed the unconstrained scalar destination schema despite reachable options in restricted input.
A candidate schema repair ran before seed 44 but had not completed formal validation/review when the cap ended.
Seed 44 missed both obligations and failed exact-boundary, terminal-failure, complete-causal-link, model-dispatch, uncommitted-tail, and replay checks; model identity, provenance, privacy, and growth checks passed.
The original attempt closed unaccepted.

The owner authorized a separate replacement capped at three additional fully disclosed samples, preserving the failed evidence and requiring validation of both repairs.
The writer reproduced the late failure provider-free before applying the exact-day repair and validating detached schemas.
Immediate preflights for the replacement reported Ollama `0.33.3` and model digest `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
These are historical observations, not current service availability claims.

| Seed | Observed result | Why it failed CC-11 |
| --- | --- | --- |
| 45 | Received the official claim, then left before testimony. | No conflict-informed decision. |
| 46 | Received the official claim, then left before testimony. | No conflict-informed decision. |
| 47 | Remained at home and received neither account. | No conflict-informed decision. |

All three replacement days reached minute 1440, passed generic audit checks, reproduced recorded evidence, and safely rejected minute-1410 duration-bearing attempts.
Their recorded private location is `/private/tmp/2084-cc11-replacement-20260911`; original bundles were retained separately.
Independent review found no blocking repair defect but rejected acceptance because no sample exercised the required live choice.
The replacement also closed unaccepted; generic integrity does not establish missing product behavior.

## Unaccepted access-timing live audit on 2026-09-22

The accepted access-gated timing configuration justified one new seed-48 run because no earlier sample had exercised that configuration.
Its owner-only bundle is `/private/tmp/2084-cc11-conflict-opportunity-20260922-seed48-complete`.
The generic audit passed exact model identity, source stability, causal links, privacy, exact-day completion, and provider-free replay.
It recorded 20 provider calls, 16 selected responses, and four safe provider failures.
The first malformed response became a safe wait at minute 420, and Mara then selected travel to the workplace at minute 450, arriving at minute 480.
Mara received the official normal-service claim at that minute but no Ilan testimony or explicit conflict, then selected travel home from that official-only input.
Both obligations were later delivered as missed, and later decisions retained the official claim but not a conflict.
The objective change at minute 479 therefore did not produce the required conflict-informed choice for this valid live path.
The sample is contrary evidence, not a preferred-branch selection or CC-4/CC-11 success.

## Authorization and remaining evidence

The owner approved this goal on 2026-09-06 and restored standing authority within unchanged boundaries on 2026-09-16.
That reactivation separated acceptance of preserved repairs and a non-steering conflict opportunity from live success.
Both exhausted combined live attempts remain closed and unaccepted.
The replacement runner does not silently renew their sampling budgets.
Read the goal's live-evidence authorization and this failed-attempt record before selecting a newly justified experiment.

CC-4 and CC-11 require the live competing-obligation choice, world-resolved consequence, delivered follow-up, exact-day boundary, and reviewed reproducible private evidence.
An older ordinary live day, timing prerequisite, authored comparison, or generic audit pass cannot substitute for that chain.
Preserve contrary samples and report inconclusive outcomes honestly.
Close CC-12 only after current checks and independent whole-goal review support every criterion.

## Completed foundations

| Milestone | Accepted result |
| --- | --- |
| First living slice | Reusable deterministic engine, spatial/time constraints, attempted actions, ordinary autonomy, physical diary, and filtered observation. |
| Official Record, 2026-08-17 | Separate publication/delivery/handover, authorized revision, preserved versions, unauthorized/stale-target rejection, and reproduction. |
| Agent Understanding, 2026-08-19 | Source-linked traces/conflicts, public-counter stance, diary resurfacing, one recheck, privacy, and exact `first_day_v3` reproduction. |
| Model-backed Mara, 2026-08-22 | Restricted structured decisions, world authority, safe failure, private evidence, recorded reproduction, and a live travel-then-work smoke. |
| Autonomous day, 2026-08-27 | Exact 1440-minute runtime, bounded continuity/retries, independent activity, causal inspection, and an independently reviewed corrected live day. |
| Social thread, 2026-09-02 | Ilan's restricted source-backed statement, world-owned access/delivery, Mara's ordinary response, negative comparisons, and offline watchability/replay. |

The ordinary-day audit first failed after an unnecessary nineteenth decision at the closed endpoint; its manifest SHA-256 was `08f2001b38640fc396822d52bd869ffbab3f74b737bee33c3978ede31acbbc86`.
A separately owner-authorized corrected run from source `8c33f213b1ea58e51e6c326a8e22ba67dc664802` completed with 18 selected provider calls and zero provider failures.
Its peak restricted input was 17,492/49,152 bytes and private evidence 181,753/8,388,608 bytes; authority, privacy, cadence, source, causal-link, growth, and replay checks passed.
The successful manifest SHA-256 was `828541e3075ee776589ad7d6cab20e98ffb4e43a332d1c6de4ae1a0523ad2ee3`.
The failed audit remains failed evidence despite that later success.

Detailed completed plans, review logs, and retired-loop records remain in Git at `0e52fc7735a48f06da74805f00c3474d5a012d31`.
Read a specific original only when its historical detail is needed, for example:

```sh
git show 0e52fc7735a48f06da74805f00c3474d5a012d31:docs/plans/first-autonomous-day/IMPLEMENTATION_PLAN.md
```
