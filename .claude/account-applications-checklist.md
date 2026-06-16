# Account Applications & Setup Checklist

**Purpose:** Single master checklist — work through top to bottom before Phase 3 starts.  
**Specs:** [SPEC-05](../../docs/SPEC-05-deployment.md) · [SPEC-03](../../docs/SPEC-03-monetisation.md) · [SPEC-02](../../docs/SPEC-02-web-system.md) §9

---

## Stage 1 — Domain & Hosting (do now, before M3)

| # | Task | Where | Notes |
|---|------|--------|-------|
| 1.1 | Purchase `.com` domain | Namecheap / Cloudflare Registrar | ~$10/yr; AdSense hard requirement |
| 1.2 | Connect domain DNS to Vercel | Vercel → Settings → Domains | Vercel gives you CNAME/A records |
| 1.3 | Verify HTTPS is active | `https://yourdomain.com` | Vercel auto-provisions TLS |
| 1.4 | Update `NEXT_PUBLIC_SITE_URL` in Vercel env vars | Vercel → Project → Settings → Env | Must match exact domain with `https://` |

---

## Stage 2 — Analytics & Search Console (do with M3)

| # | Task | Where | Notes |
|---|------|--------|-------|
| 2.1 | Create GA4 property | analytics.google.com | Get `G-XXXXXXXXXX` measurement ID |
| 2.2 | Add `NEXT_PUBLIC_GA_MEASUREMENT_ID` to Vercel env | Vercel | Paste GA4 measurement ID |
| 2.3 | Add GA4 `<script>` to `apps/web/app/layout.tsx` | Code | Phase 3 implementation task |
| 2.4 | Add site to Google Search Console | search.google.com/search-console | Choose "Domain" property type |
| 2.5 | Verify GSC ownership via DNS TXT record | Your DNS provider | GSC gives you the TXT record value |
| 2.6 | Submit sitemap | GSC → Sitemaps → `https://yourdomain.com/sitemap.xml` | After Vercel deploy with `next-sitemap` |
| 2.7 | Wait for 15+ pages indexed | GSC → Coverage | ~1–2 weeks; required before AdSense |

---

## Stage 3 — Payment Setup (do before AdSense + affiliates pay out)

| # | Task | Where | Notes |
|---|------|--------|-------|
| 3.1 | Create Payoneer account | payoneer.com | Recommended hub for all affiliate payments |
| 3.2 | Link Payoneer → HK bank account | Payoneer → Withdraw → Bank Transfer | Batch monthly withdrawal |
| 3.3 | Create PayPal account (backup) | paypal.com | Some programs only support PayPal |
| 3.4 | Note: AdSense pays direct wire to HK bank | AdSense → Payments → Payment method | Min $100 USD per month |

---

## Stage 4 — Google AdSense (start after 20+ articles indexed)

| # | Task | Where | Gate |
|---|------|--------|------|
| 4.1 | Confirm pre-AdSense checklist passes | SPEC-02 §9 | All items ticked |
| 4.2 | Create AdSense account | adsense.google.com | Google account required |
| 4.3 | Enter site URL | AdSense signup | Use exact domain |
| 4.4 | Paste AdSense verification snippet into `layout.tsx` | Code | Phase 3 task |
| 4.5 | Submit W-8BEN tax form | AdSense → Payments → Tax info | Select W-8BEN (individual), HK address, HKID |
| 4.6 | Wait for review | Email notification | Typically 2–4 weeks |
| 4.7 | Upon approval: create ad units in AdSense dashboard | AdSense → Ads | Get unit IDs |
| 4.8 | Add `ca-pub-XXXXXXXX` to `NEXT_PUBLIC_ADSENSE_PUBLISHER_ID` | Vercel env | |
| 4.9 | Add ad unit IDs to `monetisation/adsense_config.json` | Code | |
| 4.10 | Enable Auto-ads on informational pages only | SPEC-03 §3.3 | |

---

## Stage 5 — Affiliate Programs (apply when 10+ relevant articles live)

### Priority tier (apply first)

