-- Adds 'draft' to the status CHECK constraint and maps keywords onto
-- affiliate categories. SQLite cannot alter a CHECK, so the table is rebuilt.
-- Published URLs stay on their current category.
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
                              CHECK(status IN ('pending','published','needs_rewrite','failed','generating','draft')),
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

UPDATE keywords
SET category = 'seo'
WHERE slug IN (
    'surfer-seo-vs-clearscope',
    'surfer-seo-review-2026',
    'how-to-use-surfer-seo',
    'frase-vs-surfer-seo',
    'best-ai-tools-for-seo-content',
    'clearscope-review-2026',
    'neuronwriter-review-2026',
    'surfer-seo-content-editor-tutorial'
);

UPDATE keywords SET affiliate_partner = 'surfer'
WHERE slug IN ('clearscope-review-2026', 'neuronwriter-review-2026');

UPDATE keywords SET affiliate_partner = 'copy_ai'
WHERE slug IN ('copy-ai-review-2026', 'how-to-use-copy-ai');

UPDATE keywords SET affiliate_partner = 'descript'
WHERE slug IN (
    'descript-vs-riverside',
    'descript-review-2026',
    'how-to-use-descript',
    'kapwing-vs-descript',
    'veed-io-vs-descript'
);

UPDATE keywords SET affiliate_partner = 'notion'
WHERE slug IN (
    'notion-ai-vs-chatgpt',
    'notion-ai-review-2026',
    'how-to-use-notion-ai'
);

UPDATE keywords SET affiliate_partner = 'zapier'
WHERE slug IN (
    'zapier-ai-features-explained',
    'how-to-automate-tasks-with-zapier-ai'
);

INSERT OR IGNORE INTO keywords
    (keyword, category, intent, monthly_volume, difficulty, slug, affiliate_partner)
VALUES
    ('semrush vs ahrefs', 'seo', 'comparison', 5400, 38, 'semrush-vs-ahrefs', 'semrush'),
    ('semrush review 2026', 'seo', 'informational', 6200, 36, 'semrush-review-2026', 'semrush'),
    ('ahrefs review 2026', 'seo', 'informational', 4800, 34, 'ahrefs-review-2026', 'ahrefs'),
    ('best seo tools 2026', 'seo', 'comparison', 8100, 40, 'best-seo-tools-2026', 'semrush'),
    ('how to use semrush', 'seo', 'tutorial', 2900, 28, 'how-to-use-semrush', 'semrush'),
    ('how to use ahrefs', 'seo', 'tutorial', 2600, 27, 'how-to-use-ahrefs', 'ahrefs'),
    ('ahrefs vs moz', 'seo', 'comparison', 2200, 30, 'ahrefs-vs-moz', 'ahrefs'),
    ('best keyword research tools 2026', 'seo', 'comparison', 3600, 33, 'best-keyword-research-tools-2026', 'semrush'),
    ('surfer seo vs semrush', 'seo', 'comparison', 1400, 26, 'surfer-seo-vs-semrush', 'surfer'),
    ('semrush vs moz', 'seo', 'comparison', 1800, 29, 'semrush-vs-moz', 'semrush'),
    ('how to do keyword research with ahrefs', 'seo', 'tutorial', 1600, 24, 'how-to-do-keyword-research-with-ahrefs', 'ahrefs'),
    ('ahrefs webmaster tools review', 'seo', 'informational', 900, 18, 'ahrefs-webmaster-tools-review', 'ahrefs'),
    ('semrush keyword magic tool tutorial', 'seo', 'tutorial', 1300, 22, 'semrush-keyword-magic-tool-tutorial', 'semrush'),
    ('ahrefs site explorer tutorial', 'seo', 'tutorial', 1500, 23, 'ahrefs-site-explorer-tutorial', 'ahrefs');

COMMIT;
PRAGMA foreign_keys = ON;
