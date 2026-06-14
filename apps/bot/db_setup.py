from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "keywords.db"

_DDL = """
CREATE TABLE IF NOT EXISTS keywords (
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
"""

_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_keywords_status   ON keywords(status);",
    "CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);",
    "CREATE INDEX IF NOT EXISTS idx_keywords_slug     ON keywords(slug);",
    "CREATE INDEX IF NOT EXISTS idx_keywords_priority ON keywords(monthly_volume, difficulty);",
    "CREATE INDEX IF NOT EXISTS idx_keywords_video    ON keywords(video_status);",
]


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(_DDL)
    for stmt in _INDEXES:
        conn.execute(stmt)
    conn.commit()
    return conn


if __name__ == "__main__":
    conn = init_db()
    conn.close()
    print(f"db_initialized path={DB_PATH}")
