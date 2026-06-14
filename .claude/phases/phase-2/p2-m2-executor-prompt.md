# Phase 2 Milestone 2 — Executor Prompt

**Use when:** M1 is **COMPLETED** in `execution-log.md`.  
**Plan:** [p2-m2-plan.md](./p2-m2-plan.md) · **Spec:** `docs/SPEC-02-web-system.md`

Copy everything inside the fenced block below into Gemini.

---

```markdown
# Task: Phase 2 Milestone 2 — Homepage, category, CTA, schema (Affiliate Intelligence)

Implement **Phase 2 M2** in `apps/web/`. M1 is done: MDX loader + article page exist.

Read first (in this order):
1. `.claude/phases/phase-2/p2-m2-plan.md` — canonical scope
2. `docs/SPEC-02-web-system.md` §3–§5
3. `apps/web/lib/mdx.ts` — understand existing `getAllArticles()`, `getMDXDataBySlug()`
4. `apps/web/app/[category]/[slug]/page.tsx` — M1 article page to refactor in Step D

## Goal

- `/` — dynamic homepage from `getAllArticles()` (no hardcoded article links)
- `/[category]` — category index with ArticleCard grid
- Article page — CTA injection (3 placements), JSON-LD, TOC sidebar, shared Breadcrumb component
- `npm run test` + `npm run build` pass

## Do NOT implement (M3)

- `/about`, `/contact`, `/privacy-policy`, `/disclaimer`
- next-sitemap / robots.ts / OG image generation
- gsc_feedback.py

## Hard rules

- TypeScript strict, no `any`, Tailwind only, Server Components default
- No code comments unless strictly necessary
- All outbound affiliate links: `rel="sponsored noopener noreferrer"`
- All canonical / JSON-LD URLs must end with a trailing slash: `/category/slug/`
  (SPEC-02 §4.1: canonical format is `https://{domain}/{category}/{slug}/`)
- Mark M2 **NEEDS REVIEW** in execution-log — not COMPLETED

---

## Step A — Shared components (`apps/web/components/`)

Create five files. No inline logic beyond rendering props.

### `Breadcrumb.tsx`
Props: `category: string, slug: string, title: string`  
Renders: Home > Category > Title  
Use `<a>` tags (not `<Link>`) only if you need absolute paths; `<Link>` preferred.

### `ArticleCard.tsx`
Props: `frontmatter: Frontmatter` (import type from `lib/mdx.ts`)  
Renders: title, description, `published_at` date, category badge, link to `/{category}/{slug}`

### `AffiliateCTA.tsx`
Props: `href: string, text: string, partner: string, placement: 'top' | 'inline' | 'bottom'`  
Renders: anchor tag with `rel="sponsored noopener noreferrer"`, disclosure string  
`"We may earn a commission if you click this link."`  
Style differs by `placement` (top = banner, inline = card, bottom = card).

### `TableOfContents.tsx`
Props: `headings: { id: string; text: string; level: number }[]`  
Pure render — no extraction logic here. Receives pre-parsed headings as a prop.

### `YouTubeEmbed.tsx`
Props: `url?: string`  
Returns `null` if `url` is falsy. Renders a lazy `<iframe>` otherwise.

---

## Step B — `lib/schema_builder.ts`

Export three pure functions. All URL parameters must include trailing slash.

```ts
buildArticleSchema(frontmatter: Frontmatter, siteUrl: string): object
buildFaqSchema(faqData: FAQData, siteUrl: string): object
buildBreadcrumbSchema(category: string, slug: string, title: string, siteUrl: string): object
```

`siteUrl` = `process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'` (no trailing slash on the env var itself; append it per URL).

Example breadcrumb item URL: `${siteUrl}/${category}/${slug}/`

---

## Step C — `lib/cta_injector.ts`

### Path helper (IMPORTANT — monorepo structure)

`apps/web/` is NOT the repo root. The affiliate map lives at:
```
{repo-root}/monetisation/affiliate_map/{slug}.json
```

From `apps/web/`, resolve as:
```ts
import path from 'path';
const mapPath = path.join(process.cwd(), '..', '..', 'monetisation', 'affiliate_map', `${slug}.json`);
```

Export this as `getAffiliateMapPath(slug: string): string`.

### `getAffiliateMap(slug: string): AffiliateMap | null`

- Reads file at `getAffiliateMapPath(slug)`
- Returns parsed JSON if file exists, `null` if not

### AffiliateMap shape (matches bot output)

```ts
interface AffiliateMap {
  slug: string;
  primary_partner: string;
  cta_variant: 'A' | 'B';
  links: Record<string, string>; // partner -> URL, may be empty {}
}
```

### Resolving the CTA URL

`links` can be an empty object `{}` (e.g. during dry-runs). Resolution order:

1. `affiliateMap.links[affiliateMap.primary_partner]` — use if non-empty string
2. Fall back to a static map in `lib/affiliate-links.ts`:
   ```ts
   // lib/affiliate-links.ts
   export const AFFILIATE_LINKS: Record<string, string> = {
     jasper: 'https://www.jasper.ai',
     writesonic: 'https://writesonic.com',
     copy_ai: 'https://www.copy.ai',
   };
   ```
