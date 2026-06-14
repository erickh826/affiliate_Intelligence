# Phase 1 Manual — Content Bot Pipeline

**Audience:** Human operators and AI agents  
**Source of truth:** `docs/SPEC-01-content-bot.md`, `.claude/phases/phase-1/plan.md`, `.claude/phases/phase-1/execution-log.md`, `.claude/phases/phase-1/p1-t6-artifact-refactor.md` (P1-T6 contract refactor, Gemini-approved)  
**Update rule:** Append new instructions as tasks complete. Do not rewrite history unless correcting a documented mistake.

---

## 1. Operating Principles

- Follow `plan.md` for task order and scope.
- Follow `execution-log.md` for current status.
- Follow `qa-checklist.md` for acceptance checks.
- If spec and code disagree, follow `docs/SPEC-01-content-bot.md`.
- If a worker agent wants to change task order, it must propose the change and wait for approval.
- Do not skip review gates before moving to the next task.

---

## 2. Current Phase Status

| Task | Status | Notes |
|---|---|---|
| P1-T0 | Completed | Runtime folders and `.env.example` are present. |
| P1-T1 | Completed | SQLite schema and seed work completed and approved after Gemini CLI review. |
| P1-T2 | Completed | Keyword manager is implemented, tested, and reviewed. |
| P1-T3 | Completed | Research agent is implemented with mocked Firecrawl/Perplexity tests. |
| P1-T4 | Completed | Generation agent is implemented, tested, and reviewed. |
| P1-T5 | Completed | Quality gate is implemented, tested, and reviewed. |
| P1-T5.5 | Completed | Contracts landed in `apps/bot/models.py`; reviewer approved with notes (writer still on loose dict until P1-T6 refactor). |
| P1-T6 | Completed | ArticleArtifact refactor reviewed 2026-05-18; `apply_article_updates` → `build_article_artifact` → `write_article`. |
| P1-T7 | Completed | Pipeline orchestration via `main.py` is implemented and verified with robust dry-run safety and E2E integration tests. |

---

## 3. Standard Task Workflow

Use this workflow for every Phase 1 task:

1. Read the relevant sections in `plan.md`, `qa-checklist.md`, and `docs/SPEC-01-content-bot.md`.
2. Confirm the previous task is marked completed in `execution-log.md`.
3. Mark the current task as `IN PROGRESS`.
4. Implement only the current task scope.
5. Run task-specific tests.
6. Run the relevant lint/format checks.
7. Record commands, results, and issues in `execution-log.md`.
8. Submit for review.
9. Only after approval, mark the task as `COMPLETED`.

---

## 4. Handoff Format

Every human or AI agent must report handoff in this format:

```md
## Task Handoff

Task: P1-Tx
Status: COMPLETED | BLOCKED | NEEDS REVIEW

Changed files:
- path/to/file

Commands run:
- command

Result:
- pass/fail summary

Risks or blockers:
- item or "None"

Contract changes:
- item or "None"
```

---

## 5. P1-T2 Execution Notes

`P1-T2` implements `apps/bot/keyword_manager.py`.

Required behavior:

- Select eligible keywords by priority score: `monthly_volume / (difficulty + 1)`.
- Default selection must filter:
  - `status IN ('pending', 'needs_rewrite')`
  - `monthly_volume > 100`
  - `difficulty < 45`
- A force option may override the difficulty threshold, but default behavior must stay strict.
- Selection must claim rows in the same SQLite transaction to prevent duplicate processing.
- Claimed rows should move to `generating`.
- Rewrite flow must support `needs_rewrite`.
- Publishing rewritten content must not erase current GSC performance fields.
- `KeywordManager` must support context manager usage for connection cleanup.

Suggested test coverage:

- Selects highest-priority eligible rows.
- Excludes low-volume rows.
- Excludes `difficulty >= 45` unless force override is enabled.
- Select-and-lock prevents duplicate claim in sequential calls.
- `needs_rewrite` rows can be selected and claimed.
- `update_status()` handles valid transitions.
- GSC fields survive rewrite publish updates.
- Context manager closes the SQLite connection.

---

## 6. Gate Before P1-T3

Do not start `P1-T3` until all are true:

- `apps/bot/keyword_manager.py` exists.
- `apps/bot/tests/test_keyword_manager.py` exists.
- Keyword selection tests pass.
- Select-and-lock behavior is tested.
- `pytest apps/bot/tests/` passes.
- `ruff check apps/bot/` passes.
- `execution-log.md` marks `P1-T2` as `COMPLETED`.
- Review result is approved.

---

## 7. How to Extend This Manual

When a task is completed:

1. Add a short section named `P1-Tx Completion Notes`.
2. Record what is now safe for future agents to assume.
3. Add any commands that future agents should reuse.
4. Add new gates for the next task if review found important constraints.

Do not remove older completion notes. This file should become a cumulative operating manual for Phase 1.

---

## P1-T3 Completion Notes

Safe assumptions for future agents:

