from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import platform
import re
import traceback
from collections import Counter
from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from db_setup import DB_PATH
from generation_agent import (
    LLMAPIError,
    ProviderOutageError,
    ValidationError,
    _fallback_model,
    _outline_model,
    _section_model,
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
from research_agent import ResearchAgentError, _perplexity_preset, build_research_bundle

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONTENT_ROOT = _PROJECT_ROOT / "apps" / "web" / "content"
_DEFAULT_AFFILIATE_MAP_ROOT = _PROJECT_ROOT / "monetisation" / "affiliate_map"

_LOG = logging.getLogger(__name__)

_RETRYABLE_MARKERS = (
    "timeout",
    "timed out",
    "429",
    "rate limit",
    "insufficient_quota",
    "credit_balance_exhausted",
    "credit balance",
    "no credits remaining",
    "purchase credits",
    "overloaded",
    "connection",
    "temporarily",
    "502",
    "503",
    "504",
)


_SECRET_ENV_VARS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "PERPLEXITY_API_KEY",
    "FIRECRAWL_API_KEY",
)
_SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"pplx-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"fc-[A-Za-z0-9_\-]{8,}"),
)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def _dist_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "not_installed"


def _key_configured(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _redact(text: str) -> str:
    redacted = text
    for name in _SECRET_ENV_VARS:
        value = os.environ.get(name, "")
        if len(value) >= 8:
            redacted = redacted.replace(value, f"[redacted:{name}]")
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[redacted]", redacted)
    return redacted


def _runtime_context() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "openai": {
            "sdk": _dist_version("openai"),
            "outline_model": _outline_model(),
            "section_fallback_model": _fallback_model(),
            "api_key_configured": _key_configured("OPENAI_API_KEY"),
        },
        "anthropic": {
            "sdk": _dist_version("anthropic"),
            "writing_model": _section_model(),
            "api_key_configured": _key_configured("ANTHROPIC_API_KEY"),
        },
        "perplexity": {
            "preset": _perplexity_preset(),
            "api_key_configured": _key_configured("PERPLEXITY_API_KEY"),
        },
        "firecrawl": {
            "api_key_configured": _key_configured("FIRECRAWL_API_KEY"),
        },
    }


def _format_counts(items: list[str]) -> str:
    if not items:
        return "none"
    counts = Counter(items)
    return ",".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _log_article_failure(
    event: str,
    slug: str,
    step: str,
    exc: BaseException,
    *,
    unexpected: bool,
    failed_steps: list[str],
    error_types: list[str],
) -> None:
    failed_steps.append(step)
    error_types.append(type(exc).__name__)
    message = f"unexpected: {exc}" if unexpected else str(exc)
    _LOG.info(
        json.dumps(
            {
                "event": event,
                "slug": slug,
                "step": step,
                "error_type": type(exc).__name__,
                "error": _redact(message),
                "traceback": _redact(traceback.format_exc()),
            }
        )
    )


def _log_batch_finished(
    *,
    batch: int,
    dry_run: bool,
    selected: int,
    outcomes: list[str],
    failed_steps: list[str],
    error_types: list[str],
    exit_code: int,
) -> None:
    succeeded = sum(1 for outcome in outcomes if outcome == "success")
    failed = sum(1 for outcome in outcomes if outcome == "failed")
    retryable = sum(1 for outcome in outcomes if outcome == "retryable")
    outages = sum(1 for outcome in outcomes if outcome == "outage")
    released = sum(1 for outcome in outcomes if outcome == "released")
    step_counts = _format_counts(failed_steps)
    type_counts = _format_counts(error_types)
    _LOG.info(
        json.dumps(
            {
                "event": "batch_finished",
                "batch": batch,
                "dry_run": dry_run,
                "selected": selected,
                "succeeded": succeeded,
                "failed": failed,
                "retryable": retryable,
                "outages": outages,
                "released": released,
                "exit_code": exit_code,
                "failed_steps": step_counts,
                "error_types": type_counts,
            }
        )
    )
    _LOG.info(
        "batch_summary selected=%s succeeded=%s failed=%s retryable=%s "
        "outages=%s released=%s exit_code=%s failed_steps=%s error_types=%s",
        selected,
        succeeded,
        failed,
        retryable,
        outages,
        released,
        exit_code,
        step_counts,
        type_counts,
    )


def _is_retryable_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _RETRYABLE_MARKERS)


