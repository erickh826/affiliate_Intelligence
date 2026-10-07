from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import jsonschema

_LOG = logging.getLogger(__name__)

_OUTLINE_MODEL = "gpt-4o-mini"
_SECTION_MODEL = "claude-haiku-4-5-20251001"
_FALLBACK_MODEL = "gpt-4o"
_MAX_CONCURRENCY = 3

_MDX_SAFETY = (
    "MDX SAFETY RULES:\n"
    "1. ONLY use approved MDX components: <AffiliateCTA />.\n"
    "2. PROHIBIT raw HTML tags (e.g., <div>, <span>).\n"
    "3. ESCAPE curly braces used in normal prose as \\{ and \\}; do not escape approved placeholders like {{LINK_*}} or approved MDX component props.\n"
)

_SYSTEM_OUTLINE = (
    "You are an SEO content strategist for AI tools. "
    "Write outlines that match specific search intent. "
    "Output MUST be valid JSON matching the provided schema."
)

_SYSTEM_SECTION = (
    "You write sections of articles about AI tools. "
    "Be specific — include pricing, API limits, code examples. "
    "No generic AI filler phrases. "
    f"{_MDX_SAFETY}"
)

_EEAT: dict[str, str] = {
    "comparison": "Include a pricing comparison table.",
    "tutorial": "Include a code snippet or numbered steps.",
    "informational": "Include ≥1 statistic with source.",
}


class GenerationError(RuntimeError):
    """Base class for generation errors."""


class LLMAPIError(GenerationError):
    """Errors from external LLM APIs."""


class ProviderOutageError(LLMAPIError):
    """Quota or billing failure on every outline provider for this run."""


class ValidationError(GenerationError):
    """Errors when validating LLM output."""


_OUTAGE_MARKERS = (
    "insufficient_quota",
    "credit_balance_exhausted",
    "credit balance",
    "no credits remaining",
    "exceeded your current quota",
    "purchase credits",
    "billing",
)


def _is_provider_outage(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _OUTAGE_MARKERS)


def _parse_json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise json.JSONDecodeError("no json object", cleaned, 0)
    payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise LLMAPIError("Anthropic outline response was not a JSON object")
    return payload


def _summarise_research(research_bundle: dict[str, Any]) -> str:
    facts = research_bundle.get("facts", [])[:5]
    tools = research_bundle.get("tools_mentioned", [])[:3]
    facts_str = "; ".join(
        f["claim"] for f in facts if isinstance(f, dict) and "claim" in f
    )
    tools_str = ", ".join(
        t["name"] for t in tools if isinstance(t, dict) and "name" in t
    )
    return f"Key facts: {facts_str}. Tools: {tools_str}."


def _outline_prompt(keyword: str, intent: str, research_summary: str) -> str:
    return (
        f"Keyword: '{keyword}'\n"
        f"Intent: {intent}\n"
        f"Research: {research_summary}\n\n"
        "Generate:\n"
        "- H1 title (keyword included naturally)\n"
        "- Meta description (150–160 chars)\n"
        "- 6–8 H2 sections with 2–3 H3 each\n"
        "- 5 FAQ questions from PAA data\n"
        "- Comparison table columns (if intent=comparison)\n\n"
        "Return a JSON object matching this schema. "
        "faqs must be an array of strings, not objects. "
        "The h1 must contain the keyword exactly.\n"
        f"{_outline_schema_text()}"
    )


def _outline_model() -> str:
    return os.environ.get("OPENAI_MODEL_OUTLINE", _OUTLINE_MODEL)


def _section_model() -> str:
    return os.environ.get("ANTHROPIC_MODEL_WRITING", _SECTION_MODEL)


def _fallback_model() -> str:
    return os.environ.get("OPENAI_MODEL_FALLBACK", _FALLBACK_MODEL)


def _outline_schema_text() -> str:
    schema_path = Path(__file__).parent / "outline_schema.json"
    return schema_path.read_text(encoding="utf-8")


