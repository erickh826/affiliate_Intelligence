# Phase 2 — Execution Log

**Started:** 2026-06-05
**Completed:** —
**Status:** M1 COMPLETED · M2 NEEDS REVIEW

**M1 prompts:** [executor](./p2-m1-claude-executor-prompt.md) · [review](./p2-m1-review-prompt.md) · [roadmap](./p2-roadmap.md)  
**M2 prompts:** [plan](./p2-m2-plan.md) · [executor](./p2-m2-executor-prompt.md) · [review](./p2-m2-review-prompt.md)

---

## Run Summary

| Run # | Date | Command | Result | Duration |
|---|---|---|---|---|
| 1 | 2026-06-05 | `npm run build` | PASS | 10s |
| 2 | 2026-06-05 | `npm run dev` | PASS | — |
| 3 | 2026-05-31 | `npm run test` | PASS (4) | — |
| 4 | 2026-05-31 | `npm run build` (post M1 P1 fixes) | PASS | ~5s |
| 5 | 2026-06-14 | `npm run test` (M2) | PASS (21) | 260ms |
| 6 | 2026-06-14 | `npm run build` (M2) | PASS | ~5s |
| — | — | `npx eslint web/` | — | — |

---

## Task Execution

### M1 — MDX + article page (T2.1 partial, T2.3, T2.4)
- **Status:** COMPLETED
- **Started:** 2026-06-05
- **Completed:** 2026-05-31
- **Notes:** Gemini initial implementation; P1 gaps closed 2026-05-31: `generateMetadata` on article page, Vitest `__tests__/mdx.test.ts` (4 tests), `getAllArticles` skips `content/faq/`, MDX components extracted to `lib/mdx-components.tsx` (no `any`). `npm run test` → 4 passed; `npm run build` → SSG `/ai-writing/best-ai-writing-tools-2026`. Review: APPROVE WITH NOTES → P1 items resolved.

### T2.1 — Next.js scaffold
- **Status:** COMPLETED (PARTIAL)
- **Started:** 2026-06-05
- **Completed:** 2026-06-05
- **Notes:** Installed dependencies (Tailwind v4, MDX remote, typography), set up design tokens and fonts.

### T2.2 — Layout + homepage
- **Status:** COMPLETED (NEEDS REVIEW)
- **Started:** 2026-06-05
- **Completed:** 2026-06-14
- **Notes:** M2: `app/page.tsx` fully dynamic from `getAllArticles()` — category cards + latest 6 articles sorted by `published_at` desc. No hardcoded links.

### T2.3 — MDX rendering pipeline
- **Status:** COMPLETED
- **Started:** 2026-06-05
- **Completed:** 2026-06-05
- **Notes:** Implemented `lib/mdx.ts` with frontmatter parsing and FAQ data fetching.

### T2.4 — Article page
- **Status:** COMPLETED
- **Started:** 2026-06-05
- **Completed:** 2026-06-05
- **Notes:** Implemented `[category]/[slug]/page.tsx` with breadcrumbs, byline, MDX render, and FAQ section.

### T2.5 — Category index
- **Status:** COMPLETED (NEEDS REVIEW)
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** `app/[category]/page.tsx` with `generateStaticParams`, sorted by `published_at` desc. Pagination deferred: `searchParams` forces dynamic rendering in Next.js 16; hardcoded `page=1` for now, adds pagination when >12 articles.

### T2.6 — CTA injection
- **Status:** COMPLETED (NEEDS REVIEW)
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** `lib/cta_injector.ts` + `lib/affiliate-links.ts`. 3-layer URL resolution: `links[primary_partner]` → `AFFILIATE_LINKS` static map → newsletter fallback. Inline CTA uses `contentParts` split in `lib/mdx.ts`.

### T2.7 — Schema builder
- **Status:** COMPLETED (NEEDS REVIEW)
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** `lib/schema_builder.ts` with `buildArticleSchema`, `buildFaqSchema`, `buildBreadcrumbSchema`. All URLs include trailing slash per SPEC-02 §4.1. JSON-LD injected via `<script type="application/ld+json">` in article page.

