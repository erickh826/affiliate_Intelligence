# Phase 1 Plan — Content Bot Pipeline (SPEC-01)

**Status:** READY FOR EXECUTION  
**Spec:** `docs/SPEC-01-content-bot.md`  
**Timeline:** Weeks 1–2

---

## Objective

Deliver a runnable Phase 1 pipeline in `apps/bot/` that selects keywords from SQLite, performs research + generation, applies quality gate rules, and writes MDX output to `apps/web/content/`.

---

## Task Split (8 Tasks)

### P1-T0 — Baseline and Runtime Folders
- Ensure baseline folders/files exist: `data/`, `monetisation/affiliate_map/`, `.env.example`.
- Confirm `apps/bot/main.py` dry-run command is executable.
- Align local run commands with `apps/bot` and `apps/web` layout.
- **Done when:** baseline filesystem is complete and dry-run command works.

### P1-T1 — SQLite Schema and Seed
- Implement DB setup script for `data/keywords.db` using schema in `.ai-context/data-schema.md`.
- Add indexes for selection flow (`status`, `category`, `slug`, priority-related lookup).
- Add seed script with initial dataset (start with 50+ rows; scale to 200).
- **Done when:** schema + indexes + seed run without manual SQL edits.

### P1-T2 — Keyword Manager
- Create `apps/bot/keyword_manager.py`.
- Implement `select_keywords(batch_size, mode)` with priority score `volume / (difficulty + 1)`.
- Use a select-and-lock pattern so selected rows are claimed in the same SQLite transaction (`pending`/`needs_rewrite` → `generating`).
- Apply `difficulty < 45` as the default hard filter unless explicitly overridden by a force option.
- Implement `get_keyword(slug)` and `update_status(slug, status)`.
- Support rewrite flow for `needs_rewrite`, including safe `needs_rewrite` → `published` handling without losing current GSC fields.
- Implement context manager support for clean SQLite connection lifecycle.
- **Done when:** selector behavior, claim safety, status transitions, difficulty filtering, and connection cleanup are covered by unit tests.

### P1-T3 — Research Agent
- Create `apps/bot/research_agent.py`.
- Implement Firecrawl SERP extraction + Perplexity enrichment.
- Produce `research_bundle` conforming to SPEC-01 schema.
- Add retry (3x) and exponential backoff for external API failures.
- **Done when:** mocked tests validate output shape and retry behavior.

### P1-T4 — Generation Agent
- Create `apps/bot/generation_agent.py`.
- Implement `generate_outline()` and `write_sections()` with max concurrency = 3.
- Generate article body section-by-section; do not rely on one long-form LLM call for articles expected to exceed 2,000 words.
- Pass `affiliate_partner` into generation context and emit stable CTA placeholders or approved MDX component calls.
- Include strict MDX safety instructions: allowed components only, no raw HTML, and no unescaped MDX-breaking braces.
- Include internal-link placeholders such as `[AI Writing Tools]({{LINK_AI_WRITING}})` until a link graph exists.
- Accept a style guide parameter for consistent E-E-A-T tone and voice.
- Add intent-specific content constraints from SPEC-01.
- Add Anthropic failure fallback to OpenAI model.
- **Done when:** one section-by-section article draft can be generated in dry-run mode using mocks, with CTA placeholders, MDX-safe output instructions, internal-link placeholders, and concurrency limit tests.

### P1-T5 — Quality Gate
- Create `apps/bot/quality_gate.py`.
- Implement all SPEC-01 checks (word count, uniqueness, H1 keyword, FAQ count, etc.).
- Load banned phrase logic from a maintained config file under `apps/bot/config/`.
- Add `keyword_in_intro` check so the target keyword appears in the first 100 words.
- Add basic MDX syntax preflight for approved self-closing components and illegal raw syntax.
- Add image placeholder check as a WARN-level SEO readiness signal.
- Add readability scoring as a WARN-level signal for overly dense prose.
- Include deterministic FAIL/WARN/PASS contract.
- Return structured check results for downstream logging.
- **Done when:** all rule branches are covered by tests.

### P1-T5.5 — Shared Bot Models / Contracts
- Create `apps/bot/models.py` as the Phase 1 internal contract layer.
- Use `TypedDict` for `ResearchContext`, `GeneratedSection`, `GenerationContext`, `Frontmatter`, and `ArticleArtifact`.
- Keep current runtime keys stable; do not rename existing research/generation fields unless downstream code and tests are updated.
- Make `ArticleArtifact` the input contract for `P1-T6` so `mdx_writer.py` only handles file output, DB state update, and deploy trigger behavior.
- **Done when:** contracts are importable, covered by lightweight tests, and referenced by `P1-T6` implementation.

### P1-T6 — MDX Writer and State Update
- Create `apps/bot/mdx_writer.py`.
- Write article output to `apps/web/content/{category}/{slug}.mdx`.
- Write FAQ JSON and affiliate map stub.
- Implement DB status updates and optional deploy hook trigger.
- **Contract refactor (approved):** see `.claude/phases/phase-1/p1-t6-artifact-refactor.md` — `build_article_artifact` + `write_article(ArticleArtifact)`.
- **Done when:** file output and DB update behavior are verified in tests **and** the supported public writer API takes `ArticleArtifact` (single contract handoff; no reliance on unstructured dicts as the primary input).

### P1-T7 — Pipeline Orchestration and E2E
- **Claude prompt:** [p1-t7-claude-executor-prompt.md](./p1-t7-claude-executor-prompt.md) · **Review:** [p1-t7-review-prompt.md](./p1-t7-review-prompt.md)
- Expand `apps/bot/main.py` to orchestrate T2→T6.
- Keep `--dry-run` mode safe (skip deploy and external side effects).
- Add structured logs and per-article summary.
- Add integration test for `--batch 3 --dry-run`.
- **Done when:** end-to-end dry-run passes with test suite green.

---

## Execution Order

`P1-T0 → P1-T1 → P1-T2 → P1-T3 → P1-T4 → P1-T5 → P1-T5.5 → P1-T6 → P1-T7`

---

## Definition of Done (Phase 1)

- `python apps/bot/main.py --batch 3 --dry-run` completes successfully.
- `pytest apps/bot/tests/` passes.
- `ruff check apps/bot/` passes.
- MDX artifacts are generated under `apps/web/content/`.
- Status transitions in `data/keywords.db` are correct for success/failure paths.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| API rate limits or outages | Pipeline stalls | Retry with backoff, fallback model, strict timeout defaults |
| Quality gate too permissive | Low-value content published | Harden thresholds + add manual spot-check for first batch |
| SQLite contention | Update failures | Use WAL mode and short transactions |
| Cross-step schema drift | Runtime errors | Typed contracts + test fixtures shared across modules |
