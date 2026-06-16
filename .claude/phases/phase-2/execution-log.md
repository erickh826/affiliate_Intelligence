# Phase 2 — Execution Log

**Started:** 2026-06-05
**Completed:** —
**Status:** M1 COMPLETED · M2 COMPLETED · M3 NEEDS REVIEW

**M1 prompts:** [executor](./p2-m1-claude-executor-prompt.md) · [review](./p2-m1-review-prompt.md) · [roadmap](./p2-roadmap.md)  
**M2 prompts:** [plan](./p2-m2-plan.md) · [executor](./p2-m2-executor-prompt.md) · [review](./p2-m2-review-prompt.md)
**M3 prompts:** [plan](./p2-m3-plan.md) · [executor](./p2-m3-executor-prompt.md)

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
| 7 | 2026-06-14 | `npm run test` (M2 blocker recheck) | PASS (31) | 213ms |
| 8 | 2026-06-14 | `npm run build` (M2 blocker recheck) | PASS | ~5s |
| 9 | 2026-06-16 | `npm install` | PASS | ~50s |
| 10 | 2026-06-16 | `npm run test` (M3) | PASS (35) | ~0.5s |
| 11 | 2026-06-16 | `npm run build` (M3) | PASS | ~5s |
| 12 | 2026-06-16 | `npm run lint` (M3) | PASS | <1s |
| 13 | 2026-06-16 | `npx prettier --check .` | PASS | <1s |
| 14 | 2026-06-16 | `python -m ruff check apps/bot/` | PASS | — |

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
- **Status:** COMPLETED
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
- **Status:** COMPLETED
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** `app/[category]/page.tsx` with `generateStaticParams`, sorted by `published_at` desc. Pagination deferred: `searchParams` forces dynamic rendering in Next.js 16; hardcoded `page=1` for now, adds pagination when >12 articles.

### T2.6 — CTA injection
- **Status:** COMPLETED
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** `lib/cta_injector.ts` + `lib/affiliate-links.ts`. 3-layer URL resolution: `links[primary_partner]` → `AFFILIATE_LINKS` static map → newsletter fallback. Inline CTA uses `contentParts` split in `lib/mdx.ts`.

### T2.7 — Schema builder
- **Status:** COMPLETED
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** `lib/schema_builder.ts` with `buildArticleSchema`, `buildFaqSchema`, `buildBreadcrumbSchema`. All URLs include trailing slash per SPEC-02 §4.1. JSON-LD injected via `<script type="application/ld+json">` in article page.

### T2.8 — Shared components
- **Status:** COMPLETED
- **Started:** 2026-06-14
- **Completed:** 2026-06-14
- **Notes:** Created `Breadcrumb`, `ArticleCard`, `AffiliateCTA` (3 placement styles), `TableOfContents` (prop-driven, headings from `lib/mdx.ts`), `YouTubeEmbed` (stub), `NewsletterCTA` (fallback).

### T2.9 — Static pages
- **Status:** COMPLETED
- **Started:** 2026-06-16
- **Completed:** 2026-06-16
- **Notes:** Added `/about`, `/contact`, `/privacy-policy`, and `/disclaimer` as static Server Component pages with metadata. `/about` includes author identity and LinkedIn placeholder; `/contact` uses Formspree env with `#` fallback; privacy/disclaimer pages are date-stamped.

### T2.10 — SEO setup
- **Status:** COMPLETED
- **Started:** 2026-06-16
- **Completed:** 2026-06-16
- **Notes:** Removed unsupported `app/[category]/[slug]/head.tsx`; moved JSON-LD scripts into article `page.tsx`. Added `metadataBase`, canonical metadata, `next-sitemap.config.js`, `postbuild` sitemap generation, and static `public/og-default.svg` placeholder. `npm run build` generates `sitemap.xml`, `sitemap-0.xml`, and `robots.txt`.

### T2.11 — GSC feedback stub
- **Status:** COMPLETED
- **Started:** 2026-06-16
- **Completed:** 2026-06-16
- **Notes:** Added `apps/bot/gsc_feedback.py` Phase 4 stub and documented manual Search Console verification / sitemap submission steps in `apps/bot/README.md`.

### T2.12 — Tests
- **Status:** COMPLETED
- **Started:** 2026-05-31
- **Completed:** 2026-06-16
- **Notes:** M3: added `__tests__/static-pages.test.ts` and kept MDX/schema/CTA tests green after SEO/theme/static page changes. Total: 35 tests passing.

### M3 — E-E-A-T, SEO, tooling, and deployment scaffolding
- **Status:** NEEDS REVIEW
- **Started:** 2026-06-16
- **Completed:** —
- **Notes:** Implemented static pages, byline link to `/about`, sticky disclaimer on comparison articles, theme toggle, sitemap/robots generation, bot GSC stub, and GitHub workflow scaffolding (`ci.yml`, `bot-cron.yml`). Verification passed: `npm run test`, `npm run build`, `npm run lint`, `npx prettier --check .`, `python -m ruff check apps/bot/`.

---

## Issues Encountered