- `apps/bot/research_agent.py` exists.
- `scrape_serps()` returns `competitors_scraped` records with `url`, `title`, `headings`, and `body_summary`.
- `query_perplexity()` returns `facts`, `tools_mentioned`, and `faq_seeds`.
- `build_research_bundle()` returns the SPEC-01 research bundle shape.
- External API calls are injectable through an HTTP client protocol for mocked tests.
- Firecrawl and Perplexity failures retry up to 3 times with exponential backoff.

Reusable verification commands:

```bash
python -m pytest apps/bot/tests/
python -m ruff check apps/bot/
```

Gate before P1-T4:

- `apps/bot/research_agent.py` exists.
- `apps/bot/tests/test_research_agent.py` passes.
- `build_research_bundle()` output shape remains stable.
- `pytest apps/bot/tests/` passes.
- `ruff check apps/bot/` passes.

---

## P1-T4 Review Findings to Include

Gemini CLI review identified these constraints for `apps/bot/generation_agent.py`:

- Long-form article generation must be section-by-section to avoid output token truncation for articles expected to exceed 2,000 words.
- `affiliate_partner` must be passed into generation context so the output can include stable CTA placeholders or approved MDX component calls.
- The system prompt must define MDX safety rules: allowed components only, no raw HTML tags, and no unescaped MDX-breaking braces.
- Section writing must enforce max concurrency with a semaphore or equivalent queue.
- Internal links should use placeholders such as `[AI Writing Tools]({{LINK_AI_WRITING}})` until the link graph exists.
- A style guide parameter should control consistent E-E-A-T tone and voice.

Gate before marking P1-T4 complete:

- Outline generation is mocked and tested.
- Section-by-section writing is mocked and tested.
- Max concurrency behavior is tested.
- Affiliate CTA placeholder behavior is tested.
- MDX safety prompt instructions are tested.
- Internal-link placeholder instruction is tested.
- Style guide parameter is tested.
- Fallback model behavior is tested.

---

## P1-T4 Completion Notes

Safe assumptions for future agents:

- `apps/bot/generation_agent.py` exists.
- `apps/bot/outline_schema.json` exists and is used by outline validation.
- `generate_outline()` supports dry-run and live outline generation.
- `write_sections()` generates article content section-by-section.
- Section writing enforces max concurrency with a semaphore.
- Section prompts include E-E-A-T constraints, affiliate CTA context, internal-link placeholders, and style guide text.
- MDX safety instructions allow approved placeholders such as `{{LINK_*}}` while still warning against unsafe raw braces in prose.
- Anthropic section generation falls back to OpenAI only for wrapped LLM API errors.
- `openai`, `anthropic`, and `jsonschema` are listed in `apps/bot/requirements.txt`.

Reusable verification commands:

```bash
python -m pytest apps/bot/tests/
python -m ruff check apps/bot/
```

Gate before P1-T5:

- `P1-T4` is marked `COMPLETED` in `execution-log.md`.
- Generation agent tests pass.
- `pytest apps/bot/tests/` passes.
- `ruff check apps/bot/` passes.
- `quality_gate.py` should validate the generated section structure: `h2`, `h3s`, `content`, and `word_count`.

---

## P1-T5 Review Notes

Quality gate review found one blocking robustness issue and one documented limitation:

- Malformed generated sections must not crash the quality gate. If section structure is invalid, `run_quality_gate()` should return a structured `FAIL` result and set `article_updates["status"] = "failed"`.
- The current internal-link check covers unresolved placeholders like `{{LINK_AI_WRITING}}`. Full markdown link target validation should be revisited in `P1-T6` or `P1-T7` once MDX files exist under `apps/web/content/`.

Additional review findings to include before marking P1-T5 complete:

- Banned phrases should come from `apps/bot/config/banned_phrases.txt`, not only a hard-coded list. The config should include SPEC-01 phrases plus common AI filler phrases such as "in the rapidly evolving landscape", "as an AI language model", and "delve into".
- Add `keyword_in_intro` so the keyword appears in the first 100 words, not only in H1.
- Add basic MDX syntax preflight for allowed components such as `<AffiliateCTA />` and obvious illegal raw syntax.
- Add an image placeholder check as a WARN-level SEO readiness signal.
- Add readability scoring as a WARN-level signal for prose that is too dense.

---

## P1-T5 Completion Notes

Safe assumptions for future agents:

- `apps/bot/quality_gate.py` exists.
- `apps/bot/config/banned_phrases.txt` is the source for banned AI filler phrases.
- `run_quality_gate()` returns a structured `QAResult` with `overall`, `checks`, and `article_updates`.
- Invalid generated section structure returns `FAIL` without crashing.
- Failing checks set `article_updates["status"] = "failed"`.
- Quality checks cover word count, duplicate similarity, factual anchors, keyword in H1, keyword in first 100 words, meta length auto-fix, FAQ count, internal link placeholders, banned phrases, MDX preflight, image placeholder presence, and readability.
- Full markdown link target validation is still deferred until `P1-T6` or `P1-T7`, when MDX output exists under `apps/web/content/`.

