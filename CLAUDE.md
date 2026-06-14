# CLAUDE.md — Agent Entry for Claude Code

**Last updated:** 2026-05-12

---

## Project: Affiliate Intelligence (Programmatic SEO Content Machine)

You are working on an automated content publishing system that generates AI tool comparison articles, publishes them on a Next.js website, and monetises via AdSense + affiliate marketing.

---

## Context Files (READ FIRST)

| File | Purpose |
|---|---|
| `.ai-context/project.md` | Project overview, tech stack, timeline |
| `.ai-context/conventions.md` | Coding style, naming, commit format |
| `.ai-context/architecture.md` | System diagram, data flow, failure modes |
| `.ai-context/data-schema.md` | `keywords` table — all columns, types, constraints |

---

## Spec Files (Authoritative)

When implementing, always refer to the relevant SPEC:

| Spec | Scope |
|---|---|
| `docs/SPEC-01-content-bot.md` | Python content pipeline (keyword selector → research → outline → write → QA → MDX) |
| `docs/SPEC-02-web-system.md` | Next.js site (SSG, MDX rendering, CTA injection, SEO, GSC loop) |
| `docs/SPEC-03-monetisation.md` | AdSense + affiliate setup, CTA config, revenue tracking |
| `docs/SPEC-04-video-pipeline.md` | Article-to-video pipeline (Phase 4) |
| `docs/SPEC-05-deployment.md` | Vercel deploy, GitHub Actions cron, CI/CD, content sync |

**Rule:** SPEC files are the source of truth. If code and spec disagree, fix the code.

---

## Key Rules

1. **Python code** → `apps/bot/` directory. Use `black` + `ruff`. Type hints required.
2. **TypeScript/React code** → `apps/web/` directory. Use Prettier + ESLint. Strict mode.
3. **Never commit `.env`** files or API keys.
4. **Quality gate is non-negotiable** — no article bypasses the checks in SPEC-01 §7.
5. **No comments in code** unless explicitly asked.
6. **Commit format:** Conventional Commits with spec scope (`feat(s01):`, `fix(s02):`, etc.).
7. **Run linters** before committing: `ruff check apps/bot/` and `npx eslint apps/web/`
8. **Run tests** before committing: `pytest apps/bot/tests/` and `npm run test --prefix apps/web/`

---

## Architecture Quick Reference

```
keywords.db → SPEC-01 Bot → apps/web/content/*.mdx → SPEC-02 Next.js → Public Site
                                                              ↓
                                                    AdSense + Affiliate CTAs (SPEC-03)
                                                              ↓
                                                    GSC Feedback Loop → keywords.db
                                                    (needs_rewrite → back to SPEC-01)
```

---

## Common Tasks

- **Add a new pipeline step:** Update SPEC-01 first, then implement in `apps/bot/`, then update `architecture.md`
- **Add a new page type:** Update SPEC-02 first, then implement in `apps/web/app/`
- **Add a new affiliate program:** Update SPEC-03 §4, add entry to affiliate map files
- **Schema change:** Update `data-schema.md` + relevant SPEC, write migration in `data/migrations/`
