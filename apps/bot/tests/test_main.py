from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from pathlib import Path

import pytest

from category_weights import mdx_is_draft
from db_setup import init_db
from generation_agent import (
    ProviderOutageError,
    ValidationError,
    generate_outline,
    write_sections,
)
from main import assemble_article, run
from mdx_writer import MDXWriterError
from mdx_writer import write_article as real_write_article
from quality_gate import CheckResult, QAResult
from research_agent import ResearchAgentError, build_research_bundle

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
        assert row[0] == "draft"
        assert row[1] is None
        assert "draft: true" in mdx_files[0].read_text(encoding="utf-8")
        assert published == 0

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
        drafts = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE status = 'draft'"
        ).fetchone()[0]
        conn.close()
        assert drafts == 1

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

    def test_provider_outage_releases_batch_and_exits_nonzero(
        self, seeded_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = {"n": 0}

        def fake_research(
            keyword: str, intent: str, dry_run: bool = False, **_kwargs: object
        ) -> dict:
            calls["n"] += 1
            return build_research_bundle(keyword, intent, dry_run=True)

        async def outage_outline(
            keyword: str, intent: str, research: dict, dry_run: bool = False
        ) -> dict:
            raise ProviderOutageError(
                "Outline providers unavailable: credit_balance_exhausted"
            )

        monkeypatch.setattr("main.build_research_bundle", fake_research)
        monkeypatch.setattr("main.generate_outline", outage_outline)

        code = run(
            batch=3,
            dry_run=False,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )

        conn = sqlite3.connect(seeded_db)
        statuses = dict(conn.execute("SELECT slug, status FROM keywords").fetchall())
        conn.close()
        assert code == 2
        assert calls["n"] == 1
        assert list((tmp_path / "content").rglob("*.mdx")) == []
        assert set(statuses.values()) == {"pending"}

    def test_retryable_research_timeout_stays_pending(
        self, seeded_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = {"n": 0}

        def flaky_research(
            keyword: str, intent: str, dry_run: bool = False, **_kwargs: object
        ) -> dict:
            calls["n"] += 1
            if calls["n"] == 1:
                raise ResearchAgentError(
                    "external research request failed: The read operation timed out"
                )
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

        monkeypatch.setattr("main.build_research_bundle", flaky_research)
        monkeypatch.setattr("main.generate_outline", fake_outline)
        monkeypatch.setattr("main.write_sections", fake_sections)

        content_root = tmp_path / "content"
        code = run(
            batch=2,
            dry_run=False,
            db_path=seeded_db,
            content_root=content_root,
            affiliate_map_root=tmp_path / "affiliate",
        )

        conn = sqlite3.connect(seeded_db)
        timed_out = conn.execute(
            "SELECT status FROM keywords WHERE slug = ?",
            ("best-ai-writing-tools",),
        ).fetchone()
        failed = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE status = 'failed'"
        ).fetchone()[0]
        drafts = conn.execute(
            "SELECT COUNT(*) FROM keywords WHERE status = 'draft'"
        ).fetchone()[0]
        conn.close()
        assert code == 0
        assert calls["n"] == 2
        assert timed_out == ("pending",)
        assert failed == 0
        assert drafts == 1
        assert len(list(content_root.rglob("*.mdx"))) == 1

    def test_validation_error_still_marks_failed(
        self, seeded_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_research(
            keyword: str, intent: str, dry_run: bool = False, **_kwargs: object
        ) -> dict:
            return build_research_bundle(keyword, intent, dry_run=True)

        async def bad_outline(
            keyword: str, intent: str, research: dict, dry_run: bool = False
        ) -> dict:
            raise ValidationError("Outline validation failed")

        monkeypatch.setattr("main.build_research_bundle", fake_research)
        monkeypatch.setattr("main.generate_outline", bad_outline)

        code = run(
            batch=1,
            dry_run=False,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )

        conn = sqlite3.connect(seeded_db)
        status = conn.execute(
            "SELECT status FROM keywords WHERE slug = ?",
            ("best-ai-writing-tools",),
        ).fetchone()
        conn.close()
        assert code == 2
        assert status == ("failed",)
        assert list((tmp_path / "content").rglob("*.mdx")) == []


def _assert_logs_omit_secrets(text: str) -> None:
    for name in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "PERPLEXITY_API_KEY",
        "FIRECRAWL_API_KEY",
    ):
        value = os.environ.get(name, "")
        if len(value) >= 8:
            assert value not in text


def _json_events(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for message in caplog.messages:
        if message.startswith("{"):
            payload = json.loads(message)
            if isinstance(payload, dict):
                events.append(payload)
    return events


class TestDiagnosticLogging:
    @pytest.mark.parametrize(
        "failing_step",
        ["research", "outline", "sections", "write"],
    )
    def test_article_error_logs_step_type_traceback_and_redacts_secrets(
        self,
        failing_step: str,
        seeded_db: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        secret = "sk-diag-secret-value-should-not-leak"
        monkeypatch.setenv("OPENAI_API_KEY", secret)
        caplog.set_level(logging.INFO, logger="main")

        def fake_research(
            keyword: str, intent: str, dry_run: bool = False, **_kwargs: object
        ) -> dict:
            if failing_step == "research":
                raise ResearchAgentError(f"research exploded {secret}")
            return build_research_bundle(keyword, intent, dry_run=True)

        async def fake_outline(
            keyword: str, intent: str, research: dict, dry_run: bool = False
        ) -> dict:
            if failing_step == "outline":
                raise TypeError(
                    "AsyncMessages.create() got an unexpected keyword argument "
                    f"'temperature' {secret}"
                )
            return await generate_outline(keyword, intent, research, dry_run=True)

        async def fake_sections(
            outline: dict,
            research: dict,
            intent: str,
            dry_run: bool = False,
            **kwargs: object,
        ) -> list:
            if failing_step == "sections":
                raise TypeError(f"section exploded {secret}")
            return await write_sections(
                outline, research, intent, dry_run=True, **kwargs
            )

        def fake_write(*args: object, **kwargs: object) -> object:
            if failing_step == "write":
                raise MDXWriterError(f"write exploded {secret}")
            return real_write_article(*args, **kwargs)

        monkeypatch.setattr("main.build_research_bundle", fake_research)
        monkeypatch.setattr("main.generate_outline", fake_outline)
        monkeypatch.setattr("main.write_sections", fake_sections)
        monkeypatch.setattr("main.write_article", fake_write)

        run(
            batch=1,
            dry_run=False,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )

        events = _json_events(caplog)
        started = next(event for event in events if event["event"] == "batch_started")
        runtime = started["runtime"]
        assert isinstance(runtime, dict)
        anthropic = runtime["anthropic"]
        openai = runtime["openai"]
        assert isinstance(anthropic, dict)
        assert isinstance(openai, dict)
        assert anthropic["writing_model"] == "claude-haiku-4-5-20251001"
        assert openai["outline_model"] == "gpt-4o-mini"
        assert "sdk" in anthropic
        assert openai["api_key_configured"] is True

        failure = next(event for event in events if event["event"] == "article_error")
        assert failure["step"] == failing_step
        if failing_step == "research":
            assert failure["error_type"] == "ResearchAgentError"
            assert not str(failure["error"]).startswith("unexpected:")
        elif failing_step == "write":
            assert failure["error_type"] == "MDXWriterError"
        else:
            assert failure["error_type"] == "TypeError"
            assert str(failure["error"]).startswith("unexpected:")
        assert "Traceback (most recent call last)" in str(failure["traceback"])
        assert "[redacted:OPENAI_API_KEY]" in str(failure["error"])
        assert secret not in caplog.text
        _assert_logs_omit_secrets(caplog.text)

        summary = next(
            message
            for message in caplog.messages
            if message.startswith("batch_summary")
        )
        assert f"failed_steps={failing_step}:1" in summary
        assert "selected=1" in summary
        assert "succeeded=0" in summary

    def test_dry_run_summary_reports_successes(
        self,
        seeded_db: Path,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO, logger="main")
        code = run(
            batch=3,
            dry_run=True,
            db_path=seeded_db,
            content_root=tmp_path / "content",
            affiliate_map_root=tmp_path / "affiliate",
        )
        assert code == 0
        summary = next(
            message
            for message in caplog.messages
            if message.startswith("batch_summary")
        )
        assert "selected=3 succeeded=1 failed=2" in summary
        assert "failed_steps=write:2" in summary
        assert "exit_code=0" in summary
        _assert_logs_omit_secrets(caplog.text)


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
    draft_status = {
        row[0]
        for row in conn.execute(
            "SELECT slug FROM keywords WHERE status = 'draft' AND slug IS NOT NULL"
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

    live_mdx = set()
    draft_mdx = set()
    for path in content_root.rglob("*.mdx"):
        if mdx_is_draft(path.read_text(encoding="utf-8")):
            draft_mdx.add(path.stem)
        else:
            live_mdx.add(path.stem)

    assert mdx_slugs == faq_slugs == map_slugs
    assert published <= live_mdx
    assert draft_mdx <= draft_status
    assert mdx_slugs == published | draft_status


_STILL_FAILED = {
    "best-ai-coding-assistants-2026",
    "best-ai-image-generators-2026",
    "best-ai-productivity-tools-2026",
    "how-to-create-ai-art-for-free",
    "how-to-make-ai-videos-for-youtube",
    "how-to-use-midjourney",
}


def _migration_slugs(name: str) -> list[str]:
    root = Path(__file__).resolve().parents[3]
    sql = (root / "data" / "migrations" / name).read_text(encoding="utf-8")
    in_list = sql.split("slug IN", 1)[1]
    return re.findall(r"'([a-z0-9-]+)'", in_list)


def _seed_keywords(conn: sqlite3.Connection, slugs: list[str], status: str) -> None:
    conn.executemany(
        "INSERT INTO keywords "
        "(keyword, category, intent, monthly_volume, difficulty, status, slug) "
        "VALUES (?,?,?,?,?,?,?)",
        [
            (
                slug.replace("-", " "),
                "ai-writing",
                "informational",
                1000,
                20,
                status,
                slug,
            )
            for slug in slugs
        ],
    )
    conn.commit()


def _apply_migration(conn: sqlite3.Connection, name: str) -> None:
    root = Path(__file__).resolve().parents[3]
    conn.executescript(
        (root / "data" / "migrations" / name).read_text(encoding="utf-8")
    )
    conn.commit()


def test_quota_burned_keywords_are_pending(tmp_path: Path) -> None:
    slugs = _migration_slugs("002_requeue_quota_failed_keywords.sql")
    conn = init_db(tmp_path / "keywords.db")
    _seed_keywords(conn, [*slugs, *sorted(_STILL_FAILED)], "failed")
    _apply_migration(conn, "002_requeue_quota_failed_keywords.sql")
    rows = conn.execute(
        f"SELECT slug, status FROM keywords WHERE slug IN ({','.join('?' * len(slugs))})",
        slugs,
    ).fetchall()
    still_failed = {
        row[0]
        for row in conn.execute(
            "SELECT slug FROM keywords WHERE status = 'failed'"
        ).fetchall()
    }
    conn.close()
    assert len(slugs) == 25
    assert {row[0] for row in rows} == set(slugs)
    assert {row[1] for row in rows} == {"pending"}
    assert still_failed == _STILL_FAILED


def test_oct_sdk_failures_are_requeued(tmp_path: Path) -> None:
    quota_slugs = _migration_slugs("002_requeue_quota_failed_keywords.sql")
    sdk_slugs = _migration_slugs("003_requeue_oct_sdk_failed_keywords.sql")
    already_pending = sorted(set(quota_slugs) - set(sdk_slugs))
    conn = init_db(tmp_path / "keywords.db")
    _seed_keywords(conn, sdk_slugs, "failed")
    _seed_keywords(conn, already_pending, "pending")
    _seed_keywords(conn, sorted(_STILL_FAILED), "failed")
    _apply_migration(conn, "003_requeue_oct_sdk_failed_keywords.sql")
    requeued = {
        row[0]
        for row in conn.execute(
            "SELECT slug FROM keywords WHERE status = 'pending'"
        ).fetchall()
    }
    still_failed = {
        row[0]
        for row in conn.execute(
            "SELECT slug FROM keywords WHERE status = 'failed'"
        ).fetchall()
    }
    conn.close()
    assert len(sdk_slugs) == 20
    assert len(already_pending) == 5
    assert set(sdk_slugs) <= requeued
    assert set(already_pending) <= requeued
    assert still_failed == _STILL_FAILED
