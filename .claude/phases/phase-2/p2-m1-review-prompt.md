# Phase 2 Milestone 1 — Review Prompt

**Use when:** M1 executor finished and set **NEEDS REVIEW** in `phase-2/execution-log.md`.  
**Executor prompt:** [p2-m1-claude-executor-prompt.md](./p2-m1-claude-executor-prompt.md)

Copy everything inside the fenced block below into your reviewer.

---

```markdown
# Review: Phase 2 M1 — MDX pipeline + article page

Review **Phase 2 Milestone 1** (T2.1 partial, T2.3, T2.4). Do not require M2 features (CTA, schema, homepage, category index).

## References

- `docs/SPEC-02-web-system.md` §3, §4.1, §8
- `.claude/phases/phase-2/p2-roadmap.md`
- Executor handoff + diff
- Fixture: `apps/web/content/ai-writing/best-ai-writing-tools-2026.mdx`

## Commands

```bash
cd apps/web
npm install
npm run lint
npm run test
npm run build
```

Optional dev smoke: `npm run dev` → open `/ai-writing/best-ai-writing-tools-2026`

## Checklist

### MDX pipeline (`lib/mdx.ts`)

- [ ] Scans `apps/web/content/{category}/*.mdx` (excludes `faq/`)
- [ ] Parses frontmatter with all keys: `title`, `description`, `slug`, `category`, `intent`, `published_at`, `last_reviewed`, `author`, `affiliate_partner`, `schema_type`
- [ ] `getArticle`, `getAllArticles`, `getArticleSlugs` work
- [ ] `getFaq(slug)` reads `content/faq/{slug}.faq.json`
- [ ] Types align with `apps/bot/models.py` `Frontmatter` / `FAQItem`

### Article page

- [ ] Route: `app/[category]/[slug]/page.tsx`
- [ ] `generateStaticParams` covers existing MDX files
- [ ] `generateMetadata` sets title + description
- [ ] Renders H1, byline, dates, body, FAQ section
- [ ] `notFound()` for invalid slug
- [ ] Server Component (no unnecessary `"use client"`)

### Scaffold

- [ ] TypeScript strict
- [ ] Tailwind configured; dark baseline reasonable
- [ ] ESLint / Prettier present
- [ ] `npm run build` succeeds (SSG)

### Tests

- [ ] Vitest (or project test runner) covers loader against sample fixture
- [ ] Tests pass in CI-local run

### Scope control (M1)

- [ ] No requirement for CTA injector, JSON-LD, category index, E-E-A-T pages yet
- [ ] Root homepage may remain placeholder

### Docs

- [ ] `phase-2/execution-log.md` updated with NEEDS REVIEW note
- [ ] M1 not marked COMPLETED before this review

## Verdict

### APPROVE

M1 complete. Mark M1 **COMPLETED** in execution-log; unblock **M2** planning.

### APPROVE WITH NOTES

COMPLETED after notes fixed or deferred (tag P1 vs P2).

### REJECT

Blocking issues with file path and required fix.

## If APPROVE

Update `.claude/phases/phase-2/execution-log.md` (M1 COMPLETED, date, build/test counts) and `.claude/phases/phase-2/manual.md` if present.
```
