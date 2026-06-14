from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from db_setup import init_db
from main import assemble_article, run


_INSERT = (
    "INSERT INTO keywords "
    "(keyword, category, intent, monthly_volume, difficulty, status, slug, affiliate_partner) "
    "VALUES (?,?,?,?,?,?,?,?)"
)

_KEYWORDS = [
    (
        "best ai writing tools",
        "ai-writing",
        "comparison",
        5000,
        20,
        "pending",
        "best-ai-writing-tools",
        "jasper",
    ),
    (
        "jasper ai review 2026",
        "ai-writing",
        "informational",
        3000,
        25,
        "pending",
        "jasper-ai-review-2026",
        None,
    ),
    (
        "how to use jasper ai",
        "ai-writing",
        "tutorial",
        2000,
        15,
        "pending",
        "how-to-use-jasper-ai",
        "jasper",
    ),
]


@pytest.fixture()
def seeded_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "keywords.db"
    conn = init_db(db_path)
    conn.executemany(_INSERT, _KEYWORDS)
    conn.commit()
    conn.close()
    return db_path


class TestAssembleArticle:
    def test_maps_row_and_outline_fields(self) -> None:
        row = {
            "slug": "best-ai-tools",
            "keyword": "best ai tools",
            "category": "ai-writing",
            "intent": "comparison",
            "affiliate_partner": "jasper",
            "cta_variant": "A",
        }
        outline = {
            "h1": "Best AI Tools: Complete Guide",
            "meta_description": "Compare the best AI tools in 2026.",
            "sections": [],
            "faqs": ["What is the best AI tool?"],
        }
        sections = [
            {"h2": "Overview", "h3s": [], "content": "Content.", "word_count": 1}
        ]
        article = assemble_article(row, outline, sections)
        assert article["slug"] == "best-ai-tools"
        assert article["h1"] == "Best AI Tools: Complete Guide"
        assert article["sections"] == sections
        assert article["faqs"] == ["What is the best AI tool?"]
        assert article["affiliate_partner"] == "jasper"

    def test_defaults_cta_variant_to_a(self) -> None:
        row = {"slug": "s", "keyword": "k", "category": "c", "intent": "informational"}
        outline = {"h1": "H", "meta_description": "D", "sections": [], "faqs": []}
        article = assemble_article(row, outline, [])
        assert article["cta_variant"] == "A"

    def test_affiliate_partner_none_when_absent(self) -> None:
        row = {"slug": "s", "keyword": "k", "category": "c", "intent": "informational"}
        outline = {"h1": "H", "meta_description": "D", "sections": [], "faqs": []}
        article = assemble_article(row, outline, [])
        assert article["affiliate_partner"] is None


class TestRunDryRun:
    def test_returns_zero(self, seeded_db: Path, tmp_path: Path) -> None:
        code = run(
            batch=3,
            dry_run=True,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )
        assert code == 0

    def test_at_least_one_mdx_written(self, seeded_db: Path, tmp_path: Path) -> None:
        content_root = tmp_path / "content"
        run(
            batch=3,
            dry_run=True,
            db_path=seeded_db,
            content_root=content_root,
            affiliate_map_root=tmp_path / "affiliate",
        )
        mdx_files = list(content_root.rglob("*.mdx"))
        assert len(mdx_files) >= 1

    def test_no_keywords_left_generating(self, seeded_db: Path, tmp_path: Path) -> None:
        run(
            batch=3,
            dry_run=True,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )
        conn = sqlite3.connect(seeded_db)
        generating = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE status = 'generating'"
        ).fetchone()[0]
        conn.close()
        assert generating == 0

    def test_successful_articles_reset_to_pending(
        self, seeded_db: Path, tmp_path: Path
    ) -> None:
        content_root = tmp_path / "content"
        run(
            batch=3,
            dry_run=True,
            db_path=seeded_db,
            content_root=content_root,
            affiliate_map_root=tmp_path / "affiliate",
        )
        conn = sqlite3.connect(seeded_db)
        pending = conn.execute(
            "SELECT slug FROM keywords WHERE status = 'pending'"
        ).fetchall()
        conn.close()
        mdx_files = list(content_root.rglob("*.mdx"))
        assert len(mdx_files) >= 1
        assert len(pending) >= 1

    def test_deploy_not_triggered(
        self, seeded_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        deploy_calls: list[str] = []

        def fake_deploy(url: str) -> None:
            deploy_calls.append(url)

        monkeypatch.setenv("VERCEL_DEPLOY_HOOK_URL", "https://example.com/hook")
        import mdx_writer

        monkeypatch.setattr(mdx_writer, "_default_deploy_post", fake_deploy)
        run(
            batch=3,
            dry_run=True,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )
        assert deploy_calls == []

    def test_empty_db_returns_zero(self, tmp_path: Path) -> None:
        db_path = tmp_path / "empty.db"
        init_db(db_path).close()
        code = run(
            batch=3,
            dry_run=True,
            db_path=db_path,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )
        assert code == 0
