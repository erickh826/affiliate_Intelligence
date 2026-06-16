# Phase 2 — Implementation Roadmap

**Spec:** `docs/SPEC-02-web-system.md`  
**Plan:** [plan.md](./plan.md)  
**Depends on:** Phase 1 COMPLETED (`apps/bot` → `apps/web/content/`)

Phase 2 is split into **three milestones** so Claude (or another agent) can implement and review in focused passes.

---

## Milestones

| Milestone | Tasks | Goal | Prompts |
|-----------|-------|------|---------|
| **M1** | T2.1 (partial), T2.3, T2.4 | Render bot MDX at `/[category]/[slug]` | ✅ COMPLETED |
| **M2** | T2.2 (full), T2.5, T2.6, T2.7, T2.8 | Homepage, category index, CTA, schema, components | ✅ COMPLETED |
| **M3** | T2.9, T2.10, T2.11, T2.12 (full) | E-E-A-T pages, SEO, GSC stub, full test suite | ⚠ NEEDS REVIEW |

---

## M1 smoke test (Definition of Done)

After **M1** is reviewed and approved:

```bash
cd apps/web
npm install
npm run build
npm run dev
# Browser: http://localhost:3000/ai-writing/best-ai-writing-tools-2026
```

Must render the existing file:

- `apps/web/content/ai-writing/best-ai-writing-tools-2026.mdx`
- FAQ from `apps/web/content/faq/best-ai-writing-tools-2026.faq.json` (display section; schema in M2)

---

## Contract alignment (all milestones)

Web `ArticleFrontmatter` must match Phase 1 `Frontmatter` in `apps/bot/models.py`:

`title`, `description`, `slug`, `category`, `intent`, `published_at`, `last_reviewed`, `author`, `affiliate_partner`, `schema_type`

Bot writes JSON-string values in YAML frontmatter fences; parser must produce plain strings.

---

## Path conventions

| Artifact | Path |
|----------|------|
| MDX articles | `apps/web/content/{category}/{slug}.mdx` |
| FAQ JSON | `apps/web/content/faq/{slug}.faq.json` |
| Affiliate map | `monetisation/affiliate_map/{slug}.json` (repo root; M2) |
| Web app | `apps/web/` (not `web/`) |

---

## Review policy

- Each milestone: implement → **NEEDS REVIEW** in `execution-log.md` → run review prompt → **COMPLETED** → next milestone.
- Do not start M2 until M1 review passes.