def _section_prompt(
    h2: str,
    h3s: list[str],
    facts: list[dict[str, Any]],
    intent: str,
    style_guide: str | None = None,
    affiliate_partner: str | None = None,
    keyword: str | None = None,
) -> str:
    eeat = _EEAT.get(intent, "")
    style = f"Tone/Style: {style_guide}\n" if style_guide else ""
    cta = ""
    if affiliate_partner:
        cta = (
            f'AFFILIATE CTA: You MUST include exactly one <AffiliateCTA partner="{affiliate_partner}" /> '
            "at a natural breaking point in this section."
        )

    internal_links = (
        "INTERNAL LINKING: Use placeholders like [Link Text]({{LINK_SLUG}}) for entities "
        "that likely have their own pages (e.g. [AI Writing Tools]({{LINK_AI_WRITING}}))."
    )

    keyword_rule = ""
    if keyword:
        keyword_rule = (
            f"The first 100 words must contain the exact phrase '{keyword}'.\n"
        )

    return (
        f"{style}"
        f"Section: '{h2}'\n"
        f"Sub-sections: {h3s}\n"
        f"Facts to include: {facts[:3]}\n"
        f"Target: 300–400 words. Include ≥1 pricing data point.\n"
        f"{keyword_rule}"
        f"{eeat}\n"
        f"{cta}\n"
        f"{internal_links}"
    ).strip()


def _validate_outline(outline: dict[str, Any]) -> None:
    schema_path = Path(__file__).parent / "outline_schema.json"
    try:
        with open(schema_path) as f:
            schema = json.load(f)
        jsonschema.validate(instance=outline, schema=schema)
    except (json.JSONDecodeError, FileNotFoundError, jsonschema.ValidationError) as exc:
        raise ValidationError(f"Outline validation failed: {exc}") from exc


def _dry_run_outline(keyword: str, intent: str) -> dict[str, Any]:
    title = keyword.title()
    meta = (
        f"Discover the best {keyword} in 2026. "
        "Compare features, pricing, and reviews to find the right tool for your needs."
    )
    # Ensure meta is at least 100 chars for schema
    if len(meta) < 100:
        meta += " Read our comprehensive guide to stay ahead of the curve."
    meta = meta[:165]
    sections = [
        {
            "h2": f"What Is {title}?",
            "h3s": ["Definition", "How It Works", "Key Features"],
        },
        {
            "h2": "Top Tools Compared",
            "h3s": ["Tool Overview", "Pricing", "Pros and Cons"],
        },
        {
            "h2": "Best For Beginners",
            "h3s": ["Getting Started", "Free Options", "Learning Curve"],
        },
        {
            "h2": "Best For Professionals",
            "h3s": ["Advanced Features", "Enterprise Plans", "Integrations"],
        },
        {
            "h2": "Pricing Breakdown",
            "h3s": ["Free Plans", "Paid Tiers", "Value Assessment"],
        },
        {
            "h2": "How to Choose",
            "h3s": ["Key Criteria", "Use Case Matching", "Our Recommendation"],
        },
        {
            "h2": "Frequently Asked Questions",
            "h3s": ["Common Questions", "Quick Answers"],
        },
    ]
    faqs = [
        f"What is the best {keyword}?",
        f"Is {keyword} worth it in 2026?",
        f"How much does {keyword} cost?",
        f"What are the top alternatives to {keyword}?",
        f"How do I get started with {keyword}?",
    ]
    result: dict[str, Any] = {
        "h1": f"Best {title}: Complete Guide for 2026",
        "meta_description": meta,
        "sections": sections,
        "faqs": faqs,
    }
    if intent == "comparison":
        result["comparison_columns"] = ["Tool", "Price/mo", "Best For", "Rating"]
    return result


def _dry_run_section(h2: str, h3s: list[str]) -> dict[str, Any]:
    base = (
        f"This section covers {h2}. "
        "Pricing for leading tools starts at $0 for free tiers and $49/month for professional plans. "
        "Key considerations include feature depth, API access, and integration support. "
        + " ".join(
            f"Regarding {h}: compare tools on fit for your workflow and budget."
            for h in h3s
        )
    )
    padding = " ".join(
        ["Evaluate each option carefully before committing to a subscription."] * 25
    )
    content = " ".join(f"{base} {padding}".split()[:320])
    return {
        "h2": h2,
        "h3s": h3s,
        "content": content,
        "word_count": len(content.split()),
    }


