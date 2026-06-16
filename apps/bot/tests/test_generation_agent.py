from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from generation_agent import (
    _MAX_CONCURRENCY,
    _dry_run_outline,
    _dry_run_section,
    _outline_prompt,
    _section_prompt,
    _summarise_research,
    _validate_outline,
    generate_outline,
    write_sections,
)

_MOCK_RESEARCH: dict[str, Any] = {
    "keyword": "best ai writing tools",
    "intent": "comparison",
    "facts": [
        {"claim": "Jasper AI costs $49/month", "source": "jasper.ai"},
        {"claim": "GPT-4 has 128k context window", "source": "openai.com"},
        {"claim": "Writesonic starts at $19/month", "source": "writesonic.com"},
    ],
    "tools_mentioned": [
        {
            "name": "Jasper",
            "pricing": "$49/mo",
            "pros": ["fast"],
            "cons": ["expensive"],
        },
        {
            "name": "Writesonic",
            "pricing": "$19/mo",
            "pros": ["cheap"],
            "cons": ["limited"],
        },
    ],
    "faq_seeds": ["What is the best AI writing tool?"],
    "competitors_scraped": [],
}

_MOCK_OUTLINE = _dry_run_outline("best ai writing tools", "comparison")


class TestSummariseResearch:
    def test_includes_facts(self) -> None:
        s = _summarise_research(_MOCK_RESEARCH)
        assert "Jasper AI costs $49/month" in s

    def test_includes_tools(self) -> None:
        s = _summarise_research(_MOCK_RESEARCH)
        assert "Jasper" in s

    def test_empty_bundle_returns_string(self) -> None:
        assert isinstance(_summarise_research({}), str)

    def test_caps_facts_at_five(self) -> None:
        bundle = {"facts": [{"claim": f"claim {i}", "source": "x"} for i in range(10)]}
        s = _summarise_research(bundle)
        assert s.count("claim") <= 5


class TestOutlinePrompt:
    def test_contains_keyword(self) -> None:
        p = _outline_prompt("best ai tools", "comparison", "research")
        assert "best ai tools" in p

    def test_contains_intent(self) -> None:
        p = _outline_prompt("best ai tools", "comparison", "research")
        assert "comparison" in p

    def test_contains_research_summary(self) -> None:
        p = _outline_prompt("kw", "informational", "key fact here")
        assert "key fact here" in p


class TestSectionPrompt:
    def test_comparison_requires_pricing_table(self) -> None:
        p = _section_prompt("Top Tools", ["Overview"], [], "comparison")
        assert "pricing comparison table" in p.lower()

    def test_tutorial_requires_steps_or_code(self) -> None:
        p = _section_prompt("How to Use", ["Step 1"], [], "tutorial")
        assert "code snippet" in p.lower() or "numbered steps" in p.lower()

    def test_informational_requires_statistic(self) -> None:
        p = _section_prompt("Overview", ["Basics"], [], "informational")
        assert "statistic" in p.lower()

    def test_includes_h2(self) -> None:
        p = _section_prompt("My Section", ["h3a"], [], "informational")
        assert "My Section" in p

    def test_includes_h3s(self) -> None:
        p = _section_prompt("H2", ["Sub A", "Sub B"], [], "informational")
        assert "Sub A" in p

    def test_section_prompt_contains_affiliate_cta(self) -> None:
        p = _section_prompt("H2", ["H3"], [], "comparison", affiliate_partner="jasper")
        assert (
            'AFFILIATE CTA: You MUST include exactly one <AffiliateCTA partner="jasper" />'
            in p
        )

    def test_section_prompt_contains_internal_links_instruction(self) -> None:
        p = _section_prompt("H2", ["H3"], [], "comparison")
        assert "INTERNAL LINKING: Use placeholders like [Link Text]({{LINK_SLUG}})" in p

    def test_section_prompt_contains_style_guide(self) -> None:
        p = _section_prompt(
            "H2", ["H3"], [], "comparison", style_guide="Professional and authoritative"
        )
        assert "Tone/Style: Professional and authoritative" in p

    def test_system_section_contains_mdx_safety(self) -> None:
        from generation_agent import _SYSTEM_SECTION

        assert "MDX SAFETY RULES" in _SYSTEM_SECTION
        assert "ONLY use approved MDX components" in _SYSTEM_SECTION
        assert "PROHIBIT raw HTML tags" in _SYSTEM_SECTION
        assert "ESCAPE curly braces" in _SYSTEM_SECTION
        assert "do not escape approved placeholders like {{LINK_*}}" in _SYSTEM_SECTION


