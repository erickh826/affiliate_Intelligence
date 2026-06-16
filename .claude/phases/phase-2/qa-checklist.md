# Phase 2 — QA Checklist

**Phase:** 2 — Web Publishing System (SPEC-02)
**Status:** IN PROGRESS (M3 implemented; pending review)

---

## Functional Requirements

- [x] Next.js App Router with strict TypeScript
- [x] Tailwind CSS with design tokens (dark default)
- [x] Homepage renders category cards + latest articles (dynamic — M2)
- [x] MDX articles render from `apps/web/content/` via generateStaticParams
- [x] Article page layout: breadcrumb, H1, byline, body, FAQ (TOC/CTAs — M2)
- [x] Category index page with article cards sorted by date
- [x] CTA injection at 3 positions: top, inline, bottom
- [x] CTA fallback to newsletter when no affiliate map exists
- [x] All affiliate links have `rel="sponsored"` + disclosure text
- [x] Schema builder outputs Article JSON-LD
- [x] Schema builder outputs FAQPage JSON-LD
- [x] Schema builder outputs BreadcrumbList JSON-LD
- [x] YouTubeEmbed component renders when youtube_url present
- [x] YouTubeEmbed omitted when youtube_url is null

## E-E-A-T & AdSense Requirements

- [x] `/about/` with real author identity + LinkedIn
- [x] `/contact/` with working Formspree form
- [x] `/privacy-policy/` with GDPR + AdSense + cookie disclosure
- [x] `/disclaimer/` with affiliate disclosure
- [x] Sticky affiliate disclosure banner on comparison pages
- [x] Author byline on every article linked to About page
- [x] Last reviewed date displayed near title

## SEO Requirements

- [x] `sitemap.xml` auto-generated via next-sitemap
- [x] `robots.txt` allows all crawlers, points to sitemap
- [x] Canonical URL on every page
- [x] Open Graph meta: og:title, og:description, og:image, og:type=article
- [ ] `rel="next"/"prev"` on category pagination
- [ ] Structured data validates in Google Rich Results Test

## Core Web Vitals

- [ ] LCP < 2.0s
- [ ] INP < 200ms
- [ ] CLS < 0.1
- [ ] `next/image` with width/height on all images
- [ ] `font-display: swap` on all fonts
- [x] No blocking scripts except AdSense

## Responsive Design

- [ ] Mobile-responsive at 375px
- [ ] Desktop layout at 1440px
- [x] Dark mode default, system preference toggle in header

## Code Quality

- [x] Prettier passes (80 char, single quotes)
- [x] ESLint passes (next/core-web-vitals)
- [x] No `any` types
- [x] Server Components by default
- [x] `"use client"` only where needed (state, effects, event handlers)
- [x] No inline styles; Tailwind only
- [x] No code comments

## Tests

- [x] CTA injection: with/without affiliate map
- [x] Schema builder: correct JSON-LD for all 3 types
- [x] MDX render: frontmatter parsed, article renders
- [ ] Static pages return 200
