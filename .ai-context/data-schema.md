# Data Schema — keyword_database

**Last updated:** 2026-05-12

---

## Status Note

- This schema is the **target contract** for `data/keywords.db` per `SPEC-01` to `SPEC-04`.
- If the database or migration files are not present yet, treat this as planned design.
- Schema updates must start from SPEC updates, then be propagated here.

---

## Storage

- **Engine:** SQLite 3
- **File:** `data/keywords.db`
- **Table:** `keywords`
- **Single-writer:** `bot/keyword_manager.py` (Python pipeline)
- **Readers:** `bot/gsc_feedback.py`, `web/lib/` (at build time via script)

---

## Table: `keywords`

| # | Column | Type | Constraints | Owner | Description |
|---|---|---|---|---|---|
| 1 | `id` | INTEGER | PK, AUTOINCREMENT | SPEC-01 | Unique row ID |
| 2 | `keyword` | TEXT | NOT NULL, UNIQUE | SPEC-01 | Target keyword phrase |
| 3 | `category` | TEXT | NOT NULL | SPEC-01 | Site category slug (kebab-case) |
| 4 | `intent` | TEXT | NOT NULL, CHECK(intent IN ('informational','comparison','tutorial')) | SPEC-01 | Search intent classification |
| 5 | `monthly_volume` | INTEGER | NOT NULL, DEFAULT 0 | SPEC-01 | Estimated monthly search volume |
| 6 | `difficulty` | INTEGER | NOT NULL, DEFAULT 0, CHECK(difficulty BETWEEN 0 AND 100) | SPEC-01 | Keyword difficulty score (0–100) |
| 7 | `status` | TEXT | NOT NULL, DEFAULT 'pending', CHECK(status IN ('pending','generating','published','needs_rewrite','failed')) | SPEC-01/02 | Article lifecycle status |
| 8 | `slug` | TEXT | UNIQUE | SPEC-01 | URL slug (kebab-case, matches MDX filename) |
| 9 | `published_at` | TEXT | NULL | SPEC-02 | ISO 8601 date (YYYY-MM-DD) when first published |
| 10 | `gsc_impressions` | INTEGER | DEFAULT 0 | SPEC-02 | Last 7-day impressions from GSC |
| 11 | `gsc_clicks` | INTEGER | DEFAULT 0 | SPEC-02 | Last 7-day clicks from GSC |
| 12 | `gsc_ctr` | REAL | DEFAULT 0.0 | SPEC-02 | CTR = clicks / impressions |
| 13 | `gsc_position` | REAL | DEFAULT 0.0 | SPEC-02 | Average search position |
| 14 | `affiliate_partner` | TEXT | NULL | SPEC-03 | Primary affiliate partner key (e.g. 'jasper') |
| 15 | `cta_variant` | TEXT | NULL, CHECK(cta_variant IN ('A','B','C')) | SPEC-03 | Active A/B variant for CTA |
| 16 | `revenue_mtd` | REAL | DEFAULT 0.0 | SPEC-03 | Month-to-date affiliate revenue estimate (USD) |
| 17 | `youtube_url` | TEXT | NULL | SPEC-04 | Full YouTube video URL |
| 18 | `video_status` | TEXT | DEFAULT 'none', CHECK(video_status IN ('none','scripted','published')) | SPEC-04 | Video pipeline status |

---

## Column Details

### `id`
- Auto-incrementing primary key.
- Never reused even if row is deleted.

### `keyword`
- Full keyword phrase as searched (e.g. "best AI writing tools 2026").
- Must be unique — no duplicate keyword entries.
- Normalised to lowercase before insert.

### `category`
- Maps directly to URL path segment: `/{category}/{slug}/`.
- Examples: `ai-writing`, `ai-image`, `ai-video`, `ai-code`, `ai-productivity`.
- Must match an existing directory under `web/content/`.

### `intent`
- `informational` — "what is X", "how does X work"
- `comparison` — "X vs Y", "best X for Z"
- `tutorial` — "how to use X", "X setup guide"
- Affects: CTA placement, AdSense rules, E-E-A-T injection, video eligibility.

### `monthly_volume`
- Sourced from keyword research tool at seed time.
- Updated manually or via script when re-researching.

### `difficulty`
- KD score 0–100 (lower = easier to rank).
- Selection threshold: `< 45` (per SPEC-01 §3).

### `status` — Lifecycle