| # | Program | Commission | Apply at | Status |
|---|---------|------------|----------|--------|
| 5.1 | **Jasper AI** | 25% recurring 12mo | jasper.ai/affiliate | ☐ Not applied |
| 5.2 | **Writesonic** | 30% recurring 12mo | writesonic.com/affiliates | ☐ Not applied |
| 5.3 | **Surfer SEO** | 25% recurring lifetime | surfer.io/affiliate | ☐ Not applied |
| 5.4 | **ElevenLabs** | 22% recurring 12mo | elevenlabs.io/affiliates | ☐ Not applied |
| 5.5 | **Notion** | $10/free signup | notion.so/affiliate | ☐ Not applied |

### Secondary tier (apply after first affiliate is approved)

| # | Program | Commission | Apply at | Status |
|---|---------|------------|----------|--------|
| 5.6 | Semrush | $200/sale | semrush.com/partner | ☐ Not applied |
| 5.7 | Ahrefs | 20% recurring | ahrefs.com/affiliates | ☐ Not applied |
| 5.8 | Copy.ai | 30% recurring | copy.ai/affiliates | ☐ Not applied |
| 5.9 | Descript | 15%/sale | descript.com/affiliates | ☐ Not applied |

### For each affiliate application

Use this description when applying:
> "AI tools comparison and tutorial site for developers and marketers. Currently publishing long-form comparison articles on writing, SEO, and productivity tools. Traffic growing via programmatic SEO."

After approval:
- [ ] Get tracking link(s)
- [ ] Add to `monetisation/affiliate_map/{slug}.json` for relevant articles
- [ ] W-8BEN or local equivalent if required by the program

---

## Stage 6 — Tax (one-time, before first payout)

| # | Task | Notes |
|---|------|-------|
| 6.1 | AdSense W-8BEN | Filed during Stage 4.5 |
| 6.2 | W-8BEN for each affiliate network | Impact, ShareASale, etc. usually ask during signup |
| 6.3 | Keep Payoneer tax docs | Payoneer may issue 1099 if US-source income |

HK has no US tax treaty. Withholding is 30% on US-source income, but most AdSense/affiliate revenue is not US-source — effective withholding typically 0%. See SPEC-03 §3.4 for details.

---

## Stage 7 — GitHub Actions (bot running)

| # | Task | Where |
|---|------|--------|
| 7.1 | Add `OPENAI_API_KEY` to GitHub Secrets | GitHub → repo → Settings → Secrets → Actions |
| 7.2 | Add `ANTHROPIC_API_KEY` | GitHub Secrets |
| 7.3 | Add `PERPLEXITY_API_KEY` | GitHub Secrets |
| 7.4 | Add `FIRECRAWL_API_KEY` | GitHub Secrets |
| 7.5 | Add `VERCEL_DEPLOY_HOOK_URL` | GitHub Secrets (get from Vercel → Project → Settings → Git → Deploy Hooks) |
| 7.6 | Commit `ci.yml` to `.github/workflows/` | SPEC-05 §5.1 |
| 7.7 | Commit `bot-cron.yml` to `.github/workflows/` | SPEC-05 §5.2 |
| 7.8 | Manual trigger `bot-cron.yml` via `workflow_dispatch` once | GitHub → Actions → Bot cron → Run workflow |

---

## Summary: Unlock Sequence

```
Stage 1 (Domain)  done 
    ↓
Stage 2 (GSC + GA4) ← submit sitemap, wait for indexing
    ↓
Stage 3 (Payment accounts) ← parallel, takes 1–3 days
    ↓
Stage 7 (GitHub Actions) ← bot starts generating articles
    ↓  ← wait until 10+ articles indexed
Stage 5 (Affiliate applications) ← takes 3–14 days to approve
    ↓  ← wait until 20+ articles indexed
Stage 4 (AdSense application) ← takes 2–4 weeks to approve
    ↓
Stage 6 (Tax forms) ← triggered by first payout
```

---

## Status column legend

| Symbol | Meaning |
|--------|---------|
| ☐ Not applied | Haven't started |
| ⏳ Applied | Submitted, waiting for approval |
| ✅ Approved | Live and operational |
| ❌ Rejected | Need to re-apply or investigate |
