# P1-T7 — Review Prompt

**Use when:** Claude (or another executor) finished P1-T7 and set **NEEDS REVIEW** in `execution-log.md`.  
**Executor prompt:** [p1-t7-claude-executor-prompt.md](./p1-t7-claude-executor-prompt.md)

Copy everything inside the fenced block below into your reviewer.

---

```markdown
# Review: P1-T7 Pipeline orchestration (Affiliate Intelligence)

Review Phase 1 task **P1-T7** after implementation. References:

- `docs/SPEC-01-content-bot.md` §2 (pipeline), §6 (quality gate / status)
- `.claude/phases/phase-1/plan.md` — Definition of Done
- Executor handoff + diff

## Commands to run

```bash
cd /path/to/affiliate_Intelligence

rg 'def run\(|async def|select_keywords|build_research_bundle|run_quality_gate|write_article' apps/bot/main.py apps/bot/pipeline.py 2>/dev/null || rg 'def run' apps/bot/main.py

python -m ruff check apps/bot/
python -m pytest apps/bot/tests/ -q
python apps/bot/main.py --batch 3 --dry-run
```

Report pass counts and dry-run stdout (JSON log lines).

## Checklist

### Orchestration

- [ ] `KeywordManager.select_keywords(batch)` claims rows (`generating`)
- [ ] Per keyword: research → outline → sections → assemble → `run_quality_gate` → `apply_article_updates` → `build_article_artifact` → `write_article`
- [ ] `existing_articles` passed to QA grows within the batch (duplicate check)
- [ ] `asyncio` used correctly for generation steps (single event loop per batch)

### `--dry-run` safety

- [ ] `build_research_bundle(..., dry_run=True)` does not call HTTP
- [ ] `generate_outline` / `write_sections` use `dry_run=True`
- [ ] `write_article(..., dry_run=True)` skips DB publish + deploy hook
- [ ] Successful dry-run does not leave keywords stuck in `generating` (expect `pending` reset per plan)
- [ ] QA FAIL → `failed` status

### Logging

- [ ] Per-article JSON log line (`article_complete` / `article_error`)
- [ ] Batch summary log (`batch_finished` with counts)
- [ ] No secrets in logs

### CLI & tests

- [ ] `--batch` and `--dry-run` flags work
- [ ] `test_main.py` integration test: 3 keywords, dry-run, asserts exit 0 + MDX output + status rules
- [ ] Full `pytest` + `ruff` green

### Phase 1 Definition of Done

- [ ] `python apps/bot/main.py --batch 3 --dry-run` completes successfully from repo root or documented `cd apps/bot` path

## Verdict (required)

### APPROVE

P1-T7 complete; mark **COMPLETED** in `execution-log.md`; Phase 1 bot pipeline ready for manual prod trial.

### APPROVE WITH NOTES

COMPLETED after listed fixes (tag P1 vs P2).

### REJECT

Blocking issues with file:line or test name.

## If APPROVE

Update `execution-log.md` (P1-T7 COMPLETED), `manual.md` status table, `qa-checklist.md` main.py items, and optionally Phase 1 **Final Results** in execution-log (pytest count, dry-run batch summary).
```
