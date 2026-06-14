from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import jsonschema

_OUTLINE_MODEL = "gpt-4o-mini"
_SECTION_MODEL = "claude-3-5-haiku-20241022"
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


class ValidationError(GenerationError):
    """Errors when validating LLM output."""


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
        "- Comparison table columns (if intent=comparison)"
    )


def _section_prompt(
    h2: str,
    h3s: list[str],
    facts: list[dict[str, Any]],
    intent: str,
    style_guide: str | None = None,
    affiliate_partner: str | None = None,
) -> str:
    eeat = _EEAT.get(intent, "")
    style = f"Tone/Style: {style_guide}\n" if style_guide else ""
    cta = ""
    if affiliate_partner:
        cta = (
            f"AFFILIATE CTA: You MUST include exactly one <AffiliateCTA partner=\"{affiliate_partner}\" /> "
            "at a natural breaking point in this section."
        )

    internal_links = (
        "INTERNAL LINKING: Use placeholders like [Link Text]({{LINK_SLUG}}) for entities "
        "that likely have their own pages (e.g. [AI Writing Tools]({{LINK_AI_WRITING}}))."
    )

    return (
        f"{style}"
        f"Section: '{h2}'\n"
        f"Sub-sections: {h3s}\n"
        f"Facts to include: {facts[:3]}\n"
        f"Target: 300–400 words. Include ≥1 pricing data point.\n"
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
        {"h2": f"What Is {title}?", "h3s": ["Definition", "How It Works", "Key Features"]},
        {"h2": "Top Tools Compared", "h3s": ["Tool Overview", "Pricing", "Pros and Cons"]},
        {"h2": "Best For Beginners", "h3s": ["Getting Started", "Free Options", "Learning Curve"]},
        {"h2": "Best For Professionals", "h3s": ["Advanced Features", "Enterprise Plans", "Integrations"]},
        {"h2": "Pricing Breakdown", "h3s": ["Free Plans", "Paid Tiers", "Value Assessment"]},
        {"h2": "How to Choose", "h3s": ["Key Criteria", "Use Case Matching", "Our Recommendation"]},
        {"h2": "Frequently Asked Questions", "h3s": ["Common Questions", "Quick Answers"]},
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
            f"Regarding {h}: compare tools on fit for your workflow and budget." for h in h3s
        )
    )
    padding = " ".join(["Evaluate each option carefully before committing to a subscription."] * 25)
    content = " ".join(f"{base} {padding}".split()[:320])
    return {"h2": h2, "h3s": h3s, "content": content, "word_count": len(content.split())}


async def _call_outline(
    keyword: str, intent: str, research_summary: str
) -> dict[str, Any]:
    from openai import AsyncOpenAI, OpenAIError

    try:
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=_OUTLINE_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_OUTLINE},
                {"role": "user", "content": _outline_prompt(keyword, intent, research_summary)},
            ],
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content or "{}")
    except (OpenAIError, json.JSONDecodeError) as exc:
        raise LLMAPIError(f"Outline generation failed: {exc}") from exc


async def _call_anthropic_section(
    h2: str,
    h3s: list[str],
    facts: list[dict[str, Any]],
    intent: str,
    style_guide: str | None = None,
    affiliate_partner: str | None = None,
) -> str:
    from anthropic import AsyncAnthropic, AnthropicError

    try:
        client = AsyncAnthropic()
        message = await client.messages.create(
            model=_SECTION_MODEL,
            max_tokens=1024,
            system=_SYSTEM_SECTION,
            messages=[
                {
                    "role": "user",
                    "content": _section_prompt(
                        h2, h3s, facts, intent, style_guide, affiliate_partner
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
) -> str:
    from openai import AsyncOpenAI, OpenAIError

    try:
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=_FALLBACK_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_SECTION},
                {
                    "role": "user",
                    "content": _section_prompt(
                        h2, h3s, facts, intent, style_guide, affiliate_partner
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
) -> dict[str, Any]:
    async with sem:
        if dry_run:
            return _dry_run_section(h2, h3s)
        try:
            content = await _call_anthropic_section(
                h2, h3s, facts, intent, style_guide, affiliate_partner
            )
        except LLMAPIError:
            # Fallback to OpenAI
            content = await _call_openai_section(
                h2, h3s, facts, intent, style_guide, affiliate_partner
            )
        return {"h2": h2, "h3s": h3s, "content": content, "word_count": len(content.split())}


async def generate_outline(
    keyword: str,
    intent: str,
    research_bundle: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    if dry_run:
        outline = _dry_run_outline(keyword, intent)
    else:
        summary = _summarise_research(research_bundle)
        outline = await _call_outline(keyword, intent, summary)
    _validate_outline(outline)
    return outline


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
        )
        for s in outline["sections"]
    ]
    return list(await asyncio.gather(*tasks))
