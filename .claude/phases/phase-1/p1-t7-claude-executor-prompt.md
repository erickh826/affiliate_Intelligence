# P1-T7 — Claude Executor Prompt

**Use when:** Implementing pipeline orchestration in `apps/bot/main.py` (P1-T6 is **COMPLETED**).  
**Plan:** `.claude/phases/phase-1/plan.md` (P1-T7) · **Spec:** `docs/SPEC-01-content-bot.md`  
**Review after:** [p1-t7-review-prompt.md](./p1-t7-review-prompt.md)

Copy everything inside the fenced block below into Claude Code / Claude as the task prompt.

---

```markdown
# Task: P1-T7 Pipeline orchestration and E2E (Affiliate Intelligence)

Implement Phase 1 task **P1-T7**: wire the content bot pipeline end-to-end in `apps/bot/`, from keyword selection through MDX output.

## Read first

1. `docs/SPEC-01-content-bot.md` — pipeline overview (§2), status rules (§6 quality gate)
2. `.claude/phases/phase-1/plan.md` — P1-T7 acceptance
3. Existing modules (public APIs only):
   - `apps/bot/keyword_manager.py` — `KeywordManager`
   - `apps/bot/research_agent.py` — `build_research_bundle`
   - `apps/bot/generation_agent.py` — `generate_outline`, `write_sections` (async)
   - `apps/bot/quality_gate.py` — `run_quality_gate`
   - `apps/bot/mdx_writer.py` — `apply_article_updates`, `build_article_artifact`, `write_article`
4. `apps/bot/main.py` — currently a stub; expand this (or add `pipeline.py` if `main.py` would exceed ~200 lines)

## Goal

`python apps/bot/main.py --batch N --dry-run` runs the full pipeline for N keywords without live API calls (where `dry_run=True` is supported) and without publish side effects (no DB `published`, no deploy hook).

Live mode (`--dry-run` omitted) may call external APIs when keys are present; still respect writer publish semantics.

## Pipeline per keyword (T2 → T6)

For each row from `KeywordManager.select_keywords(batch_size)`:

1. **Research** — `build_research_bundle(keyword, intent, dry_run=...)`
2. **Outline** — `await generate_outline(keyword, intent, research_bundle, dry_run=...)`
3. **Sections** — `await write_sections(outline, research_bundle, intent, dry_run=..., affiliate_partner=row.get("affiliate_partner"))`
4. **Assemble** generation dict (see below)
5. **Quality gate** — `run_quality_gate(article, existing_articles=articles_written_this_run)`
6. **MDX handoff** — `merged = apply_article_updates(article, qa_result)` → `artifact = build_article_artifact(merged, qa_result)` → `write_article(artifact, dry_run=..., db_path=..., content_root=..., affiliate_map_root=...)`
7. **Status** — update `keywords.status` via `KeywordManager.update_status` (see status rules)
8. **Logging** — emit one structured JSON log line per article (see below)
9. On success (not skipped), append article dict to `articles_written_this_run` for duplicate detection in later rows

### Assemble generation dict

Build a `dict[str, Any]` matching what `quality_gate` and `mdx_writer` expect:

```python
{
    "slug": row["slug"],
    "keyword": row["keyword"],
    "category": row["category"],
    "intent": row["intent"],
    "h1": outline["h1"],
    "meta_description": outline["meta_description"],
    "sections": sections,  # from write_sections
    "faqs": outline.get("faqs", []),
    "affiliate_partner": row.get("affiliate_partner"),
    "cta_variant": row.get("cta_variant") or "A",
}
```

Prefer a small named function e.g. `assemble_article(row, outline, sections) -> dict[str, Any]` in `main.py` or `pipeline.py`.

### Research `dry_run` (required for safe E2E)

`generation_agent` already supports `dry_run`. `research_agent.build_research_bundle` does **not** yet.

Add `dry_run: bool = False` to `build_research_bundle`. When `True`, return a minimal valid bundle (same shape as SPEC-01 §4.3 / `tests/test_research_agent.py` fixtures) without HTTP calls. Add a focused unit test in `test_research_agent.py`.

When `main` runs with `--dry-run`, pass `dry_run=True` into research, outline, and sections.

### Status rules

| Outcome | `keywords.status` |
|---------|-------------------|
| QA `overall == "FAIL"` or unhandled exception for slug | `failed` |
| `write_article` skipped (`qa_failed`) | `failed` |
| PASS/WARN + live run (`dry_run=False`) | `published` is set by `write_article` (DB inside writer) — do not double-update published in main unless needed |
| PASS/WARN + `--dry-run` | Do **not** set `published`. Reset `generating` → `pending` after successful dry-run write so the DB is not stuck (call `update_status(slug, "pending")`) |

Keywords are claimed as `generating` by `select_keywords`; failed slugs must not stay `generating`.

### Structured logging

Use the `logging` module. For each article, emit **one JSON object per line** (INFO), e.g.:

```json
{"event":"article_complete","slug":"...","qa_overall":"PASS","skipped":false,"mdx_path":"...","checks_failed":0}
```

Include on failure: `"event":"article_error"`, `"slug"`, `"error": "..."`.

At run start/end, log `batch_started` / `batch_finished` with `batch`, `dry_run`, `selected`, `succeeded`, `failed`, `skipped`.

Do not log secrets or API keys.

### CLI

Keep existing flags in `build_parser()`:

- `--batch` (int, default 3)
- `--dry-run` (flag)

`main()` → `run(batch, dry_run, *, db_path=DB_PATH, ...)` so tests can inject `tmp_path` DB and content roots.

Return exit code `0` if the batch completed (even if some articles failed); non-zero only for fatal errors (DB missing, zero keywords selected when batch>0 is optional — document choice in handoff).

Use `asyncio.run()` once per batch to run async generation steps.

### Error handling

- Per-article `try/except`: catch specific exceptions (`ResearchAgentError`, `ValidationError`, `MDXWriterError`, etc.); log `article_error`; set status `failed`; continue remaining keywords.
- No bare `except:`.
- Do not abort the whole batch on one article failure unless the failure is pre-loop (e.g. cannot open DB).

## Tests

### `apps/bot/tests/test_main.py` (expand)

Integration-style test (no real HTTP):

1. `tmp_path` SQLite DB via `init_db` + insert **3** eligible keywords (`pending`, volume>100, difficulty<45)
2. Call `run(batch=3, dry_run=True, db_path=..., content_root=tmp_path/"content", affiliate_map_root=tmp_path/"affiliate")`
3. Assert return code `0`
4. Assert at least one MDX file under `content/{category}/` (or exactly 3 if QA always passes on dry-run fixtures)
5. Assert keywords are not left in `generating` after successful dry-run (expect `pending` or `failed` per rules)
6. Assert deploy was not triggered (no env hook call — use `monkeypatch` on deploy if needed)

Keep existing `test_run_returns_zero_for_dry_run` or update it to use the real pipeline with a seeded DB.

### Do not break existing tests

Full suite must stay green: `pytest apps/bot/tests/`.

## Project rules

- Type hints on all new public functions
- No code comments unless necessary
- `black` 88 char / `ruff` — run `python -m ruff check apps/bot/` and `python -m ruff format` on touched files
- Do **not** commit `.env`
- Do **not** mark P1-T7 **COMPLETED** in `execution-log.md` — set **NEEDS REVIEW** with note “pipeline orchestration implemented; ready for review”

## Verification (run and report)

```bash
cd apps/bot
python -m ruff check .
python -m ruff format --check .
python -m pytest tests/ -q
python main.py --batch 3 --dry-run
```

If pytest segfaults on Python 3.13 readline:

```bash
env PYTHONPATH=/private/tmp/no_readline:apps/bot python -m pytest apps/bot/tests/ -q
```

## Docs (minimal)

- `.claude/phases/phase-1/execution-log.md` — P1-T7 section: NEEDS REVIEW, commands, pass counts
- `.claude/phases/phase-1/qa-checklist.md` — check `main.py` items when satisfied
- `.claude/phases/phase-1/manual.md` — optional one-line gate note if you add P1-T7 execution section

## Handoff (required)

```md
## Task Handoff

Task: P1-T7 (pipeline orchestration)
Status: NEEDS REVIEW

Changed files:
- (list)

Commands run:
- python -m ruff check apps/bot/
- python -m pytest apps/bot/tests/
- python apps/bot/main.py --batch 3 --dry-run

Result:
- N passed; dry-run batch summary

Risks or blockers:
- None | ...

Contract changes:
- build_research_bundle(dry_run=...); run() orchestrates T2–T6
```

## Acceptance checklist

- [ ] `run()` orchestrates select → research → outline → sections → QA → merge → build artifact → write
- [ ] `--dry-run` avoids external HTTP (research + generation stubs) and publish DB/deploy
- [ ] Structured JSON logs per article + batch summary
- [ ] Status transitions: `failed` on FAIL/error; dry-run success resets to `pending`
- [ ] Integration test for `batch=3` dry-run
- [ ] `pytest` + `ruff` green
- [ ] Phase 1 DoD command works: `python apps/bot/main.py --batch 3 --dry-run`
```
