# Agent Guidance

## Before working

- Start with `docs/plans/CURRENT.md`, then the relevant product specification and implementation evidence.
- Work within the owner's requested scope and define observable success before making changes.
- Read only the source, tests, and architecture boundary relevant to the selected responsibility.
- Use `docs/main/CORE_CONSTRUCT.md` for product direction and reference limits, `docs/main/ARCHITECTURE.md` for implemented contracts, and `README.md` for commands.
- Treat unresolved product questions as open design space and distinguish exploration from lasting architecture.

## Product invariants

- Keep objective truth, official records, delivered observations, actor understanding, attempted actions, and observer presentation distinct.
- `EventLog` is append-only objective evidence; official revision never rewrites history.
- Publication or revision never automatically delivers knowledge.
- Actors learn only through channels they can actually access.
- Policies receive restricted state and propose attempts; the world owns validity, time, mutation, and consequence.
- Public expression is a separately resolved attempt and may differ from contextual or private understanding.
- Keep contradictions source-linked and inspectable; never erase evidence to resolve a conflict or claim to simulate consciousness.
- The focal character is autonomous and has no privileged truth access.
- Keep normal presentation focal-safe and separate from omniscient inspection.
- Model output is not automatically true, consistent, canonical memory, or a successful action.
- Label authored schedules and deterministic comparisons honestly; do not force a plot and call it emergence.
- Favor one watchable focal life, a small living world, limited knowledge, and understandable consequences over scale or elaborate systems.
- Keep the diary physical and basic; add mechanics only when they create a necessary interaction.
- Borrow transferable concepts from references, not their code, scenario, characters, or interface.

## Making and explaining changes

- State the missing behavior or uncertainty and what observation would establish success.
- Investigate and reproduce relevant behavior before choosing the implementation.
- Prefer simple rule-based mechanisms when they answer the same question.
- Check for hidden knowledge, impossible authority, and disconnected consequences.
- Preserve evidence needed to explain surprising behavior, failed samples, and counterfactuals.
- Validate in proportion to maturity, without weakening checks or acceptance criteria.
- Run `./scripts/check.sh` and request independent review for consequential changes to authority, knowledge, or evidence boundaries.
- Separate observed results from interpretation and call out authored inputs, special cases, and unresolved assumptions.
- Remove systems or documents that obscure the central question or duplicate an existing responsibility.
- Never push, merge, deploy, or broaden the requested scope without explicit owner direction.

## Documentation

- Keep each Markdown file below 200 lines by condensing important information in place.
- Do not split a long document or create another file merely to meet the limit.
- Keep each full prose sentence on its own line; do not hide length in dense paragraphs or oversized table cells.
- Retain current instructions, product direction, implemented contracts, active acceptance criteria, and useful evidence.
- Delete completed task plans, duplicate proposals, scratchpads, and operational ledgers when code, tests, retained summaries, and Git history cover their value.
- Update references when deleting documents, and keep runtime-required character inputs intact.
