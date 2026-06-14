# AGENTS.md — Agent Entry for OpenCode / General AI Agents

**Last updated:** 2026-05-12

---

## Project: Affiliate Intelligence

Automated content publishing system that generates AI tool comparison articles, publishes them on a Next.js website, and monetises via AdSense + affiliate marketing. Video pipeline in Phase 4.

---

## Context Files (Mandatory Reading)

| Order | File | Why |
|---|---|---|
| 1 | `.ai-context/project.md` | Project overview, tech stack, timeline |
| 2 | `.ai-context/conventions.md` | Coding style, naming, commit format |
| 3 | `.ai-context/architecture.md` | System diagram, data flow |
| 4 | `.ai-context/data-schema.md` | Database schema (keywords table) |

---

## Authoritative Specifications

| Spec | Covers |
|---|---|
| `docs/SPEC-01-content-bot.md` | Python pipeline: keyword selection → research → LLM writing → quality gate → MDX output |
| `docs/SPEC-02-web-system.md` | Next.js 14 site: SSG, CTA injection, SEO, GSC feedback loop |
| `docs/SPEC-03-monetisation.md` | AdSense + affiliate programs, CTA config, revenue tracking |
| `docs/SPEC-04-video-pipeline.md` | Article-to-video pipeline (Phase 4) |
| `docs/SPEC-05-deployment.md` | Vercel deploy, GitHub Actions cron, CI/CD, content sync |

**If code conflicts with a SPEC, the SPEC is correct. Fix the code.**

---

## Implementation Rules

### Python (apps/bot/)
- Formatter: `black` (88 char line)
- Linter: `ruff`
- Type hints on all public function signatures
- Max 3 concurrent LLM calls (`asyncio.Semaphore(3)`)
- No bare `except:` — catch specific exceptions
- LLM failures → retry 3x with exponential backoff
- Test: `pytest apps/bot/tests/`

### TypeScript (apps/web/)
- Formatter: Prettier (80 char, single quotes)
- Linter: ESLint (next/core-web-vitals)
- Strict TypeScript: `"strict": true`
- Server Components by default; `"use client"` only when needed
- No `any`; use `unknown` + type guards
- Tailwind only; no inline styles
- Test: `npm run test --prefix apps/web/`

### Cross-Cutting
- No code comments unless explicitly requested
- Never commit `.env` files or API keys
- Commit format: `<type>(<scope>): <description>` where scope = `s01`|`s02`|`s03`|`s04`|`web`|`bot`|`infra`
- Run linters + tests before every commit
- Schema changes: update `data-schema.md` + SPEC + write migration → then implement

---

## Architecture Summary

```
keywords.db ──► SPEC-01 Bot ──► apps/web/content/*.mdx ──► SPEC-02 Next.js ──► Vercel ──► Public
                                                                          │
                                                                    AdSense + Affiliate (SPEC-03)
                                                                          │
                                                                    GSC Feedback Loop
                                                                    (needs_rewrite → SPEC-01)
```

---

## Before Starting Any Task

1. Read the relevant SPEC file end-to-end
2. Check `.ai-context/data-schema.md` if touching the database
3. Follow naming/style in `.ai-context/conventions.md`
4. Run existing tests to ensure baseline passes
5. After changes: lint, test, verify
