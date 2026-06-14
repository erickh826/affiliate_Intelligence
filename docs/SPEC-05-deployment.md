# SPEC-05 — Deployment & Infrastructure

**Version:** 1.0 | **Updated:** 2026-06-14  
**Related:** [SPEC-02](./SPEC-02-web-system.md) · [SPEC-01](./SPEC-01-content-bot.md) · [SPEC-03](./SPEC-03-monetisation.md)

---

## 1. Purpose

SPEC-05 defines how every moving part of the system reaches production:

| Layer | How it runs |
|-------|-------------|
| Next.js website | Vercel — auto-deploy on git push to `main` |
| Python content bot | GitHub Actions cron — daily article generation |
| GSC feedback | GitHub Actions cron — weekly DB update |
| CI quality gate | GitHub Actions on every PR/push |

---

## 2. Prerequisites

Before deployment:

- [ ] Phase 2 M3 **COMPLETED** (E-E-A-T pages, sitemap, Core Web Vitals)
- [ ] Custom `.com` domain purchased (required for AdSense)
- [ ] GitHub repo exists and `apps/web/` builds cleanly (`npm run build`)
- [ ] `apps/bot/` tests pass (`pytest apps/bot/tests/`)

---

## 3. Web Deployment (Vercel)

### 3.1 Initial setup

