from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from check_content_mdx import content_mdx_failures
from generation_agent import _sanitize_outline_mdx, write_sections
from mdx_safety import (
    mdx_syntax_issues,
    prepare_written_mdx,
    sanitize_mdx,
    strip_frontmatter,
)
from mdx_writer import build_article_artifact
from quality_gate import QAResult, run_quality_gate

_ROOT = Path(__file__).resolve().parents[3]
_COMPILE_SCRIPT = _ROOT / "apps" / "web" / "scripts" / "compile-content-mdx.mjs"
_MDX_RUNTIME = _ROOT / "apps" / "web" / "node_modules" / "@mdx-js" / "mdx"


def _section(content: str, h2: str = "Latency") -> dict[str, Any]:
    return {
        "h2": h2,
        "h3s": [],
        "content": content,
        "word_count": len(content.split()),
    }


def _article(content: str, h1: str = "Best AI writing tools") -> dict[str, Any]:
    return {
        "h1": h1,
        "keyword": "best ai writing tools",
        "meta_description": "meta",
        "sections": [_section(content)],
        "faqs": [],
    }


def test_sanitize_escapes_comparison_and_price_angles() -> None:
    raw = "Plus users wait <30 seconds and pay <$10."
    escaped = sanitize_mdx(raw)

    assert escaped == "Plus users wait \\<30 seconds and pay \\<$10."
    assert sanitize_mdx(escaped) == escaped
    assert mdx_syntax_issues(raw)
    assert mdx_syntax_issues(escaped) == []


def test_sanitize_escapes_less_than_or_equal_and_braces() -> None:
    raw = "score <= 1 when cost is {today}"
    escaped = sanitize_mdx(raw)

    assert escaped == "score \\<= 1 when cost is \\{today\\}"
    assert mdx_syntax_issues(escaped) == []


def test_spaced_comparison_stays_literal() -> None:
    raw = "5 < 10 and price < $10"
    assert sanitize_mdx(raw) == raw
    assert mdx_syntax_issues(raw) == []


def test_code_fences_and_inline_code_are_preserved() -> None:
    raw = (
        "```python\n"
        "if n <= 1:\n"
        "    return {n: n}\n"
        "```\n\n"
        "Inline `<30` and `{a}` then wait <30 seconds."
    )
    escaped = sanitize_mdx(raw)

    assert "if n <= 1:" in escaped
    assert "{n: n}" in escaped
    assert "`<30`" in escaped
    assert "`{a}`" in escaped
    assert "\\<30 seconds" in escaped
    assert mdx_syntax_issues(escaped) == []
    assert mdx_syntax_issues(raw)


def test_approved_component_and_link_placeholder_stay() -> None:
    component = (
        "<AffiliateCTA \n"
        '  productName="GitHub Copilot" \n'
        '  ctaText="Explore pricing and try free" \n'
        "/>"
    )
    linked = 'See [Docs]({{LINK_DOCS}}) and <AffiliateCTA partner="jasper" />.'

    assert sanitize_mdx(component) == component
    assert mdx_syntax_issues(component) == []
    assert sanitize_mdx(linked) == linked
    assert mdx_syntax_issues(linked) == []


def test_raw_html_fails_and_approved_placeholders_do_not() -> None:
    html = mdx_syntax_issues("<div>Broken MDX</div>")
    open_component = mdx_syntax_issues("<AffiliateCTA>")

    assert html and "unapproved" in html[0]
    assert open_component and "self-closing" in open_component[0]
    assert mdx_syntax_issues("{{IMAGE_AI_WRITING_TOOLS}}") == []
    assert mdx_syntax_issues("raw {{LINK_DOCS}} in prose") == []


def test_writer_neutralizes_placeholders_mdx_would_execute() -> None:
    raw = "See [Docs]({{LINK_DOCS}}) and {{IMAGE_AI_WRITING_TOOLS}} plus {{LINK_DOCS}}."
    written = prepare_written_mdx(raw)

    assert "[Docs]({{LINK_DOCS}})" in written
    assert "{{IMAGE_" not in written
    assert "\\{\\{LINK_DOCS\\}\\}" in written
    if _MDX_RUNTIME.exists():
        assert _render_mdx(written)


