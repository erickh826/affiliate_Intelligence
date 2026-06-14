# Phase 1 — QA Checklist

**Phase:** 1 — Content Bot Pipeline (SPEC-01)
**Status:** IN PROGRESS (P1-T0–T6 done; P1-T7 orchestration pending)

---

## Functional Requirements

- [ ] `data/keywords.db` created with correct schema (18 columns, CHECK constraints, indexes)
- [ ] 200 keyword rows seeded across 5 categories
- [ ] `keyword_manager.py`: selects keywords by volume/(difficulty+1) priority
- [ ] `keyword_manager.py`: filters by status, volume>100, difficulty<45
- [ ] `keyword_manager.py`: rewrite mode selects `needs_rewrite` rows
- [ ] `keyword_manager.py`: selected rows are claimed via select-and-lock transaction
- [ ] `keyword_manager.py`: default selection excludes difficulty >=45 unless force override is used
- [ ] `keyword_manager.py`: status transitions preserve GSC performance fields during rewrite publish
- [ ] `keyword_manager.py`: SQLite connection lifecycle is managed via context manager
- [x] `research_agent.py`: Firecrawl scrapes top-5 SERP results
- [x] `research_agent.py`: Perplexity API extracts facts, tools, FAQ seeds
- [x] `research_agent.py`: research_bundle schema matches SPEC-01 §4.3
- [x] `generation_agent.py`: outline generated via gpt-4o-mini
- [x] `generation_agent.py`: outline validated against outline_schema.json
- [x] `generation_agent.py`: sections written via claude-3-5-haiku (max 3 concurrent)
- [x] `generation_agent.py`: long-form articles are generated section-by-section to avoid token truncation
- [x] `generation_agent.py`: affiliate_partner context is included and CTA placeholders or approved MDX components are emitted
- [x] `generation_agent.py`: system prompt includes MDX safety rules and forbids raw HTML tags
- [x] `generation_agent.py`: internal-link placeholders are included where relevant
- [x] `generation_agent.py`: style guide parameter controls tone and voice
- [x] `generation_agent.py`: E-E-A-T injection per intent type
- [x] `generation_agent.py`: fallback to gpt-4o when Anthropic API unavailable
- [x] `quality_gate.py`: word count > 1,200 check
- [x] `quality_gate.py`: cosine similarity < 0.85 uniqueness check
- [x] `quality_gate.py`: factual anchor count >= 3 (WARN)
- [x] `quality_gate.py`: keyword present in H1
- [x] `quality_gate.py`: keyword present in first 100 words
- [x] `quality_gate.py`: meta description 140-165 chars (AUTO-FIX)
- [x] `quality_gate.py`: FAQ count >= 4
- [x] `quality_gate.py`: broken internal links check (WARN)
- [x] `quality_gate.py`: AI filler phrase count < 3
- [x] `quality_gate.py`: banned phrase list is loaded from `apps/bot/config/banned_phrases.txt`
- [x] `quality_gate.py`: banned phrase config includes SPEC-01 phrases plus common AI filler phrases
- [x] `quality_gate.py`: basic MDX syntax preflight checks approved component syntax
- [x] `quality_gate.py`: image placeholder check warns when no image or image placeholder exists
- [x] `quality_gate.py`: readability score warns when prose is too dense
- [x] `quality_gate.py`: FAIL sets status=failed, skips article
- [x] `models.py`: defines `ResearchContext`
- [x] `models.py`: defines `GeneratedSection`
- [x] `models.py`: defines `GenerationContext`
- [x] `models.py`: defines `Frontmatter`
- [x] `models.py`: defines `ArticleArtifact`
- [x] `models.py`: contracts are importable and covered by lightweight tests
- [x] `mdx_writer.py`: consumes `ArticleArtifact` / `Frontmatter` contract instead of only loose dict inputs
- [x] `mdx_writer.py`: frontmatter matches SPEC-01 §8.1
- [x] `mdx_writer.py`: writes to `apps/web/content/{category}/{slug}.mdx`
- [x] `mdx_writer.py`: writes FAQ JSON to `apps/web/content/faq/{slug}.faq.json`
- [x] `mdx_writer.py`: writes affiliate map stub to `monetisation/affiliate_map/{slug}.json`
- [x] `mdx_writer.py`: deploy trigger POSTs to VERCEL_DEPLOY_HOOK_URL
- [x] `mdx_writer.py`: updates keywords.db status and published_at
- [x] `main.py`: `--batch N` flag works
- [x] `main.py`: `--dry-run` flag skips deploy and DB update
- [x] `main.py`: structured JSON logging per article

## Error Handling

- [x] LLM API failures retry 3x with exponential backoff
- [x] Firecrawl failures handled gracefully
- [x] Perplexity API failures handled gracefully
- [x] No bare `except:` blocks
- [x] Specific exception types caught
- [x] Semaphore(3) limits concurrent LLM calls

## Code Quality

- [x] `black` formatting passes (88 char line)
- [x] `ruff` lint passes with zero errors
- [x] Type hints on all public function signatures
- [x] No `any` type usage
- [x] No code comments (unless requested)

## Tests

- [x] `pytest apps/bot/tests/` passes
- [x] All external APIs mocked in tests
- [x] Quality gate unit tests cover all 8 checks
- [x] Integration test: dry-run 3 articles end-to-end
- [x] Edge cases: empty DB, all keywords failed, API timeout

## Cost Validation

- [x] Per-article cost within $0.024 estimate (±50%)
- [x] LLM call counts logged and verifiable
