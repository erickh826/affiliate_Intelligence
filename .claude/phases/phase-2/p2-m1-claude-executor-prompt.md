# Phase 2 Milestone 1 — Claude Executor Prompt

**Use when:** Starting Phase 2 after Phase 1 is complete.  
**Scope:** T2.1 (partial scaffold), T2.3 (MDX pipeline), T2.4 (article page).  
**Roadmap:** [p2-roadmap.md](./p2-roadmap.md) · **Spec:** `docs/SPEC-02-web-system.md`  
**Review after:** [p2-m1-review-prompt.md](./p2-m1-review-prompt.md)

Copy everything inside the fenced block below into Claude Code / Claude.

---

```markdown
# Task: Phase 2 Milestone 1 — MDX pipeline + article page (Affiliate Intelligence)

Implement **Phase 2 M1** in `apps/web/`: read bot-generated MDX and render a static article page. Do **not** implement homepage, CTA injection, JSON-LD schema, category index, or E-E-A-T static pages in this task (M2/M3).

## Read first

1. `docs/SPEC-02-web-system.md` — §3 site structure, §4.1 MDX processing, §8 design tokens (use for styling baseline)
2. `.claude/phases/phase-2/plan.md` — T2.1, T2.3, T2.4
3. `.claude/phases/phase-2/p2-roadmap.md` — M1 scope and smoke test
4. `apps/bot/models.py` — `Frontmatter`, `FAQItem` field names (web types must align)
5. Existing content (smoke test fixtures):
   - `apps/web/content/ai-writing/best-ai-writing-tools-2026.mdx`
   - `apps/web/content/faq/best-ai-writing-tools-2026.faq.json`

## Current state

- `apps/web/` exists with minimal Next.js App Router (`app/layout.tsx`, `app/page.tsx`, `package.json`).
- No MDX loader, no dynamic `[category]/[slug]` route yet.
- Tailwind may be missing or minimal — add as part of T2.1 partial.

## Goal (M1 Definition of Done)

```bash
cd apps/web && npm install && npm run build && npm run dev
```

- `GET /ai-writing/best-ai-writing-tools-2026` renders the sample article (title, byline, body, FAQ list).
- `generateStaticParams` enumerates all `{category}/{slug}` from `apps/web/content/**/*.mdx` (exclude `faq/`).
- `npm run build` succeeds (SSG).
- Tests pass for MDX loader (see Tests section).

## Hard rules (project)

- TypeScript only under `apps/web/`. `"strict": true`.
- Prettier (80 char, single quotes), ESLint (`next/core-web-vitals`).
- Server Components by default; `"use client"` only if needed (e.g. future TOC toggle — M1 may use static TOC or skip TOC).
- Tailwind only; no inline styles.
- No `any`; use `unknown` + type guards.
- No code comments unless necessary.
- Do **not** commit `.env` or API keys.
- Do **not** start M2 features (CTA injector, schema builder, homepage redesign, category index).
- Mark **M1** as **NEEDS REVIEW** in `.claude/phases/phase-2/execution-log.md` — not COMPLETED until human review.

## T2.1 partial — Scaffold hardening

Enhance existing `apps/web/` (do **not** run `create-next-app` in a new folder):

- Ensure **Next.js 14.x** App Router (upgrade package.json if needed; pin reasonable versions, not unbounded `latest` if you touch deps).
- Add/configure **Tailwind CSS** (v3 or v4 per project conventions in SPEC-02; if v4 setup is heavy, v3 is acceptable for M1 — document choice in handoff).
- Add **ESLint** + **Prettier** configs matching `.ai-context/conventions.md`.
- `tsconfig.json`: `"strict": true`.
- Optional for M1: `apps/web/lib/fonts.ts` with Inter via `next/font` (Instrument Serif can be deferred).
- Apply dark-mode baseline from SPEC-02 §8 in `globals.css` / layout (`bg` ~ `#111827`, text ~ `#f9fafb`, accent `#0d9488`).
- Keep root `app/page.tsx` minimal (placeholder OK) — full homepage is M2.

## T2.3 — MDX rendering pipeline

Create `apps/web/lib/mdx.ts` (and small helpers as needed):

### Types

```typescript
// ArticleFrontmatter — align with apps/bot/models.py Frontmatter
export interface ArticleFrontmatter {
  title: string;
  description: string;
  slug: string;
  category: string;
  intent: string;
  published_at: string;
  last_reviewed: string;
  author: string;
  affiliate_partner: string | null;
  schema_type: string;
}

export interface ArticleMeta extends ArticleFrontmatter {
  content: string; // MDX/Markdown body without frontmatter fence
}
```

