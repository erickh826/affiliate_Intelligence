from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from db_setup import DB_PATH
from generation_agent import (
    LLMAPIError,
    ValidationError,
    generate_outline,
    write_sections,
)
from keyword_manager import KeywordManager
from mdx_writer import (
    MDXWriterError,
    apply_article_updates,
    build_article_artifact,
    write_article,
)
from quality_gate import run_quality_gate
from research_agent import ResearchAgentError, build_research_bundle

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONTENT_ROOT = _PROJECT_ROOT / "apps" / "web" / "content"
_DEFAULT_AFFILIATE_MAP_ROOT = _PROJECT_ROOT / "monetisation" / "affiliate_map"

_LOG = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def assemble_article(
    row: dict[str, Any],
    outline: dict[str, Any],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "slug": row["slug"],
        "keyword": row["keyword"],
        "category": row["category"],
        "intent": row["intent"],
        "h1": outline["h1"],
        "meta_description": outline["meta_description"],
        "sections": sections,
        "faqs": outline.get("faqs", []),
        "affiliate_partner": row.get("affiliate_partner"),
        "cta_variant": row.get("cta_variant") or "A",
    }


async def _process_one(
    row: dict[str, Any],
    *,
    dry_run: bool,
    articles_written: list[dict[str, Any]],
    db_path: Path,
    content_root: Path,
    affiliate_map_root: Path,
    km: KeywordManager,
) -> str:
    slug = str(row.get("slug") or row.get("keyword", "unknown"))
    try:
        research = build_research_bundle(row["keyword"], row["intent"], dry_run=dry_run)
        outline = await generate_outline(
            row["keyword"], row["intent"], research, dry_run=dry_run
        )
        sections = await write_sections(
            outline,
            research,
            row["intent"],
            dry_run=dry_run,
            affiliate_partner=row.get("affiliate_partner"),
        )
        article = assemble_article(row, outline, sections)
        qa_result = run_quality_gate(article, existing_articles=articles_written)
        merged = apply_article_updates(article, qa_result)
        artifact = build_article_artifact(merged, qa_result)
        result = write_article(
            artifact,
            dry_run=dry_run,
            db_path=db_path,
            content_root=content_root,
            affiliate_map_root=affiliate_map_root,
        )
    except (ResearchAgentError, LLMAPIError, ValidationError, MDXWriterError) as exc:
        km.update_status(slug, "failed")
        _LOG.info(
            json.dumps({"event": "article_error", "slug": slug, "error": str(exc)})
        )
        return "failed"
    except Exception as exc:
        km.update_status(slug, "failed")
        _LOG.info(
            json.dumps(
                {"event": "article_error", "slug": slug, "error": f"unexpected: {exc}"}
            )
        )
        return "failed"

    if result.skipped:
        km.update_status(slug, "failed")
        _LOG.info(
            json.dumps(
                {
                    "event": "article_complete",
                    "slug": slug,
                    "qa_overall": qa_result.overall,
                    "skipped": True,
                    "mdx_path": None,
                    "checks_failed": sum(
                        1 for c in qa_result.checks if c.result == "FAIL"
                    ),
                }
            )
        )
        return "failed"

    if dry_run:
        km.update_status(slug, "pending")

    articles_written.append(article)
    _LOG.info(
        json.dumps(
            {
                "event": "article_complete",
                "slug": slug,
                "qa_overall": qa_result.overall,
                "skipped": False,
                "mdx_path": str(result.mdx_path) if result.mdx_path else None,
                "checks_failed": sum(1 for c in qa_result.checks if c.result == "FAIL"),
            }
        )
    )
    return "success"


async def _run_batch(
    rows: list[dict[str, Any]],
    *,
    dry_run: bool,
    db_path: Path,
    content_root: Path,
    affiliate_map_root: Path,
    km: KeywordManager,
) -> list[str]:
    articles_written: list[dict[str, Any]] = []
    results = []
    for row in rows:
        outcome = await _process_one(
            row,
            dry_run=dry_run,
            articles_written=articles_written,
            db_path=db_path,
            content_root=content_root,
            affiliate_map_root=affiliate_map_root,
            km=km,
        )
        results.append(outcome)
    return results


def run(
    batch: int,
    dry_run: bool,
    *,
    db_path: Path = DB_PATH,
    content_root: Path = _DEFAULT_CONTENT_ROOT,
    affiliate_map_root: Path = _DEFAULT_AFFILIATE_MAP_ROOT,
) -> int:
    _configure_logging()
    with KeywordManager(db_path) as km:
        rows = km.select_keywords(batch)
        _LOG.info(
            json.dumps(
                {
                    "event": "batch_started",
                    "batch": batch,
                    "dry_run": dry_run,
                    "selected": len(rows),
                }
            )
        )
        if not rows:
            _LOG.info(
                json.dumps(
                    {
                        "event": "batch_finished",
                        "batch": batch,
                        "dry_run": dry_run,
                        "selected": 0,
                        "succeeded": 0,
                        "failed": 0,
                    }
                )
            )
            return 0

        outcomes = asyncio.run(
            _run_batch(
                rows,
                dry_run=dry_run,
                db_path=db_path,
                content_root=content_root,
                affiliate_map_root=affiliate_map_root,
                km=km,
            )
        )

    succeeded = sum(1 for o in outcomes if o == "success")
    failed = sum(1 for o in outcomes if o == "failed")
    _LOG.info(
        json.dumps(
            {
                "event": "batch_finished",
                "batch": batch,
                "dry_run": dry_run,
                "selected": len(outcomes),
                "succeeded": succeeded,
                "failed": failed,
            }
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Affiliate Intelligence bot runner")
    parser.add_argument("--batch", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run(batch=args.batch, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
