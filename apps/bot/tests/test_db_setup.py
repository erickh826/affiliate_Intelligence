from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from db_setup import init_db
from seed_keywords import _SEED, _to_slug, seed


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_keywords.db"


def _index_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    return {r[0] for r in rows}


class TestInitDb:
    def test_creates_keywords_table(self, tmp_db: Path) -> None:
        conn = init_db(tmp_db)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        assert ("keywords",) in tables
        conn.close()

    def test_all_indexes_created(self, tmp_db: Path) -> None:
        conn = init_db(tmp_db)
        names = _index_names(conn)
        expected = {
            "idx_keywords_status",
            "idx_keywords_category",
            "idx_keywords_slug",
            "idx_keywords_priority",
            "idx_keywords_video",
        }
        assert expected.issubset(names)
        conn.close()

    def test_wal_mode(self, tmp_db: Path) -> None:
        conn = init_db(tmp_db)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_idempotent(self, tmp_db: Path) -> None:
        init_db(tmp_db).close()
        init_db(tmp_db).close()

    def test_schema_columns(self, tmp_db: Path) -> None:
        conn = init_db(tmp_db)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(keywords)").fetchall()}
        required = {
            "id", "keyword", "category", "intent", "monthly_volume", "difficulty",
            "status", "slug", "published_at", "gsc_impressions", "gsc_clicks",
            "gsc_ctr", "gsc_position", "affiliate_partner", "cta_variant",
            "revenue_mtd", "youtube_url", "video_status",
        }
        assert required == cols
        conn.close()

    def test_check_constraint_intent(self, tmp_db: Path) -> None:
        conn = init_db(tmp_db)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO keywords (keyword, category, intent) VALUES (?,?,?)",
                ("kw", "cat", "invalid"),
            )
        conn.close()

    def test_check_constraint_status(self, tmp_db: Path) -> None:
        conn = init_db(tmp_db)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO keywords (keyword, category, intent, status) VALUES (?,?,?,?)",
                ("kw2", "cat", "informational", "unknown"),
            )
        conn.close()

    def test_check_constraint_difficulty_bounds(self, tmp_db: Path) -> None:
        conn = init_db(tmp_db)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO keywords (keyword, category, intent, difficulty) VALUES (?,?,?,?)",
                ("kw3", "cat", "informational", 101),
            )
        conn.close()


class TestToSlug:
    def test_spaces_to_hyphens(self) -> None:
        assert _to_slug("best ai tools") == "best-ai-tools"

    def test_lowercased(self) -> None:
        assert _to_slug("Jasper AI Review") == "jasper-ai-review"

    def test_strips_special_chars(self) -> None:
        assert _to_slug("dall-e 3 review!") == "dall-e-3-review"

    def test_year_preserved(self) -> None:
        assert _to_slug("best tools 2026") == "best-tools-2026"


class TestSeed:
    def test_seed_count_at_least_fifty(self, tmp_db: Path) -> None:
        count = seed(tmp_db)
        assert count >= 50

    def test_seed_covers_all_seed_rows(self, tmp_db: Path) -> None:
        count = seed(tmp_db)
        assert count == len(_SEED)

    def test_seed_is_idempotent(self, tmp_db: Path) -> None:
        first = seed(tmp_db)
        second = seed(tmp_db)
        assert first == second

    def test_seed_slugs_populated(self, tmp_db: Path) -> None:
        seed(tmp_db)
        conn = sqlite3.connect(tmp_db)
        null_slugs = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE slug IS NULL"
        ).fetchone()[0]
        conn.close()
        assert null_slugs == 0

    def test_seed_status_all_pending(self, tmp_db: Path) -> None:
        seed(tmp_db)
        conn = sqlite3.connect(tmp_db)
        non_pending = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE status != 'pending'"
        ).fetchone()[0]
        conn.close()
        assert non_pending == 0

    def test_seed_valid_for_selection(self, tmp_db: Path) -> None:
        seed(tmp_db)
        conn = sqlite3.connect(tmp_db)
        selectable = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE monthly_volume > 100 AND difficulty < 45"
        ).fetchone()[0]
        conn.close()
        assert selectable >= 50

    def test_all_intents_represented(self, tmp_db: Path) -> None:
        seed(tmp_db)
        conn = sqlite3.connect(tmp_db)
        intents = {
            r[0]
            for r in conn.execute("SELECT DISTINCT intent FROM keywords").fetchall()
        }
        conn.close()
        assert intents == {"informational", "comparison", "tutorial"}

    def test_all_categories_represented(self, tmp_db: Path) -> None:
        seed(tmp_db)
        conn = sqlite3.connect(tmp_db)
        cats = {
            r[0]
            for r in conn.execute("SELECT DISTINCT category FROM keywords").fetchall()
        }
        conn.close()
        assert cats == {"ai-writing", "ai-image", "ai-video", "ai-code", "ai-productivity"}