def test_div_inside_fence_is_not_a_syntax_failure() -> None:
    raw = "```html\n<div>Broken</div>\n```\n"
    assert mdx_syntax_issues(raw) == []
    assert sanitize_mdx(raw) == raw


def test_quality_gate_fails_bare_angle_and_passes_escaped() -> None:
    broken = run_quality_gate(_article("Plus users wait <30 seconds and pay <$10."))
    fixed = run_quality_gate(
        _article(sanitize_mdx("Plus users wait <30 seconds and pay <$10."))
    )

    assert _check(broken, "mdx_syntax").result == "FAIL"
    assert _check(fixed, "mdx_syntax").result == "PASS"


def test_writer_escapes_angles_before_disk() -> None:
    article = {
        "slug": "midjourney-vs-dall-e-3",
        "keyword": "midjourney vs dall-e 3",
        "category": "ai-image",
        "intent": "comparison",
        "h1": "Midjourney vs DALL-E 3",
        "meta_description": "Compare Midjourney and DALL-E 3 for image generation.",
        "sections": [
            _section(
                "| Response Time | queue | <30 seconds |",
                h2="Customization Options",
            )
        ],
        "faqs": [],
    }
    body = build_article_artifact(article, QAResult(overall="PASS"))["mdx_body"]

    assert "\\<30 seconds" in body
    assert "<30" not in body.replace("\\<30", "")


def test_outline_and_sections_escape_at_generation() -> None:
    outline = _sanitize_outline_mdx(
        {
            "h1": "Latency <30",
            "sections": [{"h2": "Under <$10", "h3s": ["a < b", "limit <30"]}],
        }
    )
    assert outline["h1"] == "Latency \\<30"
    assert outline["sections"][0]["h2"] == "Under \\<$10"
    assert outline["sections"][0]["h3s"] == ["a < b", "limit \\<30"]

    async def fake_section(*_args: Any, **_kwargs: Any) -> str:
        return "Plus users wait <30 seconds and pay <$10 {now}."

    with patch("generation_agent._call_anthropic_section", side_effect=fake_section):
        sections = asyncio.run(
            write_sections(
                {"sections": [{"h2": "Latency <30", "h3s": []}]},
                {"facts": [], "keyword": "latency"},
                "comparison",
                dry_run=False,
            )
        )

    assert sections[0]["h2"] == "Latency \\<30"
    assert "\\<30" in sections[0]["content"]
    assert "\\<$10" in sections[0]["content"]
    assert "\\{now\\}" in sections[0]["content"]
    assert sections[0]["word_count"] == len(sections[0]["content"].split())
    assert mdx_syntax_issues(sections[0]["content"]) == []


def test_published_articles_pass_mdx_check() -> None:
    assert content_mdx_failures() == []


def test_strip_frontmatter_keeps_body() -> None:
    text = '---\ntitle: "<30"\n---\n\nBody <30'
    assert strip_frontmatter(text).strip() == "Body <30"


def test_compiler_agrees_on_crashing_angles() -> None:
    if not _MDX_RUNTIME.exists():
        pytest.skip("@mdx-js/mdx is not installed")
    samples = {
        "<30 seconds": False,
        "under <$10": False,
        "score <= 1": False,
        "5 < 10 and price < $10": True,
        "```\nif n <= 1:\n  return {n: 1}\n```\n": True,
        "<AffiliateCTA />": True,
        "<div>hi</div>": True,
    }
    for source, should_render in samples.items():
        rendered = _render_mdx(source)
        assert rendered is should_render, source
        if not should_render:
            assert mdx_syntax_issues(source)
            assert _render_mdx(sanitize_mdx(source)) is True
            assert mdx_syntax_issues(sanitize_mdx(source)) == []


def test_content_files_render_with_site_compiler() -> None:
    if not _MDX_RUNTIME.exists():
        pytest.skip("@mdx-js/mdx is not installed")
    completed = subprocess.run(
        ["node", str(_COMPILE_SCRIPT)],
        cwd=_ROOT / "apps" / "web",
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def _render_mdx(source: str) -> bool:
    completed = subprocess.run(
        ["node", str(_COMPILE_SCRIPT), "--stdin"],
        input=source,
        cwd=_ROOT / "apps" / "web",
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode == 0


def _check(result: QAResult, name: str) -> Any:
    return next(check for check in result.checks if check.name == name)