| # | Task | Issue | Resolution | Time Lost |
|---|---|---|---|---|
| 1 | T2.4 | `params` in Next.js 16 is a Promise. | Wrapped `params` in `await`. | 5m |
| 2 | T2.4 | Duplicate H1 and FAQ headings from MDX. | Used custom MDX components to suppress headings. | 10m |
| 3 | T2.6 | Inline CTA guard was `contentParts[2]` (truthy for 2+ H2s). Requirement: omit inline CTA when <3 H2 sections. | **RESOLVED 2026-06-14:** replaced guard with `contentParts.slice(2).map((part, i, arr) => ... i === 0 && arr.length > 1 && ctaConfig)` — CTA only renders when `arr.length > 1` i.e. 3+ H2 sections exist. | — |
| 4 | T2.7 / M3 | JSON-LD scripts were moved into unsupported `app/[category]/[slug]/head.tsx`. | **RESOLVED 2026-06-16:** deleted `head.tsx` and injected JSON-LD directly from article `page.tsx`. | — |
| 5 | T2.12 | Missing test: `<3 H2s => no inline CTA`. | **RESOLVED 2026-06-14:** exported `splitAtH2` from `lib/mdx.ts`; added `splitAtH2` describe block to `mdx.test.ts` with explicit tests: 2 H2s → `slice(2).length === 1` (CTA suppressed); 3 H2s → `slice(2).length > 1` (CTA renders); sample article confirms ≥3 H2s. Total tests: 31 passed. | — |
| 6 | M3 tooling | `next/font/google` blocked production build because external Google Fonts could not be fetched in the current environment. | Switched to local/system font stacks in `globals.css`; build now passes without network font fetch. | — |
| 7 | M3 tooling | ESLint 9 ignored `.eslintrc.json` and initially linted `.next/` build artifacts. | Replaced with `apps/web/eslint.config.mjs` flat config and ignored `.next/`, `node_modules/`, `public/`. | — |

---

## Final Results

- **M1:** COMPLETED
- **M2:** COMPLETED
- **M3:** NEEDS REVIEW
- **Build result:** PASS — routes: `/`, `/about`, `/contact`, `/privacy-policy`, `/disclaimer`, `/[category]`, `/[category]/[slug]`
- **Test results:** 35 passed (14 mdx + 10 schema_builder + 7 cta_injector + 4 static-pages)
- **Lint results:** PASS (`npm run lint`)
- **Formatting results:** PASS (`npx prettier --check .`)
- **Bot lint results:** PASS (`python -m ruff check apps/bot/`)

### M3 files changed
- **New:** `apps/web/app/about/page.tsx`, `contact/page.tsx`, `privacy-policy/page.tsx`, `disclaimer/page.tsx`
- **New:** `apps/web/components/ThemeToggle.tsx`
- **New:** `apps/web/public/og-default.svg`
- **New:** `apps/web/next-sitemap.config.js`, `apps/web/eslint.config.mjs`, `apps/web/.prettierrc`
- **New:** `apps/web/__tests__/static-pages.test.ts`
- **New:** `apps/bot/gsc_feedback.py`
- **New:** `.github/workflows/ci.yml`, `.github/workflows/bot-cron.yml`
- **Modified:** `apps/web/app/[category]/[slug]/page.tsx` — JSON-LD moved into page, author links to `/about`, sticky comparison disclaimer
- **Modified:** `apps/web/app/layout.tsx` — `metadataBase`, OG fallback, nav/footer links, theme toggle mount
- **Modified:** `apps/web/app/page.tsx`, `apps/web/app/[category]/page.tsx` — canonical metadata
- **Modified:** `apps/web/app/globals.css`, `components/ArticleCard.tsx` — theme variables, `content-visibility`, system font stacks
- **Modified:** `apps/web/package.json`, `apps/web/package-lock.json` — `next-sitemap`, ESLint, Prettier scripts/deps
- **Modified:** `apps/bot/README.md` — Search Console setup note

### M2 files changed
- **New:** `apps/web/components/` — `Breadcrumb.tsx`, `ArticleCard.tsx`, `AffiliateCTA.tsx`, `TableOfContents.tsx`, `YouTubeEmbed.tsx`, `NewsletterCTA.tsx`
- **New:** `apps/web/lib/schema_builder.ts`, `apps/web/lib/affiliate-links.ts`, `apps/web/lib/cta_injector.ts`
- **Modified:** `apps/web/lib/mdx.ts` — added `Heading` type, `contentParts`, `headings` to `MDXData`; exported `getHeadings()`; internal `splitAtH2()`
- **Modified:** `apps/web/app/[category]/[slug]/page.tsx` — sidebar layout, 3 CTA placements, `<Breadcrumb>`, `<TableOfContents>`
- **New:** `apps/web/app/[category]/page.tsx` — category index with `generateStaticParams`, sorted articles
- **Modified:** `apps/web/app/page.tsx` — dynamic homepage from `getAllArticles()`
- **New:** `apps/web/__tests__/schema_builder.test.ts`, `apps/web/__tests__/cta_injector.test.ts`
- **New:** `apps/web/__tests__/fixtures/affiliate-map-with-links.json`, `affiliate-map-empty-links.json`

### M2 known deviations
- Pagination with `searchParams` deferred: Next.js 16 forces dynamic rendering when `searchParams` is used as a page param; category page hardcoded to `page=1` until article count exceeds 12.

- **Next step:** M3 review
