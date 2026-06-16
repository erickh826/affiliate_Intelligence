from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from typing import Any, Literal

Result = Literal["PASS", "FAIL", "WARN"]
Action = Literal["none", "regenerate", "skip", "auto-fix", "rewrite-section", "log"]

_CONFIG_DIR = Path(__file__).parent / "config"
_BANNED_PHRASES_PATH = _CONFIG_DIR / "banned_phrases.txt"
_APPROVED_MDX_COMPONENTS = frozenset({"AffiliateCTA", "Image"})


def _load_banned_phrases(path: Path = _BANNED_PHRASES_PATH) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


BANNED_PHRASES: list[str] = _load_banned_phrases()

_FACTUAL_RE = re.compile(
    r"\$[\d,]+|"
    r"\d+\s*%|"
    r"\d[\d,]*\s+"
    r"(?:users|customers|companies|teams|tools|articles|people|"
    r"languages|integrations|templates|tokens|requests)",
    re.IGNORECASE,
)

_LINK_PLACEHOLDER_RE = re.compile(r"\{\{LINK_[A-Z0-9_]+\}\}")
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)
_TAG_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9]*)\b[^>]*>")
_SENTENCE_RE = re.compile(r"[.!?]+")
_SYLLABLE_RE = re.compile(r"[aeiouy]+", re.IGNORECASE)
_IMAGE_PLACEHOLDER_RE = re.compile(
    r"!\[[^\]]*\]\([^)]+\)|\{\{IMAGE_[A-Z0-9_]+\}\}|<Image\b[^>]*/>",
    re.IGNORECASE,
)


@dataclass
class CheckResult:
    name: str
    result: Result
    message: str
    action: Action


@dataclass
class QAResult:
    overall: Result
    checks: list[CheckResult] = field(default_factory=list)
    article_updates: dict[str, Any] = field(default_factory=dict)


def _full_text(article: dict[str, Any]) -> str:
    h1 = article.get("h1", "")
    meta = article.get("meta_description", "")
    sections = " ".join(s.get("content", "") for s in article.get("sections", []))
    faqs = " ".join(article.get("faqs", []))
    return f"{h1} {meta} {sections} {faqs}"


def _section_word_count(section: dict[str, Any]) -> int:
    word_count = section.get("word_count")
    if isinstance(word_count, int):
        return word_count
    content = section.get("content", "")
    if isinstance(content, str):
        return len(content.split())
    return 0


def _total_words(article: dict[str, Any]) -> int:
    return sum(_section_word_count(s) for s in article.get("sections", []))


def _check_section_structure(article: dict[str, Any]) -> CheckResult:
    sections = article.get("sections", [])
    if not isinstance(sections, list) or not sections:
        return CheckResult(
            "section_structure",
            "FAIL",
            "sections must be a non-empty list",
            "regenerate",
        )

    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            return CheckResult(
                "section_structure",
                "FAIL",
                f"section {index} is not an object",
                "regenerate",
            )
        h2 = section.get("h2")
        h3s = section.get("h3s")
        content = section.get("content")
        if not isinstance(h2, str) or not h2.strip():
            return CheckResult(
                "section_structure",
                "FAIL",
                f"section {index} missing h2",
                "regenerate",
            )
        if not isinstance(h3s, list) or not all(isinstance(h3, str) for h3 in h3s):
            return CheckResult(
                "section_structure",
                "FAIL",
                f"section {index} h3s must be a string list",
                "regenerate",
            )
        if not isinstance(content, str) or not content.strip():
            return CheckResult(
                "section_structure",
                "FAIL",
                f"section {index} missing content",
                "regenerate",
            )
        if _section_word_count(section) != len(content.split()):
            return CheckResult(
                "section_structure",
                "FAIL",
                f"section {index} word_count does not match content",
                "regenerate",
            )

    return CheckResult("section_structure", "PASS", "section structure valid", "none")


def _check_word_count(article: dict[str, Any]) -> CheckResult:
    n = _total_words(article)
    if n > 1200:
        return CheckResult("word_count", "PASS", f"{n} words", "none")
    return CheckResult("word_count", "FAIL", f"{n} words <= 1,200", "regenerate")


def _check_keyword_in_h1(article: dict[str, Any]) -> CheckResult:
    keyword = article.get("keyword", "").lower().strip()
    h1 = article.get("h1", "").lower()
    if keyword and keyword in h1:
        return CheckResult("keyword_in_h1", "PASS", f"'{keyword}' in H1", "none")
    return CheckResult(
        "keyword_in_h1", "FAIL", f"'{keyword}' not found in H1", "regenerate"
    )


