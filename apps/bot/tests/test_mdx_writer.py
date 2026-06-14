from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from db_setup import init_db
from mdx_writer import apply_article_updates, build_article_artifact, write_article
from models import ArticleArtifact
from quality_gate import CheckResult, QAResult


def _article(**overrides: Any) -> dict[str, Any]:
    article: dict[str, Any] = {
        "slug": "best-ai-writing-tools",
        "keyword": "best ai writing tools",
        "category": "ai-writing",
        "intent": "comparison",
        "h1": "Best AI Writing Tools for Teams",
        "meta_description": (
            "Compare the best AI writing tools for teams, including pricing, "
            "features, workflow fit, and practical trade-offs for content teams."
        ),
        "author": "Editorial Team",
        "affiliate_partner": "jasper",
        "cta_variant": "B",
        "sections": [
            {
                "h2": "How AI Writing Tools Compare",
                "h3s": ["Pricing", "Workflow"],
                "content": (
                    "Best AI writing tools differ by pricing, workflow fit, "
                    "collaboration features, and quality controls."
                ),
                "word_count": 14,
            }
        ],
        "faqs": [
            {
                "question": "What is the best AI writing tool?",
                "answer": "The best option depends on budget and workflow.",
            },
            "How much do AI writing tools cost?",
        ],
    }
    article.update(overrides)
    return article


def _qa_result(**updates: Any) -> QAResult:
    return QAResult(
        overall="PASS",
        checks=[CheckResult("word_count", "PASS", "ok", "none")],
        article_updates=updates,
    )


def _artifact(article: dict[str, Any], qa_result: QAResult) -> ArticleArtifact:
    merged = apply_article_updates(article, qa_result)
    return build_article_artifact(merged, qa_result)


def _frontmatter_keys(mdx: str) -> list[str]:
    lines = mdx.splitlines()
    end = lines.index("---", 1)
    return [line.split(":", 1)[0] for line in lines[1:end]]


def _db_with_keyword(path: Path, slug: str = "best-ai-writing-tools") -> None:
    conn = init_db(path)
    conn.execute(
        """
        INSERT INTO keywords
        (keyword, category, intent, monthly_volume, difficulty, status, slug)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "best ai writing tools",
            "ai-writing",
            "comparison",
            1000,
            20,
            "generating",
            slug,
        ),
    )
    conn.commit()
    conn.close()


def test_frontmatter_fields_match_spec_01_section_8_1(tmp_path: Path) -> None:
    qa_result = _qa_result()
    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=True,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
        today=date(2026, 5, 17),
    )

    mdx = result.mdx_path.read_text(encoding="utf-8")  # type: ignore[union-attr]

    assert _frontmatter_keys(mdx) == [
        "title",
        "description",
        "slug",
        "category",
        "intent",
        "published_at",
        "last_reviewed",
        "author",
        "affiliate_partner",
        "schema_type",
    ]
    assert 'published_at: "2026-05-17"' in mdx


def test_article_updates_are_applied_to_frontmatter(tmp_path: Path) -> None:
    qa_result = _qa_result(meta_description="Compare updated metadata from QA.")
    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=True,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
    )

    mdx = result.mdx_path.read_text(encoding="utf-8")  # type: ignore[union-attr]

    assert 'description: "Compare updated metadata from QA."' in mdx


def test_output_paths(tmp_path: Path) -> None:
    qa_result = _qa_result()
    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=True,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
    )

    assert (
        result.mdx_path
        == tmp_path / "content" / "ai-writing" / "best-ai-writing-tools.mdx"
    )
    assert (
        result.faq_path
        == tmp_path / "content" / "faq" / "best-ai-writing-tools.faq.json"
    )
    assert (
        result.affiliate_map_path
        == tmp_path / "affiliate_map" / "best-ai-writing-tools.json"
    )
    assert result.mdx_path.exists()
    assert result.faq_path.exists()
    assert result.affiliate_map_path.exists()


def test_failed_qa_skips_article_write(tmp_path: Path) -> None:
    qa_result = QAResult(
        overall="FAIL",
        checks=[CheckResult("word_count", "FAIL", "short", "regenerate")],
        article_updates={"status": "failed"},
    )
    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=True,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
    )

    assert result.skipped is True
    assert result.reason == "qa_failed"
    assert not (tmp_path / "content").exists()
    assert not (tmp_path / "affiliate_map").exists()


def test_faq_json_output(tmp_path: Path) -> None:
    qa_result = _qa_result()
    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=True,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
    )

    payload = json.loads(result.faq_path.read_text(encoding="utf-8"))  # type: ignore[union-attr]

    assert payload == {
        "slug": "best-ai-writing-tools",
        "faqs": [
            {
                "question": "What is the best AI writing tool?",
                "answer": "The best option depends on budget and workflow.",
            },
            {"question": "How much do AI writing tools cost?", "answer": ""},
        ],
    }


def test_affiliate_map_stub_output(tmp_path: Path) -> None:
    qa_result = _qa_result()
    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=True,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
    )

    payload = json.loads(result.affiliate_map_path.read_text(encoding="utf-8"))  # type: ignore[union-attr]

    assert payload == {
        "slug": "best-ai-writing-tools",
        "primary_partner": "jasper",
        "cta_variant": "B",
        "links": {},
    }


def test_dry_run_skips_deploy_and_db_update(tmp_path: Path, monkeypatch: Any) -> None:
    db_path = tmp_path / "keywords.db"
    _db_with_keyword(db_path)
    calls: list[str] = []
    monkeypatch.setenv("VERCEL_DEPLOY_HOOK_URL", "https://deploy.example/hook")
    qa_result = _qa_result()

    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=True,
        db_path=db_path,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
        deploy_post=calls.append,
    )

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT status, published_at FROM keywords WHERE slug = ?",
            ("best-ai-writing-tools",),
        ).fetchone()

    assert result.db_updated is False
    assert result.deploy_triggered is False
    assert calls == []
    assert row == ("generating", None)


def test_publish_updates_db_status_and_published_at(
    tmp_path: Path, monkeypatch: Any
) -> None:
    db_path = tmp_path / "keywords.db"
    _db_with_keyword(db_path)
    calls: list[str] = []
    monkeypatch.setenv("VERCEL_DEPLOY_HOOK_URL", "https://deploy.example/hook")
    qa_result = _qa_result()

    result = write_article(
        _artifact(_article(), qa_result),
        dry_run=False,
        db_path=db_path,
        content_root=tmp_path / "content",
        affiliate_map_root=tmp_path / "affiliate_map",
        deploy_post=calls.append,
        today=date(2026, 5, 17),
    )

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT status, published_at FROM keywords WHERE slug = ?",
            ("best-ai-writing-tools",),
        ).fetchone()

    assert result.db_updated is True
    assert result.deploy_triggered is True
    assert calls == ["https://deploy.example/hook"]
    assert row == ("published", "2026-05-17")
