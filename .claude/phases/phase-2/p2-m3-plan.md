# Phase 2 Milestone 3 — Plan

**Status:** NEEDS REVIEW  
**Spec:** `docs/SPEC-02-web-system.md` §5–§9  
**Depends on:** M2 — homepage, category index, CTA, schema, shared components landed

**Executor prompt:** [p2-m3-executor-prompt.md](./p2-m3-executor-prompt.md)  
**Review:** *TBD: `p2-m3-review-prompt.md`*

---

## Objective

Make the site **AdSense-eligible and production-ready**: E-E-A-T static pages, sitemap/SEO plumbing, Core Web Vitals hygiene, GSC feedback stub, and full test coverage. After M3 Phase 2 is complete.

---

## In scope (M3)

| Task | Deliverable | Acceptance |
|------|-------------|------------|
| **T2.9** | E-E-A-T static pages | `/about`, `/contact`, `/privacy-policy`, `/disclaimer` — all render 200, AdSense pre-checklist satisfied |
| **T2.10** | SEO plumbing | `next-sitemap` config → `sitemap.xml` + `robots.txt`; canonical tag on all pages; OG image via `@vercel/og`; Core Web Vitals targets in code |
| **T2.11** | GSC feedback stub | `apps/bot/gsc_feedback.py` stub with documented cron setup |
| **T2.12 (full)** | Tests | CTA injection (3 placements + fallback), schema builder (all 3 types), MDX render, static pages return 200 |
| **Tech debt** | ESLint + Prettier | `.eslintrc.js` + `.prettierrc` aligned with `.ai-context/conventions.md`; `npm run lint` passes cleanly |
| **UX** | Light mode toggle | System preference + manual toggle in header; dark = default |

---

## Out of scope (Phase 3+)

- Actual AdSense code injection (Phase 3 — SPEC-03)
- Affiliate link management + live revenue tracking (Phase 3)
- YouTube embed wiring to live DB (Phase 4)
- GSC weekly cron implementation (Phase 4)
- Vercel deployment setup (operations, not Phase 2 code)

---

## Design decisions

### 1. E-E-A-T pages (T2.9)

All four pages live under `apps/web/app/{page}/page.tsx` as static Server Components.

| Page | Content requirements (SPEC-02 §6) |
|------|-----------------------------------|
| `/about` | Real author name, LLM developer background, LinkedIn URL, photo placeholder. Author byline on articles must link here. |
| `/contact` | Formspree `<form action="https://formspree.io/f/{id}">`. Form ID = `NEXT_PUBLIC_FORMSPREE_ID` env; render mailto fallback when env absent. |
| `/privacy-policy` | GDPR basics + AdSense cookie disclosure + analytics disclosure. Mention GA4 by name. Date-stamped. |
| `/disclaimer` | Affiliate disclosure. Sticky banner on `intent === "comparison"` article pages (add conditional to article layout). |

Author byline fix: update `app/[category]/[slug]/page.tsx` byline to link `article.frontmatter.author` → `/about`.

### 2. SEO plumbing (T2.10)

**next-sitemap:**

```bash
npm install next-sitemap
```

Create `next-sitemap.config.js` at `apps/web/`:

```js
/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
  generateRobotsTxt: true,
  exclude: ['/api/*'],
};
```

Add `postbuild` script: `"postbuild": "next-sitemap"`.

**Canonical + OG:**

- `generateMetadata` already sets `title` + `description` + basic OG (M1).
- Add `metadataBase` in root `layout.tsx` using `NEXT_PUBLIC_SITE_URL`.
- Add `alternates.canonical` in `generateMetadata` on article page: `${siteUrl}/${category}/${slug}/` (trailing slash per SPEC-02 §4.1).
- OG image: use `@vercel/og` with a simple text template. Add `opengraph-image.tsx` under `app/[category]/[slug]/` (Next.js 14+ convention). Falls back to site-level placeholder if `@vercel/og` adds unacceptable build complexity — document in handoff.

**Core Web Vitals:**

- Audit any `<img>` → replace with `next/image` (width, height required).
- Confirm `font-display: swap` is set in `lib/fonts.ts` / Tailwind config (already done in M1 — verify).
- Add `content-visibility: auto` Tailwind class to `ArticleCard` list items.
- No blocking scripts except AdSense placeholder (AdSense code added in Phase 3).

### 3. GSC feedback stub (T2.11)

File: `apps/bot/gsc_feedback.py`

```python
"""
GSC Feedback Loop — Phase 4 implementation stub.
Reads Search Console click data and updates keywords.db.

Full implementation: GitHub Actions weekly cron (Phase 4).
Setup:
  1. Verify domain in GSC via DNS TXT record.
  2. Submit sitemap: https://{domain}/sitemap.xml
  3. Create service account + download JSON key → GSC_SERVICE_ACCOUNT_JSON env.
"""

# TODO (Phase 4): implement with google-auth-library + searchconsole API
```

Document in `apps/bot/README.md` how to verify domain and submit sitemap manually.

### 4. Light mode toggle

Add a `ThemeToggle` client component (minimal `"use client"`) to the site header. Store preference in `localStorage`; apply `dark` class to `<html>`. System preference is the initial default (already set via `dark` class in `layout.tsx`).