def _release_keyword(km: KeywordManager, row: dict[str, Any]) -> None:
    slug = str(row.get("slug") or "").strip()
    if not slug:
        return
    status = str(row.get("status") or "pending")
    if status not in {"pending", "needs_rewrite"}:
        status = "pending"
    km.update_status(slug, status)


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
    failed_steps: list[str],
    error_types: list[str],
) -> str:
    slug = str(row.get("slug") or row.get("keyword", "unknown"))
    step = "research"
    try:
        research = build_research_bundle(row["keyword"], row["intent"], dry_run=dry_run)
        attempts = 1 if dry_run else 2
        article: dict[str, Any] | None = None
        qa_result = None
        for attempt in range(attempts):
            step = "outline"
            outline = await generate_outline(
                row["keyword"], row["intent"], research, dry_run=dry_run
            )
            step = "sections"
            sections = await write_sections(
                outline,
                research,
                row["intent"],
                dry_run=dry_run,
                affiliate_partner=row.get("affiliate_partner"),
            )
            step = "write"
            article = assemble_article(row, outline, sections)
            qa_result = run_quality_gate(article, existing_articles=articles_written)
            if qa_result.overall != "FAIL":
                break
            if any(
                check.result == "FAIL" and check.action == "skip"
                for check in qa_result.checks
            ):
                break
            if attempt < attempts - 1:
                _LOG.info(
                    json.dumps(
                        {
                            "event": "article_retry",
                            "slug": slug,
                            "attempt": attempt + 1,
                        }
                    )
                )
        if article is None or qa_result is None:
            raise MDXWriterError("article generation produced no result")
        merged = apply_article_updates(article, qa_result)
        artifact = build_article_artifact(merged, qa_result)
        result = write_article(
            artifact,
            dry_run=dry_run,
            db_path=db_path,
            content_root=content_root,
            affiliate_map_root=affiliate_map_root,
        )
    except ProviderOutageError as exc:
        _release_keyword(km, row)
        _log_article_failure(
            "provider_outage",
            slug,
            step,
            exc,
            unexpected=False,
            failed_steps=failed_steps,
            error_types=error_types,
        )
        return "outage"
    except (ResearchAgentError, LLMAPIError, ValidationError, MDXWriterError) as exc:
        if _is_retryable_error(exc):
            _release_keyword(km, row)
            _log_article_failure(
                "article_retryable",
                slug,
                step,
                exc,
                unexpected=False,
                failed_steps=failed_steps,
                error_types=error_types,
            )
            return "retryable"
        km.update_status(slug, "failed")
        _log_article_failure(
            "article_error",
            slug,
            step,
            exc,
            unexpected=False,
            failed_steps=failed_steps,
            error_types=error_types,
        )
        return "failed"
    except Exception as exc:  # noqa: BLE001
        if _is_retryable_error(exc):
            _release_keyword(km, row)
            _log_article_failure(
                "article_retryable",
                slug,
                step,
                exc,
                unexpected=True,
                failed_steps=failed_steps,
                error_types=error_types,
            )
            return "retryable"
        km.update_status(slug, "failed")
        _log_article_failure(
            "article_error",
            slug,
            step,
            exc,
            unexpected=True,
            failed_steps=failed_steps,
            error_types=error_types,
        )
        return "failed"

    if result.skipped:
        km.update_status(slug, "failed")
        failed_steps.append("write")
        failed_checks = [
            check.name for check in qa_result.checks if check.result == "FAIL"
        ]
        error_types.append(failed_checks[0] if failed_checks else "quality_gate_skip")
        _LOG.info(
            json.dumps(
                {
                    "event": "article_complete",
                    "slug": slug,
                    "qa_overall": qa_result.overall,
                    "skipped": True,
                    "mdx_path": None,
                    "failed_checks": failed_checks,
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
                "draft": result.draft,
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
    failed_steps: list[str],
    error_types: list[str],
) -> list[str]:
    articles_written: list[dict[str, Any]] = []
    results = []
    for index, row in enumerate(rows):
        outcome = await _process_one(
            row,
            dry_run=dry_run,
            articles_written=articles_written,
            db_path=db_path,
            content_root=content_root,
            affiliate_map_root=affiliate_map_root,
            km=km,
            failed_steps=failed_steps,
            error_types=error_types,
        )
        results.append(outcome)
        if outcome == "outage":
            for remaining in rows[index + 1 :]:
                _release_keyword(km, remaining)
                results.append("released")
                _LOG.info(
                    json.dumps(
                        {
                            "event": "keyword_released",
                            "slug": remaining.get("slug"),
                            "status": remaining.get("status"),
                            "reason": "provider_outage",
                        }
                    )
                )
            break
    return results


def run(
    batch: int,
    dry_run: bool,
    *,
    db_path: Path = DB_PATH,
    content_root: Path = _DEFAULT_CONTENT_ROOT,
    affiliate_map_root: Path = _DEFAULT_AFFILIATE_MAP_ROOT,
    published_counts: Mapping[str, int] | None = None,
) -> int:
    _configure_logging()
    with KeywordManager(db_path) as km:
        rows = km.select_keywords(
            batch,
            content_root=content_root,
            published_counts=published_counts,
        )
        failed_steps: list[str] = []
        error_types: list[str] = []
        category_mix = dict(Counter(str(row.get("category") or "") for row in rows))
        _LOG.info(
            json.dumps(
                {
                    "event": "batch_started",
                    "batch": batch,
                    "dry_run": dry_run,
                    "selected": len(rows),
                    "weight_mode": km.last_weight_mode,
                    "category_mix": category_mix,
                    "runtime": _runtime_context(),
                }
            )
        )
        _LOG.info(
            "category_mix mode=%s %s",
            km.last_weight_mode,
            " ".join(
                f"{category}={count}"
                for category, count in sorted(category_mix.items())
            ),
        )
        if not rows:
            _log_batch_finished(
                batch=batch,
                dry_run=dry_run,
                selected=0,
                outcomes=[],
                failed_steps=failed_steps,
                error_types=error_types,
                exit_code=0,
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
                failed_steps=failed_steps,
                error_types=error_types,
            )
        )

    succeeded = sum(1 for outcome in outcomes if outcome == "success")
    exit_code = 0
    if not dry_run and len(rows) > 0 and succeeded == 0:
        exit_code = 2
    _log_batch_finished(
        batch=batch,
        dry_run=dry_run,
        selected=len(rows),
        outcomes=outcomes,
        failed_steps=failed_steps,
        error_types=error_types,
        exit_code=exit_code,
    )
    return exit_code


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
