# Architecture — System Diagram & Data Flow

**Last updated:** 2026-05-12

---

## Status Note

- This document describes the **target architecture** defined by `SPEC-01` to `SPEC-04`.
- It is not a guarantee that all components are already implemented in the current repository state.
- For implementation disputes, the spec files take precedence.

---

## 1. System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        AFFILIATE INTELLIGENCE                         │
│                                                                      │
│  ┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐  │
│  │  keywords.db│────►│  SPEC-01         │────►│  apps/web/content/│  │
│  │  (SQLite)   │     │  Content Bot     │     │  *.mdx articles  │  │
│  └──────┬──────┘     │  (Python)        │     └────────┬─────────┘  │
│         │            └──────────────────┘              │            │
│         │                       │                      │            │
│         │                  Quality Gate                 ▼            │
│         │                  (PASS/FAIL)          ┌──────────────────┐│
│         │                       │               │  SPEC-02         ││
│         │                       ▼               │  Next.js Site    ││
│         │              FAIL → status=failed     │  (App Router)    ││
│         │                              │        └────────┬─────────┘│
│         │                              │                 │          │
│         │                              │          Vercel Deploy     │
│         │                              │                 │          │
│         │                              ▼                 ▼          │
│         │                     [Public Website]                     │
│         │                              │                            │
│         │                    ┌─────────┼─────────┐                 │
│         │                    │                   │                  │
│         │              ┌─────▼─────┐    ┌───────▼──────┐          │
│         │              │  AdSense  │    │  Affiliate   │          │
│         │              │  (display)│    │  CTAs        │          │
│         │              └─────┬─────┘    └───────┬──────┘          │
│         │                    │                   │                  │
│         │                    └───────┬──────────┘                 │
│         │                            │                            │
│         │                     SPEC-03 Monetisation                │
│         │                            │                            │
│         │              ┌─────────────▼─────────────┐              │
│         │              │  GSC Feedback Loop (weekly)│              │
│         │              │  gsc_feedback.py           │              │
│         │              └─────────────┬─────────────┘              │
│         │                            │                            │
│         │         Low CTR → needs_rewrite ◄── back to SPEC-01    │
│         │                                                         │
│         │    (Phase 4)                                            │
│         │  ┌──────────────────────────────────┐                   │
│         │  │  SPEC-04 Video Pipeline          │                   │
│         │  │  Article → Script → AI Video     │                   │
│         │  │  → YouTube → embed back          │                   │
│         │  └──────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow — Step by Step

### 2.1 Content Generation (SPEC-01)

```
1. keyword_manager.py
   → SELECT from keywords.db WHERE status='pending' AND volume>100 AND difficulty<45
   → ORDER BY volume/(difficulty+1) DESC LIMIT N

2. research_agent.py
   → Firecrawl: scrape top-5 SERP results
   → Perplexity API: extract facts, pricing, complaints
   → Output: research_bundle dict

3. generation_agent.py
   → generate_outline(research_bundle)  → gpt-4o-mini
   → validate against outline_schema.json
   → write_sections(outline)            → claude-3-5-haiku (3 concurrent)

4. quality_gate.py
   → Check: word count, uniqueness, banned phrases, keyword in H1, FAQ count
   → FAIL → status='failed', log reason, skip article
   → WARN → log, continue
   → PASS → proceed

5. mdx_writer.py
   → Write apps/web/content/{category}/{slug}.mdx
   → Write apps/web/content/faq/{slug}.faq.json
   → Write monetisation/affiliate_map/{slug}.json (if new CTA needed)
   → UPDATE keywords.db: status='published', published_at=today

6. Deploy Trigger
   → POST to VERCEL_DEPLOY_HOOK_URL
```

### 2.2 Web Publishing (SPEC-02)