async def _call_outline(
    keyword: str, intent: str, research_summary: str
) -> dict[str, Any]:
    from openai import AsyncOpenAI, OpenAIError

    try:
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=_outline_model(),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_OUTLINE},
                {
                    "role": "user",
                    "content": _outline_prompt(keyword, intent, research_summary),
                },
            ],
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content or "{}")
    except (OpenAIError, json.JSONDecodeError) as exc:
        raise LLMAPIError(f"Outline generation failed: {exc}") from exc


async def _call_anthropic_outline(
    keyword: str, intent: str, research_summary: str
) -> dict[str, Any]:
    from anthropic import AnthropicError, AsyncAnthropic

    system = (
        f"{_SYSTEM_OUTLINE} Return only one JSON object. "
        "Do not wrap it in markdown fences."
    )
    try:
        client = AsyncAnthropic()
        message = await client.messages.create(
            model=_section_model(),
            max_tokens=4096,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": _outline_prompt(keyword, intent, research_summary),
                }
            ],
            temperature=0.3,
        )
        text = message.content[0].text
    except (AnthropicError, IndexError, AttributeError) as exc:
        raise LLMAPIError(f"Anthropic outline generation failed: {exc}") from exc
    try:
        return _parse_json_payload(text)
    except (json.JSONDecodeError, LLMAPIError) as exc:
        raise LLMAPIError(f"Anthropic outline generation failed: {exc}") from exc


async def _load_outline(
    keyword: str, intent: str, research_summary: str
) -> dict[str, Any]:
    try:
        return await _call_outline(keyword, intent, research_summary)
    except LLMAPIError as openai_exc:
        _LOG.info(
            json.dumps(
                {
                    "event": "outline_fallback",
                    "provider": "anthropic",
                    "model": _section_model(),
                    "error": str(openai_exc),
                }
            )
        )
        try:
            return await _call_anthropic_outline(keyword, intent, research_summary)
        except LLMAPIError as anthropic_exc:
            if _is_provider_outage(openai_exc) or _is_provider_outage(anthropic_exc):
                raise ProviderOutageError(
                    "Outline providers unavailable: "
                    f"openai={openai_exc}; anthropic={anthropic_exc}"
                ) from anthropic_exc
            raise LLMAPIError(
                "Outline generation failed: "
                f"{openai_exc}; anthropic fallback failed: {anthropic_exc}"
            ) from anthropic_exc


async def _call_anthropic_section(
    h2: str,
    h3s: list[str],
    facts: list[dict[str, Any]],
    intent: str,
    style_guide: str | None = None,
    affiliate_partner: str | None = None,
    keyword: str | None = None,
) -> str:
    from anthropic import AnthropicError, AsyncAnthropic

    try:
        client = AsyncAnthropic()
        message = await client.messages.create(
            model=_section_model(),
            max_tokens=1400,
            system=_SYSTEM_SECTION,
            messages=[
                {
                    "role": "user",
                    "content": _section_prompt(
                        h2,
                        h3s,
                        facts,
                        intent,
                        style_guide,
                        affiliate_partner,
                        keyword,
                    ),
                }
            ],
        )
        return message.content[0].text
    except (AnthropicError, IndexError) as exc:
        raise LLMAPIError(f"Anthropic section generation failed: {exc}") from exc


