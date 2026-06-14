# P1-T6 — Codex Executor Prompt

**Use when:** Implementing the ArticleArtifact refactor (post–Gemini plan approval).  
**Plan:** [p1-t6-artifact-refactor.md](./p1-t6-artifact-refactor.md)  
**Review after:** Use [p1-t6-review-prompt.md](./p1-t6-review-prompt.md) — do not mark P1-T6 COMPLETED until review passes.

Copy everything inside the fenced block below into Codex as the task prompt.

---

```markdown
# Task: P1-T6 ArticleArtifact refactor (Affiliate Intelligence)

You are implementing an **approved** refactor in repo `affiliate_Intelligence`. Read the canonical plan first:

`.claude/phases/phase-1/p1-t6-artifact-refactor.md`

Also skim: `apps/bot/models.py`, `apps/bot/mdx_writer.py`, `apps/bot/tests/test_mdx_writer.py`, `docs/SPEC-01-content-bot.md` §8.1.

## Goal

Replace the public MDX writer API:

- **Remove:** `write_article(article: dict[str, Any], qa_result: QAResult, ...)`
- **Add:** `build_article_artifact(merged: dict[str, Any], qa_result: QAResult) -> ArticleArtifact`
- **Add:** `write_article(artifact: ArticleArtifact, *, dry_run=False, ...) -> MDXWriteResult`

`ArticleArtifact`, `Frontmatter`, `FAQItem`, `AffiliateMap` are defined in `apps/bot/models.py`.

## Hard rules (project)

- Python only under `apps/bot/`. Type hints on all public functions.
- No code comments unless explicitly required.
- No bare `except:`.
- Do **not** import `models` from `quality_gate.py` (avoid circular imports). `mdx_writer.py` may import from `models`.
- Do **not** change `outline` TypedDict (P2 out of scope).
- Do **not** mark P1-T6 as **COMPLETED** in `execution-log.md` — human will review after your PR. Set status to **NEEDS REVIEW** with note “ArticleArtifact refactor implemented; ready for combined review”.
- Do **not** start P1-T7 (`main.py` orchestration) unless trivial import fixes are required for tests.

## Design (must follow exactly)

### Single merge

1. Caller (tests / future orchestration) merges QA updates **once** using the same logic as today’s `_apply_article_updates(article, qa_result)` (skip keys named `status`).
2. `build_article_artifact(merged, qa_result)` receives the **already-merged** generation dict. It must **not** call `_apply_article_updates` again.
3. `write_article(artifact)` must **not** merge `article_updates` again. It only reads `artifact["qa_result"].overall` and writes files / DB / deploy.

Export `apply_article_updates` as a **public** function (rename from `_apply_article_updates` or thin wrapper) so tests and P1-T7 can reuse it without duplicating merge logic.

### build_article_artifact

From `merged` dict, build:

- `slug`, `category` (required strings; same validation as today)
- `frontmatter: Frontmatter` — map `meta_description` → `description`, `h1` or `title` → `title`, defaults: `author` = `"Affiliate Intelligence Editorial Team"` if missing, `schema_type` = `"Article"`, `affiliate_partner` from merged (see typing below). `published_at` / `last_reviewed` may be placeholders (e.g. `""`); **render time** overwrites them.
- `mdx_body: str` — same as current `_build_mdx_body(merged)` (`# h1` + `## h2` sections)
- `faq_json: list[FAQItem]` — same as `_normalise_faqs(merged)`
- `affiliate_map: AffiliateMap` — same as `_build_affiliate_map(merged)`
- `qa_result` — attach the passed `QAResult` unchanged

Refactor existing private helpers (`_build_mdx_body`, `_normalise_faqs`, `_build_affiliate_map`, etc.) so they are only used from the builder path (no duplicate derivation in `write_article`).

### write_article(artifact)

