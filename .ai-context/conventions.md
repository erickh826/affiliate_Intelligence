# Conventions

**Last updated:** 2026-05-12

---

## Applicability Status (Important)

- **Active now:** repository-level documentation, naming clarity, secret hygiene, and spec-first workflow.
- **Planned / activates with implementation folders:** Python rules for `apps/bot/` and TypeScript rules for `apps/web/`.
- If a command references a folder or config that does not exist yet, treat it as future-state guidance.

---

## Active Conventions (Current Repo)

### Documentation and Specs
- `SPEC-01` to `SPEC-04` are implementation source of truth.
- `.ai-context/` provides condensed guidance and should not override specs.
- Update related spec first when requirements change.

### Security and Secrets
- Never commit `.env` or secret-bearing files.
- Keep credential examples only in `.env.example` (blank values).
- Never print API keys in logs or sample outputs.

### Git Hygiene
- Use Conventional Commits where possible.
- Keep commits focused by concern (`docs`, `spec`, `infra`, etc.).
- Avoid coupling speculative implementation changes with planning docs.

---

## Python (apps/bot/) — Planned Conventions

### Style
- **Formatter:** `black` (line-length 88)
- **Linter:** `ruff` (replace flake8 + isort)
- **Type hints:** required on all public function signatures
- **Docstrings:** Google style on public functions; omit on private helpers
- **Max concurrent LLM calls:** 3 (enforced by `asyncio.Semaphore(3)`)

### Naming
| Object | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `keyword_manager.py` |
| Classes | `PascalCase` | `QualityGateChecker` |
| Functions | `snake_case` | `generate_outline()` |
| Constants | `UPPER_SNAKE` | `BANNED_PHRASES` |
| CLI entry | `main.py` | `python main.py --batch 3 --dry-run` |

### Imports Order (ruff auto)
1. `stdlib`
2. `third-party`
3. `local`

### Error Handling
- Use structured exceptions: `class PipelineError(Exception): pass`
- Never bare `except:` — always catch specific exceptions
- LLM call failures → retry with exponential backoff (max 3)
- Quality gate FAIL → set `status=failed`, log reason, continue next article

### Testing (when `apps/bot/` exists)
- Framework: `pytest` + `pytest-asyncio`
- Run: `pytest apps/bot/tests/`
- Mock all external APIs (OpenAI, Anthropic, Firecrawl, Perplexity)
- No network calls in CI

---

## TypeScript / React (apps/web/) — Planned Conventions

### Style
- **Formatter:** Prettier (printWidth 80, singleQuote true, trailingComma all)
- **Linter:** ESLint (next/core-web-vitals config)
- **Strict mode:** `"strict": true` in tsconfig.json

### Naming
| Object | Convention | Example |
|---|---|---|
| Files / dirs | `kebab-case.tsx` | `affiliate-cta.tsx` |
| Components | `PascalCase` export | `AffiliateCTA` |
| Hooks | `useCamelCase` | `useGscData` |
| Utils | `camelCase` | `injectCta()` |
| Types / Interfaces | `PascalCase` | `ArticleFrontmatter` |
| Env vars | `NEXT_PUBLIC_SCREAMING_SNAKE` | `NEXT_PUBLIC_SITE_URL` |

### Component Rules
- One component per file
- Server Components by default; add `"use client"` only when needed (state, effects, event handlers)
- Props: define `interface ComponentNameProps` above the component
- No inline styles; Tailwind utility classes only
- No `any` — use `unknown` + type guard

### Import Order (ESLint import plugin)
1. React / Next
2. Third-party
3. `@/` aliases (components, lib)
4. Relative (`./`, `../`)

### Testing (when `apps/web/` exists)
- Framework: Vitest + React Testing Library
- Run: `npm run test`
- Mock `next/`, external APIs
- Target: critical paths (CTA injection, schema builder, MDX render)

---

## File Naming (Cross-Project)

| Type | Convention | Example |
|---|---|---|
| MDX articles | `{slug}.mdx` | `best-ai-writing-tools.mdx` |
| FAQ JSON | `{slug}.faq.json` | `best-ai-writing-tools.faq.json` |
| Affiliate map | `{slug}.json` | `best-ai-writing-tools.json` |
| Video scripts | `{slug}.txt` | `best-ai-writing-tools.txt` |
| DB file | `keywords.db` | SQLite in `data/` |

---

## Git & Commits

### Branch Naming
- `feature/<spec>-<short-desc>` → `feature/s01-keyword-selector`
- `fix/<short-desc>` → `fix/quality-gate-wordcount`
- `phase/<number>-<desc>` → `phase/04-video-pipeline`

### Commit Format (Conventional Commits)
```
<type>(<scope>): <description>

[optional body]
```

| Type | When |
|---|---|
| `feat` | New feature per spec |
| `fix` | Bug fix |
| `refactor` | Code restructure, no behaviour change |
| `docs` | Spec or doc update |
| `test` | Add / update tests |
| `chore` | Build, CI, deps |

**Scope** = spec or module: `s01`, `s02`, `s03`, `s04`, `web`, `bot`, `infra`

Examples:
- `feat(s01): add keyword selector with volume/difficulty priority`
- `fix(s02): correct canonical URL for category pages`
- `docs(s03): update affiliate CTA variant descriptions`

### Commit Guardrails
- Never commit `.env` files
- Never commit `node_modules/`, `__pycache__/`, `.next/`
- Run linters before commit **only for existing stacks**:
  - Python stack present: `ruff check apps/bot/`
  - Web stack present: `npx eslint apps/web/`

---

## MDX Frontmatter

All bot-generated MDX must include:

```yaml
---
title: "string"
description: "140-165 chars"
slug: "kebab-case"
category: "kebab-case"
intent: "comparison|informational|tutorial"
published_at: "YYYY-MM-DD"
last_reviewed: "YYYY-MM-DD"
author: "string"
affiliate_partner: "string"
schema_type: "Article"
---
```

No extra fields without updating `data-schema.md` first.

---

## API Key Safety
- All keys in `.env` (gitignored)
- `.env.example` lists required keys with blank values
- Never log, print, or commit API keys
- Use `os.environ["KEY"]` in Python; `process.env.KEY` in Node
