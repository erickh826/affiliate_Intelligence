# Programmatic SEO Content Machine — Project README

**Version:** 1.0 | **Updated:** 2026-05-12 | **Owner:** LLM Developer (HK)

---

## Project Overview

An automated content publishing system that:
1. Generates AI-assisted long-form articles (Programmatic SEO) targeting AI tool comparison keywords
2. Publishes them on a fast, E-E-A-T-compliant Next.js website
3. Monetises via Google AdSense (display) + affiliate marketing (recurring commissions)
4. Exports video scripts for AI-generated short-form video content (Phase 4)

> **Core principle:** Automation handles scale. Human review handles quality gates.
> Every page must have independent search value — never thin content.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       SYSTEM OVERVIEW                            │
│                                                                  │
│  [keywords.db]──►[SPEC-01: Content Bot]──►[/content/*.mdx]       │
│       ▲                │                         │               │
│       │           Quality Gate               [SPEC-02]          │
│  [GSC API]             │                    Web Publisher        │
│  Feedback           Passed                      │               │
│  Loop ◄─────────────────────────────────[Public Website]        │
│                                               │    │            │
│                                          [AdSense][Affiliate]   │
│                                               └────┘            │
│                                            [SPEC-03]            │
│                                         Monetisation            │
│                                                                  │
│  (Phase 4)──►[SPEC-04: Video Pipeline]                          │
│              Article → Script → AI Video → YouTube              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Sub-System Specs

| Spec File | System | Purpose |
|---|---|---|
| [SPEC-01-content-bot.md](./docs/SPEC-01-content-bot.md) | **Content Bot Pipeline** | LLM article generation, keyword DB, quality gate, MDX output |
| [SPEC-02-web-system.md](./docs/SPEC-02-web-system.md) | **Web Publishing System** | Next.js site, SEO rendering, CTA injection, GSC integration |
| [SPEC-03-monetisation.md](./docs/SPEC-03-monetisation.md) | **Monetisation System** | AdSense setup, affiliate accounts, CTA map, revenue tracking |
| [SPEC-04-video-pipeline.md](./docs/SPEC-04-video-pipeline.md) | **Video Pipeline** (Phase 4) | Article-to-script, AI video generation, YouTube publish |

---

## Repository Structure

```
pseo-project/
│
├── README.md                          ← This file
│
├── docs/                               ← Spec files
│   ├── SPEC-01-content-bot.md
│   ├── SPEC-02-web-system.md
│   ├── SPEC-03-monetisation.md
│   └── SPEC-04-video-pipeline.md
│
├── apps/
│   ├── bot/                           ← SPEC-01: Python pipeline
│   │   ├── main.py                    ← Batch generation runner
│   │   ├── keyword_manager.py         ← Read/write keyword_database.csv
│   │   ├── research_agent.py          ← Firecrawl + Perplexity
│   │   ├── generation_agent.py        ← LLM generation
│   │   ├── quality_gate.py            ← Automated QA checks
│   │   ├── mdx_writer.py              ← MDX + frontmatter output
│   │   ├── gsc_feedback.py            ← Weekly GSC feedback loop
│   │   └── video_script_extractor.py  ← SPEC-04 script generator
│   │
│   └── web/                           ← SPEC-02: Next.js website
│       ├── app/                       ← App Router pages
│       ├── components/                ← Shared UI (AffiliateCTA, YouTubeEmbed, etc.)
│       ├── content/                   ← MDX articles (bot-written)
│       ├── lib/                       ← cta_injector.ts, schema_builder.ts
│       └── next.config.ts
│
├── packages/
│   └── shared-types/                  ← Cross-language schema contracts
│
├── monetisation/                      ← SPEC-03: monetisation config
│   ├── affiliate_map/                 ← Per-article CTA configs (JSON)
│   ├── adsense_config.json
│   └── revenue_log.csv
│
├── data/
│   └── keywords.db                    ← Master keyword + article status DB (SQLite)
│
└── .env.example
```

---

## Data Contract: `data/keywords.db`

Single source of truth shared across all specs. Stored as SQLite to support concurrent writes from the bot pipeline and GSC feedback cron without race conditions.

| Column | Owner | Description |
|---|---|---|
| `id` | SPEC-01 | Unique row ID |
| `keyword` | SPEC-01 | Target keyword |
| `category` | SPEC-01 | Site category slug |
| `intent` | SPEC-01 | `informational` / `comparison` / `tutorial` |
| `monthly_volume` | SPEC-01 | Estimated monthly searches |
| `difficulty` | SPEC-01 | KD score 0–100 |
| `status` | SPEC-01/02 | `pending` / `published` / `needs_rewrite` / `failed` |
| `slug` | SPEC-01 | URL slug |
| `published_at` | SPEC-02 | First deploy date |
| `gsc_impressions` | SPEC-02 | Last 7-day GSC impressions |
| `gsc_clicks` | SPEC-02 | Last 7-day GSC clicks |
| `gsc_ctr` | SPEC-02 | CTR = clicks / impressions |
| `gsc_position` | SPEC-02 | Average search position |
| `affiliate_partner` | SPEC-03 | Primary affiliate to feature |
| `cta_variant` | SPEC-03 | Active A/B variant |
| `revenue_mtd` | SPEC-03 | Month-to-date affiliate estimate |
| `youtube_url` | SPEC-04 | Embedded YouTube URL |
| `video_status` | SPEC-04 | `none` / `scripted` / `published` |

---

## Data Flow

```
data/keywords.db (SQLite)
        │
        ▼ (SPEC-01)
  Bot generates MDX articles → apps/web/content/
        │
        ▼ (SPEC-02)
  Next.js builds static site → Vercel → Public
        │
        ├──► AdSense display revenue
        └──► Affiliate link clicks → commissions
                                  (SPEC-03)
        │
        ▼ (SPEC-02 feedback loop)
  GSC data → keywords.db
  Low CTR pages → status=needs_rewrite → re-queued to SPEC-01
        │
        ▼ (SPEC-04, Phase 4)
  High-traffic articles → Video scripts → AI video → YouTube
  YouTube URL → embedded back into article page
```

---

## Execution Timeline

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
| 12+ | Video pipeline begins (SPEC-04) | SPEC-04 |

---

## Quick Start

```bash
# 1. Init repo
git init pseo-project && cd pseo-project

# 2. Bot setup
cd apps/bot && pip install -r requirements.txt
cp ../../.env.example ../../.env

# 3. Web setup
cd ../web && npm install && npm run dev

# 4. Init SQLite database
cd ../../data && python -c "import sqlite3; sqlite3.connect('keywords.db').close()"

# 5. First test batch (3 articles, dry run)
cd ../apps/bot && python main.py --batch 3 --dry-run
```

---

*All specs live in `docs/`. Cross-reference by filename.*