### 5. ESLint + Prettier (tech debt)

Add to `apps/web/`:

- `.eslintrc.json`: `{ "extends": ["next/core-web-vitals"] }`
- `.prettierrc`: `{ "semi": true, "singleQuote": true, "printWidth": 80 }`
- Add `"lint:fix": "eslint apps/web --fix"` and `"format": "prettier --write apps/web"` scripts
- Run `npx eslint apps/web/` — fix all reported errors; warnings are acceptable

### 6. Full test coverage (T2.12)

Expand `apps/web/__tests__/` to cover M2 additions. Use Vitest + `@testing-library/react` for component tests.

| Test file | Coverage |
|-----------|----------|
| `schema_builder.test.ts` | Article, FAQ, Breadcrumb JSON-LD output; trailing slash on URLs |
| `cta_injector.test.ts` | With affiliate map (3 placements), without map (fallback), empty `links` (fallback), <3 H2s (no inline CTA) |
| `mdx.test.ts` (extend M1) | `getHeadings()`, `contentParts` split |
| `static-pages.test.ts` | Smoke: getStaticProps / render check or route list |

Add `@testing-library/react` + `jsdom` (vitest env) for component tests:

```bash
npm install -D @testing-library/react @vitest/coverage-v8 jsdom
```

---

## Implementation order

| Step | Work |
|------|------|
| A | ESLint + Prettier config; run lint; fix errors |
| B | `app/about/page.tsx`, `app/contact/page.tsx`, `app/privacy-policy/page.tsx`, `app/disclaimer/page.tsx` |
| C | Byline on article page → link to `/about`; sticky disclaimer banner on comparison pages |
| D | `next-sitemap` config + `postbuild` script; `metadataBase` + canonical in layout |
| E | OG image (`opengraph-image.tsx` or static placeholder) |
| F | Core Web Vitals audit: `next/image`, `content-visibility`, font swap check |
| G | Light mode toggle (`ThemeToggle` component) |
| H | `apps/bot/gsc_feedback.py` stub + README note |
| I | Expand `__tests__/`: schema, CTA, static-pages, MDX headings |
| J | `npm run test && npm run build && npm run lint`; update `execution-log.md` → M3 NEEDS REVIEW |
| K | **Deployment setup** — Vercel import, env vars, custom domain, `ci.yml` + `bot-cron.yml` to `.github/workflows/`; follow `docs/SPEC-05-deployment.md` §7 checklist |

---

## Verification

```bash
cd apps/web
npm install
npm run lint
npm run test
npm run build
# postbuild runs next-sitemap automatically → check public/sitemap.xml, public/robots.txt
npm run dev
```

Manual checks:

- `/about` renders author info
- `/contact` shows form
- `/privacy-policy` and `/disclaimer` return 200
- Article page byline links to `/about`
- Comparison article shows sticky disclaimer banner
- `<head>` of article page contains canonical URL and JSON-LD
- Page source includes `sitemap.xml` reference in `robots.txt`
- Light mode toggle switches theme

Google tools (post-deploy):

- Google Rich Results Test on article URL
- PageSpeed Insights / Lighthouse ≥ 90 Performance

---

## Risks

| Risk | Mitigation |
|------|------------|
| `@vercel/og` requires Edge runtime | Fall back to static `og:image` placeholder if Edge setup adds complexity; document in handoff |
| `next-sitemap` path resolution in monorepo | Run from `apps/web`; set `outDir: 'public'` in config |
| Formspree form ID missing in dev | Render mailto fallback when `NEXT_PUBLIC_FORMSPREE_ID` is absent; never render broken `action=""` |
| ESLint errors in M2 code | Fix in Step A before touching other files |

---

## M3 Definition of Done

Phase 2 is **COMPLETED** when all of the following pass:

- [ ] `/about`, `/contact`, `/privacy-policy`, `/disclaimer` return 200
- [ ] Author byline links to `/about`
- [ ] Sticky affiliate disclosure on comparison pages
- [ ] `sitemap.xml` + `robots.txt` generated by `npm run build`
- [ ] Canonical URL in `<head>` of article pages
- [ ] OG image present (static placeholder acceptable)
- [ ] Core Web Vitals: no `<img>` without `next/image`, fonts swap
- [ ] Light mode toggle works
- [ ] `apps/bot/gsc_feedback.py` stub exists
- [ ] Vitest covers schema, CTA, static pages
- [ ] `npm run lint` passes (zero errors)
- [ ] `npm run test` passes
- [ ] `npm run build` passes
- [ ] SPEC-02 §9 Pre-AdSense Checklist satisfied (code-side items only)
- [ ] execution-log M3 → NEEDS REVIEW (not COMPLETED until human review)
- [ ] Vercel project live at custom domain
- [ ] `ci.yml` + `bot-cron.yml` committed and passing
- [ ] SPEC-05 §7 Pre-Phase-3 deployment checklist complete

---

## Post-M3: Phase 2 close-out

After M3 review passes:

1. Update `execution-log.md` — Phase 2 **COMPLETED**
2. Check off `qa-checklist.md` remaining items
3. Update `p2-roadmap.md` — all milestones COMPLETED
4. **Unblock Phase 3** — AdSense + affiliate monetisation (SPEC-03)
