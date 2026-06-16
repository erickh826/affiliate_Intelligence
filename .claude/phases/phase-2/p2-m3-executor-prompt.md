# Phase 2 M3 — Executor Prompt

**Use when:** M2 is **COMPLETED** in `execution-log.md`.  
**Plan:** [p2-m3-plan.md](./p2-m3-plan.md) · **Spec:** `docs/SPEC-02-web-system.md` §5–§9 · **Deployment:** `docs/SPEC-05-deployment.md`

Copy everything inside the fenced block below into the executor agent.

---

```markdown
# Task: Phase 2 M3 — E-E-A-T pages, SEO, tests, deployment (Affiliate Intelligence)

Implement **Phase 2 M3** in `apps/web/` and `apps/bot/`. M2 is done: homepage, category index, CTAs, schema, shared components all landed.

Read first (in order):
1. `.claude/phases/phase-2/p2-m3-plan.md` — canonical scope
2. `docs/SPEC-02-web-system.md` §5–§9
3. `docs/SPEC-05-deployment.md` §5 — GitHub Actions workflow bodies

---

## Known M2 bug to fix first (Step A.0)

`app/[category]/[slug]/head.tsx` is NOT a recognised special file in Next.js 14+ App Router.
JSON-LD is defined there but never rendered — it does not appear in page source.

**Fix:** Delete `head.tsx`. Move JSON-LD injection into `page.tsx`:

```tsx
// In ArticlePage, add to the returned JSX (inside the outer div, before content):
<>
  <script
    type="application/ld+json"
    dangerouslySetInnerHTML={{ __html: JSON.stringify(buildArticleSchema(article.frontmatter, SITE_URL)) }}
  />
  <script
    type="application/ld+json"
    dangerouslySetInnerHTML={{ __html: JSON.stringify(buildBreadcrumbSchema(category, slug, article.frontmatter.title, SITE_URL)) }}
  />
  {faqData && (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(buildFaqSchema(faqData, SITE_URL)) }}
    />
  )}
</>
```

Import `buildArticleSchema`, `buildBreadcrumbSchema`, `buildFaqSchema` from `lib/schema_builder`.
After this fix, verify JSON-LD appears in `npm run build` output and page source.

---

## Step A — ESLint + Prettier

Add to `apps/web/`:

- `.eslintrc.json`:
```json
{ "extends": ["next/core-web-vitals"] }
```

- `.prettierrc`:
```json
{ "semi": true, "singleQuote": true, "printWidth": 80, "trailingComma": "all" }
```

Run `npx eslint apps/web/src --ext .ts,.tsx` (or `npx next lint` from `apps/web/`). Fix all **errors**; warnings acceptable.

---

## Step B — E-E-A-T static pages

Create these as Server Components (no `"use client"`):

### `app/about/page.tsx`
- H1: "About"
- Author name (use `process.env.NEXT_PUBLIC_AUTHOR_NAME` with fallback `"The Editor"`)
- 2–3 sentence bio: LLM developer and AI tools researcher
- LinkedIn link placeholder: `https://linkedin.com/in/your-profile` (use `NEXT_PUBLIC_LINKEDIN_URL` env, fallback `#`)
- `generateMetadata`: title "About | {siteName}", description

### `app/contact/page.tsx`
- H1: "Contact"
- Formspree `<form action={…}>`:
  ```tsx
  const formId = process.env.NEXT_PUBLIC_FORMSPREE_ID;
  const action = formId ? `https://formspree.io/f/${formId}` : '#';
  ```
- Fields: name, email, message, submit button
- Never render `action=""` — use `#` fallback
- `generateMetadata`

### `app/privacy-policy/page.tsx`
- H1: "Privacy Policy"
- Date-stamped (hardcode current date)
- Sections: data collected (GA4 analytics cookies, no personal data sold), AdSense (Google may show ads based on visits — see google.com/policies/privacy), cookies (can disable in browser settings), contact link
- `generateMetadata`

### `app/disclaimer/page.tsx`
- H1: "Disclaimer"
- Sections: affiliate disclosure (links marked `rel="sponsored"`, commissions earned), editorial independence (reviews are independent, not paid placements), no guarantees
- Date-stamped
- `generateMetadata`

---

## Step C — Article page: byline link + sticky disclaimer

### Byline link
In `app/[category]/[slug]/page.tsx`, change the byline author span to a link:

```tsx
<a href="/about" className="hover:text-accent transition-colors">
  {article.frontmatter.author}
</a>
```

### Sticky disclaimer banner
In `app/[category]/[slug]/page.tsx`, when `article.frontmatter.intent === 'comparison'`, render at the bottom of the page (after FAQ):

```tsx
{article.frontmatter.intent === 'comparison' && (
  <div className="fixed bottom-0 left-0 right-0 bg-surface/95 backdrop-blur border-t border-gray-700 py-3 px-4 text-xs text-gray-400 text-center z-50">
    This page contains affiliate links. We may earn a commission at no cost to you.{' '}
    <a href="/disclaimer" className="text-accent hover:underline">Learn more</a>
  </div>
)}
```

---

## Step D — SEO plumbing

### `next-sitemap`

```bash
cd apps/web && npm install next-sitemap
```

Create `apps/web/next-sitemap.config.js`:

```js
/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
  generateRobotsTxt: true,
  exclude: ['/api/*'],
  outDir: 'public',
};
```

Add to `apps/web/package.json` scripts:
```json
"postbuild": "next-sitemap"
```

### `metadataBase` in root layout

In `app/layout.tsx`, add/update the exported metadata:

```tsx
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  // keep existing title/description
};
```

