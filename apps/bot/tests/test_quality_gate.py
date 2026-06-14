from __future__ import annotations

from typing import Any

from quality_gate import (
    BANNED_PHRASES,
    CheckResult,
    QAResult,
    _cosine_similarity,
    run_quality_gate,
)


def _section(
    label: str, words: int = 310, content: str | None = None
) -> dict[str, Any]:
    sentence = f"{label} tools help teams write clear drafts with simple workflows."
    if content is None:
        text = " ".join([sentence] * ((words // len(sentence.split())) + 1))
        text = " ".join(text.split()[:words])
    else:
        text = content
    return {
        "h2": f"{label} Section",
        "h3s": [f"{label} Detail"],
        "content": text,
        "word_count": len(text.split()),
    }


def _intro_section(content: str | None = None) -> dict[str, Any]:
    return _section(
        "alpha",
        content=content
        or (
            "Best AI writing tools help content teams compare pricing and workflow fit. "
            "{{IMAGE_AI_WRITING_TOOLS}} "
            + " ".join(["These tools make planning drafts simple and clear."] * 38)
        ),
    )


def _sync_word_count(section: dict[str, Any]) -> None:
    section["word_count"] = len(str(section.get("content", "")).split())


def _article(**overrides: Any) -> dict[str, Any]:
    article: dict[str, Any] = {
        "slug": "best-ai-writing-tools",
        "keyword": "best ai writing tools",
        "h1": "Best AI Writing Tools for Teams",
        "meta_description": (
            "Compare the best AI writing tools for teams, including pricing, "
            "features, workflow fit, and practical trade-offs for modern "
            "content operations teams."
        ),
        "sections": [
            _intro_section(),
            _section("bravo"),
            _section("charlie"),
            _section(
                "delta",
                content=(
                    "Jasper starts at $49 per month. Teams report 30% faster drafts. "
                    "This guide compares 12 tools for long-context writing. "
                    + " ".join(f"delta-word-{i}" for i in range(290))
                ),
            ),
        ],
        "faqs": [
            "What is the best AI writing tool?",
            "How much do AI writing tools cost?",
            "Which AI writing tool is best for teams?",
            "Are free AI writing tools worth using?",
        ],
    }
    article.update(overrides)
    return article


def _check(results: QAResult, name: str) -> CheckResult:
    return next(check for check in results.checks if check.name == name)


def test_valid_article_passes_all_checks() -> None:
    result = run_quality_gate(_article())

    assert result.overall == "PASS"
    assert all(check.result == "PASS" for check in result.checks)
    assert result.article_updates == {}


def test_word_count_under_threshold_fails_and_sets_failed_status() -> None:
    article = _article(sections=[_section("short", words=200)])

    result = run_quality_gate(article)

    assert result.overall == "FAIL"
    assert _check(result, "word_count").result == "FAIL"
    assert _check(result, "word_count").action == "regenerate"
    assert result.article_updates["status"] == "failed"


def test_duplicate_detection_uses_cosine_similarity_threshold() -> None:
    article = _article()
    existing = [{**article, "slug": "existing-ai-writing-tools"}]

    result = run_quality_gate(article, existing_articles=existing)

    assert _cosine_similarity("alpha alpha beta", "alpha beta beta") > 0
    assert _check(result, "duplicate_detection").result == "FAIL"
    assert _check(result, "duplicate_detection").action == "skip"


def test_different_existing_article_passes_duplicate_check() -> None:
    article = _article()
    existing = [
        _article(
            slug="email-marketing-automation",
            keyword="email marketing automation",
            h1="Email Marketing Automation Guide",
            sections=[
                _section("email"),
                _section("campaign"),
                _section("automation"),
                _section("crm"),
            ],
        )
    ]

    result = run_quality_gate(article, existing_articles=existing)

    assert _check(result, "duplicate_detection").result == "PASS"


def test_factual_anchor_count_below_threshold_warns() -> None:
    article = _article(
        sections=[
            _intro_section(
                "Best AI writing tools help content teams compare options. "
                "{{IMAGE_AI_WRITING_TOOLS}} "
                + " ".join(["These tools make planning drafts simple and clear."] * 38)
            ),
            _section("bravo"),
            _section("charlie"),
            _section("delta"),
        ]
    )

    result = run_quality_gate(article)

    assert result.overall == "WARN"
    assert _check(result, "factual_anchors").result == "WARN"
    assert _check(result, "factual_anchors").action == "log"


def test_missing_keyword_in_h1_fails() -> None:
    result = run_quality_gate(_article(h1="Top Content Platforms for Teams"))

    assert result.overall == "FAIL"
    assert _check(result, "keyword_in_h1").result == "FAIL"


def test_missing_keyword_in_intro_fails() -> None:
    article = _article(
        sections=[
            _section(
                "alpha",
                content="{{IMAGE_AI_WRITING_TOOLS}} This opening talks about workflow but omits the target phrase. "
                + " ".join(["Teams can compare pricing and features clearly."] * 40),
            ),
            _section("bravo"),
            _section("charlie"),
            _section(
                "delta",
                content=(
                    "Jasper starts at $49 per month. Teams report 30% faster drafts. "
                    "This guide compares 12 tools for long-context writing. "
                    + " ".join(["This section is clear and useful."] * 50)
                ),
            ),
        ]
    )

    result = run_quality_gate(article)

    assert result.overall == "FAIL"
    assert _check(result, "keyword_in_intro").result == "FAIL"


def test_short_meta_description_is_auto_fixed() -> None:
    result = run_quality_gate(_article(meta_description="Short meta."))

    fixed = result.article_updates["meta_description"]
    assert _check(result, "meta_length").result == "WARN"
    assert _check(result, "meta_length").action == "auto-fix"
    assert 140 <= len(fixed) <= 165


def test_long_meta_description_is_auto_fixed() -> None:
    result = run_quality_gate(_article(meta_description="Long meta " * 30))

    fixed = result.article_updates["meta_description"]
    assert _check(result, "meta_length").result == "WARN"
    assert 140 <= len(fixed) <= 165


def test_faq_count_below_threshold_fails() -> None:
    result = run_quality_gate(_article(faqs=["Question one?", "Question two?"]))

    assert result.overall == "FAIL"
    assert _check(result, "faq_count").result == "FAIL"


def test_unresolved_internal_link_placeholder_warns() -> None:
    article = _article(
        sections=[
            _intro_section(),
            _section("bravo"),
            _section("charlie"),
            _section(
                "delta",
                content=(
                    "Jasper starts at $49 per month. Teams report 30% faster drafts. "
                    "Some platforms support 128k tokens for long-context writing. "
                    "[AI Writing Tools]({{LINK_AI_WRITING}}) "
                    + " ".join(f"delta-word-{i}" for i in range(290))
                ),
            ),
        ],
    )

    result = run_quality_gate(article)

    assert result.overall == "WARN"
    assert _check(result, "internal_links").result == "WARN"
    assert _check(result, "internal_links").action == "log"


def test_raw_html_tag_fails_mdx_syntax_preflight() -> None:
    article = _article(
        sections=[
            _section(
                "alpha",
                content=(
                    "Best AI writing tools help teams choose better software. "
                    "{{IMAGE_AI_WRITING_TOOLS}} <div>Broken MDX</div> "
                    + " ".join(["This section stays readable and useful."] * 40)
                ),
            ),
            _section("bravo"),
            _section("charlie"),
            _section(
                "delta",
                content=(
                    "Jasper starts at $49 per month. Teams report 30% faster drafts. "
                    "This guide compares 12 tools for long-context writing. "
                    + " ".join(["This section stays readable and useful."] * 50)
                ),
            ),
        ]
    )

    result = run_quality_gate(article)

    assert result.overall == "FAIL"
    assert _check(result, "mdx_syntax").result == "FAIL"


def test_affiliate_cta_self_closing_component_passes_mdx_syntax() -> None:
    article = _article(
        sections=[
            _section(
                "alpha",
                content=(
                    'Best AI writing tools help teams choose better software. <AffiliateCTA partner="jasper" /> '
                    "{{IMAGE_AI_WRITING_TOOLS}} "
                    + " ".join(["This section stays readable and useful."] * 40)
                ),
            ),
            _section("bravo"),
            _section("charlie"),
            _section(
                "delta",
                content=(
                    "Jasper starts at $49 per month. Teams report 30% faster drafts. "
                    "This guide compares 12 tools for long-context writing. "
                    + " ".join(["This section stays readable and useful."] * 50)
                ),
            ),
        ]
    )

    result = run_quality_gate(article)

    assert _check(result, "mdx_syntax").result == "PASS"


def test_missing_image_placeholder_warns() -> None:
    article = _article()
    article["sections"][0]["content"] = article["sections"][0]["content"].replace(
        "{{IMAGE_AI_WRITING_TOOLS}}", ""
    )
    _sync_word_count(article["sections"][0])

    result = run_quality_gate(article)

    assert result.overall == "WARN"
    assert _check(result, "image_placeholder").result == "WARN"


def test_dense_readability_warns() -> None:
    dense = (
        "Best AI writing tools "
        + " ".join(["hypercontextualization multidimensionality"] * 620)
        + " {{IMAGE_AI_WRITING_TOOLS}} Jasper starts at $49 per month. Teams report 30% faster drafts. This guide compares 12 tools."
    )
    result = run_quality_gate(_article(sections=[_section("dense", content=dense)]))

    assert result.overall == "WARN"
    assert _check(result, "readability").result == "WARN"


def test_three_banned_phrase_instances_warn_for_section_rewrite() -> None:
    article = _article(
        sections=[
            _section(
                "alpha",
                content=(
                    "Best AI writing tools {{IMAGE_AI_WRITING_TOOLS}} "
                    "In today's digital landscape, this can be a game-changer. "
                    "At the end of the day, teams still need proof. "
                    "Jasper starts at $49 per month. Teams report 30% faster drafts. "
                    "This guide compares 12 tools. "
                    + " ".join(f"alpha-word-{i}" for i in range(1180))
                ),
            )
        ]
    )

    result = run_quality_gate(article)

    assert result.overall == "WARN"
    assert _check(result, "banned_phrases").result == "WARN"
    assert _check(result, "banned_phrases").action == "rewrite-section"


def test_banned_phrases_match_spec() -> None:
    for phrase in [
        "in today's digital landscape",
        "it's worth noting that",
        "at the end of the day",
        "needless to say",
        "as an AI language model",
        "game-changer",
        "empower your",
        "unlock the power of",
        "transformative journey",
        "in conclusion",
    ]:
        assert phrase in BANNED_PHRASES


def test_banned_phrases_include_configured_ai_filler_phrases() -> None:
    assert "in the rapidly evolving landscape" in BANNED_PHRASES
    assert "delve into" in BANNED_PHRASES


def test_missing_generated_section_shape_fails() -> None:
    article = _article(
        sections=[{"h2": "Incomplete", "content": "text", "word_count": 1}]
    )

    result = run_quality_gate(article)

    assert result.overall == "FAIL"
    assert _check(result, "section_structure").result == "FAIL"


def test_non_object_section_returns_structured_failure() -> None:
    result = run_quality_gate(_article(sections=["not-a-section-object"]))

    assert result.overall == "FAIL"
    assert result.article_updates["status"] == "failed"
    assert _check(result, "section_structure").result == "FAIL"


def test_mismatched_section_word_count_fails() -> None:
    bad_section = _section("bad")
    bad_section["word_count"] = bad_section["word_count"] + 1

    result = run_quality_gate(_article(sections=[bad_section]))

    assert result.overall == "FAIL"
    assert _check(result, "section_structure").result == "FAIL"
