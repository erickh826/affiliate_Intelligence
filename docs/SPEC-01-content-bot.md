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
[1] Keyword Selector ── picks N rows by volume/difficulty ratio
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

Priority score: `volume / (difficulty + 1)` — highest selected first.

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

```python
messages = [
    {"role": "system", "content": "Extract factual data only. No opinions."},
    {"role": "user", "content": 
        f"Research '{keyword}':\n"
        "1. Top 5 tools with pricing\n"
        "2. Market statistics with sources\n"
        "3. Common user complaints\n"
        "4. Expert recommendations"
    }
]
# model: llama-3.1-sonar-large-128k-online
```

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
```

Output validated against `outline_schema.json` before proceeding.

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
# model: claude-3-5-haiku
```

E-E-A-T injection rules per intent:
- `comparison`: requires pricing comparison table
- `tutorial`: requires code snippet or numbered steps
- `informational`: requires ≥1 statistic with source

---

## 7. Quality Gate

**File:** `apps/bot/quality_gate.py`

Any FAIL → article marked `status=failed`, pipeline skips it.

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
---
```

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
| Research | `llama-3.1-sonar-large-128k-online` (Perplexity) | Real-time web access |
| Outline | `gpt-4o-mini` | Fast, cheap, sufficient |
| Section writing | `claude-3-5-haiku` | Best quality/cost for prose |
| Quality gate | `gpt-4o-mini` | Classifier task |
| Fallback (Anthropic down) | `gpt-4o` | Same quality, higher cost |

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
```

---

*Related: [README.md](../README.md) | [SPEC-02](./SPEC-02-web-system.md) | [SPEC-03](./SPEC-03-monetisation.md)*
