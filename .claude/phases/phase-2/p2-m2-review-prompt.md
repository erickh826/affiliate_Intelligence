# Phase 2 M2 — Review Prompt

**Use when:** M2 is marked **NEEDS REVIEW** in `execution-log.md`.  
**Plan:** [p2-m2-plan.md](./p2-m2-plan.md) · **Spec:** `docs/SPEC-02-web-system.md` §3–§5, §8  
**Execution log:** [execution-log.md](./execution-log.md)

Copy everything inside the fenced block below into the review agent.

---

```markdown
# Review Task: Phase 2 M2 — Homepage, Category, CTA, Schema (Affiliate Intelligence)

You are a **code reviewer**. M2 has been implemented and is at status NEEDS REVIEW.
Your job is to verify it against the plan and spec — not implement anything.

Read first (in order):
1. `.claude/phases/phase-2/p2-m2-plan.md` — canonical scope + design decisions
2. `.claude/phases/phase-2/execution-log.md` — what was built, deviations noted
3. `docs/SPEC-02-web-system.md` §3–§5, §8 — authoritative requirements

---

## Files to review

### New files (M2)
- `apps/web/components/Breadcrumb.tsx`
- `apps/web/components/ArticleCard.tsx`
- `apps/web/components/AffiliateCTA.tsx`
- `apps/web/components/TableOfContents.tsx`
- `apps/web/components/YouTubeEmbed.tsx`
- `apps/web/components/NewsletterCTA.tsx`
- `apps/web/lib/schema_builder.ts`
- `apps/web/lib/affiliate-links.ts`
- `apps/web/lib/cta_injector.ts`
- `apps/web/app/[category]/page.tsx`
- `apps/web/__tests__/schema_builder.test.ts`
- `apps/web/__tests__/cta_injector.test.ts`
- `apps/web/__tests__/fixtures/affiliate-map-with-links.json`
- `apps/web/__tests__/fixtures/affiliate-map-empty-links.json`

### Modified files (M2 delta)
- `apps/web/lib/mdx.ts` — `getHeadings()`, `contentParts`, `headings` added
- `apps/web/app/[category]/[slug]/page.tsx` — sidebar layout, 3 CTAs, JSON-LD, TOC
- `apps/web/app/page.tsx` — dynamic from `getAllArticles()`

---

## Checklist

### A. CTA injection (T2.6) — highest risk

- [ ] `lib/cta_injector.ts` reads `monetisation/affiliate_map/{slug}.json` at build time via a path helper (not hardcoded absolute path)
- [ ] URL resolution order: `links[primary_partner]` → `lib/affiliate-links.ts` static map → newsletter fallback. Never renders `href="undefined"` or empty `href`
- [ ] `AffiliateCTA` on all outbound links: `rel="sponsored noopener noreferrer"` + visible disclosure text
- [ ] **Inline CTA uses `contentParts`**: raw MDX content is split at `## ` boundaries in `lib/mdx.ts` (or `getMDXDataBySlug`), and the article page renders separate `<MDXRemote>` calls with the inline CTA inserted between `contentParts[2]` and `contentParts[3]`. Inline CTA is **omitted** when fewer than 3 H2 sections exist
- [ ] Top CTA: rendered after page header, before MDX body
- [ ] Bottom CTA: rendered before FAQ block
- [ ] Newsletter fallback renders when no affiliate map file exists

### B. Schema builder (T2.7)

- [ ] `buildArticleSchema` emits valid JSON-LD with `@type: "Article"` (or `"TechArticle"`)
- [ ] `buildFaqSchema` emits `@type: "FAQPage"` with `mainEntity` array
- [ ] `buildBreadcrumbSchema` emits `@type: "BreadcrumbList"`
- [ ] **All URLs in JSON-LD end with a trailing slash** (`https://domain/category/slug/`) per SPEC-02 §4.1
- [ ] JSON-LD injected via `<script type="application/ld+json">` in article page `<head>` (not inline in body)
- [ ] `NEXT_PUBLIC_SITE_URL` used with `http://localhost:3000` fallback

### C. Homepage + category index (T2.2, T2.5)

- [ ] `app/page.tsx`: zero hardcoded article slugs; all data from `getAllArticles()`
- [ ] `app/[category]/page.tsx`: `generateStaticParams` present (required for SSG)
- [ ] Articles sorted by `published_at` desc in each page (not inside `getAllArticles()`)
- [ ] Category list derived from unique `frontmatter.category` values

### D. Shared components (T2.8)

- [ ] `Breadcrumb.tsx`: renders Home > Category > Title; all segments are links except the last
- [ ] `ArticleCard.tsx`: shows title, description, date, category badge; title links to article
- [ ] `TableOfContents.tsx`: receives `headings` as prop (no extraction logic inside component); renders anchor links
- [ ] `YouTubeEmbed.tsx`: renders iframe when `url` prop present; renders nothing when absent
- [ ] No `any` types in any component

### E. `lib/mdx.ts` changes

- [ ] `getHeadings(content: string)` exported and returns `{ id, text, level }[]`
- [ ] `contentParts: string[]` present in `MDXData` (split at `## `)
- [ ] Full `content` still available (backwards-compatible with M1 tests)
- [ ] `SKIP_CONTENT_DIRS` still excludes `faq/` (M1 behaviour preserved)

### F. TypeScript correctness

- [ ] No `any` in new or modified files
- [ ] Strict mode: no implicit `any`, no missing return types on exported functions
- [ ] `"use client"` present on components that use state/effects; absent on Server Components

### G. Tests (T2.12)

- [ ] `schema_builder.test.ts`: covers `buildArticleSchema`, `buildFaqSchema`, `buildBreadcrumbSchema`; verifies trailing slash in URLs
- [ ] `cta_injector.test.ts`: covers (1) affiliate map with links, (2) affiliate map with empty `links`, (3) no map file, (4) <3 H2s → no inline CTA
- [ ] `npm run test` passes — report the count

### H. Build

- [ ] `npm run build` passes with no errors
- [ ] All routes SSG: `/` ○, `/[category]` ●, `/[category]/[slug]` ●

---

## Known accepted deviations (do not block on these)

- Pagination with `searchParams` deferred — Next.js 16 forces dynamic rendering; category page is hardcoded to `page=1` until article count exceeds 12. Acceptable for M2.
- `npm run lint` (`next lint`) CLI path issue (Next 16 bug) — deferred to M3 ESLint config fix.

---

## Verdict

Output one of:

**APPROVE** — all P1 items pass; deviations limited to accepted list above.

**APPROVE WITH NOTES** — minor issues; list each one; no blocking defects.

**BLOCK** — list each blocking issue with:
  - File + line number
  - What the spec/plan requires
  - What was found instead

If BLOCK, do NOT fix the code — report only. The implementer will address findings before re-review.

---

## After review

Update `.claude/phases/phase-2/execution-log.md`:
- If APPROVE / APPROVE WITH NOTES: change M2 status to **COMPLETED**, add reviewer notes
- If BLOCK: leave NEEDS REVIEW, add blocking issues under "Issues Encountered"
```