class TestValidateOutline:
    def test_valid_outline_passes(self) -> None:
        _validate_outline(dict(_MOCK_OUTLINE))

    def test_missing_h1_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {k: v for k, v in _MOCK_OUTLINE.items() if k != "h1"}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_missing_meta_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {k: v for k, v in _MOCK_OUTLINE.items() if k != "meta_description"}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_missing_sections_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {k: v for k, v in _MOCK_OUTLINE.items() if k != "sections"}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_missing_faqs_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {k: v for k, v in _MOCK_OUTLINE.items() if k != "faqs"}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_too_few_sections_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {**_MOCK_OUTLINE, "sections": _MOCK_OUTLINE["sections"][:3]}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_too_many_sections_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {**_MOCK_OUTLINE, "sections": _MOCK_OUTLINE["sections"] * 2}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_too_few_faqs_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {**_MOCK_OUTLINE, "faqs": _MOCK_OUTLINE["faqs"][:3]}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_meta_over_165_raises(self) -> None:
        from generation_agent import ValidationError

        bad = {**_MOCK_OUTLINE, "meta_description": "x" * 200}
        with pytest.raises(ValidationError, match="Outline validation failed"):
            _validate_outline(bad)

    def test_meta_at_165_is_unchanged(self) -> None:
        outline = {**_MOCK_OUTLINE, "meta_description": "a" * 165}
        _validate_outline(outline)
        assert len(outline["meta_description"]) == 165


class TestDryRunOutline:
    def test_produces_valid_outline(self) -> None:
        _validate_outline(_dry_run_outline("best ai tools", "informational"))

    def test_comparison_includes_comparison_columns(self) -> None:
        outline = _dry_run_outline("best ai tools", "comparison")
        assert "comparison_columns" in outline
        assert len(outline["comparison_columns"]) >= 1

    def test_informational_has_no_comparison_columns(self) -> None:
        assert "comparison_columns" not in _dry_run_outline("kw", "informational")

    def test_tutorial_has_no_comparison_columns(self) -> None:
        assert "comparison_columns" not in _dry_run_outline("kw", "tutorial")

    def test_keyword_present_in_h1(self) -> None:
        outline = _dry_run_outline("best ai writing tools", "comparison")
        assert "best ai writing tools" in outline["h1"].lower()

    def test_exactly_five_faqs(self) -> None:
        assert len(_dry_run_outline("kw", "informational")["faqs"]) == 5


class TestDryRunSection:
    def test_has_all_required_keys(self) -> None:
        s = _dry_run_section("Top Tools", ["Overview", "Pricing"])
        for k in ("h2", "h3s", "content", "word_count"):
            assert k in s

    def test_word_count_matches_content(self) -> None:
        s = _dry_run_section("Top Tools", ["Overview"])
        assert s["word_count"] == len(s["content"].split())

    def test_word_count_at_least_200(self) -> None:
        assert _dry_run_section("H2", ["h3"])["word_count"] >= 200

    def test_h2_preserved(self) -> None:
        assert _dry_run_section("My Section", ["h3"])["h2"] == "My Section"

    def test_h3s_preserved(self) -> None:
        h3s = ["Sub A", "Sub B"]
        assert _dry_run_section("H2", h3s)["h3s"] == h3s


class TestGenerateOutlineDryRun:
    def test_returns_valid_outline(self) -> None:
        outline = asyncio.run(
            generate_outline(
                "best ai tools", "comparison", _MOCK_RESEARCH, dry_run=True
            )
        )
        _validate_outline(outline)

    def test_does_not_call_openai(self) -> None:
        with patch("generation_agent._call_outline") as mock:
            asyncio.run(
                generate_outline(
                    "best ai tools", "comparison", _MOCK_RESEARCH, dry_run=True
                )
            )
        mock.assert_not_called()

    def test_comparison_outline_has_columns(self) -> None:
        outline = asyncio.run(generate_outline("tools", "comparison", {}, dry_run=True))
        assert "comparison_columns" in outline