def _check_keyword_in_intro(article: dict[str, Any]) -> CheckResult:
    keyword = article.get("keyword", "").lower().strip()
    sections = article.get("sections", [])
    first_content = sections[0].get("content", "") if sections else ""
    intro = " ".join(str(first_content).split()[:100]).lower()
    if keyword and keyword in intro:
        return CheckResult(
            "keyword_in_intro", "PASS", f"'{keyword}' in first 100 words", "none"
        )
    return CheckResult(
        "keyword_in_intro",
        "FAIL",
        f"'{keyword}' not found in first 100 words",
        "regenerate",
    )


def _check_meta_length(article: dict[str, Any]) -> tuple[CheckResult, dict[str, Any]]:
    meta = article.get("meta_description", "")
    n = len(meta)
    if 140 <= n <= 165:
        return CheckResult("meta_length", "PASS", f"meta {n} chars", "none"), {}
    fixed = _fix_meta_description(article)
    updates: dict[str, Any] = {"meta_description": fixed}
    if n > 165:
        return (
            CheckResult(
                "meta_length",
                "WARN",
                f"meta {n} chars > 165, auto-fixed to {len(fixed)}",
                "auto-fix",
            ),
            updates,
        )
    return (
        CheckResult(
            "meta_length",
            "WARN",
            f"meta {n} chars < 140, auto-fixed to {len(fixed)}",
            "auto-fix",
        ),
        updates,
    )


def _fix_meta_description(article: dict[str, Any]) -> str:
    meta = str(article.get("meta_description", "")).strip()
    h1 = str(article.get("h1", "")).strip()
    keyword = str(article.get("keyword", "")).strip()
    base = meta or h1 or keyword or "AI tool comparison guide"
    additions = [
        " Compare features, pricing, use cases, and trade-offs.",
        " Use this practical guide to choose the right option for your workflow.",
        " Updated with clear recommendations for buyers and teams.",
    ]
    fixed = base
    for addition in additions:
        if len(fixed) >= 140:
            break
        fixed = f"{fixed.rstrip('.')}.{addition}"
    while len(fixed) < 140:
        fixed = f"{fixed.rstrip('.')}. Includes practical pricing and feature guidance."
    if len(fixed) <= 165:
        return fixed
    truncated = fixed[:165].rsplit(" ", 1)[0].rstrip(" ,.;:")
    if len(truncated) < 140:
        truncated = fixed[:165].rstrip(" ,.;:")
    return truncated


def _check_faq_count(article: dict[str, Any]) -> CheckResult:
    n = len(article.get("faqs", []))
    if n >= 4:
        return CheckResult("faq_count", "PASS", f"{n} FAQs", "none")
    return CheckResult("faq_count", "FAIL", f"{n} FAQs < 4", "regenerate")


def _check_factual_anchors(article: dict[str, Any]) -> CheckResult:
    text = _full_text(article)
    matches = _FACTUAL_RE.findall(text)
    n = len(matches)
    if n >= 3:
        return CheckResult("factual_anchors", "PASS", f"{n} factual anchors", "none")
    return CheckResult("factual_anchors", "WARN", f"{n} factual anchors < 3", "log")


def _check_banned_phrases(article: dict[str, Any]) -> CheckResult:
    text = _full_text(article).lower()
    found: list[str] = []
    for phrase in BANNED_PHRASES:
        found.extend(
            match.group(0) for match in re.finditer(re.escape(phrase.lower()), text)
        )
    n = len(found)
    if n < 3:
        return CheckResult("banned_phrases", "PASS", f"{n} banned phrase(s)", "none")
    return CheckResult(
        "banned_phrases",
        "WARN",
        f"{n} banned phrases: {found}",
        "rewrite-section",
    )


def _check_internal_links(article: dict[str, Any]) -> CheckResult:
    text = _full_text(article)
    unresolved = _LINK_PLACEHOLDER_RE.findall(text)
    if not unresolved:
        return CheckResult("internal_links", "PASS", "no broken internal links", "none")
    preview = unresolved[:3]
    return CheckResult(
        "internal_links",
        "WARN",
        f"{len(unresolved)} unresolved link placeholder(s): {preview}",
        "log",
    )


def _check_mdx_syntax(article: dict[str, Any]) -> CheckResult:
    text = _full_text(article)
    for match in _TAG_RE.finditer(text):
        component = match.group(1)
        tag = match.group(0)
        if component not in _APPROVED_MDX_COMPONENTS:
            return CheckResult(
                "mdx_syntax",
                "FAIL",
                f"raw or unapproved tag found: {tag}",
                "regenerate",
            )
        if tag.startswith("</") or not tag.endswith("/>"):
            return CheckResult(
                "mdx_syntax",
                "FAIL",
                f"approved component must be self-closing: {tag}",
                "regenerate",
            )
    return CheckResult("mdx_syntax", "PASS", "MDX syntax preflight passed", "none")


