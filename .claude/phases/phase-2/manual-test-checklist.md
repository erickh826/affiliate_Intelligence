# Phase 2 Manual Test Checklist

**Scope:** M1 baseline validation before or during M2 work  
**Primary target:** `apps/web/`  
**Current article fixture:** `/ai-writing/best-ai-writing-tools-2026`

---

## Scripts

### 1. Install dependencies

```bash
cd apps/web
npm install
```

### 2. Start dev server

```bash
cd apps/web
npm run dev
```

Default URL:

```text
http://localhost:3000
```

### 3. Run automated baseline checks

```bash
cd apps/web
npm run test
npm run build
```

### 4. Optional production smoke check

```bash
cd apps/web
npm run start
```

Use this after `npm run build` if you want to verify the built app instead of only dev mode.

---

## Manual Test Items

### A. Article page render

URL:

```text
http://localhost:3000/ai-writing/best-ai-writing-tools-2026
```

Check:

- [ ] Page loads without 404, 500, or hydration error
- [ ] H1/title is visible once only
- [ ] Byline is visible
- [ ] Published date is visible
- [ ] Last reviewed date is visible when frontmatter provides it
- [ ] Main MDX body renders fully
- [ ] FAQ section renders
- [ ] No duplicate FAQ heading appears

### B. Homepage baseline

URL:

```text
http://localhost:3000/
```

Check:

- [ ] Homepage loads without runtime error
- [ ] Existing article link is clickable
- [ ] No broken layout in header/footer

### C. 404 behavior

URL:

```text
http://localhost:3000/ai-writing/not-a-real-slug
```

Check:

- [ ] Missing article returns a proper 404 page
- [ ] App does not crash on invalid slug

### D. Build / SSG baseline

Command:

```bash
cd apps/web
npm run build
```

Check:

- [ ] Build completes successfully
- [ ] Build output includes the article route `/ai-writing/best-ai-writing-tools-2026`
- [ ] No MDX parsing error occurs during build

### E. MDX + FAQ data loading

Source files:

- `apps/web/content/ai-writing/best-ai-writing-tools-2026.mdx`
- `apps/web/content/faq/best-ai-writing-tools-2026.faq.json`

Check:

- [ ] Frontmatter fields map correctly to page content
- [ ] FAQ JSON matches the article slug
- [ ] `content/faq/` is not treated as an article directory

### F. Mobile baseline

Viewport:

```text
375px width
```

Check:

- [ ] Title does not overflow
- [ ] Breadcrumb does not overlap or wrap badly
- [ ] FAQ cards stay within viewport width
- [ ] Main content remains readable without horizontal scrolling

---

## Recommended Order

1. Run `npm install`
2. Run `npm run test`
3. Run `npm run build`
4. Run `npm run dev`
5. Test article page
6. Test homepage
7. Test 404 route
8. Test mobile viewport

---

## Record Template

```md
## Manual Test Run

Date:
Tester:
Branch/commit:

Commands run:
- npm run test
- npm run build
- npm run dev

Results:
- Article page:
- Homepage:
- 404 route:
- Mobile:

Issues found:
- None / list issues
```