class TestGenerateOutlineLive:
    def test_calls_call_outline(self) -> None:
        expected = _dry_run_outline("best ai tools", "comparison")
        with patch(
            "generation_agent._call_outline",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = asyncio.run(
                generate_outline(
                    "best ai tools", "comparison", _MOCK_RESEARCH, dry_run=False
                )
            )
        assert result["h1"] == expected["h1"]

    def test_validates_outline_from_api(self) -> None:
        from generation_agent import ValidationError

        bad_outline: dict[str, Any] = {"h1": "title"}
        with patch(
            "generation_agent._call_outline",
            new_callable=AsyncMock,
            return_value=bad_outline,
        ):
            with pytest.raises(ValidationError):
                asyncio.run(generate_outline("kw", "comparison", {}, dry_run=False))


class TestWriteSectionsDryRun:
    def test_returns_one_section_per_outline_h2(self) -> None:
        sections = asyncio.run(
            write_sections(_MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=True)
        )
        assert len(sections) == len(_MOCK_OUTLINE["sections"])

    def test_all_sections_have_content(self) -> None:
        sections = asyncio.run(
            write_sections(_MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=True)
        )
        assert all(s["content"] for s in sections)

    def test_h2s_match_outline(self) -> None:
        sections = asyncio.run(
            write_sections(_MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=True)
        )
        outline_h2s = {s["h2"] for s in _MOCK_OUTLINE["sections"]}
        result_h2s = {s["h2"] for s in sections}
        assert outline_h2s == result_h2s

    def test_does_not_call_anthropic(self) -> None:
        with patch("generation_agent._call_anthropic_section") as mock:
            asyncio.run(
                write_sections(
                    _MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=True
                )
            )
        mock.assert_not_called()

    def test_does_not_call_openai(self) -> None:
        with patch("generation_agent._call_openai_section") as mock:
            asyncio.run(
                write_sections(
                    _MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=True
                )
            )
        mock.assert_not_called()


class TestWriteSectionsLive:
    def test_max_concurrency_never_exceeded(self) -> None:
        active = 0
        max_active = 0

        async def mock_anthropic(h2: str, *a: Any, **kw: Any) -> str:
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.02)
            active -= 1
            return "content with $49/month pricing"

        with patch(
            "generation_agent._call_anthropic_section", side_effect=mock_anthropic
        ):
            asyncio.run(
                write_sections(
                    _MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=False
                )
            )

        assert max_active <= _MAX_CONCURRENCY

    def test_falls_back_to_openai_when_anthropic_fails(self) -> None:
        from generation_agent import LLMAPIError

        async def fail(*a: Any, **kw: Any) -> str:
            raise LLMAPIError("anthropic down")

        async def succeed(*a: Any, **kw: Any) -> str:
            return "openai fallback content $29/month"

        with (
            patch("generation_agent._call_anthropic_section", side_effect=fail),
            patch("generation_agent._call_openai_section", side_effect=succeed),
        ):
            sections = asyncio.run(
                write_sections(
                    _MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=False
                )
            )
            assert sections[0]["content"] == "openai fallback content $29/month"

        assert all("openai fallback" in s["content"] for s in sections)

    def test_openai_not_called_when_anthropic_succeeds(self) -> None:
        async def succeed_anthropic(*a: Any, **kw: Any) -> str:
            return "anthropic content $49/month"

        with (
            patch(
                "generation_agent._call_anthropic_section",
                side_effect=succeed_anthropic,
            ),
            patch("generation_agent._call_openai_section") as openai_mock,
        ):
            asyncio.run(
                write_sections(
                    _MOCK_OUTLINE, _MOCK_RESEARCH, "comparison", dry_run=False
                )
            )

        openai_mock.assert_not_called()

    def test_sections_include_word_count(self) -> None:
        async def mock_content(*a: Any, **kw: Any) -> str:
            return "word " * 350

        with patch(
            "generation_agent._call_anthropic_section", side_effect=mock_content
        ):
            sections = asyncio.run(
                write_sections(
                    _MOCK_OUTLINE, _MOCK_RESEARCH, "informational", dry_run=False
                )
            )

        assert all(s["word_count"] > 0 for s in sections)
        assert all(s["word_count"] == len(s["content"].split()) for s in sections)
