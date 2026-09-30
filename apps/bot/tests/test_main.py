from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from db_setup import init_db
from generation_agent import generate_outline, write_sections
from main import assemble_article, run
from quality_gate import CheckResult, QAResult
from research_agent import build_research_bundle

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

    def test_dry_run_does_not_write_mdx(self, seeded_db: Path, tmp_path: Path) -> None:
        content_root = tmp_path / "content"
        run(
            batch=3,
            dry_run=True,
            db_path=seeded_db,
            content_root=content_root,
            affiliate_map_root=tmp_path / "affiliate",
        )
        assert list(content_root.rglob("*.mdx")) == []

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
        assert list(content_root.rglob("*.mdx")) == []
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


class TestRunLive:
    def test_publishes_mdx_and_keyword_status(
        self, seeded_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        content_root = tmp_path / "content"

        def fake_research(
            keyword: str, intent: str, dry_run: bool = False, **_kwargs: object
        ) -> dict:
            return build_research_bundle(keyword, intent, dry_run=True)

        async def fake_outline(
            keyword: str, intent: str, research: dict, dry_run: bool = False
        ) -> dict:
            return await generate_outline(keyword, intent, research, dry_run=True)

        async def fake_sections(
            outline: dict,
            research: dict,
            intent: str,
            dry_run: bool = False,
            **kwargs: object,
        ) -> list:
            return await write_sections(
                outline, research, intent, dry_run=True, **kwargs
            )

        monkeypatch.setattr("main.build_research_bundle", fake_research)
        monkeypatch.setattr("main.generate_outline", fake_outline)
        monkeypatch.setattr("main.write_sections", fake_sections)

        code = run(
            batch=1,
            dry_run=False,
            db_path=seeded_db,
            content_root=content_root,
            affiliate_map_root=tmp_path / "affiliate",
        )

        mdx_files = list(content_root.rglob("*.mdx"))
        assert code == 0
        assert len(mdx_files) == 1
        conn = sqlite3.connect(seeded_db)
        row = conn.execute(
            "SELECT status, published_at FROM keywords WHERE slug = ?",
            (mdx_files[0].stem,),
        ).fetchone()
        published = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE status = 'published'"
        ).fetchone()[0]
        conn.close()
        assert row is not None
        assert row[0] == "published"
        assert row[1]
        assert published == 1

    def test_retries_regenerate_failures_before_publish(
        self, seeded_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = {"n": 0}

        def fake_research(
            keyword: str, intent: str, dry_run: bool = False, **_kwargs: object
        ) -> dict:
            return build_research_bundle(keyword, intent, dry_run=True)

        async def fake_outline(
            keyword: str, intent: str, research: dict, dry_run: bool = False
        ) -> dict:
            return await generate_outline(keyword, intent, research, dry_run=True)

        async def flaky_sections(
            outline: dict,
            research: dict,
            intent: str,
            dry_run: bool = False,
            **kwargs: object,
        ) -> list:
            calls["n"] += 1
            if calls["n"] == 1:
                return [
                    {
                        "h2": "Short",
                        "h3s": [],
                        "content": "too short",
                        "word_count": 2,
                    }
                ]
            return await write_sections(
                outline, research, intent, dry_run=True, **kwargs
            )

        monkeypatch.setattr("main.build_research_bundle", fake_research)
        monkeypatch.setattr("main.generate_outline", fake_outline)
        monkeypatch.setattr("main.write_sections", flaky_sections)

        code = run(
            batch=1,
            dry_run=False,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )

        assert code == 0
        assert calls["n"] == 2
        conn = sqlite3.connect(seeded_db)
        published = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE status = 'published'"
        ).fetchone()[0]
        conn.close()
        assert published == 1

    def test_duplicate_skip_does_not_retry(
        self, seeded_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = {"n": 0}

        def fake_research(
            keyword: str, intent: str, dry_run: bool = False, **_kwargs: object
        ) -> dict:
            return build_research_bundle(keyword, intent, dry_run=True)

        async def counting_outline(
            keyword: str, intent: str, research: dict, dry_run: bool = False
        ) -> dict:
            calls["n"] += 1
            return await generate_outline(keyword, intent, research, dry_run=True)

        async def fake_sections(
            outline: dict,
            research: dict,
            intent: str,
            dry_run: bool = False,
            **kwargs: object,
        ) -> list:
            return await write_sections(
                outline, research, intent, dry_run=True, **kwargs
            )

        def skip_gate(
            _article: dict, existing_articles: list | None = None
        ) -> QAResult:
            return QAResult(
                overall="FAIL",
                checks=[
                    CheckResult("duplicate_detection", "FAIL", "duplicate", "skip")
                ],
                article_updates={"status": "failed"},
            )

        monkeypatch.setattr("main.build_research_bundle", fake_research)
        monkeypatch.setattr("main.generate_outline", counting_outline)
        monkeypatch.setattr("main.write_sections", fake_sections)
        monkeypatch.setattr("main.run_quality_gate", skip_gate)

        run(
            batch=1,
            dry_run=False,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )

        assert calls["n"] == 1
        assert list((tmp_path / "content").rglob("*.mdx")) == []


def test_published_rows_match_content_files() -> None:
    root = Path(__file__).resolve().parents[3]
    db_path = root / "data" / "keywords.db"
    content_root = root / "apps" / "web" / "content"
    affiliate_root = root / "monetisation" / "affiliate_map"

    conn = sqlite3.connect(db_path)
    published = {
        row[0]
        for row in conn.execute(
            "SELECT slug FROM keywords WHERE status = 'published' AND slug IS NOT NULL"
        )
    }
    conn.close()

    mdx_slugs = {path.stem for path in content_root.rglob("*.mdx")}
    faq_dir = content_root / "faq"
    faq_slugs = (
        {path.name.removesuffix(".faq.json") for path in faq_dir.glob("*.faq.json")}
        if faq_dir.exists()
        else set()
    )
    map_slugs = (
        {path.stem for path in affiliate_root.glob("*.json")}
        if affiliate_root.exists()
        else set()
    )

    assert mdx_slugs == published
    assert faq_slugs == published
    assert map_slugs == published
