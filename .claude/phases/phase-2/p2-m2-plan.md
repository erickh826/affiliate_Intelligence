# Phase 2 Milestone 2 — Plan

**Status:** READY FOR EXECUTION  
**Spec:** `docs/SPEC-02-web-system.md` §3–§5, §8  
**Depends on:** M1 — COMPLETED (`/[category]/[slug]` MDX article page landed)

**Executor prompt:** [p2-m2-executor-prompt.md](./p2-m2-executor-prompt.md)  
**Review:** *TBD: `p2-m2-review-prompt.md` after M2 implementation*

---

## Pre-execution Review Notes (2026-06-14)

> These notes were added after a plan review. The executor prompt has been updated to address all items below.
> This plan now incorporates those fixes. If the executor prompt drifts from this file later, update the prompt.

### Critical fixes applied to executor prompt

**Inline CTA — concrete implementation required**  
`MDXRemote` (RSC mode) compiles the full MDX tree at once — you cannot inject React nodes into a compiled tree after the fact. The solution is to split the raw content string at `## ` boundaries *before* compilation in `getMDXDataBySlug`, producing `contentParts: string[]`. The article page then renders each part as a separate `<MDXRemote>` call with `<AffiliateCTA placement="inline">` inserted between part[2] and part[3]. This is the only reliable approach without a remark plugin.

**`generateStaticParams` required on `app/[category]/page.tsx`**  
Without it, Next.js treats category index pages as dynamic routes and does not pre-render them at build time. `npm run build` may appear to pass but Vercel will serve them as server-rendered pages (breaking the SSG requirement).

**Empty `links: {}` in affiliate map**  
The existing fixture `monetisation/affiliate_map/best-ai-writing-tools-2026.json` has `links: {}`. `AffiliateCTA` must not render a bare `href="undefined"`. Resolution order: (1) `links[primary_partner]` if non-empty, (2) `lib/affiliate-links.ts` static map, (3) newsletter fallback.

### Spec alignment fixes applied

**Trailing slash on all canonical URLs**  
SPEC-02 §4.1 specifies `https://{domain}/{category}/{slug}/` with trailing slash. All JSON-LD URLs in `schema_builder.ts` and `buildBreadcrumbSchema` must follow this format. `generateMetadata` canonical should also include the slash.

**`getAllArticles()` sort responsibility**  
Sorting by `published_at` desc happens in each page component, not inside `getAllArticles()`. `getAllArticles()` remains unsorted (consumers may need different orderings).

### Minor clarifications applied

- `getHeadings()` lives in `lib/mdx.ts` and is exported; `TableOfContents` receives `headings` as a prop — no extraction logic in the component.
- Homepage: no hero component — H1 tagline + subtitle as plain text only.
- `lib/affiliate-links.ts` static map codified as the fallback layer between `links: {}` and newsletter CTA.

---

## Objective

Turn the single-article renderer into a **publishable site shell**: dynamic homepage, category indexes, affiliate CTA injection, JSON-LD schema, and shared layout components — still **without** full E-E-A-T static pages (M3).

---

## In scope (M2)

| Task | Deliverable | Acceptance |
|------|-------------|------------|
| **T2.2 (full)** | `app/page.tsx` | Lists latest articles from `getAllArticles()`, category cards, links to `/[category]/[slug]` — no hardcoded slug |
| **T2.5** | `app/[category]/page.tsx` | Article cards sorted by `published_at` desc; page-based pagination if >12; `rel="next"/"prev"` when paginated |
| **T2.6** | `lib/cta_injector.ts` | Read `monetisation/affiliate_map/{slug}.json` at build time; inject `<AffiliateCTA>` at top / inline (after ~3rd H2) / bottom (before FAQ) |
| **T2.7** | `lib/schema_builder.ts` | Article + FAQPage + BreadcrumbList JSON-LD; inject in article page `<head>` |
| **T2.8** | `components/` | `AffiliateCTA`, `Breadcrumb`, `ArticleCard`, `TableOfContents` (static from headings), `YouTubeEmbed` stub (render if `youtube_url` prop passed — DB wiring optional) |

---

## Out of scope (defer to M3)

- `/about`, `/contact`, `/privacy-policy`, `/disclaimer`
- `next-sitemap`, `robots.ts`, `@vercel/og` image generation
- `apps/bot/gsc_feedback.py` stub
- Full Vitest coverage for CTA/schema (add at least smoke tests in M2; expand in M3)

---

## Design decisions

### 1. Affiliate map path

Read from repo root at build time:

```
monetisation/affiliate_map/{slug}.json
```

Resolve via `path.join(process.cwd(), '..', '..', 'monetisation', 'affiliate_map', ...)` from `apps/web`, or a shared `getProjectRoot()` helper. Document the chosen path in handoff.

Shape matches bot output + `AffiliateMap` in `apps/bot/models.py`:

```json
{
  "slug": "...",
  "primary_partner": "jasper",
  "cta_variant": "A",
  "links": {}
}
```

CTA URLs come from SPEC-03 affiliate config later; M2 may use placeholder `links` or a minimal `lib/affiliate-links.ts` map for known partners.
URL resolution order:

1. `links[primary_partner]` when present and non-empty
2. `lib/affiliate-links.ts` static map for known partners
3. Newsletter fallback CTA when no partner URL is available

### 2. CTA placement (SPEC-02 §4.2)

| Placement | Rule |
|-----------|------|
| `top` | After page header, before MDX body |
| `inline` | After the 3rd `##` section by rendering `contentParts` and inserting CTA between `contentParts[2]` and `contentParts[3]` |
| `bottom` | Before FAQ block |

Fallback when no map file: newsletter CTA component (static mailto or `#` placeholder).

All outbound links: `rel="sponsored noopener noreferrer"` + disclosure string from SPEC-02.

Implementation constraint:

- Do not try to inject React nodes into an already-compiled `MDXRemote` tree.
- Split raw MDX content at `## ` boundaries in `getMDXDataBySlug`, return `contentParts: string[]`, and render each part with separate `<MDXRemote>` calls.
- Insert the inline CTA between `contentParts[2]` and `contentParts[3]` when a third H2 exists; omit the inline CTA otherwise.

### 3. Schema (T2.7)

Inject in `app/[category]/[slug]/page.tsx` or a small `ArticleJsonLd` server component:

- `buildArticleSchema(frontmatter, siteUrl)`
- `buildFaqSchema(faqData)` when FAQ exists
- `buildBreadcrumbSchema(category, slug, title, siteUrl)`

Use `NEXT_PUBLIC_SITE_URL` with fallback `http://localhost:3000` for dev.
All canonical and JSON-LD URLs must end with a trailing slash, matching SPEC-02 §4.1.

### 4. Homepage + category index data source

Both use `getAllArticles()` from `lib/mdx.ts` — no duplicate filesystem scans.

Category list: unique `frontmatter.category` values.
`getAllArticles()` remains unsorted; each page sorts its own view as needed.

### 5. Article page enhancements (M2 delta on M1)

- Replace inline breadcrumb nav with `<Breadcrumb />` component
- Add `<TableOfContents />` from heading parse exported by `lib/mdx.ts`
- Wire CTA injector + JSON-LD
- Sidebar layout: prose + TOC/CTA column per SPEC-02 §3 (simplified grid OK)
- Top and bottom CTA render even when affiliate links fall back to newsletter; inline CTA only renders when a valid affiliate map exists and at least three H2 sections are present.

---

## Implementation order

| Step | Work |
|------|------|
| A | **Shared components:** `Breadcrumb`, `ArticleCard`, `AffiliateCTA`, `TableOfContents`, `YouTubeEmbed` (stub) |
| B | **`lib/schema_builder.ts`** + unit tests |
| C | **`lib/cta_injector.ts`** + read affiliate map; unit tests with fixture JSON |
| D | **`lib/mdx.ts` refactor:** export `getHeadings()`, add `contentParts`, keep full `content` intact |
| E | **Article page refactor:** sidebar layout, CTAs, JSON-LD, TOC |
| F | **`app/[category]/page.tsx`** category index with `generateStaticParams` |
| G | **`app/page.tsx`** dynamic homepage from `getAllArticles()` |
| H | **Vitest:** schema_builder, cta_injector smoke tests |
| I | **`npm run build`** + update `execution-log.md` → M2 NEEDS REVIEW |

---

## Verification

```bash
cd apps/web
npm install
npm run test
npm run build
npm run dev
```

Manual checks:

- `/` lists sample article card
- `/ai-writing` lists articles in category
- `/ai-writing/best-ai-writing-tools-2026` shows CTAs (if affiliate map exists), JSON-LD in page source, TOC links
- `/ai-writing` is statically generated via `generateStaticParams`

Affiliate map fixture: `monetisation/affiliate_map/best-ai-writing-tools-2026.json` (create if missing from bot dry-run).

---

## Risks

| Risk | Mitigation |
|------|------------|
| CTA inline insertion with MDXRemote | Split content by `##` in loader before compilation; do not mutate compiled trees |
| Monorepo path to affiliate_map | Single `getAffiliateMapPath(slug)` helper + test |
| Category route 404 from M1 breadcrumb | Implement T2.5 before calling M2 done |

---

## M2 Definition of Done

- [ ] Homepage and category index driven by `getAllArticles()`
- [ ] Article page has 3 CTA placements + fallback
- [ ] JSON-LD Article + FAQ + Breadcrumb present on article page
- [ ] Shared components extracted; no `any` in new code
- [ ] Vitest covers schema + CTA helpers
- [ ] `npm run build` passes
- [ ] execution-log M2 → NEEDS REVIEW (not COMPLETED until review)
