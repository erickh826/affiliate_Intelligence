# SPEC-05 — Deployment & Infrastructure

**Version:** 1.0 | **Updated:** 2026-09-30  
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
           data/keywords.db (status=published)
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

Runs daily at 02:00 UTC (`--batch 5`). `workflow_dispatch` stays available for a manual run. The workflow commits new MDX, FAQ JSON, affiliate maps, and `data/keywords.db`. It does not commit deletions under those paths, so a run cannot remove an article already on `main`.

GitHub turns scheduled workflows off on a public repository after 60 days without repository activity (`disabled_inactivity`). The `cron` key in the file does not fire while that state is set. Re-enable from the Actions tab or with `gh workflow enable bot-cron.yml`.

If any of the four API secrets is empty, the job fails before `main.py` runs and does not commit. Per-article generation errors are already handled inside the bot (that keyword is marked `failed`, the batch continues, exit code stays 0). `VERCEL_DEPLOY_HOOK_URL` is optional: an empty hook does not fail the job. A push to `main` still deploys when the Vercel Git integration is connected. The hook URL is not passed into the bot step, so the hook is not called before the commit lands.

```yaml
name: Bot - Daily Article Generation

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: bot-daily-generation
  cancel-in-progress: false

env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  PERPLEXITY_API_KEY: ${{ secrets.PERPLEXITY_API_KEY }}
  FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}

jobs:
  generate:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Require GitHub Actions API secrets
        run: |
          missing=0
          for name in OPENAI_API_KEY ANTHROPIC_API_KEY PERPLEXITY_API_KEY FIRECRAWL_API_KEY; do
            value="$(printenv "$name" || true)"
            if [ -z "$value" ]; then
              echo "::error title=Missing Actions secret::$name is empty. Cursor Runtime Secrets are not injected into GitHub Actions."
              missing=1
            fi
          done
          unset value
          if [ "$missing" -ne 0 ]; then
            exit 1
          fi
      - run: pip install -r apps/bot/requirements.txt
      - name: Run bot
        run: python apps/bot/main.py --batch 5
      - name: Checkpoint keyword database
        run: |
          python - <<'PY'
          import sqlite3
          conn = sqlite3.connect("data/keywords.db")
          conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
          conn.close()
          PY
          rm -f data/keywords.db-wal data/keywords.db-shm
      - name: Detect content changes
        id: content_changes
        run: |
          git add -- apps/web/content apps/web/content/faq monetisation/affiliate_map data/keywords.db
          while IFS= read -r path; do
            [ -z "$path" ] && continue
            git restore --staged -- "$path"
            echo "left existing file in place: $path"
          done < <(git diff --cached --diff-filter=D --name-only)
          if git diff --cached --quiet; then
            echo "changed=false" >> "$GITHUB_OUTPUT"
          else
            echo "changed=true" >> "$GITHUB_OUTPUT"
          fi
      - name: Commit new articles
        if: steps.content_changes.outputs.changed == 'true'
        run: |
          git config user.name "affiliate-bot"
          git config user.email "bot@users.noreply.github.com"
          git commit -m "feat(s01): add batch articles [$(date +%Y-%m-%d)]"
          git push origin HEAD:main
      - name: Trigger Vercel deploy
        if: success() && steps.content_changes.outputs.changed == 'true'
        continue-on-error: true
        env:
          VERCEL_DEPLOY_HOOK_URL: ${{ secrets.VERCEL_DEPLOY_HOOK_URL }}
        run: |
          if [ -z "$VERCEL_DEPLOY_HOOK_URL" ]; then
            echo "VERCEL_DEPLOY_HOOK_URL is unset. A push to main still deploys when the Vercel Git integration is connected."
            exit 0
          fi
          curl --fail-with-body -sS -X POST "$VERCEL_DEPLOY_HOOK_URL"
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

Set these in GitHub → repo → Settings → Secrets and variables → Actions. Cursor Runtime Secrets (used by Cloud Agents) are a different store. Actions cannot read them, and this spec does not list secret values.

| Secret | Used by | Required for bot cron |
|--------|---------|------------------------|
| `OPENAI_API_KEY` | bot-cron.yml | Yes |
| `ANTHROPIC_API_KEY` | bot-cron.yml | Yes |
| `PERPLEXITY_API_KEY` | bot-cron.yml | Yes |
| `FIRECRAWL_API_KEY` | bot-cron.yml | Yes |
| `VERCEL_DEPLOY_HOOK_URL` | bot-cron.yml | No. Empty skips the hook step. Vercel Git integration still deploys pushes to `main`. |
| `GSC_SERVICE_ACCOUNT_JSON` | gsc-feedback.yml | No. Phase 4 only. |

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
- [ ] All 4 API keys added as GitHub Actions secrets (Cursor Runtime Secrets are not visible to this workflow)
- [ ] `VERCEL_DEPLOY_HOOK_URL` added as a GitHub Actions secret (optional; a push to `main` still deploys via the Vercel Git integration)
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
