# P1-T6 — ArticleArtifact Refactor Plan

**Status:** APPROVED (Gemini review, 2026-05-18)  
**Blocks:** Final P1-T6 sign-off until implemented  
**Related:** `apps/bot/models.py`, `apps/bot/mdx_writer.py`, `docs/SPEC-01-content-bot.md` §8.1, `.claude/phases/phase-1/plan.md` (P1-T6), `.claude/phases/phase-1/qa-checklist.md`  
**Prompts:** [p1-t6-codex-executor-prompt.md](./p1-t6-codex-executor-prompt.md) (implement) · [p1-t6-review-prompt.md](./p1-t6-review-prompt.md) (review after implementation)

---

## Objective

Satisfy the Phase 1 sign-off gate for **P1-T6**: the public MDX writer API must take a single **`ArticleArtifact`** (with embedded `qa_result`), not a loose `dict[str, Any]` plus a detached `QAResult`.

Current code (pre-refactor):

```python
write_article(article: dict[str, Any], qa_result: QAResult, *, dry_run=False, ...) -> MDXWriteResult
```

Target:

```python
build_article_artifact(merged: dict[str, Any], qa_result: QAResult) -> ArticleArtifact
write_article(artifact: ArticleArtifact, *, dry_run=False, ...) -> MDXWriteResult
```

---

## Design (approved)

### 1. Public signature

- `write_article(artifact: ArticleArtifact, *, dry_run=False, ...) -> MDXWriteResult`
- Inspect only `artifact["qa_result"]` for PASS / WARN / FAIL.
- Remove the second `qa_result` parameter from the public writer API.

### 2. Split responsibilities

**(a) `build_article_artifact(merged, qa_result) -> ArticleArtifact`**

- Input: generation-shaped dict **after** the same merge as today’s `_apply_article_updates(dict, qa_result)` (omit `status` keys, same as current writer).
- Output: fully typed artifact — `slug`, `category`, `frontmatter`, `mdx_body`, `faq_json`, `affiliate_map`, `qa_result`.
- Reuse existing private derivation (`_normalise_faqs`, section → body, affiliate stub) keyed off **merged** dict **once** inside the builder (no duplicate logic in `write_article`).

**(b) `write_article(artifact)` — output and side effects only**

- If `artifact["qa_result"].overall == "FAIL"`: return early using `artifact["slug"]`; no file writes, DB update, or deploy (unchanged semantics).
- `_render_frontmatter(frontmatter, today_iso=...)`: inject `published_at` and `last_reviewed` from `today` at render time.
- Write MDX: frontmatter fence + blank line + `artifact["mdx_body"]`.
- Write FAQ JSON and affiliate map JSON from `artifact["faq_json"]` and `artifact["affiliate_map"]`.
- DB `published` + optional Vercel deploy hook: unchanged from current implementation.

### 3. Single merge rule

- Apply `qa_result.article_updates` when building **`merged`** (before `build_article_artifact`).
- **`write_article` must not merge `article_updates` again** — prevents double application of meta auto-fix and future QA keys.
- QA today updates `meta_description` on the generation dict; the builder maps that into `Frontmatter["description"]` when assembling the artifact.

### 4. FAIL path

- Orchestration may still construct an `ArticleArtifact` with `qa_result.overall == "FAIL"` and a valid `slug` (other fields may be minimal).
- `write_article` skips all side effects based on `overall` only (same as today).

### 5. Optional typing (same PR if trivial)

- `Frontmatter["affiliate_partner"]`: `str | None` in `models.py` (align with `GenerationContext`).
- Serialize `None` as `""` in frontmatter output.

### 6. Out of scope (P2)

- `Outline` TypedDict tightening for `GenerationContext["outline"]` — keep `dict[str, Any]` until a dedicated schema task.

---

## Implementation steps

| Step | Work |
|------|------|
| A | Implement `build_article_artifact(merged, qa_result)` in `mdx_writer.py`; refactor `_build_frontmatter` / `_build_mdx_body` / `_build_affiliate_map` / `_normalise_faqs` so merged-dict derivation runs only inside this builder. |
| B | Implement `_render_frontmatter(fm: Frontmatter, *, today_iso: str) -> str` with the same key order as existing tests (SPEC-01 §8.1); set `published_at` and `last_reviewed` from `today_iso` at render time. |
| C | Rewrite `write_article(artifact)`; remove public `write_article(article: dict, qa_result)`. |
| D | Update `test_mdx_writer.py`: `_article()` → merge → `build_article_artifact` → `write_article`; strengthen FAIL test to use artifact-only slug (no detached `qa_result` param). |
| E | Run `ruff check apps/bot/` and `pytest apps/bot/tests/`; update `manual.md`, `qa-checklist.md`, and `execution-log.md`; mark P1-T6 **COMPLETED** only after human/agent review of the refactor PR. |

---

## Acceptance criteria

- `pytest apps/bot/tests/` passes; `ruff check apps/bot/` clean.
- No documented public path uses `write_article(dict, qa_result)`.
- Behaviour parity with pre-refactor writer:
  - FAIL → skip all writes and side effects.
  - WARN / PASS → same output paths under `apps/web/content/` and `monetisation/affiliate_map/`.
  - QA meta auto-fix visible in frontmatter `description` via **merged → artifact** pipeline only.
- `qa-checklist.md` item for `ArticleArtifact` consumption can be checked.

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Circular imports (`quality_gate` ↔ `models`) | Import `ArticleArtifact` / `Frontmatter` from `models.py` in `mdx_writer` only; do not import `models` from `quality_gate`. |
| Incomplete `Frontmatter` on FAIL stubs | Builder fills defaults (`author`, `schema_type`, etc.); use minimal valid strings where TypedDict requires keys. |
| P1-T7 orchestration duplication | Export `build_article_artifact` from `mdx_writer` as the single assembly entry point for `main.py`. |

---

## P1-T6 review policy (two stages)

### Stage 1 — Behaviour review (allowed **before** refactor)

Review the **current** `mdx_writer.py` implementation against SPEC-01 §8.1 and `test_mdx_writer.py`:

- Frontmatter field set and order
- Output paths (MDX, FAQ JSON, affiliate stub)
- QA FAIL skip, dry-run vs publish, DB status / `published_at`, deploy hook
- Application of `article_updates` (e.g. meta description) before write

**Outcome:** Approve **behaviour** with note: contract gate still open until Stage 2.

### Stage 2 — Contract review (required for P1-T6 **COMPLETED**)

After this plan is implemented:

- Public API is `write_article(ArticleArtifact)` only
- `build_article_artifact` exists and tests use merge → build → write
- No double-merge of `article_updates` in `write_article`

**Outcome:** Approve P1-T6 for **COMPLETED** in `execution-log.md` and unblock **P1-T7**.

---

## Approval log

| Date | Reviewer | Decision |
|------|----------|----------|
| 2026-05-18 | Gemini | Plan approved — proceed with implementation per this document |
