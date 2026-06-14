# Phase 2 — QA Checklist

**Phase:** 2 — Web Publishing System (SPEC-02)
**Status:** IN PROGRESS (M1 done; M2 planned)

---

## Functional Requirements

- [x] Next.js App Router with strict TypeScript
- [x] Tailwind CSS with design tokens (dark default)
- [ ] Homepage renders category cards + latest articles (dynamic — M2)
- [x] MDX articles render from `apps/web/content/` via generateStaticParams
- [x] Article page layout: breadcrumb, H1, byline, body, FAQ (TOC/CTAs — M2)
- [ ] Category index page with article cards sorted by date
- [ ] CTA injection at 3 positions: top, inline, bottom
- [ ] CTA fallback to newsletter when no affiliate map exists
- [ ] All affiliate links have `rel="sponsored"` + disclosure text
- [ ] Schema builder outputs Article JSON-LD
- [ ] Schema builder outputs FAQPage JSON-LD
- [ ] Schema builder outputs BreadcrumbList JSON-LD
- [ ] YouTubeEmbed component renders when youtube_url present
- [ ] YouTubeEmbed omitted when youtube_url is null

## E-E-A-T & AdSense Requirements

- [ ] `/about/` with real author identity + LinkedIn
- [ ] `/contact/` with working Formspree form
- [ ] `/privacy-policy/` with GDPR + AdSense + cookie disclosure
- [ ] `/disclaimer/` with affiliate disclosure
- [ ] Sticky affiliate disclosure banner on comparison pages
- [ ] Author byline on every article linked to About page
- [ ] Last reviewed date displayed near title

## SEO Requirements

- [ ] `sitemap.xml` auto-generated via next-sitemap
- [ ] `robots.txt` allows all crawlers, points to sitemap
- [ ] Canonical URL on every page
- [ ] Open Graph meta: og:title, og:description, og:image, og:type=article
- [ ] `rel="next"/"prev"` on category pagination
- [ ] Structured data validates in Google Rich Results Test

## Core Web Vitals

- [ ] LCP < 2.0s
- [ ] INP < 200ms
- [ ] CLS < 0.1
- [ ] `next/image` with width/height on all images
- [ ] `font-display: swap` on all fonts
- [ ] No blocking scripts except AdSense

## Responsive Design

- [ ] Mobile-responsive at 375px
- [ ] Desktop layout at 1440px
- [ ] Dark mode default, system preference toggle in header

## Code Quality

- [ ] Prettier passes (80 char, single quotes)
- [ ] ESLint passes (next/core-web-vitals)
- [ ] No `any` types
- [ ] Server Components by default
- [ ] `"use client"` only where needed (state, effects, event handlers)
- [ ] No inline styles; Tailwind only
- [ ] No code comments

## Tests

- [ ] CTA injection: with/without affiliate map
- [ ] Schema builder: correct JSON-LD for all 3 types
- [ ] MDX render: frontmatter parsed, article renders
- [ ] Static pages return 200
