# P1-T6 — Combined Review Prompt

**Use when:** Codex (or another executor) has finished the ArticleArtifact refactor and set P1-T6 to **NEEDS REVIEW** in `execution-log.md`.  
**References:** [p1-t6-artifact-refactor.md](./p1-t6-artifact-refactor.md), [p1-t6-codex-executor-prompt.md](./p1-t6-codex-executor-prompt.md), `docs/SPEC-01-content-bot.md` §8.1, `.claude/phases/phase-1/qa-checklist.md`

Copy everything inside the fenced block below into your reviewer (Gemini, Cursor, etc.).

---

```markdown
# Review: P1-T6 MDX Writer + ArticleArtifact contract (Affiliate Intelligence)

You are the **reviewer** for Phase 1 task **P1-T6**. The executor should have implemented the approved refactor per:

`.claude/phases/phase-1/p1-t6-artifact-refactor.md`

Read the executor handoff in the PR / chat, then verify the codebase yourself. Do **not** approve P1-T7 work in this review.

## Review scope (single combined pass)

Cover **behaviour** and **contract** together — no separate Stage 1 / Stage 2 sign-off.

| Area | What to verify |
|------|----------------|
| **Public API** | `write_article(artifact: ArticleArtifact, ...)` only; no public `write_article(dict, qa_result)`. |
| **Builder** | `build_article_artifact(merged, qa_result) -> ArticleArtifact` exported; `apply_article_updates` exported; builder does **not** re-merge QA updates. |
| **Single merge** | `write_article` does **not** read or apply `qa_result.article_updates`; merge happens before `build_article_artifact` only. |
| **FAIL path** | `overall == "FAIL"` → skip all files, DB, deploy; uses `artifact["slug"]`; tests use artifact-only call (no detached `qa_result` param). |
| **Frontmatter** | Key order: `title`, `description`, `slug`, `category`, `intent`, `published_at`, `last_reviewed`, `author`, `affiliate_partner`, `schema_type`. Dates from `today` at render time. |
| **Outputs** | MDX under `apps/web/content/{category}/{slug}.mdx`; FAQ `apps/web/content/faq/{slug}.faq.json`; affiliate `monetisation/affiliate_map/{slug}.json`. |
| **QA meta fix** | When `article_updates` contains `meta_description`, merged → artifact → written `description` in frontmatter reflects fix; not applied if merge skipped before build. |
| **Dry-run / publish** | `dry_run=True`: files written, no DB/deploy. `dry_run=False`: `status=published`, `published_at` set, deploy hook when env set. |
| **Models** | `ArticleArtifact` matches usage; optional `Frontmatter["affiliate_partner"]: str \| None` with `None` → `""` in output. |
| **Imports** | `quality_gate.py` does **not** import `models`. |
| **Tests & lint** | `pytest apps/bot/tests/` green; `ruff check apps/bot/` clean. |

## Commands to run

```bash
cd /path/to/affiliate_Intelligence

# Grep checks
rg 'def write_article' apps/bot/
rg 'write_article\(' apps/bot/ --glob '*.py'
rg 'apply_article_updates|_apply_article_updates' apps/bot/mdx_writer.py
rg 'article_updates' apps/bot/mdx_writer.py

# Tests
python -m ruff check apps/bot/
python -m pytest apps/bot/tests/ -q
```

If pytest fails to collect on Python 3.13 (readline segfault), retry:

```bash
env PYTHONPATH=/private/tmp/no_readline:apps/bot python -m pytest apps/bot/tests/ -q
```

Report exact commands and pass counts.

## Files to read (minimum)

- `apps/bot/mdx_writer.py` — full file
- `apps/bot/models.py` — `Frontmatter`, `ArticleArtifact`
- `apps/bot/tests/test_mdx_writer.py` — all tests
- Executor diff / handoff changed-files list
- `.claude/phases/phase-1/execution-log.md` — P1-T6 section (should be NEEDS REVIEW, not COMPLETED, until you approve)

## Checklist (mark pass/fail)

### Contract

- [ ] Public `write_article` accepts `ArticleArtifact` only
- [ ] `build_article_artifact` exists and is used by tests
- [ ] `apply_article_updates` is public and skips `status` keys
- [ ] No double-merge of `article_updates` in `write_article`
- [ ] `build_article_artifact` does not call `apply_article_updates` internally

### Behaviour (SPEC-01 §8.1 + existing tests)

- [ ] Frontmatter field set and order correct
- [ ] MDX body = frontmatter fence + `mdx_body` from artifact
- [ ] FAQ JSON shape `{ "slug", "faqs": [...] }`
- [ ] Affiliate map stub shape unchanged
- [ ] FAIL skips all side effects
- [ ] WARN/PASS write files; publish path updates DB + deploy hook
- [ ] Meta description auto-fix flows through merge → builder → `description`

### Quality

- [ ] Type hints on new/changed public functions
- [ ] No bare `except:`
- [ ] No unnecessary comments added
- [ ] `pytest` + `ruff` pass

### Docs (executor should have updated)

- [ ] `qa-checklist.md` — ArticleArtifact item checked if satisfied
- [ ] `execution-log.md` — accurate pytest count and NEEDS REVIEW note
- [ ] P1-T6 **not** marked COMPLETED before this review

## Verdict format (required)

Reply with exactly one of:

### APPROVE

- P1-T6 behaviour and contract meet the plan.
- Safe to mark **P1-T6 COMPLETED** in `execution-log.md` and unblock **P1-T7**.
- List any non-blocking follow-ups (P2).

### APPROVE WITH NOTES

- P1-T6 may be marked **COMPLETED** after listed notes are fixed or explicitly deferred.
- Number each note (P1 = must fix before P1-T7, P2 = defer).

### REJECT

- Do not mark COMPLETED.
- Number blocking issues with file:line or test name and required fix.

## If APPROVE or APPROVE WITH NOTES (executor or maintainer may apply)

Update `.claude/phases/phase-1/execution-log.md`:

- P1-T6 **Status:** COMPLETED
- **Completed:** (review date)
- **Notes:** reviewer verdict + pytest/ruff counts

Update `.claude/phases/phase-1/manual.md` status table: P1-T6 → Completed.

Ensure `.claude/phases/phase-1/qa-checklist.md` reflects checked items for `mdx_writer` / `ArticleArtifact`.

Do **not** implement P1-T7 in the review task unless explicitly asked.
```
