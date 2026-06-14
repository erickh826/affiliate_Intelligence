# System Specification — Consolidated

**Last updated:** 2026-05-12
**Source of truth:** SPEC-01/02/03/04 files in `docs/`. This file is a consolidated reference for multi-model review.

---

## 1. System Purpose

Programmatic SEO content machine that:
1. Generates AI-assisted long-form articles targeting AI tool comparison keywords
2. Publishes them on a fast, E-E-A-T-compliant Next.js website
3. Monetises via Google AdSense + affiliate marketing
4. Exports video scripts for AI-generated short-form video content (Phase 4)

**Core principle:** Automation handles scale. Human review handles quality gates. Every page must have independent search value — never thin content.

---

## 2. Architecture

```
keywords.db (SQLite) ──► SPEC-01 Bot (Python) ──► web/content/*.mdx ──► SPEC-02 Next.js ──► Vercel ──► Public Site
                                                                                                │
                                                                                          AdSense + Affiliate (SPEC-03)
                                                                                          │
                                                                                          GSC Feedback Loop
                                                                                          (needs_rewrite → SPEC-01)
                                                                                          │
                                                                                          SPEC-04 Video Pipeline (Phase 4)
                                                                                          (Article → Script → AI Video → YouTube → embed back)
```

---

## 3. Phase Breakdown

| Phase | Spec | Scope | Timeline |
|---|---|---|---|
| 1 | SPEC-01 | Content Bot Pipeline: keyword DB, research agent, LLM writing, quality gate, MDX output | Weeks 1–2 |
| 2 | SPEC-02 | Web Publishing: Next.js site, MDX rendering, CTA injection, SEO, E-E-A-T, GSC setup | Weeks 2–4 |
| 3 | SPEC-03 | Monetisation: AdSense application, affiliate accounts, CTA config, revenue tracking | Weeks 4–8 |
| 4 | SPEC-04 | Video Pipeline: article-to-script, AI video generation, YouTube publish, cross-embed | Week 12+ |

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Content Pipeline | Python 3.11+, asyncio |
| LLM (Research) | Perplexity `llama-3.1-sonar-large-128k-online` |
| LLM (Outline/QA) | OpenAI `gpt-4o-mini` |
| LLM (Writing) | Anthropic `claude-3-5-haiku` |
| LLM Fallback | OpenAI `gpt-4o` |
| Web Scraping | Firecrawl |
| Website | Next.js 14 App Router, Tailwind CSS v4 |
| Deployment | Vercel (free tier) |
| Database | SQLite (`data/keywords.db`) |
| Analytics | GA4 + Google Search Console |
| Video (Phase 4) | Creatomate → HeyGen → YouTube Shorts |

---

## 5. Data Model — keywords table

| Column | Type | Constraints | Owner |
|---|---|---|---|
| `id` | INTEGER | PK, AUTOINCREMENT | SPEC-01 |
| `keyword` | TEXT | NOT NULL, UNIQUE | SPEC-01 |
| `category` | TEXT | NOT NULL | SPEC-01 |
| `intent` | TEXT | CHECK IN ('informational','comparison','tutorial') | SPEC-01 |
| `monthly_volume` | INTEGER | NOT NULL, DEFAULT 0 | SPEC-01 |
| `difficulty` | INTEGER | 0–100 | SPEC-01 |
| `status` | TEXT | CHECK IN ('pending','published','needs_rewrite','failed') | SPEC-01/02 |
| `slug` | TEXT | UNIQUE | SPEC-01 |
| `published_at` | TEXT | ISO 8601 | SPEC-02 |
| `gsc_impressions` | INTEGER | DEFAULT 0 | SPEC-02 |
| `gsc_clicks` | INTEGER | DEFAULT 0 | SPEC-02 |
| `gsc_ctr` | REAL | DEFAULT 0.0 | SPEC-02 |
| `gsc_position` | REAL | DEFAULT 0.0 | SPEC-02 |
| `affiliate_partner` | TEXT | NULL | SPEC-03 |
| `cta_variant` | TEXT | CHECK IN ('A','B','C') | SPEC-03 |
| `revenue_mtd` | REAL | DEFAULT 0.0 | SPEC-03 |
| `youtube_url` | TEXT | NULL | SPEC-04 |
| `video_status` | TEXT | CHECK IN ('none','scripted','published') | SPEC-04 |

Full DDL and indexes in `.ai-context/data-schema.md`.

---

## 6. Pipeline — SPEC-01 (Phase 1)

```
1. Keyword Selector    → SELECT pending/needs_rewrite WHERE volume>100, difficulty<45
2. Research Agent      → Firecrawl top-5 SERPs + Perplexity API
3. Outline Generator   → gpt-4o-mini: H2/H3 + FAQ seeds
4. Section Writer      → claude-3-5-haiku (3 concurrent, asyncio.Semaphore(3))
5. Assembly            → combine sections + frontmatter
6. Quality Gate        → word count>1200, uniqueness<0.85, keyword in H1, FAQ>=4, banned phrases<3
7. MDX Writer          → write web/content/{category}/{slug}.mdx
8. Deploy Trigger      → POST VERCEL_DEPLOY_HOOK_URL
```

