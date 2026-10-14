# SPEC-01 — Content Bot Pipeline

**Version:** 1.0 | **Updated:** 2026-05-12
**Related:** [README](../README.md) | [SPEC-02](./SPEC-02-web-system.md)

---

## 1. Purpose

SPEC-01 defines the automated content generation pipeline. It reads keyword targets from `data/keywords.db` (SQLite), researches each topic, generates long-form MDX articles via LLM, runs quality checks, and writes output to `apps/web/content/` for publishing by SPEC-02.

---

## 2. Pipeline Overview

```
data/keywords.db (status=pending)
         │
[1] Keyword Selector ── category-weighted batch, then volume/difficulty ratio
         │
[2] Research Agent ── Firecrawl top-5 SERPs + Perplexity API
         │
[3] Outline Generator ── LLM: H2/H3 structure + FAQ seeds
         │
[4] Section Writer ── parallel LLM calls (3 concurrent max)
         │
[5] Assembly ── combine sections + frontmatter
         │
[6] Quality Gate ── AUTO-FAIL checks (word count, uniqueness, filler)
         │
[7] MDX Writer ── write apps/web/content/[category]/[slug].mdx
         │
[8] Deploy Trigger ── POST to Vercel Deploy Hook
```

---

## 3. Keyword Selector

**File:** `apps/bot/keyword_manager.py`

Reads from `data/keywords.db` via SQLite. Selection criteria:
- `status == "pending"` OR `status == "needs_rewrite"`
- `monthly_volume > 100`
- `difficulty < 45`

Priority score: `volume / (difficulty + 1)` — highest selected first inside a category.

Category mix is controlled by `monetisation/category_weights.json`. While either focus category (`ai-writing`, `seo`) has fewer than `published_target` live articles (default 10, counted from MDX whose `draft` is not true), the batch uses `focus_weights` so most keywords come from AI Writing and SEO. After both reach the target, the batch uses `even_weights` and rotates across `ai-writing`, `seo`, `ai-video`, `ai-productivity`, and `ai-code`. Slots a category cannot fill spill into the other configured categories. `ai-image` stays in the database and is not part of this rotation.

Batch limits:
- Dev: 3 articles/run
- Prod: 10 articles/run
- Daily max: 20 articles

---

## 4. Research Agent

**File:** `apps/bot/research_agent.py`

### 4.1 Firecrawl Scraping

For each keyword, Firecrawl scrapes top 5 organic results:
- Extracts: headings, key claims, statistics, tool names
- Strips: navigation, ads, footers
- Output: list of `{url, title, headings[], body_summary}` dicts

### 4.2 Perplexity API Call

Sonar Chat Completions (`/chat/completions`, including `sonar-deep-research`) retired on 2026-09-27. Research uses the Agent API replacement for Sonar Deep Research.

```python
# POST https://api.perplexity.ai/v1/agent
# preset: high   # override with PERPLEXITY_PRESET
# background: true, then poll GET /v1/agent/{id} until status=completed
# response_format: json_schema {facts, tools_mentioned, faq_seeds}
```

`PERPLEXITY_MODEL=sonar-deep-research` still maps to preset `high`.

### 4.3 Research Bundle Schema

```python
research_bundle = {
    "keyword": str,
    "intent": str,                    # "comparison"|"informational"|"tutorial"
    "competitors_scraped": [
        {"url": str, "title": str, "headings": list, "body_summary": str}
    ],
    "facts": [{"claim": str, "source": str}],
    "tools_mentioned": [
        {"name": str, "pricing": str, "pros": list, "cons": list}
    ],
    "faq_seeds": list[str]            # from scraped PAA boxes
}
```

---

## 5. Outline Generator

**File:** `apps/bot/generation_agent.py → generate_outline()`

