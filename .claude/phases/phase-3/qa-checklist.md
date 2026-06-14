# Phase 3 — QA Checklist

**Phase:** 3 — Monetisation System (SPEC-03)
**Status:** NOT STARTED

---

## AdSense Requirements

- [ ] Pre-AdSense checklist all items verified (SPEC-02 §9)
- [ ] AdSense verification snippet in `<head>`
- [ ] AdSense application submitted
- [ ] Ad unit config matches SPEC-03 §3.3 (publisher_id, ad_units, page_rules)
- [ ] Page-level ad rules: informational = sidebar + in-article; comparison = sidebar only
- [ ] AdSense script loads conditionally per page intent
- [ ] AdSense auto-ads suppressed above fold on comparison pages

## Affiliate Requirements

- [ ] 3+ affiliate programs applied to
- [ ] At least 1 affiliate account approved
- [ ] Affiliate map JSON exists for each published article
- [ ] Primary CTA: correct partner, URL with UTM, anchor text
- [ ] Secondary CTA: correct placement (inline)
- [ ] Bottom CTA: correct placement (before FAQ)
- [ ] All affiliate links: `rel="sponsored"`
- [ ] All affiliate links: disclosure text present

## CTA A/B Testing

- [ ] `cta_rotator.py` swaps variants weekly
- [ ] Variant A/B/C text matches SPEC-03 §5.2
- [ ] Variant stored in keywords.db `cta_variant` column
- [ ] UTM params track CTR per variant

## Revenue Tracking

- [ ] `revenue_log.csv` created with correct columns
- [ ] Current month seeded with zeros
- [ ] Manual update process documented

## Compliance

- [ ] FTC affiliate disclosure on every comparison page
- [ ] Sticky disclosure banner visible on comparison pages
- [ ] Cookie consent banner (CookieYes or equivalent)
- [ ] AdSense/GA4 only load after consent
- [ ] GDPR compliant: granular consent categories
- [ ] `rel="sponsored"` on all affiliate `<a>` tags
- [ ] No incentivised click language

## Tax & Payment

- [ ] W-8BEN submitted to Google (HK individual)
- [ ] Payment method configured: wire to HK bank
- [ ] Payoneer account created (recommended for affiliate networks)

## Code Quality

- [ ] `black` + `ruff` pass on `bot/cta_rotator.py`
- [ ] Prettier + ESLint pass on new React components
- [ ] Type hints on `cta_rotator.py` public functions
- [ ] No `any` types in new components
- [ ] Tailwind only; no inline styles
- [ ] No code comments