### T2.8 — Shared components
- **Status:** COMPLETED (NEEDS REVIEW)
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** Created `Breadcrumb`, `ArticleCard`, `AffiliateCTA` (3 placement styles), `TableOfContents` (prop-driven, headings from `lib/mdx.ts`), `YouTubeEmbed` (stub), `NewsletterCTA` (fallback).

### T2.9 — Static pages
- **Status:** NOT STARTED
- **Started:** —
- **Completed:** —
- **Notes:**

### T2.10 — SEO setup
- **Status:** NOT STARTED
- **Started:** —
- **Completed:** —
- **Notes:**

### T2.11 — GSC feedback stub
- **Status:** NOT STARTED
- **Started:** —
- **Completed:** —
- **Notes:**

### T2.12 — Tests
- **Status:** COMPLETED (NEEDS REVIEW)
- **Started:** 2026-05-31
- **Completed:** 2026-06-14
- **Notes:** M2: added `__tests__/schema_builder.test.ts` (10 tests), `__tests__/cta_injector.test.ts` (7 tests). Total: 21 tests passing.

---

## Issues Encountered

| # | Task | Issue | Resolution | Time Lost |
|---|---|---|---|---|
| 1 | T2.4 | `params` in Next.js 16 is a Promise. | Wrapped `params` in `await`. | 5m |
| 2 | T2.4 | Duplicate H1 and FAQ headings from MDX. | Used custom MDX components to suppress headings. | 10m |
| 3 | T2.6 | Inline CTA guard is incorrect: `apps/web/app/[category]/[slug]/page.tsx` inserts inline CTA when `contentParts[2]` exists (L132-L137), which can be true with only two H2 sections when intro content exists. M2 requires inline CTA omitted when fewer than 3 H2 sections. | **BLOCKING (review):** update inline insertion guard to require at least 3 H2 sections and re-review. | — |
| 4 | T2.7 | JSON-LD scripts are rendered in page body in `apps/web/app/[category]/[slug]/page.tsx` (L76-L89), not in `<head>` as required by M2 checklist/SPEC alignment note. | **BLOCKING (review):** move JSON-LD injection into head and re-review. | — |
| 5 | T2.12 | `apps/web/__tests__/cta_injector.test.ts` (L24-L67) does not cover the required `<3 H2s => no inline CTA` scenario from M2 review checklist. | **BLOCKING (review):** add missing test coverage and re-review. | — |

---

## Final Results

- **M1:** COMPLETED
- **M2:** NEEDS REVIEW
- **Build result:** PASS — all routes SSG: `/` ○, `/[category]` ●, `/[category]/[slug]` ●
- **Test results:** 21 passed (4 mdx loader + 10 schema_builder + 7 cta_injector)
- **Lint results:** `next lint` CLI issue deferred (Next 16)

### M2 files changed
- **New:** `apps/web/components/` — `Breadcrumb.tsx`, `ArticleCard.tsx`, `AffiliateCTA.tsx`, `TableOfContents.tsx`, `YouTubeEmbed.tsx`, `NewsletterCTA.tsx`
- **New:** `apps/web/lib/schema_builder.ts`, `apps/web/lib/affiliate-links.ts`, `apps/web/lib/cta_injector.ts`
- **Modified:** `apps/web/lib/mdx.ts` — added `Heading` type, `contentParts`, `headings` to `MDXData`; exported `getHeadings()`; internal `splitAtH2()`
- **Modified:** `apps/web/app/[category]/[slug]/page.tsx` — sidebar layout, 3 CTA placements, JSON-LD, `<Breadcrumb>`, `<TableOfContents>`
- **New:** `apps/web/app/[category]/page.tsx` — category index with `generateStaticParams`, sorted articles
- **Modified:** `apps/web/app/page.tsx` — dynamic homepage from `getAllArticles()`
- **New:** `apps/web/__tests__/schema_builder.test.ts`, `apps/web/__tests__/cta_injector.test.ts`
- **New:** `apps/web/__tests__/fixtures/affiliate-map-with-links.json`, `affiliate-map-empty-links.json`

### M2 known deviations
- Pagination with `searchParams` deferred: Next.js 16 forces dynamic rendering when `searchParams` is used as a page param; category page hardcoded to `page=1` until article count exceeds 12.

- **Next milestone:** M3 — see p2-m3-plan.md (TBD)