```
1. Vercel Build
   → next build reads apps/web/content/*.mdx
   → generateStaticParams() creates static pages per category/slug
   → cta_injector.ts reads affiliate_map/{slug}.json → injects <AffiliateCTA>
   → schema_builder.ts generates JSON-LD (Article, FAQPage, BreadcrumbList)

2. Public Site
   → Static HTML served via Vercel CDN
   → GA4 tracks pageviews, CTA clicks (via UTM params)
   → AdSense auto-ads on informational pages

3. GSC Feedback Loop (weekly cron)
   → gsc_feedback.py: query GSC API for last 7 days
   → UPDATE keywords.db: gsc_impressions, gsc_clicks, gsc_ctr, gsc_position
   → IF impressions>200 AND ctr<0.01 → SET status='needs_rewrite'
   → needs_rewrite rows re-enter SPEC-01 pipeline (rewrite mode)
```

### 2.3 Monetisation (SPEC-03)

```
1. AdSense
   → Auto-ads injected on informational pages
   → Sidebar + in-article units on tutorial pages
   → Suppressed above fold on comparison pages (affiliate priority)

2. Affiliate CTAs
   → affiliate_map/{slug}.json defines: primary_cta, secondary_cta, bottom_cta
   → Placements: top (after H1), inline (after H2 #3), bottom (before FAQ)
   → All links: rel="sponsored" + disclosure text
   → A/B variants rotated weekly by cta_rotator.py

3. Revenue Logging
   → Monthly manual update to revenue_log.csv
   → Tracked per partner per month
```

### 2.4 Video Pipeline (SPEC-04, Phase 4)

```
1. Article Selector
   → keywords.db WHERE status='published' AND gsc_impressions>500/week
   → AND intent IN ('comparison','tutorial')

2. Script Extractor
   → Read .mdx → extract key facts, pricing, top-3 tools
   → LLM: 60-second HOOK→VALUE→PROOF→CTA script

3. AI Video Generator
   → Creatomate (start) / HeyGen (scale)
   → Output: vertical .mp4 (1080×1920, <60s)

4. YouTube Upload
   → YouTube Data API v3
   → Title, description (with affiliate links), tags

5. Cross-embed
   → UPDATE keywords.db: youtube_url, video_status='published'
   → Next Vercel build → <YouTubeEmbed> in article page
```

---

## 3. External Service Dependencies

| Service | Purpose | Spec | Cost |
|---|---|---|---|
| OpenAI API | Outline + QA | SPEC-01 | ~$0.003/article |
| Anthropic API | Section writing | SPEC-01 | ~$0.018/article |
| Perplexity API | Real-time research | SPEC-01 | ~$0.003/article |
| Firecrawl | SERP scraping | SPEC-01 | Free tier / $0.001 |
| Vercel | Hosting + CDN | SPEC-02 | Free tier |
| Google AdSense | Display ads | SPEC-03 | Revenue share |
| GA4 + GSC | Analytics | SPEC-02 | Free |
| Creatomate | Video gen | SPEC-04 | ~$0.03-0.05/render |
| HeyGen | Video gen (scale) | SPEC-04 | ~$0.10-0.20/min |
| YouTube | Video hosting | SPEC-04 | Free |

---

## 4. Key Architectural Decisions

| Decision | Rationale |
|---|---|
| SQLite for keyword DB | Single-writer (bot), zero ops, portable |
| MDX for articles | Bot-writable, version-controlled, Next.js native |
| Static generation (SSG) | Fastest Core Web Vitals, no server needed |
| Python for bot, TypeScript for web | Best ecosystem per domain |
| Vercel free tier | Zero cost until traffic justifies upgrade |
| Dark mode default | Target audience (developers) preference |
| Quality gate before publish | Prevents thin/low-quality content from reaching site |

---

## 5. Failure Modes & Recovery

| Failure | Detection | Recovery |
|---|---|---|
| LLM API down | HTTP 5xx / timeout | Retry 3x with backoff; fallback model per SPEC-01 §10 |
| Quality gate FAIL | Automated check | Set status='failed', log reason, continue next article |
| Vercel deploy fail | Deploy hook returns non-200 | Log error, retry once after 60s |
| GSC API quota exceeded | 403 response | Skip feedback loop, retry next week |
| Duplicate content detected | Cosine similarity > 0.85 | Skip article, mark status='failed' |
| Affiliate link broken | Manual audit / 404 check | Update affiliate_map, trigger rebuild |