```
pending ──► generating ──► published ──► needs_rewrite ──► generating ──► published (rewrite)
   │              │
   ▼              ▼
(crash)        failed
   │
   ▼
 pending (manual reset)
```

- `pending` — Keyword queued, no article yet.
- `generating` — Claimed by `select_keywords()`; pipeline is actively processing. Prevents double-selection across concurrent runs. Reset to `pending` manually if pipeline crashes.
- `published` — Article live on website.
- `needs_rewrite` — Flagged by GSC feedback loop (high impressions, low CTR).
- `failed` — Quality gate FAIL or duplicate detected. Not auto-retried.

### `slug`
- Derived from keyword: lowercase, spaces→hyphens, strip special chars.
- Must match the MDX filename: `web/content/{category}/{slug}.mdx`.
- Set at article generation time (SPEC-01 §8).

### `published_at`
- Set when `status` transitions to `published`.
- ISO 8601 date string: `YYYY-MM-DD`.
- Displayed on article page as publication date (E-E-A-T signal).

### `gsc_impressions`, `gsc_clicks`, `gsc_ctr`, `gsc_position`
- Updated weekly by `bot/gsc_feedback.py`.
- Rolling 7-day window.
- `gsc_ctr` = `gsc_clicks / NULLIF(gsc_impressions, 0)`, stored as real.
- Rewrite trigger: `gsc_impressions > 200 AND gsc_ctr < 0.01` → `status='needs_rewrite'`.

### `affiliate_partner`
- Key matching a program in SPEC-03 §4 (e.g. 'jasper', 'writesonic', 'surfer').
- Used by `cta_injector.ts` to load the correct affiliate_map JSON.
- NULL → renders newsletter CTA fallback.

### `cta_variant`
- A/B test variant for CTA copy.
- Rotated weekly by `bot/cta_rotator.py`.
- `A` = action text, `B` = benefit text, `C` = social proof.

### `revenue_mtd`
- Month-to-date affiliate revenue estimate in USD.
- Reset to 0 at start of each month.
- Updated from affiliate dashboard reports (manual or API).

### `youtube_url`
- Set by SPEC-04 after video published.
- NULL means no video yet.
- Format: `https://www.youtube.com/watch?v={id}` or `https://www.youtube.com/shorts/{id}`.

### `video_status`
- `none` — No video produced or planned.
- `scripted` — Script generated (`bot/video_scripts/{slug}.txt`), awaiting video.
- `published` — Video live on YouTube, `youtube_url` set.

---

## Indexes

```sql
CREATE INDEX idx_keywords_status ON keywords(status);
CREATE INDEX idx_keywords_category ON keywords(category);
CREATE INDEX idx_keywords_slug ON keywords(slug);
CREATE INDEX idx_keywords_priority ON keywords(monthly_volume, difficulty);
CREATE INDEX idx_keywords_video_status ON keywords(video_status);
```

---

## Seed SQL

```sql
CREATE TABLE IF NOT EXISTS keywords (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword         TEXT    NOT NULL UNIQUE,
    category        TEXT    NOT NULL,
    intent          TEXT    NOT NULL CHECK(intent IN ('informational','comparison','tutorial')),
    monthly_volume  INTEGER NOT NULL DEFAULT 0,
    difficulty      INTEGER NOT NULL DEFAULT 0 CHECK(difficulty BETWEEN 0 AND 100),
    status          TEXT    NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','generating','published','needs_rewrite','failed')),
    slug            TEXT    UNIQUE,
    published_at    TEXT,
    gsc_impressions INTEGER DEFAULT 0,
    gsc_clicks      INTEGER DEFAULT 0,
    gsc_ctr         REAL    DEFAULT 0.0,
    gsc_position    REAL    DEFAULT 0.0,
    affiliate_partner TEXT,
    cta_variant     TEXT    CHECK(cta_variant IN ('A','B','C')),
    revenue_mtd     REAL    DEFAULT 0.0,
    youtube_url     TEXT,
    video_status    TEXT    DEFAULT 'none' CHECK(video_status IN ('none','scripted','published'))
);
```

---

## Migration Policy

1. Add new columns as `ALTER TABLE keywords ADD COLUMN ...` with sensible defaults.
2. Never remove or rename columns without a migration script in `data/migrations/`.
3. Update this document and relevant SPEC files before altering schema.
4. All changes must be backward-compatible for one release cycle.
