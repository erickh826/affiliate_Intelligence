# Phase 3 Plan — Monetisation System (SPEC-03)

**Status:** DRAFT
**Spec:** `docs/SPEC-03-monetisation.md`  
**Timeline:** Weeks 4–8
**Depends on:** Phase 1 (articles published), Phase 2 M3 + deployment (site live at custom domain, E-E-A-T pages)

**Account applications:** [.claude/account-applications-checklist.md](../../account-applications-checklist.md)

**Contract dependency:** Phase 3 must treat Phase 1 `ArticleArtifact.affiliate_map`, `Frontmatter.affiliate_partner`, and `keywords.affiliate_partner` as the monetisation handoff contract. Affiliate map JSON fields should stay compatible with the `P1-T6` writer output and Phase 2 CTA injector.

---

## Objective

Set up Google AdSense display advertising and affiliate marketing. Apply for programs, configure CTA injection, implement revenue tracking, and establish compliance (FTC, GDPR).

---

## Deliverables

| # | Deliverable | File/Dir | Acceptance Criteria |
|---|---|---|---|
| 1 | AdSense application submitted | — | Verification snippet in layout.tsx, application filed |
| 2 | Ad config | `monetisation/adsense_config.json` | Publisher ID, ad units, page rules per intent |
| 3 | Affiliate accounts (3+) | — | Approved for Surfer, Writesonic, Jasper (or equivalents) |
| 4 | Affiliate map files | `monetisation/affiliate_map/*.json` | Per-article CTA config: primary, secondary, bottom |
| 5 | CTA rotator script | `bot/cta_rotator.py` | Weekly A/B variant swap, UTM tracking |
| 6 | Revenue log | `monetisation/revenue_log.csv` | Monthly tracking per partner |
| 7 | Cookie consent | `web/components/CookieConsent.tsx` | CookieYes integration, GDPR compliant |
| 8 | Affiliate disclosure | `web/components/AffiliateDisclosure.tsx` | Sticky banner on comparison pages |
| 9 | W-8BEN filed | — | Tax form submitted to Google for HK publisher |

---

## Task Breakdown

### T3.1 — Pre-AdSense checklist verification
- Verify all E-E-A-T pages live (about, contact, privacy, disclaimer)
- Verify 20+ articles indexed in GSC
- Verify custom domain with HTTPS
- Verify mobile-responsive at 375px
- Verify Core Web Vitals passing

### T3.2 — AdSense application
- Create AdSense account
- Paste verification snippet into `web/app/layout.tsx` `<head>`
- Submit application
- Document: expected 2–4 week review period

### T3.3 — Ad unit configuration
- Create `monetisation/adsense_config.json` per SPEC-03 §3.3
- Implement page-level ad rules: informational = full auto-ads, comparison = sidebar only
- Add AdSense script to layout (conditional per page intent)

### T3.4 — Affiliate program applications
- Apply to priority programs: Surfer SEO, Writesonic, Jasper AI, ElevenLabs, Notion
- Use site URL + description: "AI tools comparison site for developers and marketers"
- Submit W-8BEN where required
- Track application status in notes below

### T3.5 — Affiliate map configuration
- For each published article, create `monetisation/affiliate_map/{slug}.json`
- Map fields: `primary_cta`, `secondary_cta`, `bottom_cta`, `disclosure_required`
- Match affiliate partner to article topic (e.g. writing tool article → Jasper CTA)
- All URLs include UTM params for CTR tracking
- Keep affiliate map shape compatible with Phase 1 `ArticleArtifact.affiliate_map` and Phase 2 CTA injection.

### T3.6 — CTA rotator script
- `bot/cta_rotator.py`: weekly cron that swaps `cta_variant` in keywords.db
- Variant A: action text ("Start Free Trial →")
- Variant B: benefit text ("Save 30% on Your First Month")
- Variant C: social proof ("Join 50,000+ Teams")
- Log variant assignments

### T3.7 — Revenue tracking
- Create `monetisation/revenue_log.csv` with columns per SPEC-03 §6.1
- Seed with current month (all zeros)
- Document: manual monthly update process until automation in later phase

### T3.8 — Cookie consent implementation
- Integrate CookieYes (or equivalent) consent banner
- `web/components/CookieConsent.tsx`
- Only load AdSense/GA4 after consent given
- GDPR compliant: granular consent categories

### T3.9 — Affiliate disclosure component
- `web/components/AffiliateDisclosure.tsx`
- Sticky banner on comparison pages (bottom of viewport)
- Text: "We may earn a commission if you click affiliate links."
- Dismissible but reappears on new page

### T3.10 — W-8BEN tax form
- Complete W-8BEN for Google AdSense (HK individual)
- Fields: legal name, HK address, HKID (or leave US TIN blank)
- HK has no US tax treaty → 30% withholding on US-source income (most AdSense is non-US source → 0%)
- Payment: wire to HK bank, min $100 USD

---

## Dependencies

| Dependency | Version | Purpose |
|---|---|---|
| CookieYes | SaaS | GDPR cookie consent |
| AdSense | SaaS | Display advertising |
| Affiliate networks | SaaS | Commission tracking |

*Note: Phase 3 is primarily configuration + business operations, not heavy coding.*

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AdSense application rejected | Medium | No display revenue for weeks | Ensure all checklist items pass before applying; resubmit after fixes |
| Affiliate applications rejected | Medium | Limited CTA options | Apply to 5+ programs, start with easiest (Notion $10 flat) |
| AdSense policy violation | Low | Account suspended | Review policies, no incentivised clicks, no thin content |
| Low affiliate conversion | High | Revenue below target | A/B test CTA variants, improve article quality, focus on high-intent keywords |
| Cookie consent blocks analytics | Medium | No traffic data | Default to analytics-only cookies accepted, granular consent |