def _check_image_placeholder(article: dict[str, Any]) -> CheckResult:
    text = _full_text(article)
    if _IMAGE_PLACEHOLDER_RE.search(text):
        return CheckResult(
            "image_placeholder", "PASS", "image placeholder present", "none"
        )
    return CheckResult(
        "image_placeholder",
        "WARN",
        "no image placeholder or approved image component found",
        "log",
    )


def _count_syllables(word: str) -> int:
    normalized = re.sub(r"[^a-z]", "", word.lower())
    if not normalized:
        return 0
    groups = _SYLLABLE_RE.findall(normalized)
    count = len(groups)
    if normalized.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _readability_score(text: str) -> float:
    words = _TOKEN_RE.findall(text)
    if not words:
        return 0.0
    sentences = [s for s in _SENTENCE_RE.split(text) if s.strip()]
    sentence_count = max(len(sentences), 1)
    syllables = sum(_count_syllables(word) for word in words)
    return (
        206.835
        - 1.015 * (len(words) / sentence_count)
        - 84.6 * (syllables / len(words))
    )


def _check_readability(article: dict[str, Any]) -> CheckResult:
    score = _readability_score(_full_text(article))
    if score >= 30:
        return CheckResult(
            "readability", "PASS", f"Flesch reading ease {score:.1f}", "none"
        )
    return CheckResult(
        "readability",
        "WARN",
        f"Flesch reading ease {score:.1f} < 30",
        "log",
    )


def _cosine_similarity(text_a: str, text_b: str) -> float:
    tokens_a = _TOKEN_RE.findall(text_a.lower())
    tokens_b = _TOKEN_RE.findall(text_b.lower())
    if not tokens_a or not tokens_b:
        return 0.0
    vector_a = Counter(tokens_a)
    vector_b = Counter(tokens_b)
    shared = vector_a.keys() & vector_b.keys()
    dot = sum(vector_a[token] * vector_b[token] for token in shared)
    norm_a = sqrt(sum(count * count for count in vector_a.values()))
    norm_b = sqrt(sum(count * count for count in vector_b.values()))
    return dot / (norm_a * norm_b)


def _check_duplicate(
    article: dict[str, Any],
    existing_articles: list[dict[str, Any]],
) -> CheckResult:
    if not existing_articles:
        return CheckResult(
            "duplicate_detection", "PASS", "no existing articles to compare", "none"
        )
    text = _full_text(article)
    for existing in existing_articles:
        sim = _cosine_similarity(text, _full_text(existing))
        if sim >= 0.85:
            slug = existing.get("slug", "unknown")
            return CheckResult(
                "duplicate_detection",
                "FAIL",
                f"similarity {sim:.2f} >= 0.85 vs '{slug}'",
                "skip",
            )
    return CheckResult("duplicate_detection", "PASS", "unique content", "none")


def run_quality_gate(
    article: dict[str, Any],
    existing_articles: list[dict[str, Any]] | None = None,
) -> QAResult:
    """Run deterministic SPEC-01 quality checks for a generated article."""
    checks: list[CheckResult] = []
    article_updates: dict[str, Any] = {}

    section_structure = _check_section_structure(article)
    checks.append(section_structure)
    if section_structure.result == "FAIL":
        article_updates["status"] = "failed"
        return QAResult(overall="FAIL", checks=checks, article_updates=article_updates)

    checks.append(_check_word_count(article))
    checks.append(_check_keyword_in_h1(article))
    checks.append(_check_keyword_in_intro(article))

    meta_check, meta_updates = _check_meta_length(article)
    checks.append(meta_check)
    article_updates.update(meta_updates)

    checks.append(_check_faq_count(article))
    checks.append(_check_factual_anchors(article))
    checks.append(_check_banned_phrases(article))
    checks.append(_check_internal_links(article))
    checks.append(_check_mdx_syntax(article))
    checks.append(_check_image_placeholder(article))
    checks.append(_check_readability(article))
    checks.append(_check_duplicate(article, existing_articles or []))

    if any(c.result == "FAIL" for c in checks):
        overall: Result = "FAIL"
        article_updates["status"] = "failed"
    elif any(c.result == "WARN" for c in checks):
        overall = "WARN"
    else:
        overall = "PASS"

    return QAResult(overall=overall, checks=checks, article_updates=article_updates)