3. If still not found → render newsletter fallback CTA (static `mailto:` or `#newsletter`)

### CTA placement (inline after 3rd H2) — CONCRETE APPROACH

Do NOT try to inject React nodes into a compiled MDXRemote tree. Instead, **split the raw MDX content string** in `getMDXDataBySlug` before compilation:

Update `lib/mdx.ts`:
```ts
export interface MDXData {
  frontmatter: Frontmatter;
  content: string;          // full content (unchanged — keep for TOC extraction)
  contentParts: string[];   // content split at ## boundaries; length >= 1
  headings: { id: string; text: string; level: number }[];
  filePath: string;
}
```

Add two helpers in `lib/mdx.ts`:

```ts
// Export this — used by TableOfContents
export function getHeadings(content: string): { id: string; text: string; level: number }[] {
  // parse lines starting with ## or ###
  // id = text.toLowerCase().replace(/[^a-z0-9]+/g, '-')
}

// Internal — called inside getMDXDataBySlug
function splitAtH2(content: string): string[] {
  // Split on /^## /m boundaries; keep the ## in each part
  // Returns at least one element (the whole content if no ## found)
}
```

In the article page (Step D), render parts as separate `<MDXRemote>` calls with CTA inserted between them.

---

## Step D — Refactor article page (`app/[category]/[slug]/page.tsx`)

Replace the inline breadcrumb nav with `<Breadcrumb />`.

Sidebar layout (two-column above 1024px, single column below):
```
prose (max-w-[720px]) | sticky sidebar (TOC, top CTA)
```

CTA injection in render order:
1. `<AffiliateCTA placement="top" ...>` — above `<MDXRemote source={contentParts[0]} />`
2. Parts 0 and 1 rendered normally
3. `<AffiliateCTA placement="inline" ...>` — between part[2] and part[3] (if part[2] exists; skip otherwise)
4. Remaining parts
5. `<AffiliateCTA placement="bottom" ...>` — before FAQ section
6. FAQ section (existing)

When `getAffiliateMap(slug)` returns `null` → render `<NewsletterCTA />` (a simple static component you create) at top and bottom only; omit inline.

JSON-LD: inject via `<script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />` inside a `<>` fragment at the top of the returned JSX. Render all three schemas (Article + FAQ if faqData exists + Breadcrumb).

Wire `headings` from `MDXData` into `<TableOfContents headings={article.headings} />`.

---

## Step E — `app/[category]/page.tsx`

**Must include `generateStaticParams`** — without it, category pages won't be pre-rendered at build time:

```ts
export async function generateStaticParams() {
  const articles = await getAllArticles();
  const categories = [...new Set(articles.map(a => a.frontmatter.category))];
  return categories.map(category => ({ category }));
}
```

Sort articles by `published_at` desc **in the page component** (not in `getAllArticles()`):
```ts
const sorted = articles
  .filter(a => a.frontmatter.category === category)
  .sort((a, b) => b.frontmatter.published_at.localeCompare(a.frontmatter.published_at));
```

Pagination: if `sorted.length > 12`, accept `searchParams: { page?: string }`, slice accordingly. Add `rel="next"/"prev"` `<link>` tags via `generateMetadata`.

---

## Step F — `app/page.tsx`

Keep it simple — no special hero component needed:

- H1 tagline + subtitle (plain text, copy from SPEC or use placeholder)
- Category cards: one card per unique category from `getAllArticles()`, linking to `/[category]`
- Latest articles: up to 6 `<ArticleCard>` sorted by `published_at` desc

No new components required beyond what Step A creates.

---

## Step G — Tests (`apps/web/__tests__/`)

### `schema_builder.test.ts`
- `buildArticleSchema` returns correct `@type: "Article"`
- `buildBreadcrumbSchema` URLs include trailing slash
- `buildFaqSchema` returns correct `@type: "FAQPage"`

### `cta_injector.test.ts`
- `getAffiliateMap` returns parsed object when fixture JSON exists
- `getAffiliateMap` returns `null` when file missing
- URL resolution: `links` populated → uses link; `links` empty → falls back to `AFFILIATE_LINKS`; unknown partner → returns newsletter fallback

Mock the filesystem in tests (`vi.mock('fs')` or write fixture files under `__tests__/fixtures/`).

---

## Verification

```bash
cd apps/web
npm install
npm run test
npm run build
```

Then `npm run dev` and manually check:
- `/` — category cards present, article cards present, no hardcoded slugs
- `/ai-writing` — article list sorted newest first
- `/ai-writing/best-ai-writing-tools-2026` — TOC sidebar, 3 CTA placements, JSON-LD visible in page source (`<script type="application/ld+json">`)

Affiliate map fixture already exists at `monetisation/affiliate_map/best-ai-writing-tools-2026.json`.

---

## Handoff

When done, update `execution-log.md`:
- Status: **NEEDS REVIEW**
- List all new/modified files
- Paste `npm run test` and `npm run build` output (last 20 lines each)
- Note any deviation from this prompt and why
```