```python
system_prompt = (
    "You are an SEO content strategist for AI tools. "
    "Write outlines that match specific search intent."
)
user_prompt = (
    f"Keyword: '{keyword}'\n"
    f"Intent: {intent}\n"
    f"Research: {research_bundle_summary}\n\n"
    "Generate:\n"
    "- H1 title (keyword included naturally)\n"
    "- Meta description (150–160 chars)\n"
    "- 6–8 H2 sections with 2–3 H3 each\n"
    "- 5 FAQ questions from PAA data\n"
    "- Comparison table columns (if intent=comparison)"
)
# model: gpt-4o-mini
# fallback: claude-haiku-4-5-20251001 (ANTHROPIC_MODEL_WRITING) when OpenAI fails
```

Output validated against `outline_schema.json` before proceeding.

If the OpenAI outline call fails (including HTTP 429 `credit_balance_exhausted`), `generate_outline()` retries the same prompt on Anthropic using `ANTHROPIC_MODEL_WRITING` and the existing `ANTHROPIC_API_KEY`. The Anthropic outline request does not send `temperature`; `anthropic` 1.x removed that argument, and `anthropic` and `openai` are pinned in `apps/bot/requirements.txt`. Client-side SDK errors (`TypeError`, `ValueError`) are raised as `LLMAPIError`. No extra secret is required. When the OpenAI failure is quota or billing, including when the Anthropic call then fails as an `LLMAPIError`, the bot raises `ProviderOutageError`: locked keywords return to `pending` or `needs_rewrite`, later keywords in the batch are released, and the process exits 2. A live batch that selects keywords and writes no MDX also exits 2, so the cron does not commit an MDX-less database change. Draft MDX counts as a successful write for that exit code. Dry runs and empty selections exit 0. Transient timeouts stay retryable. A quality-gate duplicate (`action=skip`) still sets `status=failed` and writes no MDX. Other FAIL and WARN results are written with `draft: true`.

---

## 6. Section Writer

**File:** `apps/bot/generation_agent.py → write_sections()`

Each H2 written in a separate LLM call, parallelised (max 3 concurrent via `asyncio.gather`):

```python
system_prompt = (
    "You write sections of articles about AI tools. "
    "Be specific — include pricing, API limits, code examples. "
    "No generic AI filler phrases."
)
user_prompt = (
    f"Section: '{h2_heading}'\n"
    f"Sub-sections: {h3_list}\n"
    f"Facts to include: {section_facts}\n"
    "Target: 300–400 words. Include ≥1 pricing data point."
)
# model: claude-haiku-4-5-20251001
```

E-E-A-T injection rules per intent:
- `comparison`: requires pricing comparison table
- `tutorial`: requires code snippet or numbered steps
- `informational`: requires ≥1 statistic with source

---

## 7. Quality Gate

**File:** `apps/bot/quality_gate.py`

Duplicate FAIL (`action=skip`) → `status=failed`, pipeline skips the write. Any other FAIL or WARN is written with `draft: true` (`status=draft`) and is omitted from listings and the sitemap. PASS is published (`draft: false`) even when the category has no enabled affiliate program. In that case the page renders no affiliate CTA and no placeholder referral URL.

| Check | Threshold | Action |
|---|---|---|
| Word count | > 1,200 words | FAIL → regenerate |
| Duplicate detection | Cosine similarity < 0.85 vs existing articles | FAIL → skip |
| Factual anchor count | ≥ 3 specific claims | WARN → log |
| Keyword in H1 | Must be present | FAIL → regenerate |
| Meta description length | 140–165 chars | AUTO-FIX |
| FAQ count | ≥ 4 questions | FAIL → regenerate |
| Broken internal links | Zero | WARN → log |
| AI filler phrase count | < 3 instances | WARN → rewrite section |
| MDX syntax | Approved self-closing components only (`AffiliateCTA`, `Image`). No raw HTML. No MDX-breaking `<` (`<30`, `<$10`, `<=`) or unescaped `{` `}` outside fenced code, inline code, link destinations, and component props | FAIL → regenerate |

Section text is escaped when it is generated and again when the MDX file is written. A `<` that is not a complete JSX tag is stored as `\<` (so `<30` and `<$10` cannot abort `next build`). Prose braces are stored as `\{` and `\}`. Fenced code, inline code, `{{LINK_*}}` / `{{IMAGE_*}}` placeholders, and approved self-closing components are left intact. Placeholders that sit in prose, where MDX would evaluate them, still fail this check. `python apps/bot/check_content_mdx.py` runs the same check on `apps/web/content/**/*.mdx`. The daily bot runs it before commit, and `apps/web` CI renders every article with `@mdx-js/mdx` before `next build`.

