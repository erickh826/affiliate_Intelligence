from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable
from urllib import request
from urllib.error import URLError

from db_setup import DB_PATH
from models import AffiliateMap, ArticleArtifact, FAQItem, Frontmatter
from quality_gate import QAResult

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONTENT_ROOT = _PROJECT_ROOT / "apps" / "web" / "content"
_AFFILIATE_MAP_ROOT = _PROJECT_ROOT / "monetisation" / "affiliate_map"
_AUTHOR_NAME = "Affiliate Intelligence Editorial Team"
_SCHEMA_TYPE = "Article"

DeployPost = Callable[[str], None]


@dataclass(frozen=True)
class MDXWriteResult:
    slug: str
    skipped: bool
    mdx_path: Path | None = None
    faq_path: Path | None = None
    affiliate_map_path: Path | None = None
    db_updated: bool = False
    deploy_triggered: bool = False
    reason: str | None = None


class MDXWriterError(RuntimeError):
    pass


def _default_deploy_post(url: str) -> None:
    req = request.Request(url, method="POST")
    try:
        with request.urlopen(req, timeout=10):
            return
    except URLError as exc:
        raise MDXWriterError(f"Deploy hook failed: {exc}") from exc


def apply_article_updates(
    article: dict[str, Any], qa_result: QAResult
) -> dict[str, Any]:
    updated = dict(article)
    for key, value in qa_result.article_updates.items():
        if key != "status":
            updated[key] = value
    return updated


def _article_field(article: dict[str, Any], key: str) -> str:
    value = article.get(key)
    if value is None:
        raise MDXWriterError(f"missing article field: {key}")
    text = str(value).strip()
    if not text:
        raise MDXWriterError(f"empty article field: {key}")
    return text


def _frontmatter_value(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _build_frontmatter(article: dict[str, Any]) -> Frontmatter:
    title = str(article.get("title") or _article_field(article, "h1")).strip()
    partner = article.get("affiliate_partner")
    return {
        "title": title,
        "description": _article_field(article, "meta_description"),
        "slug": _article_field(article, "slug"),
        "category": _article_field(article, "category"),
        "intent": _article_field(article, "intent"),
        "published_at": "",
        "last_reviewed": "",
        "author": str(article.get("author") or _AUTHOR_NAME),
        "affiliate_partner": str(partner).strip() if partner is not None else None,
        "schema_type": _SCHEMA_TYPE,
    }


def _render_frontmatter(frontmatter: Frontmatter, *, today_iso: str) -> str:
    partner = frontmatter["affiliate_partner"] or ""
    fields = [
        ("title", frontmatter["title"]),
        ("description", frontmatter["description"]),
        ("slug", frontmatter["slug"]),
        ("category", frontmatter["category"]),
        ("intent", frontmatter["intent"]),
        ("published_at", today_iso),
        ("last_reviewed", today_iso),
        ("author", frontmatter["author"]),
        ("affiliate_partner", partner),
        ("schema_type", frontmatter["schema_type"]),
    ]
    lines = ["---"]
    lines.extend(f"{key}: {_frontmatter_value(str(value))}" for key, value in fields)
    lines.append("---")
    return "\n".join(lines)


def _build_mdx_body(article: dict[str, Any]) -> str:
    sections = article.get("sections", [])
    if not isinstance(sections, list) or not sections:
        raise MDXWriterError("article sections must be a non-empty list")

    parts: list[str] = [f"# {_article_field(article, 'h1')}"]
    for section in sections:
        if not isinstance(section, dict):
            raise MDXWriterError("article section must be an object")
        h2 = _article_field(section, "h2")
        content = _article_field(section, "content")
        parts.append(f"## {h2}\n\n{content}")

    return "\n\n".join(parts)


def _normalise_faqs(article: dict[str, Any]) -> list[FAQItem]:
    faqs = article.get("faqs", [])
    if not isinstance(faqs, list):
        raise MDXWriterError("article faqs must be a list")

    normalised: list[FAQItem] = []
    for item in faqs:
        if isinstance(item, str):
            normalised.append({"question": item, "answer": ""})
        elif isinstance(item, dict):
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if not question:
                raise MDXWriterError("FAQ object missing question")
            normalised.append({"question": question, "answer": answer})
        else:
            raise MDXWriterError("FAQ item must be a string or object")
    return normalised


def _build_affiliate_map(article: dict[str, Any]) -> AffiliateMap:
    partner = str(article.get("affiliate_partner") or "")
    cta_variant = str(article.get("cta_variant") or "A")
    return {
        "slug": _article_field(article, "slug"),
        "primary_partner": partner or None,
        "cta_variant": cta_variant,
        "links": {},
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _update_published_status(db_path: Path, slug: str, published_at: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE keywords
            SET    status       = 'published',
                   published_at = COALESCE(published_at, ?)
            WHERE  slug = ?
            """,
            (published_at, slug),
        )


def _trigger_deploy(deploy_post: DeployPost) -> bool:
    url = os.environ.get("VERCEL_DEPLOY_HOOK_URL")
    if not url:
        return False
    deploy_post(url)
    return True


def build_article_artifact(
    merged: dict[str, Any], qa_result: QAResult
) -> ArticleArtifact:
    slug = _article_field(merged, "slug")
    category = _article_field(merged, "category")
    return {
        "slug": slug,
        "category": category,
        "frontmatter": _build_frontmatter(merged),
        "mdx_body": _build_mdx_body(merged),
        "faq_json": _normalise_faqs(merged),
        "affiliate_map": _build_affiliate_map(merged),
        "qa_result": qa_result,
    }


def write_article(
    artifact: ArticleArtifact,
    *,
    dry_run: bool = False,
    db_path: Path = DB_PATH,
    content_root: Path = _CONTENT_ROOT,
    affiliate_map_root: Path = _AFFILIATE_MAP_ROOT,
    deploy_post: DeployPost = _default_deploy_post,
    today: date | None = None,
) -> MDXWriteResult:
    slug = str(artifact.get("slug") or "").strip()
    if not slug:
        raise MDXWriterError("missing article field: slug")
    qa_result = artifact["qa_result"]
    if qa_result.overall == "FAIL":
        return MDXWriteResult(slug=slug, skipped=True, reason="qa_failed")

    category = str(artifact.get("category") or "").strip()
    if not category:
        raise MDXWriterError("missing article field: category")
    published_at = (today or date.today()).isoformat()
    mdx_path = content_root / category / f"{slug}.mdx"
    faq_path = content_root / "faq" / f"{slug}.faq.json"
    affiliate_map_path = affiliate_map_root / f"{slug}.json"

    mdx_path.parent.mkdir(parents=True, exist_ok=True)
    mdx = (
        f"{_render_frontmatter(artifact['frontmatter'], today_iso=published_at)}"
        f"\n\n{artifact['mdx_body']}\n"
    )
    mdx_path.write_text(mdx, encoding="utf-8")

    _write_json(
        faq_path,
        {
            "slug": slug,
            "faqs": artifact["faq_json"],
        },
    )
    _write_json(affiliate_map_path, artifact["affiliate_map"])

    db_updated = False
    deploy_triggered = False
    if not dry_run:
        _update_published_status(db_path, slug, published_at)
        db_updated = True
        deploy_triggered = _trigger_deploy(deploy_post)

    return MDXWriteResult(
        slug=slug,
        skipped=False,
        mdx_path=mdx_path,
        faq_path=faq_path,
        affiliate_map_path=affiliate_map_path,
        db_updated=db_updated,
        deploy_triggered=deploy_triggered,
    )