### Functions (minimum public API)

- `getContentRoot(): Path` — `apps/web/content`
- `getAllArticles(): ArticleMeta[]` — scan `content/{category}/*.mdx`, skip `content/faq/`
- `getArticle(category: string, slug: string): ArticleMeta | null`
- `getArticleSlugs(): { category: string; slug: string }[]` — for `generateStaticParams`
- `getFaq(slug: string): { slug: string; faqs: { question: string; answer: string }[] } | null` — read `content/faq/{slug}.faq.json`

### Parsing

- Use `gray-matter` (or equivalent) to split frontmatter + body.
- Frontmatter values from bot are JSON-encoded strings in YAML (e.g. `title: "Best ..."`). Parsed result must be plain strings.
- Validate required frontmatter keys; throw or skip invalid files with clear errors in build logs.

### Rendering approach (pick one, prefer simplicity for M1)

**Option A (recommended for M1):** Treat body as **Markdown** — install `react-markdown` + `remark-gfm`. Bot output is `# H1` + `## H2` markdown (no custom MDX components yet).

**Option B:** Full MDX with `@next/mdx` — only if you also register allowed components stub; do not block M1 on custom components.

Article page renders parsed body; duplicate H1 in frontmatter vs body is OK for M1 (style prose so page title uses frontmatter `title`).

## T2.4 — Article page

Create `apps/web/app/[category]/[slug]/page.tsx`:

- `export async function generateStaticParams()` from `getArticleSlugs()`
- `export async function generateMetadata()` — `title: \`${frontmatter.title} | ${siteName}\``, `description`, basic Open Graph title/description (full OG image is M3)
- Server Component page layout per SPEC-02 §3 (simplified for M1):
  - Breadcrumb text: Home > {category} > {title} (links optional for M1; category link can 404 until M2)
  - H1 from `frontmatter.title`
  - Byline: `By {author}` · `{published_at}` · `Last reviewed: {last_reviewed}`
  - Article body (prose, max-width ~720px, layout ~1100px)
  - FAQ section if `getFaq(slug)` returns data — render questions/answers
- `notFound()` if article missing
- Use `NEXT_PUBLIC_SITE_NAME` env with fallback `"Affiliate Intelligence"`

Do **not** implement sidebar TOC, AffiliateCTA, YouTube embed, or related-articles grid in M1 (M2).

## Tests

Add Vitest (or use existing if present) under `apps/web/`:

- `__tests__/mdx.test.ts` (or similar):
  - `getAllArticles()` finds `best-ai-writing-tools-2026`
  - `getArticle('ai-writing', 'best-ai-writing-tools-2026')` parses frontmatter fields
  - `getFaq('best-ai-writing-tools-2026')` returns FAQ array
- Add `"test": "vitest run"` to `apps/web/package.json`

Mock filesystem or use repo fixture paths relative to project root.

## Verification (run and report)

```bash
cd apps/web
npm install
npm run lint
npm run test
npm run build
npm run dev   # manual check URL optional; build success is required
```

From repo root (optional):

```bash
npx eslint apps/web/
```

## Docs (minimal)

Update `.claude/phases/phase-2/execution-log.md`:

- Add section **M1 — MDX + article page**
- **Status:** NEEDS REVIEW
- List changed files, `npm run build` / test results

Update `.claude/phases/phase-2/qa-checklist.md` — check items you satisfy (MDX pipeline, article route).

Do **not** mark Phase 2 overall COMPLETED.

## Handoff (required)

```md
## Task Handoff

Task: Phase 2 M1 (T2.1 partial + T2.3 + T2.4)
Status: NEEDS REVIEW

Changed files:
- (list)

Commands run:
- npm run lint / test / build

Result:
- build pass/fail; test count

Smoke URL:
- /ai-writing/best-ai-writing-tools-2026

Risks or blockers:
- None | ...

Deferred to M2:
- (list)
```

## Acceptance checklist

- [ ] `apps/web/lib/mdx.ts` reads `content/{category}/*.mdx`
- [ ] `ArticleFrontmatter` matches bot `Frontmatter` keys
- [ ] `app/[category]/[slug]/page.tsx` with `generateStaticParams`
- [ ] Sample article builds and renders
- [ ] FAQ JSON displayed when present
- [ ] Tailwind + dark baseline applied
- [ ] Vitest covers loader
- [ ] `npm run build` passes
- [ ] execution-log updated; M1 not marked COMPLETED
```
