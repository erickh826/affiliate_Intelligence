from __future__ import annotations

from typing import Any, TypedDict

from quality_gate import QAResult

__all__ = [
    "ResearchContext",
    "GeneratedSection",
    "GenerationContext",
    "Frontmatter",
    "FAQItem",
    "AffiliateMap",
    "ArticleArtifact",
]


class ResearchContext(TypedDict):
    keyword: str
    intent: str
    competitors_scraped: list[dict[str, Any]]
    facts: list[dict[str, Any]]
    tools_mentioned: list[dict[str, Any]]
    faq_seeds: list[str]


class GeneratedSection(TypedDict):
    h2: str
    h3s: list[str]
    content: str
    word_count: int


class GenerationContext(TypedDict):
    keyword: str
    slug: str
    category: str
    intent: str
    h1: str
    meta_description: str
    sections: list[GeneratedSection]
    faqs: list[str]
    affiliate_partner: str | None
    outline: dict[str, Any]


class Frontmatter(TypedDict):
    title: str
    description: str
    slug: str
    category: str
    intent: str
    published_at: str
    last_reviewed: str
    author: str
    affiliate_partner: str | None
    schema_type: str


class FAQItem(TypedDict):
    question: str
    answer: str


class AffiliateMap(TypedDict):
    slug: str
    primary_partner: str | None
    cta_variant: str
    links: dict[str, str]


class ArticleArtifact(TypedDict):
    slug: str
    category: str
    frontmatter: Frontmatter
    mdx_body: str
    faq_json: list[FAQItem]
    affiliate_map: AffiliateMap
    qa_result: QAResult