Reusable verification commands:

```bash
python -m pytest apps/bot/tests/
python -m ruff check apps/bot/
```

Gate before P1-T6:

- `P1-T5` and `P1-T5.5` are marked `COMPLETED` in `execution-log.md`.
- Quality gate tests pass.
- `pytest apps/bot/tests/` passes.
- `ruff check apps/bot/` passes.
- `apps/bot/models.py` and `apps/bot/tests/test_models.py` exist and match the Phase 1 handoff shapes.
- `mdx_writer.py` should consume `QAResult.article_updates` and avoid writing failed articles.

P1-T6 review status:

- `write_article(...)` now takes `ArticleArtifact` as the primary article argument, with embedded `qa_result`.
- `Frontmatter["affiliate_partner"]` is aligned with generation as `str | None`.
- P1-T6 still stays `NEEDS REVIEW` until human combined review; optional later work is tightening `outline` TypedDict to match JSON schema.

---

## P1-T5.5 Contract Notes

**As of 2026-05-18:** `apps/bot/models.py` and `apps/bot/tests/test_models.py` exist; see `execution-log.md` for reviewer notes. The P1-T6 ArticleArtifact writer refactor is implemented and awaiting combined review.

Purpose:

- Prevent loose dict drift between research, generation, QA, MDX output, Phase 2 rendering, and Phase 3 monetisation.
- Make `mdx_writer.py` consume a stable `ArticleArtifact` instead of re-interpreting raw generation or QA objects.

Recommended contracts:

- `ResearchContext`: current `research_agent.build_research_bundle()` shape. Keep existing runtime keys stable (`competitors_scraped`, `facts`, `tools_mentioned`, `faq_seeds`) unless downstream code is updated.
- `GeneratedSection`: `h2`, `h3s`, `content`, `word_count`.
- `GenerationContext`: `keyword`, `slug`, `category`, `intent`, `h1`, `meta_description`, `sections`, `faqs`, `affiliate_partner`, and `outline`.
- `Frontmatter`: fields required by SPEC-01 §8.1 and Phase 2 rendering (`title`, `description`, `slug`, `category`, `intent`, `published_at`, `last_reviewed`, `author`, `affiliate_partner`, `schema_type`).
- `ArticleArtifact`: `slug`, `category`, `frontmatter`, `mdx_body`, `faq_json`, `affiliate_map`, and `qa_result`.

Rules:

- Use `TypedDict`, not Pydantic, for this phase.
- Do not introduce runtime validation here; keep it as a typing and handoff contract layer.
- Do not rename existing runtime keys unless all downstream code and tests are updated in the same task.

---

## P1-T6 Completion Notes

**Refactor plan (Gemini-approved):** [p1-t6-artifact-refactor.md](./p1-t6-artifact-refactor.md)  
**P1-T6 prompts:** [executor](./p1-t6-codex-executor-prompt.md) · [review](./p1-t6-review-prompt.md)

Safe assumptions for future agents:

- `apps/bot/mdx_writer.py` exists.
- `write_article()` takes `ArticleArtifact` with embedded `qa_result`; `build_article_artifact(merged, qa_result)` builds the artifact after callers apply QA updates once.
- QA `article_updates` are applied before artifact construction via `apply_article_updates`, including meta description auto-fixes.
- `QAResult.overall == "FAIL"` skips article, FAQ, affiliate map, DB, and deploy side effects.
- MDX is written to `apps/web/content/{category}/{slug}.mdx`.
- FAQ JSON is written to `apps/web/content/faq/{slug}.faq.json`.
- Affiliate map stubs are written to `monetisation/affiliate_map/{slug}.json`.
- Live publish updates `keywords.status = 'published'` and sets `published_at` if empty.
- Dry-run writes file artifacts for inspection, but skips DB status updates and deploy hooks.
- Deploy hook triggering only runs when `VERCEL_DEPLOY_HOOK_URL` is set.

Reusable verification commands:

```bash
python -m pytest apps/bot/tests/
python -m ruff check apps/bot/
```

Validation note:

- On 2026-05-17, the local Python 3.13 environment segfaulted in pytest before collection while importing readline. The suite passed with a temporary no-readline shim:

```bash
env PYTHONPATH=/private/tmp/no_readline:apps/bot python -X faulthandler -m pytest apps/bot/tests/
```

## P1-T7 Execution Notes

**Claude prompt:** [p1-t7-claude-executor-prompt.md](./p1-t7-claude-executor-prompt.md) · **Review:** [p1-t7-review-prompt.md](./p1-t7-review-prompt.md)

Gate before starting P1-T7:

- P1-T6 is **COMPLETED** in `execution-log.md`.
- `pytest apps/bot/tests/` and `ruff check apps/bot/` pass.

Phase 1 Definition of Done after P1-T7:

```bash
python apps/bot/main.py --batch 3 --dry-run
```