### Banned Phrases

```python
BANNED_PHRASES = [
    "in today's digital landscape",
    "it's worth noting that",
    "at the end of the day",
    "needless to say",
    "as an AI language model",
    "game-changer",
    "empower your",
    "unlock the power of",
    "transformative journey",
    "in conclusion"
]
```

Articles with 3+ banned phrases trigger section-level rewrite (body preserved, section replaced).

---

## 8. MDX Writer

**File:** `apps/bot/mdx_writer.py`

### 8.1 Frontmatter

```yaml
---
title: "{title}"
description: "{meta_description}"
slug: "{slug}"
category: "{category}"
intent: "{intent}"
published_at: "{date}"
last_reviewed: "{date}"
author: "{author_name}"
affiliate_partner: "{partner}"
schema_type: "Article"
draft: false
---
```

`affiliate_partner` is the program id in `monetisation/affiliates.json`. The MDX file does not store the referral URL. `draft: true` keeps the article out of the homepage, category indexes, and sitemap. Publish a draft by setting `draft: false` in that frontmatter.

### 8.2 Output Paths

```
apps/web/content/{category}/{slug}.mdx
apps/web/content/faq/{slug}.faq.json
monetisation/affiliate_map/{slug}.json    (if new CTA mapping needed)
```

### 8.3 Deploy Trigger

```python
import requests, os
requests.post(os.environ["VERCEL_DEPLOY_HOOK_URL"])
# keywords.db: status=published, slug, published_at updated
```

---

## 9. Rewrite Mode

Triggered when `status == "needs_rewrite"` (set by SPEC-02 GSC feedback loop via `keywords.db`):

- Re-runs steps 1–4 (keyword, research, outline)
- Rewrites: H1 title, meta description, first 2 H2 sections
- Does NOT overwrite: comparison tables, FAQs, affiliate CTAs
- Updates: `last_reviewed = today` in frontmatter

---

## 10. LLM Model Config

| Stage | Model | Reason |
|---|---|---|
| Research | Perplexity Agent API preset `high` | Replaces retired `sonar-deep-research`; real-time web access |
| Outline | `gpt-4o-mini` (`OPENAI_MODEL_OUTLINE`) | Fast, cheap, sufficient |
| Outline fallback (OpenAI down or quota) | `claude-haiku-4-5-20251001` (`ANTHROPIC_MODEL_WRITING`) | Uses the Anthropic key already required by section writing |
| Section writing | `claude-haiku-4-5-20251001` (`ANTHROPIC_MODEL_WRITING`) | Replaces retired `claude-3-5-haiku-20241022` |
| Quality gate | deterministic checks in `quality_gate.py` | No model call |
| Fallback (Anthropic down) | `gpt-4o` (`OPENAI_MODEL_FALLBACK`) | Same quality, higher cost |

---

## 11. Cost per Article (Estimate)

| Stage | Est. Cost |
|---|---|
| Perplexity research | ~$0.003 |
| Outline (gpt-4o-mini) | ~$0.001 |
| 7 sections (claude-haiku) | ~$0.018 |
| Quality gate | ~$0.002 |
| **Total** | **~$0.024** |

At 20 articles/day: ~$0.48/day → ~$14.40/month.

---

## 12. Environment Variables

```env
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
PERPLEXITY_API_KEY=
FIRECRAWL_API_KEY=
VERCEL_DEPLOY_HOOK_URL=
PERPLEXITY_PRESET=high
OPENAI_MODEL_OUTLINE=gpt-4o-mini
ANTHROPIC_MODEL_WRITING=claude-haiku-4-5-20251001
OPENAI_MODEL_FALLBACK=gpt-4o
```

---

*Related: [README.md](../README.md) | [SPEC-02](./SPEC-02-web-system.md) | [SPEC-03](./SPEC-03-monetisation.md)*