async def _call_openai_section(
    h2: str,
    h3s: list[str],
    facts: list[dict[str, Any]],
    intent: str,
    style_guide: str | None = None,
    affiliate_partner: str | None = None,
    keyword: str | None = None,
) -> str:
    from openai import AsyncOpenAI, OpenAIError

    try:
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=_fallback_model(),
            messages=[
                {"role": "system", "content": _SYSTEM_SECTION},
                {
                    "role": "user",
                    "content": _section_prompt(
                        h2,
                        h3s,
                        facts,
                        intent,
                        style_guide,
                        affiliate_partner,
                        keyword,
                    ),
                },
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content or ""
    except OpenAIError as exc:
        raise LLMAPIError(f"OpenAI fallback section generation failed: {exc}") from exc


async def _write_one_section(
    h2: str,
    h3s: list[str],
    facts: list[dict[str, Any]],
    intent: str,
    dry_run: bool,
    sem: asyncio.Semaphore,
    style_guide: str | None = None,
    affiliate_partner: str | None = None,
    keyword: str | None = None,
) -> dict[str, Any]:
    async with sem:
        if dry_run:
            return _dry_run_section(h2, h3s)
        try:
            content = await _call_anthropic_section(
                h2, h3s, facts, intent, style_guide, affiliate_partner, keyword
            )
        except LLMAPIError as anthropic_exc:
            try:
                content = await _call_openai_section(
                    h2, h3s, facts, intent, style_guide, affiliate_partner, keyword
                )
            except LLMAPIError as openai_exc:
                if _is_provider_outage(anthropic_exc) or _is_provider_outage(
                    openai_exc
                ):
                    raise ProviderOutageError(
                        "Section providers unavailable: "
                        f"anthropic={anthropic_exc}; openai={openai_exc}"
                    ) from openai_exc
                raise LLMAPIError(
                    "Section generation failed: "
                    f"{anthropic_exc}; openai fallback failed: {openai_exc}"
                ) from openai_exc
        return {
            "h2": h2,
            "h3s": h3s,
            "content": content,
            "word_count": len(content.split()),
        }


def _clamp_meta_description(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) > 165:
        truncated = cleaned[:165].rsplit(" ", 1)[0].rstrip(" ,.;:")
        cleaned = truncated if len(truncated) >= 100 else cleaned[:165].rstrip(" ,.;:")
    pad = " Compare features, pricing, and practical trade-offs for this search."
    while len(cleaned) < 100:
        cleaned = f"{cleaned.rstrip('.')}.{pad}"
        if len(cleaned) > 165:
            cleaned = cleaned[:165].rsplit(" ", 1)[0].rstrip(" ,.;:")
            break
    return cleaned


def _normalize_outline(outline: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(outline, dict):
        return outline
    normalized = dict(outline)
    meta = normalized.get("meta_description")
    if isinstance(meta, str):
        normalized["meta_description"] = _clamp_meta_description(meta)
    faqs = normalized.get("faqs")
    if isinstance(faqs, list):
        questions: list[str] = []
        for item in faqs:
            if isinstance(item, str) and item.strip():
                questions.append(item.strip())
            elif isinstance(item, dict):
                question = item.get("question") or item.get("q")
                if isinstance(question, str) and question.strip():
                    questions.append(question.strip())
        normalized["faqs"] = questions
    sections = normalized.get("sections")
    if isinstance(sections, list):
        cleaned: list[dict[str, Any]] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            h2 = section.get("h2")
            h3s = section.get("h3s")
            if not isinstance(h2, str) or not h2.strip():
                continue
            if not isinstance(h3s, list):
                h3s = []
            cleaned.append(
                {"h2": h2.strip(), "h3s": [h3 for h3 in h3s if isinstance(h3, str)]}
            )
        normalized["sections"] = cleaned[:8]
    return normalized


async def generate_outline(
    keyword: str,
    intent: str,
    research_bundle: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    if dry_run:
        outline = _dry_run_outline(keyword, intent)
        _validate_outline(outline)
        return outline

    summary = _summarise_research(research_bundle)
    last_error: ValidationError | None = None
    for _attempt in range(3):
        outline = _normalize_outline(await _load_outline(keyword, intent, summary))
        try:
            _validate_outline(outline)
        except ValidationError as exc:
            last_error = exc
            continue
        return outline
    if last_error is None:
        raise ValidationError("Outline validation failed")
    raise last_error


async def write_sections(
    outline: dict[str, Any],
    research_bundle: dict[str, Any],
    intent: str,
    dry_run: bool = False,
    style_guide: str | None = None,
    affiliate_partner: str | None = None,
) -> list[dict[str, Any]]:
    sem = asyncio.Semaphore(_MAX_CONCURRENCY)
    facts = research_bundle.get("facts", [])
    keyword = str(research_bundle.get("keyword") or "").strip()
    tasks = [
        _write_one_section(
            s["h2"],
            s.get("h3s", []),
            facts,
            intent,
            dry_run,
            sem,
            style_guide,
            affiliate_partner,
            keyword if index == 0 and keyword else None,
        )
        for index, s in enumerate(outline["sections"])
    ]
    return list(await asyncio.gather(*tasks))