### Quality Gate Rules

| Check | Threshold | Action |
|---|---|---|
| Word count | > 1,200 | FAIL → regenerate |
| Duplicate detection | Cosine similarity < 0.85 | FAIL → skip |
| Factual anchor count | >= 3 specific claims | WARN |
| Keyword in H1 | Must be present | FAIL → regenerate |
| Meta description | 140–165 chars | AUTO-FIX |
| FAQ count | >= 4 | FAIL → regenerate |
| AI filler phrases | < 3 | WARN → rewrite section |

### Cost Estimate

~$0.024/article. At 20/day: ~$14.40/month.

---

## 7. Website — SPEC-02 (Phase 2)

- Next.js 14 App Router, SSG via `generateStaticParams`
- Tailwind CSS v4, dark mode default
- CTA injection: `lib/cta_injector.ts` reads `monetisation/affiliate_map/{slug}.json`
- Schema: Article + FAQPage + BreadcrumbList JSON-LD
- E-E-A-T: author byline, last reviewed date, affiliate disclosure
- Core Web Vitals: LCP<2s, INP<200ms, CLS<0.1
- GSC feedback loop: weekly cron, flag `needs_rewrite` when impressions>200 AND ctr<0.01

### Site Routes

```
/                        Homepage
/[category]/             Category index
/[category]/[slug]/      Article page
/about/                  Author bio (E-E-A-T)
/contact/                Contact form (Formspree)
/privacy-policy/         GDPR + AdSense
/disclaimer/             Affiliate disclosure
/sitemap.xml             Auto-generated
/robots.txt              Allow all
```

### Design Tokens

| Token | Dark (default) | Light |
|---|---|---|
| Background | `#111827` | `#fafaf9` |
| Surface | `#1f2937` | `#f5f5f4` |
| Accent | `#0d9488` | `#0d9488` |
| Text | `#f9fafb` | `#1c1917` |
| Font display | Instrument Serif | same |
| Font body | Inter | same |

---

## 8. Monetisation — SPEC-03 (Phase 3)

### Revenue Streams

- **AdSense:** RPM $3–$15; best for informational pages
- **Affiliate:** 20–30% recurring; best for comparison/tutorial pages

### Revenue Priority Rule

- `intent=comparison/tutorial`: Affiliate CTAs take priority, AdSense suppressed above fold
- `intent=informational`: AdSense auto-ads enabled fully

### Priority Affiliate Programs

| Program | Commission | Cookie |
|---|---|---|
| Surfer SEO | 25% recurring lifetime | 30 days |
| Writesonic | 30% recurring 12mo | 60 days |
| Jasper AI | 25% recurring 12mo | 45 days |
| ElevenLabs | 22% recurring 12mo | 30 days |
| Notion | $10 flat/signup | 90 days |

### CTA Placements

| Position | Location |
|---|---|
| `top` | After H1, before paragraph 1 |
| `inline` | After H2 section #3 |
| `bottom` | Before FAQ section |

---

## 9. Video Pipeline — SPEC-04 (Phase 4)

**Trigger:** 100+ published articles AND 1,000+ daily organic visitors.

```
1. Article Selector    → gsc_impressions>500/week, intent in (comparison, tutorial)
2. Script Extractor    → claude-3-5-haiku: 60s HOOK→VALUE→PROOF→CTA
3. AI Video Generator  → Creatomate (start) / HeyGen (scale)
4. YouTube Publisher   → Data API v3, vertical 1080×1920, <60s
5. Cross-embed         → youtube_url → keywords.db → SPEC-02 embeds on next build
```

---

## 10. Environment Variables

```env
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
PERPLEXITY_API_KEY=
FIRECRAWL_API_KEY=
VERCEL_DEPLOY_HOOK_URL=
NEXT_PUBLIC_SITE_URL=
NEXT_PUBLIC_SITE_NAME=AI Tools Hub
NEXT_PUBLIC_GA_MEASUREMENT_ID=
NEXT_PUBLIC_ADSENSE_PUBLISHER_ID=
GSC_SERVICE_ACCOUNT_JSON=
HEYGEN_API_KEY=
CREATOMATE_API_KEY=
ELEVENLABS_API_KEY=
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=
```

---

## 11. Coding Conventions (Summary)

- Python: `black` (88), `ruff`, type hints, `asyncio.Semaphore(3)`, specific exceptions only
- TypeScript: Prettier (80, single quotes), ESLint (next/core-web-vitals), strict, no `any`
- Commits: `type(scope): description` where scope = `s01`|`s02`|`s03`|`s04`|`web`|`bot`|`infra`
- No comments unless requested; no `.env` commits

Full conventions in `.ai-context/conventions.md`.