This makes all relative OG image paths resolve correctly.

### OG image (static placeholder)
If `@vercel/og` adds complexity, use a static placeholder:
- Create `apps/web/public/og-default.png` — a simple 1200×630 image or just skip the file and set a default og:image URL in metadata pointing to the deployed domain.
- In root `layout.tsx` metadata, add:
```tsx
openGraph: {
  images: [{ url: '/og-default.png', width: 1200, height: 630 }],
},
```
Note in handoff if og-default.png is a placeholder.

---

## Step E — Core Web Vitals audit

1. Search for any `<img` tags in `apps/web/app/` and `apps/web/components/` — replace with `next/image` (require `width` and `height` props). If no images exist yet, note "no images found" in handoff.
2. Confirm `font-display: swap` is set. Check `app/layout.tsx` or the font import — Next.js `next/font` sets swap by default.
3. Add `content-visibility: auto` to `ArticleCard.tsx`:
```tsx
<article style={{ contentVisibility: 'auto' }} className="…existing classes…">
```
Use inline style here — Tailwind does not have a `content-visibility` utility by default.

---

## Step F — Light mode toggle

Create `components/ThemeToggle.tsx` — this is the ONLY `"use client"` component needed:

```tsx
'use client';
import { useEffect, useState } from 'react';

export default function ThemeToggle() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDark(stored ? stored === 'dark' : prefersDark);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  return (
    <button
      onClick={() => setDark(!dark)}
      aria-label="Toggle dark mode"
      className="p-2 rounded hover:bg-surface transition-colors text-sm"
    >
      {dark ? '☀️' : '🌙'}
    </button>
  );
}
```

Add `<ThemeToggle />` to the site header in `app/layout.tsx`.

---

## Step G — `apps/bot/gsc_feedback.py` stub

Create `apps/bot/gsc_feedback.py`:

```python
"""
GSC Feedback Loop — Phase 4 implementation stub.

Full implementation: GitHub Actions weekly cron (Phase 4).
Setup docs: docs/SPEC-05-deployment.md §5.3

Manual domain verification:
  1. Add site in search.google.com/search-console
  2. Choose DNS verification → add TXT record to your DNS provider
  3. Submit sitemap: https://{domain}/sitemap.xml
  4. Create service account → download JSON key → set GSC_SERVICE_ACCOUNT_JSON env
"""
```

---

## Step H — Expand test suite

Install test dependencies if not present:

```bash
cd apps/web && npm install -D @testing-library/react jsdom
```

Update `vitest.config.ts` to support jsdom environment for component tests:

```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
```

Also: `npm install -D @vitejs/plugin-react`

### `__tests__/schema_builder.test.ts` (extend existing)
Verify all three builders have tests for:
- Correct `@type` values
- Trailing slash on all URL fields
- `NEXT_PUBLIC_SITE_URL` fallback to `http://localhost:3000`

### `__tests__/cta_injector.test.ts` (extend existing)
Verify coverage of:
- Map with valid `links[primary_partner]` → uses that URL
- Map with empty `links` → falls back to `AFFILIATE_LINKS` static map
- Map with partner not in static map → `resolveCTAUrl` returns null → `resolveCTAConfig` returns null
- No map file → `getAffiliateMap` returns null → `resolveCTAConfig` returns null

### `__tests__/static-pages.test.ts` (new)
Smoke test that static page modules export a default function:

```ts
import { describe, it, expect } from 'vitest';

describe('static pages export defaults', () => {
  it('about page', async () => {
    const mod = await import('../app/about/page');
    expect(typeof mod.default).toBe('function');
  });
  it('contact page', async () => {
    const mod = await import('../app/contact/page');
    expect(typeof mod.default).toBe('function');
  });
  it('privacy-policy page', async () => {
    const mod = await import('../app/privacy-policy/page');
    expect(typeof mod.default).toBe('function');
  });
  it('disclaimer page', async () => {
    const mod = await import('../app/disclaimer/page');
    expect(typeof mod.default).toBe('function');
  });
});
```

---

## Step I — GitHub Actions workflows

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  bot-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r apps/bot/requirements.txt
      - run: ruff check apps/bot/
      - run: pytest apps/bot/tests/ -x

  web-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: apps/web/package-lock.json
      - run: npm ci --prefix apps/web
      - run: npm run test --prefix apps/web
      - run: npm run build --prefix apps/web
```

Create `.github/workflows/bot-cron.yml` — paste the full body from `docs/SPEC-05-deployment.md` §5.2.

---

## Hard rules

- TypeScript strict, no `any`, Tailwind only (except `content-visibility` inline style — document it)
- No code comments
- Server Components by default; `"use client"` only on `ThemeToggle`
- All static pages: `generateMetadata` required

---

## Verification

```bash
cd apps/web
npm install
npm run lint       # zero errors
npm run test       # all pass
npm run build      # postbuild runs next-sitemap
```

Check `apps/web/public/sitemap.xml` and `apps/web/public/robots.txt` exist after build.

Manual check after `npm run dev`:
- `/about`, `/contact`, `/privacy-policy`, `/disclaimer` all load
- Article page: byline is a link to `/about`
- Comparison article: sticky disclaimer banner visible at bottom
- Article page source (`Ctrl+U`): `<script type="application/ld+json">` present in `<body>` (or `<head>` if moved there)
- Light mode toggle works

---

## Handoff

Status: NEEDS REVIEW — list:
- Files created/modified
- Test count and pass/fail
- `npm run build` result
- Confirmation that JSON-LD appears in article page source
- Any deviations from this prompt
```
