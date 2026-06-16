# Phase 2 Plan — Web Publishing System (SPEC-02)

**Status:** IN PROGRESS (M1 and M2 completed; M3 needs review)  
**Spec:** `docs/SPEC-02-web-system.md`  
**Timeline:** Weeks 2–4  
**Depends on:** Phase 1 (MDX output from content bot)

**Implementation prompts:** [p2-roadmap.md](./p2-roadmap.md) · **M2:** [plan](./p2-m2-plan.md) · [executor](./p2-m2-executor-prompt.md) · **M3:** [plan](./p2-m3-plan.md)

**Contract dependency:** Phase 2 must treat `apps/bot/models.py` `ArticleArtifact` and `Frontmatter` as the handoff contract from Phase 1. The web MDX loader should align with the frontmatter fields emitted by `P1-T6`.

---

## Objective

Build the Next.js 14 website that renders bot-generated MDX articles, injects affiliate CTAs, implements SEO/structured data, and meets E-E-A-T requirements for AdSense eligibility.

---

## Deliverables

| # | Deliverable | File/Dir | Acceptance Criteria |
|---|---|---|---|
| 1 | Next.js project scaffold | `web/` | App Router, Tailwind v4, strict TypeScript |
| 2 | Layout + homepage | `web/app/layout.tsx`, `web/app/page.tsx` | Dark mode default, design tokens applied |
| 3 | MDX rendering pipeline | `web/lib/mdx.ts` | Reads from `web/content/`, generateStaticParams |
| 4 | Article page | `web/app/[category]/[slug]/page.tsx` | Full article layout: breadcrumb, TOC, CTAs, FAQ, video embed |
| 5 | Category index | `web/app/[category]/page.tsx` | Article cards, pagination |
| 6 | CTA injection | `web/lib/cta_injector.ts` | Reads affiliate_map JSON, 3 placements per SPEC-02 §4.2 |
| 7 | Schema builder | `web/lib/schema_builder.ts` | Article + FAQPage + BreadcrumbList JSON-LD |
| 8 | Shared components | `web/components/` | AffiliateCTA, YouTubeEmbed, TOC, Breadcrumb, ArticleCard |
| 9 | Static pages | `web/app/about/`, `contact/`, `privacy-policy/`, `disclaimer/` | E-E-A-T + AdSense requirements |
| 10 | SEO setup | `next-sitemap`, `robots.ts`, canonical, OG | sitemap.xml, robots.txt, meta per page |
| 11 | GSC setup script | `bot/gsc_feedback.py` (stub) | Verify domain, submit sitemap |
| 12 | Tests | `web/__tests__/` | CTA injection, schema builder, MDX render |

---

## Task Breakdown

### T2.1 — Next.js scaffold
- `npx create-next-app@14 web/ --typescript --tailwind --app --src-dir=no`
- Configure: strict TS, Prettier, ESLint (next/core-web-vitals)
- Design tokens in `tailwind.config.ts` (colors, fonts, spacing)
- `web/lib/fonts.ts`: Instrument Serif + Inter via `next/font`

### T2.2 — Layout + homepage
- `layout.tsx`: `<html>` dark class, GA4 script, AdSense placeholder, nav, footer
- `page.tsx`: hero section, category cards, latest articles grid
- Mobile-first responsive at 375px

### T2.3 — MDX rendering pipeline
- Install: `@next/mdx`, `next-mdx-remote` or `mdx-bundler`
- `lib/mdx.ts`: read `web/content/**/*.mdx`, parse frontmatter, render
- `generateStaticParams()`: enumerate all category/slug combos
- Type: `ArticleFrontmatter` interface matching SPEC-01 §8.1
- Align `ArticleFrontmatter` with Phase 1 `Frontmatter` contract in `apps/bot/models.py`.

### T2.4 — Article page `[category]/[slug]`
- Layout: breadcrumb, H1, byline + date, TOC sidebar, article body, CTAs, FAQ, related articles
- `max-width: 720px` prose, `1100px` layout
- Server Component (no `"use client"` unless needed for TOC toggle)

### T2.5 — Category index `[category]`
- Article cards sorted by `published_at` desc
- `rel="next"/"prev"` pagination

### T2.6 — CTA injection `lib/cta_injector.ts`
- Read `monetisation/affiliate_map/{slug}.json` at build time
- Inject `<AffiliateCTA>` at 3 positions: top, inline, bottom
- Fallback: newsletter CTA when no affiliate map exists
- All links: `rel="sponsored"` + disclosure text

### T2.7 — Schema builder `lib/schema_builder.ts`
- `buildArticleSchema(frontmatter)` → Article JSON-LD
- `buildFaqSchema(faqJson)` → FAQPage JSON-LD
- `buildBreadcrumbSchema(category, slug)` → BreadcrumbList JSON-LD
- Inject via `<script type="application/ld+json">` in `<head>`

### T2.8 — Shared components
- `AffiliateCTA.tsx`: button with disclosure, `rel="sponsored"`
- `YouTubeEmbed.tsx`: lazy-loaded iframe, 16:9 or 9:16
- `TableOfContents.tsx`: extracted from MDX headings
- `Breadcrumb.tsx`: Home > Category > Article
- `ArticleCard.tsx`: title, description, date, category badge

### T2.9 — Static pages (E-E-A-T)
- `/about/`: real name, LLM developer background, LinkedIn link
- `/contact/`: Formspree form
- `/privacy-policy/`: GDPR + AdSense + cookie disclosure
- `/disclaimer/`: affiliate disclosure, sticky banner on comparison pages

### T2.10 — SEO setup
- `next-sitemap` config → `sitemap.xml`, `robots.txt`
- Canonical URL on every page
- Open Graph: `og:title`, `og:description`, `og:image` via `@vercel/og`
- Core Web Vitals: `next/image`, `font-display: swap`, `content-visibility: auto`

### T2.11 — GSC feedback stub
- `bot/gsc_feedback.py`: stub with TODO for weekly cron implementation
- GSC verification: DNS TXT record instructions documented
- Sitemap submission flow documented

### T2.12 — Tests
- CTA injection: with/without affiliate map, 3 placements, fallback
- Schema builder: correct JSON-LD output for all 3 types
- MDX render: frontmatter parsed, article renders without error
- Page routes: all static pages return 200

---

## Dependencies

| Dependency | Version | Purpose |
|---|---|---|
| next | 14.x | Framework |
| react | 18.x | UI |
| tailwindcss | 4.x | Styling |
| @next/mdx | 14.x | MDX support |
| next-sitemap | >=4.0 | Sitemap generation |
| gray-matter | >=4.0 | Frontmatter parsing |
| vitest | >=1.0 | Testing |
| @testing-library/react | >=14.0 | Component testing |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MDX rendering perf with 100+ articles | Medium | Slow builds | Pagination in generateStaticParams, ISR for new articles |
| Tailwind v4 breaking changes | Low | Style issues | Pin version, test visually |
| AdSense rejection | Medium | Revenue delay | Ensure all E-E-A-T pages complete before applying |
| Core Web Vitals fail | Medium | SEO ranking impact | Test with Lighthouse CI, optimize images/fonts |
