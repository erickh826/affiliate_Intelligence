# Project Context — Current vs Target

**Last updated:** 2026-05-12

---

## What We Build

A **Programmatic SEO Content Machine** that:

1. Generates AI-assisted long-form articles targeting AI tool comparison keywords
2. Publishes them on a fast, E-E-A-T-compliant Next.js website
3. Monetises via Google AdSense (display) + affiliate marketing (recurring commissions)
4. Exports video scripts for AI-generated short-form video content (Phase 4)

**Core principle:** Automation handles scale. Human review handles quality gates. Every page must have independent search value — never thin content.

---

## Reality Check (Read First)

- This repository is currently **spec-first / planning-first**.
- Architecture and workflows in this file describe the **target implementation state**.
- If a path or command below does not exist yet, treat it as planned work.
- `SPEC-01` to `SPEC-04` are authoritative for implementation details.

---

## Tech Stack (Target, Config-Driven)

| Layer | Target Technology | Configuration Source |
|---|---|---|
| Content Pipeline | Python 3.11+, asyncio | implementation default |
| LLM (Research) | Perplexity / equivalent online research model | `PERPLEXITY_MODEL` |
| LLM (Outline / QA) | OpenAI lightweight reasoning model | `OPENAI_MODEL_OUTLINE` |
| LLM (Writing) | Anthropic fast generation model | `ANTHROPIC_MODEL_WRITING` |
| Web Scraping | Firecrawl | implementation default |
| Website | Next.js 14 App Router, Tailwind CSS v4 | implementation default |
| Deployment | Vercel (free tier) | implementation default |
| Database | SQLite (`data/keywords.db`) | implementation default |
| Analytics | GA4 + Google Search Console | environment integration |
| Video (Phase 4) | Creatomate -> HeyGen -> YouTube Shorts | `SPEC-04` |

---

## Spec Files (Authoritative)

| File | Scope |
|---|---|
| `docs/SPEC-01-content-bot.md` | Content Bot Pipeline — keyword DB, research, generation, quality gate, MDX output |
| `docs/SPEC-02-web-system.md` | Web Publishing — Next.js site, SEO, CTA injection, GSC feedback loop |
| `docs/SPEC-03-monetisation.md` | Monetisation — AdSense, affiliate programs, CTA config, revenue tracking |
| `docs/SPEC-04-video-pipeline.md` | Video Pipeline (Phase 4) — article-to-script, AI video, YouTube publish |

**Rule:** When a spec file and any other document conflict, the SPEC file wins. Update the spec first, then propagate.

---

## Repository Layout

### Current (as of now)

This repository currently centers on specs and AI-context docs. Runtime folders (`apps/bot/`, `apps/web/`, `monetisation/`, `data/`) may be absent until phase execution begins.

### Target (after implementation phases)

```
pseo-project/
├── apps/bot/                          ← SPEC-01: Python pipeline
│   ├── main.py
│   ├── keyword_manager.py
│   ├── research_agent.py
│   ├── generation_agent.py
│   ├── quality_gate.py
│   ├── mdx_writer.py
│   ├── gsc_feedback.py
│   └── video_script_extractor.py
├── apps/web/                          ← SPEC-02: Next.js website
│   ├── app/
│   ├── components/
│   ├── content/
│   ├── lib/
│   └── next.config.ts
├── monetisation/                      ← SPEC-03: monetisation config
│   ├── affiliate_map/
│   ├── adsense_config.json
│   └── revenue_log.csv
├── data/
│   └── keywords.db                    ← Master keyword + article status DB
├── docs/                               ← Spec files
│   ├── SPEC-01-content-bot.md
│   ├── SPEC-02-web-system.md
│   ├── SPEC-03-monetisation.md
│   └── SPEC-04-video-pipeline.md
├── .ai-context/                       ← AI agent context files
└── .env.example
```

---

## Execution Timeline (Target Milestones)

| Week | Milestone | Spec |
|---|---|---|
| 1 | Keyword DB seeded (200 rows) | SPEC-01 |
| 1–2 | Bot pipeline: 5 articles/day locally | SPEC-01 |
| 2–3 | Next.js site live on custom domain, 15 articles | SPEC-02 |
| 3–4 | About / Privacy / Disclaimer pages done | SPEC-02 |
| 4 | AdSense application submitted | SPEC-03 |
| 5–7 | First 3 affiliate accounts approved | SPEC-03 |
| 8 | AdSense approved + first ad revenue | SPEC-03 |
| 8–11 | 100 articles, GSC impressions > 1,000/day | SPEC-01/02 |
| 12 | GSC feedback loop active | SPEC-02 |
| 12+ | Video pipeline begins | SPEC-04 |

---

## Environment Variables

When implementation is active, see `.env.example` for the full list. Key variables:

- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, `FIRECRAWL_API_KEY`
- `OPENAI_MODEL_OUTLINE`, `ANTHROPIC_MODEL_WRITING`, `PERPLEXITY_MODEL`
- `VERCEL_DEPLOY_HOOK_URL`
- `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_GA_MEASUREMENT_ID`
- `GSC_SERVICE_ACCOUNT_JSON`
- `HEYGEN_API_KEY`, `CREATOMATE_API_KEY`, `ELEVENLABS_API_KEY` (Phase 4)
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` (Phase 4)

---

## Owner & Context

- **Owner:** LLM Developer (Hong Kong)
- **Payment:** HK bank wire / Payoneer (see SPEC-03 Section 8)
- **Tax:** W-8BEN required for AdSense & some affiliate networks
