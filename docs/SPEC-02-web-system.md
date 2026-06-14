# SPEC-02 — Web Publishing System

**Version:** 1.0 | **Updated:** 2026-05-12
**Related:** [README](../README.md) | [SPEC-01](./SPEC-01-content-bot.md) | [SPEC-03](./SPEC-03-monetisation.md)

---

## 1. Purpose

SPEC-02 defines the web publishing layer. It takes MDX + metadata from SPEC-01 and renders a fast, SEO-optimised, AdSense-eligible website. It also runs the weekly GSC feedback loop that writes click data back to `data/keywords.db`.

---

## 2. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | Next.js 14 (App Router) | SSG/ISR, MDX-native, Vercel integration |
| Content | MDX files in `apps/web/content/` | Bot-writable, version-controlled |
| Styling | Tailwind CSS v4 | Utility-first, fast |
| Deployment | Vercel (free tier) | Auto-deploy on git push, global CDN |
| Analytics | GA4 + Google Search Console | Traffic + SEO measurement |
| Domain | Custom `.com` | Required for AdSense |

---

## 3. Site Structure

```
/                       ← Homepage
/[category]/            ← Category index
/[category]/[slug]/     ← Article page
/about/                 ← Author bio (E-E-A-T signal, AdSense required)
/contact/               ← Contact form (AdSense required)
/privacy-policy/        ← AdSense required
/disclaimer/            ← Affiliate disclosure
/sitemap.xml            ← Auto-generated
/robots.txt             ← Allow all crawlers
```

### Article Page Layout

```
Breadcrumb: Home > Category > Article
┌─────────────────────────────┬──────────────┐
│ H1 Title                    │ TOC          │
│ By [Author] · [Date]        │ Top CTA      │
│ Last reviewed: [Date]       │ Newsletter   │
│                             │ Related      │
│ [Article body]              │              │
│ [Affiliate CTAs]            │              │
│ [FAQ section]               │              │
│ [Video embed if available]  │              │
└─────────────────────────────┴──────────────┘
[Related articles — 3 cards]
```

---

## 4. Content Rendering

### 4.1 MDX Processing

Each `.mdx` renders as a static page via `generateStaticParams`. Frontmatter maps to:
- `<title>`: `{title} | {site_name}`
- `<meta name="description">`: `{description}`
- Open Graph: `og:title`, `og:description`, `og:image` (via `@vercel/og`)
- Canonical: `https://{domain}/{category}/{slug}/`

### 4.2 Affiliate CTA Injection

`lib/cta_injector.ts` reads `monetisation/affiliate_map/[slug].json` at build time:

| Placement | Position |
|---|---|
| `top` | After H1, before paragraph 1 |
| `inline` | After H2 section #3 |
| `bottom` | Before FAQ section |

```tsx
<AffiliateCTA
  href={cta.url}
  text={cta.anchor}
  partner={cta.partner}
  disclaimer="We may earn a commission if you click this link."
/>
```

If no affiliate_map file exists → renders newsletter CTA fallback.

### 4.3 Video Embed

If `keywords.db[youtube_url]` is set (by SPEC-04), article renders `<YouTubeEmbed>` after the introduction section. No URL → section omitted.

### 4.4 FAQ Schema

Articles with `[slug].faq.json` inject into `<head>`:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    { "@type": "Question", "name": "...",
      "acceptedAnswer": { "@type": "Answer", "text": "..." } }
  ]
}
```

---

## 5. SEO Requirements

| Requirement | Implementation |
|---|---|
| Sitemap | `/sitemap.xml` via `next-sitemap` |
| robots.txt | Allows all crawlers, points to sitemap |
| Canonical | Exact page URL on all pages |
| Structured data | FAQPage, BreadcrumbList, Article schema |
| Open Graph | `og:title`, `og:description`, `og:image`, `og:type=article` |
| Pagination | `rel="next"/"prev"` on category listing pages |

### Core Web Vitals Targets

| Metric | Target |
|---|---|
| LCP | < 2.0s |
| INP | < 200ms |
| CLS | < 0.1 |

Implementation: `next/image` with width/height, `font-display: swap`, `content-visibility: auto` on list items, no blocking scripts except AdSense.

---

## 6. E-E-A-T Signals (Required for AdSense Approval)

| Signal | Implementation |
|---|---|
| Author identity | `/about` with real name + LLM developer background + LinkedIn |
| Author byline | Every article: `By [Name]` linked to About page |
| Last reviewed date | Displayed near title |
| Expertise proof | Technical depth: API cost tables, code snippets, real testing notes |
| Affiliate disclosure | Sticky banner on comparison pages |
| Contact page | Working form (Formspree) |
| Privacy Policy | GDPR + AdSense + cookie disclosure |

---

## 7. GSC Feedback Loop

### 7.1 Initial Setup

1. Verify domain in GSC via DNS TXT record
2. Submit `sitemap.xml`
3. Wait for 15+ pages indexed before AdSense application

### 7.2 Weekly Feedback Cron (Phase 4)

`apps/bot/gsc_feedback.py` runs weekly (GitHub Actions cron). Writes directly to `data/keywords.db` via SQLite — safe to run concurrently with the bot pipeline:

```python
for page in gsc_api.get_pages(last_days=7):
    keyword_db.update(
        slug=page.slug,
        gsc_impressions=page.impressions,
        gsc_clicks=page.clicks,
        gsc_ctr=page.ctr,
        gsc_position=page.position
    )
    # Flag for rewrite if high impressions but low CTR
    if page.impressions > 200 and page.ctr < 0.01:
        keyword_db.set_status(slug=page.slug, status="needs_rewrite")
```

Rows marked `needs_rewrite` are re-queued to SPEC-01 in `rewrite_mode`.

---

## 8. Design System

| Token | Dark (default) | Light |
|---|---|---|
| Background | `#111827` | `#fafaf9` |
| Surface | `#1f2937` | `#f5f5f4` |
| Accent | `#0d9488` | `#0d9488` |
| Text | `#f9fafb` | `#1c1917` |
| Font display | Instrument Serif | same |
| Font body | Inter | same |
| Border radius | 8px cards, 12px panels | same |
| Max content width | 720px prose, 1100px layout | same |

Dark mode default. System preference toggle in header.

---

## 9. Pre-AdSense Checklist

- [ ] `/about` — real author identity
- [ ] `/contact` — working contact
- [ ] `/privacy-policy` — cookie + data disclosure
- [ ] `/disclaimer` — affiliate disclosure
- [ ] 20+ pages indexed in GSC
- [ ] Custom domain with HTTPS
- [ ] Mobile-responsive at 375px
- [ ] Core Web Vitals passing in PageSpeed Insights
- [ ] No broken links
- [ ] No placeholder/thin content

---

## 10. Environment Variables

```env
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
NEXT_PUBLIC_SITE_NAME=AI Tools Hub
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_PUBLISHER_ID=ca-pub-XXXXXXXXXXXXXXXX
GSC_SERVICE_ACCOUNT_JSON=
```

---

*Related: [README.md](../README.md) | [SPEC-01](./SPEC-01-content-bot.md) | [SPEC-03](./SPEC-03-monetisation.md) | [SPEC-05](./SPEC-05-deployment.md)*