1. `slug = artifact["slug"]` (strip; error if empty — same as today)
2. If `artifact["qa_result"].overall == "FAIL"`: return `MDXWriteResult(slug=slug, skipped=True, reason="qa_failed")` with **no** filesystem, DB, or deploy side effects.
3. Otherwise:
   - `published_at = (today or date.today()).isoformat()`
   - `_render_frontmatter(artifact["frontmatter"], today_iso=published_at)` → fenced `---` block
   - MDX file = frontmatter + `\n\n` + `artifact["mdx_body"]` + `\n`
   - FAQ JSON: `{"slug": slug, "faqs": artifact["faq_json"]}` (same shape as today)
   - Affiliate map JSON: `artifact["affiliate_map"]`
   - Paths unchanged: `{content_root}/{category}/{slug}.mdx`, `{content_root}/faq/{slug}.faq.json`, `{affiliate_map_root}/{slug}.json`
   - `dry_run=True`: write files only; skip DB + deploy. `dry_run=False`: update DB + optional `VERCEL_DEPLOY_HOOK_URL` (unchanged behaviour).

### _render_frontmatter

- Input: `Frontmatter` TypedDict + `today_iso: str`
- Output key order **must match** existing test `test_frontmatter_fields_match_spec_01_section_8_1`:

  `title`, `description`, `slug`, `category`, `intent`, `published_at`, `last_reviewed`, `author`, `affiliate_partner`, `schema_type`

- Set `published_at` and `last_reviewed` to `today_iso` at render time (ignore placeholder values on the artifact).
- Serialize string values with `json.dumps(value, ensure_ascii=False)` like today’s `_frontmatter_value`.
- `affiliate_partner`: serialize `None` as `""`.

### Optional typing (do if small)

In `apps/bot/models.py`, change `Frontmatter["affiliate_partner"]` to `str | None`. Update `apps/bot/tests/test_models.py` only if required keys / sample dicts break.

## Tests (`apps/bot/tests/test_mdx_writer.py`)

Update every test to:

```python
merged = apply_article_updates(_article(), qa_result)
artifact = build_article_artifact(merged, qa_result)
result = write_article(artifact, dry_run=..., ...)
```

Keep `_article()` and `_qa_result()` fixtures; behaviour assertions must stay equivalent (frontmatter keys/order, paths, FAQ payload, affiliate stub, meta auto-fix in `description`, dry-run vs publish, deploy hook).

**FAIL test:** build an `ArticleArtifact` with `qa_result.overall == "FAIL"` and valid `slug` (minimal other fields OK if TypedDict allows — use placeholder strings where needed). Call `write_article(artifact)` only — no second `qa_result` argument.

Add at least one test that proves `write_article` does **not** apply `article_updates` itself (e.g. pass artifact built from unmerged dict while `qa_result` carries `meta_description` update — emitted MDX `description` must **not** reflect the update unless merge ran before `build_article_artifact`).

## Verification (run and report)

```bash
cd apps/bot && python -m ruff check .
cd apps/bot && python -m pytest tests/ -q
```

If pytest segfaults on Python 3.13 readline before collection, retry:

```bash
env PYTHONPATH=/private/tmp/no_readline:apps/bot python -m pytest apps/bot/tests/ -q
```

(only if needed; report which command you used.)

## Docs updates (minimal)

- `.claude/phases/phase-1/execution-log.md`: P1-T6 notes — refactor done, **NEEDS REVIEW** (awaiting combined review); list changed files and pytest/ruff counts.
- `.claude/phases/phase-1/qa-checklist.md`: check the `ArticleArtifact` consumption item if implementation satisfies it.
- Do **not** rewrite `p1-t6-artifact-refactor.md` unless you discover a factual error.

## Handoff (required in your final message)

```md
## Task Handoff

Task: P1-T6 (ArticleArtifact refactor)
Status: NEEDS REVIEW

Changed files:
- (list)

Commands run:
- python -m ruff check apps/bot/
- python -m pytest apps/bot/tests/

Result:
- N passed, ruff clean / failures

Risks or blockers:
- None | ...

Contract changes:
- write_article(ArticleArtifact); build_article_artifact; apply_article_updates exported
```

## Acceptance checklist

- [ ] No public `write_article(dict, qa_result)` remains
- [ ] `build_article_artifact` exported from `mdx_writer.py`
- [ ] `write_article` does not call `apply_article_updates`
- [ ] Frontmatter key order unchanged vs existing test
- [ ] FAIL / WARN / PASS side-effect parity with pre-refactor
- [ ] Full pytest + ruff green
- [ ] execution-log updated; P1-T6 **not** marked COMPLETED
```
