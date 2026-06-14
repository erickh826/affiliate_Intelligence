# SPEC-03 — Monetisation System

**Version:** 1.0 | **Updated:** 2026-05-12
**Related:** [README](../README.md) | [SPEC-02](./SPEC-02-web-system.md)

---

## 1. Purpose

SPEC-03 defines the monetisation layer: Google AdSense display advertising and affiliate marketing. It covers account application procedures, CTA injection config, affiliate program priorities, and revenue tracking.

---

## 2. Revenue Streams

```
Website Traffic
     │
     ├──► Google AdSense (display ads)
     │         RPM: $3–$15 depending on niche + traffic quality
     │         Best for: informational, high-volume pages
     │
     └──► Affiliate Marketing
               Commission: 20–30% recurring
               Best for: comparison, review, tutorial pages
```

**Revenue priority rule:**
- `intent=comparison` / `intent=tutorial` pages: Affiliate CTAs take priority, AdSense in-article suppressed above fold
- `intent=informational` pages: AdSense auto-ads enabled fully

---

## 3. Google AdSense

### 3.1 Application Requirements

| Requirement | Notes |
|---|---|
| Custom domain + HTTPS | Must complete before applying |
| 20+ quality indexed articles | Track in Google Search Console |
| About / Contact / Privacy / Disclaimer pages | See SPEC-02 Section 6 |
| No adult or copyright-infringing content | Bot quality gate enforces this |
| 3+ months site age (recommended) | Faster approval |

### 3.2 Application Steps

1. Go to `adsense.google.com` → sign in with Google account
2. Enter website URL + select language (English)
3. Paste AdSense verification snippet into `apps/web/app/layout.tsx` `<head>`
4. Wait for review: typically 2–4 weeks for new sites
5. Upon approval: create ad units in AdSense dashboard
6. Enable Auto-ads on informational pages only

### 3.3 Ad Unit Config

```json
// monetisation/adsense_config.json
{
  "publisher_id": "ca-pub-XXXXXXXXXXXXXXXX",
  "ad_units": {
    "sidebar_display": "XXXXXXXXXX",
    "in_article": "XXXXXXXXXX"
  },
  "page_rules": {
    "intent=informational": ["sidebar_display", "in_article"],
    "intent=comparison":    ["sidebar_display"],
    "intent=tutorial":      ["sidebar_display", "in_article"]
  }
}
```

### 3.4 W-8BEN (Hong Kong Publishers)

Required to receive payments as a non-US person:

1. In AdSense → Payments → Tax info → Submit tax form
2. Select: **W-8BEN** (individual, NOT W-8BEN-E for companies)
3. Fields to fill:
   - Name: your legal name
   - Country: Hong Kong
   - Permanent address: HK address
   - Tax ID: HKID number (line 6a) or leave blank if no US TIN
4. Treaty benefit: HK has **no US tax treaty**. Withholding is 30% on US-source income, but most AdSense revenue is not classified as US-source → effective withholding is typically 0%
5. Payment: wire transfer to HK bank; minimum payout $100 USD

---

## 4. Affiliate Programs

### 4.1 Priority Programs (Apply First)

| Program | Commission | Cookie | Apply At |
|---|---|---|---|
| Surfer SEO | 25% recurring lifetime | 30 days | surfer.io/affiliate |
| Writesonic | 30% recurring 12 months | 60 days | writesonic.com/affiliates |
| Jasper AI | 25% recurring 12 months | 45 days | jasper.ai/affiliate |
| ElevenLabs | 22% recurring 12 months | 30 days | elevenlabs.io/affiliates |
| Notion | $10 flat per free signup | 90 days | notion.so/affiliate |

### 4.2 Secondary Programs

| Program | Commission | Notes |
|---|---|---|
| Semrush | $200 per sale | High ticket, review-style content needed |
| Ahrefs | 20% recurring | Quality review required for approval |
| Copy.ai | 30% recurring | Automation niche |
| Descript | 15% per sale | Video/podcast editing, fits SPEC-04 audience |
| Zapier | Variable | Automation workflows |

### 4.3 Application Process

For each program:
1. Apply with website URL (must have 10+ relevant articles live)
2. Description: "AI tools comparison site for developers and marketers"
3. Submit any required tax form (usually W-8BEN or equivalent)
4. Upon approval: get tracking links → add to `monetisation/affiliate_map/`
5. Run `python apps/bot/mdx_writer.py --update-ctas` to inject links into existing articles

---

## 5. CTA Injection Configuration

### 5.1 Affiliate Map File Format

```json
// monetisation/affiliate_map/best-ai-writing-tools.json
{
  "slug": "best-ai-writing-tools",
  "primary_cta": {
    "partner": "jasper",
    "url": "https://jasper.ai/?via=YOUR_REF",
    "anchor": "Try Jasper Free for 7 Days →",
    "placement": "top",
    "variant": "A"
  },
  "secondary_cta": {
    "partner": "writesonic",
    "url": "https://writesonic.com/pricing?via=YOUR_REF",
    "anchor": "Compare Writesonic Plans",
    "placement": "inline"
  },
  "bottom_cta": {
    "partner": "jasper",
    "url": "https://jasper.ai/?via=YOUR_REF",
    "anchor": "Start Your Free Trial →",
    "placement": "bottom"
  },
  "disclosure_required": true
}
```

### 5.2 A/B Testing (Phase 3+)

`variant` field controls active test. `apps/bot/cta_rotator.py` swaps variants weekly:
- Variant A: action text ("Start Free Trial →")
- Variant B: benefit text ("Save 30% on Your First Month")
- Variant C: social proof ("Join 50,000+ Teams")

CTR tracked via UTM params in affiliate URLs.

---

## 6. Revenue Tracking

### 6.1 Manual Log

Monthly update to `monetisation/revenue_log.csv`:

```csv
month,adsense_usd,jasper_usd,writesonic_usd,surfer_usd,elevenlabs_usd,total_usd
2026-05,0,0,0,0,0,0
```

### 6.2 Revenue Targets

| Month | Articles Live | AdSense | Affiliate | Total |
|---|---|---|---|---|
| 1–2 | 20 | $0 | $0 | $0 |
| 3 | 50 | $20–$50 | $0–$50 | $20–$100 |
| 4–5 | 80 | $50–$150 | $100–$300 | $150–$450 |
| 6 | 120 | $100–$300 | $300–$600 | $400–$900 |
| 12 | 300+ | $300–$800 | $1,000–$3,000 | $1,300–$3,800 |

---

## 7. Compliance

| Requirement | Implementation |
|---|---|
| FTC affiliate disclosure | Sticky banner on every comparison page |
| GDPR cookie consent | CookieYes banner on first visit |
| Affiliate link transparency | `rel="sponsored"` on all affiliate `<a>` tags |
| AdSense policies | No click fraud, no incentivised clicks |

---

## 8. Payment Setup (Hong Kong)

| Method | Details |
|---|---|
| AdSense | Wire to HK bank. Min $100 USD. Monthly. |
| Affiliate networks | PayPal most common; ShareASale/Impact support wire |
| Payoneer (recommended) | Accept USD/EUR → HK bank monthly batch, low fees |

**Recommended:** Create Payoneer → link all affiliate networks → batch withdraw to HK bank monthly.

---

*Related: [README.md](../README.md) | [SPEC-01](./SPEC-01-content-bot.md) | [SPEC-02](./SPEC-02-web-system.md) | [SPEC-04](./SPEC-04-video-pipeline.md)*