1. Go to [vercel.com/new](https://vercel.com/new) → **Import Git Repository**
2. Select this monorepo
3. **Root Directory:** set to `apps/web` (critical — do not leave blank)
4. Framework: Next.js (auto-detected)
5. Build command: `npm run build` (default)
6. Output: `.next` (default)
7. Click **Deploy**

### 3.2 Environment variables

Set in Vercel project → Settings → Environment Variables:

| Variable | Example | Required |
|----------|---------|---------|
| `NEXT_PUBLIC_SITE_URL` | `https://yourdomain.com` | Yes |
| `NEXT_PUBLIC_SITE_NAME` | `AI Tools Hub` | Yes |
| `NEXT_PUBLIC_GA_MEASUREMENT_ID` | `G-XXXXXXXXXX` | Phase 3 |
| `NEXT_PUBLIC_ADSENSE_PUBLISHER_ID` | `ca-pub-XXXXXXXX` | Phase 3 |
| `NEXT_PUBLIC_FORMSPREE_ID` | `abcdefgh` | M3 (contact form) |

Set all for `Production` + `Preview` environments.

### 3.3 Custom domain

1. Vercel → Project → Settings → Domains → Add domain
2. Add `yourdomain.com` and `www.yourdomain.com`
3. Copy the CNAME/A record values Vercel provides
4. In your DNS provider: add the records
5. Vercel issues TLS certificate automatically (~5 min)
6. Update `NEXT_PUBLIC_SITE_URL` to the final domain

### 3.4 Auto-deploy trigger

Every `git push` to `main` that touches `apps/web/**` or `apps/web/content/**` triggers a Vercel rebuild. No manual action needed.

To trigger a deploy without a code change (e.g. new MDX content only):

```bash
curl -X POST "$VERCEL_DEPLOY_HOOK_URL"
```

Set `VERCEL_DEPLOY_HOOK_URL` in GitHub Secrets (see §5).

### 3.5 `next-sitemap` on deploy

`postbuild` script in `apps/web/package.json` runs automatically:

```json
"postbuild": "next-sitemap"
```

After deploy, verify at `https://yourdomain.com/sitemap.xml` and `https://yourdomain.com/robots.txt`.

---

## 4. Content Sync (Bot → Website)

### 4.1 Architecture

```
GitHub Actions cron
  → python apps/bot/main.py --batch 5
  → writes apps/web/content/{category}/{slug}.mdx
           apps/web/content/faq/{slug}.faq.json
           monetisation/affiliate_map/{slug}.json
  → git add + commit + push to main
  → Vercel auto-deploy triggered
```

### 4.2 Git write permissions in Actions

GitHub Actions uses the built-in `GITHUB_TOKEN` for git operations — no extra PAT needed when pushing to the same repo with `permissions: contents: write`.

```yaml
permissions:
  contents: write
```

### 4.3 Commit format

Bot commits follow the project convention:

```
feat(s01): add {N} articles [{slugs}]
```

Example:

```
feat(s01): add 5 articles [best-ai-writing-tools-2026, ...]
```

---

## 5. GitHub Actions Workflows

All workflows live in `.github/workflows/`.

### 5.1 CI — `ci.yml`

Runs on every push and PR to `main`.

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

### 5.2 Bot cron — `bot-cron.yml`

Runs daily at 02:00 UTC. Generates articles and commits MDX to repo.

```yaml
name: Bot — Daily Article Generation

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

permissions:
  contents: write

env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
  FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r apps/bot/requirements.txt
      - name: Run bot
        run: python apps/bot/main.py --batch 5
      - name: Commit new articles
        run: |
          git config user.name "affiliate-bot"
          git config user.email "bot@users.noreply.github.com"
          git add apps/web/content/ apps/web/content/faq/ monetisation/affiliate_map/
          git diff --cached --quiet || git commit -m "feat(s01): add batch articles [$(date +%Y-%m-%d)]"
          git push
      - name: Trigger Vercel deploy
        if: success()
        run: curl -X POST "${{ secrets.VERCEL_DEPLOY_HOOK_URL }}"
```

### 5.3 GSC feedback cron — `gsc-feedback.yml`

Runs weekly on Monday 03:00 UTC (Phase 4 — when `gsc_feedback.py` is fully implemented).

```yaml
name: GSC — Weekly Feedback

on:
  schedule:
    - cron: '0 3 * * 1'
  workflow_dispatch:

env:
  GSC_SERVICE_ACCOUNT_JSON: ${{ secrets.GSC_SERVICE_ACCOUNT_JSON }}

jobs:
  feedback:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r apps/bot/requirements.txt
      - run: python apps/bot/gsc_feedback.py
      - name: Commit DB changes
        run: |
          git config user.name "affiliate-bot"
          git config user.email "bot@users.noreply.github.com"
          git add data/keywords.db
          git diff --cached --quiet || git commit -m "chore(infra): gsc feedback update $(date +%Y-%m-%d)"
          git push
```

---

## 6. GitHub Secrets Required

Set in GitHub → repo → Settings → Secrets → Actions:

| Secret | Used by | When |
|--------|---------|------|
| `OPENAI_API_KEY` | bot-cron.yml | Phase 1+ |
| `ANTHROPIC_API_KEY` | bot-cron.yml | Phase 1+ |
| `PERPLEXITY_API_KEY` | bot-cron.yml | Phase 1+ |
| `FIRECRAWL_API_KEY` | bot-cron.yml | Phase 1+ |
| `VERCEL_DEPLOY_HOOK_URL` | bot-cron.yml | Phase 2+ |
| `GSC_SERVICE_ACCOUNT_JSON` | gsc-feedback.yml | Phase 4 |

---

## 7. Deployment Checklist (Pre-Phase 3)

Run through this after M3 is complete:

### Web
- [ ] Vercel project created, root dir set to `apps/web`
- [ ] All env vars set in Vercel (Production + Preview)
- [ ] Custom domain added, DNS propagated, HTTPS active
- [ ] `https://yourdomain.com` loads without error
- [ ] `https://yourdomain.com/sitemap.xml` exists
- [ ] `https://yourdomain.com/robots.txt` exists
- [ ] `https://yourdomain.com/about` loads
- [ ] `https://yourdomain.com/privacy-policy` loads
- [ ] Article page loads with CTA and JSON-LD in source

### Bot pipeline
- [ ] All 4 API keys added to GitHub Secrets
- [ ] `VERCEL_DEPLOY_HOOK_URL` added to GitHub Secrets
- [ ] `bot-cron.yml` committed to `.github/workflows/`
- [ ] Manual trigger (`workflow_dispatch`) tested once — confirms articles generate and commit
- [ ] Vercel rebuild triggered after bot commit

### CI
- [ ] `ci.yml` committed to `.github/workflows/`
- [ ] CI passes on `main` branch

### AdSense application gate (SPEC-02 §9)
- [ ] 15+ pages indexed in GSC (submit sitemap first, wait ~1 week)
- [ ] All E-E-A-T pages live (`/about`, `/contact`, `/privacy-policy`, `/disclaimer`)
- [ ] No thin/placeholder content on any indexed page
- [ ] Mobile-responsive at 375px
- [ ] Core Web Vitals pass in PageSpeed Insights

---

## 8. Rollback

| Problem | Rollback |
|---------|---------|
| Bad deploy breaks site | Vercel → Deployments → previous deploy → **Promote to Production** |
| Bot commit breaks build | `git revert HEAD` → push → Vercel rebuilds |
| Bot generates bad content | Set `status = 'error'` in `keywords.db` for affected slugs; delete MDX files; push |

---

*Related: [SPEC-01](./SPEC-01-content-bot.md) · [SPEC-02](./SPEC-02-web-system.md) · [SPEC-03](./SPEC-03-monetisation.md)*
