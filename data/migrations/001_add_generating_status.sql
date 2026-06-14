-- Adds 'generating' to the status CHECK constraint.
-- SQLite does not support ALTER COLUMN, so we recreate the table.
PRAGMA foreign_keys = OFF;
BEGIN;

CREATE TABLE keywords_new (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword           TEXT    NOT NULL UNIQUE,
    category          TEXT    NOT NULL,
    intent            TEXT    NOT NULL
                              CHECK(intent IN ('informational','comparison','tutorial')),
    monthly_volume    INTEGER NOT NULL DEFAULT 0,
    difficulty        INTEGER NOT NULL DEFAULT 0
                              CHECK(difficulty BETWEEN 0 AND 100),
    status            TEXT    NOT NULL DEFAULT 'pending'
                              CHECK(status IN ('pending','published','needs_rewrite','failed','generating')),
    slug              TEXT    UNIQUE,
    published_at      TEXT,
    gsc_impressions   INTEGER DEFAULT 0,
    gsc_clicks        INTEGER DEFAULT 0,
    gsc_ctr           REAL    DEFAULT 0.0,
    gsc_position      REAL    DEFAULT 0.0,
    affiliate_partner TEXT,
    cta_variant       TEXT    CHECK(cta_variant IN ('A','B','C')),
    revenue_mtd       REAL    DEFAULT 0.0,
    youtube_url       TEXT,
    video_status      TEXT    DEFAULT 'none'
                              CHECK(video_status IN ('none','scripted','published'))
);

INSERT INTO keywords_new SELECT * FROM keywords;
DROP TABLE keywords;
ALTER TABLE keywords_new RENAME TO keywords;

CREATE INDEX IF NOT EXISTS idx_keywords_status   ON keywords(status);
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);
CREATE INDEX IF NOT EXISTS idx_keywords_slug     ON keywords(slug);
CREATE INDEX IF NOT EXISTS idx_keywords_priority ON keywords(monthly_volume, difficulty);
CREATE INDEX IF NOT EXISTS idx_keywords_video    ON keywords(video_status);

COMMIT;
PRAGMA foreign_keys = ON;
