from __future__ import annotations

from quality_gate import CheckResult, QAResult

from models import (
    AffiliateMap,
    ArticleArtifact,
    FAQItem,
    Frontmatter,
    GeneratedSection,
    GenerationContext,
    ResearchContext,
)

_ALL_CONTRACTS = (
    ResearchContext,
    GeneratedSection,
    GenerationContext,
    Frontmatter,
    FAQItem,
    AffiliateMap,
    ArticleArtifact,
)

_REQUIRED_KEYS: dict[type, set[str]] = {
    ResearchContext: {
        "keyword",
        "intent",
        "competitors_scraped",
        "facts",
        "tools_mentioned",
        "faq_seeds",
    },
    GeneratedSection: {"h2", "h3s", "content", "word_count"},
    GenerationContext: {
        "keyword",
        "slug",
        "category",
        "intent",
        "h1",
        "meta_description",
        "sections",
        "faqs",
        "affiliate_partner",
        "outline",
    },
    Frontmatter: {
        "title",
        "description",
        "slug",
        "category",
        "intent",
        "published_at",
        "last_reviewed",
        "author",
        "affiliate_partner",
        "schema_type",
    },
    FAQItem: {"question", "answer"},
    AffiliateMap: {"slug", "primary_partner", "cta_variant", "links"},
    ArticleArtifact: {
        "slug",
        "category",
        "frontmatter",
        "mdx_body",
        "faq_json",
        "affiliate_map",
        "qa_result",
    },
}


class TestImports:
    def test_all_contracts_importable(self) -> None:
        for cls in _ALL_CONTRACTS:
            assert cls is not None

    def test_all_contracts_are_typed_dicts(self) -> None:
        for cls in _ALL_CONTRACTS:
            assert hasattr(cls, "__annotations__")


class TestContractKeys:
    def test_research_context_keys(self) -> None:
        assert _REQUIRED_KEYS[ResearchContext].issubset(ResearchContext.__annotations__)

    def test_generated_section_keys(self) -> None:
        assert _REQUIRED_KEYS[GeneratedSection].issubset(
            GeneratedSection.__annotations__
        )

    def test_generation_context_keys(self) -> None:
        assert _REQUIRED_KEYS[GenerationContext].issubset(
            GenerationContext.__annotations__
        )

    def test_frontmatter_keys(self) -> None:
        assert _REQUIRED_KEYS[Frontmatter].issubset(Frontmatter.__annotations__)

    def test_faq_item_keys(self) -> None:
        assert _REQUIRED_KEYS[FAQItem].issubset(FAQItem.__annotations__)

    def test_affiliate_map_keys(self) -> None:
        assert _REQUIRED_KEYS[AffiliateMap].issubset(AffiliateMap.__annotations__)

    def test_article_artifact_keys(self) -> None:
        assert _REQUIRED_KEYS[ArticleArtifact].issubset(ArticleArtifact.__annotations__)


class TestResearchContext:
    def test_minimal_valid_dict(self) -> None:
        ctx: ResearchContext = {
            "keyword": "best ai writing tools",
            "intent": "comparison",
            "competitors_scraped": [
                {
                    "url": "https://example.com",
                    "title": "Example",
                    "headings": [],
                    "body_summary": "",
                }
            ],
            "facts": [{"claim": "Jasper costs $49/month", "source": "jasper.ai"}],
            "tools_mentioned": [
                {"name": "Jasper", "pricing": "$49/mo", "pros": [], "cons": []}
            ],
            "faq_seeds": ["What is the best AI writing tool?"],
        }
        assert ctx["keyword"] == "best ai writing tools"
        assert ctx["intent"] == "comparison"
        assert len(ctx["competitors_scraped"]) == 1
        assert len(ctx["facts"]) == 1
        assert len(ctx["tools_mentioned"]) == 1
        assert len(ctx["faq_seeds"]) == 1

    def test_empty_lists_valid(self) -> None:
        ctx: ResearchContext = {
            "keyword": "kw",
            "intent": "informational",
            "competitors_scraped": [],
            "facts": [],
            "tools_mentioned": [],
            "faq_seeds": [],
        }
        assert ctx["competitors_scraped"] == []


class TestGeneratedSection:
    def test_minimal_valid_dict(self) -> None:
        section: GeneratedSection = {
            "h2": "Top AI Writing Tools",
            "h3s": ["Jasper AI", "Writesonic"],
            "content": "Jasper AI costs $49/month and offers unlimited words.",
            "word_count": 9,
        }
        assert section["h2"] == "Top AI Writing Tools"
        assert section["word_count"] == 9

    def test_empty_h3s_valid(self) -> None:
        section: GeneratedSection = {
            "h2": "Overview",
            "h3s": [],
            "content": "Content here.",
            "word_count": 2,
        }
        assert section["h3s"] == []


class TestGenerationContext:
    def test_minimal_valid_dict(self) -> None:
        section: GeneratedSection = {
            "h2": "Overview",
            "h3s": ["Definition"],
            "content": "Content about AI tools.",
            "word_count": 4,
        }
        ctx: GenerationContext = {
            "keyword": "best ai writing tools",
            "slug": "best-ai-writing-tools",
            "category": "ai-writing",
            "intent": "comparison",
            "h1": "Best AI Writing Tools: Complete Guide for 2026",
            "meta_description": "Compare the best AI writing tools in 2026. Features, pricing, and honest reviews.",
            "sections": [section],
            "faqs": ["What is the best AI writing tool?"],
            "affiliate_partner": "jasper",
            "outline": {
                "h1": "Best AI Writing Tools",
                "sections": [],
                "faqs": [],
                "meta_description": "",
            },
        }
        assert ctx["slug"] == "best-ai-writing-tools"
        assert ctx["affiliate_partner"] == "jasper"

    def test_affiliate_partner_can_be_none(self) -> None:
        ctx: GenerationContext = {
            "keyword": "kw",
            "slug": "kw",
            "category": "ai-writing",
            "intent": "informational",
            "h1": "KW Title",
            "meta_description": "Description.",
            "sections": [],
            "faqs": [],
            "affiliate_partner": None,
            "outline": {},
        }
        assert ctx["affiliate_partner"] is None


class TestFrontmatter:
    def test_minimal_valid_dict(self) -> None:
        fm: Frontmatter = {
            "title": "Best AI Writing Tools: Complete Guide for 2026",
            "description": "Compare the best AI writing tools in 2026.",
            "slug": "best-ai-writing-tools",
            "category": "ai-writing",
            "intent": "comparison",
            "published_at": "2026-05-18",
            "last_reviewed": "2026-05-18",
            "author": "Affiliate Intelligence Editorial Team",
            "affiliate_partner": "jasper",
            "schema_type": "Article",
        }
        assert fm["schema_type"] == "Article"
        assert fm["published_at"] == "2026-05-18"

    def test_spec_01_fields_present(self) -> None:
        spec_fields = {
            "title",
            "description",
            "slug",
            "category",
            "intent",
            "published_at",
            "last_reviewed",
            "author",
            "affiliate_partner",
            "schema_type",
        }
        assert spec_fields == set(Frontmatter.__annotations__.keys())


class TestFAQItem:
    def test_minimal_valid_dict(self) -> None:
        item: FAQItem = {
            "question": "What is Jasper AI?",
            "answer": "Jasper AI is an AI writing tool.",
        }
        assert item["question"] == "What is Jasper AI?"

    def test_empty_answer_valid(self) -> None:
        item: FAQItem = {"question": "Q?", "answer": ""}
        assert item["answer"] == ""


class TestAffiliateMap:
    def test_minimal_valid_dict(self) -> None:
        amap: AffiliateMap = {
            "slug": "best-ai-writing-tools",
            "primary_partner": "jasper",
            "cta_variant": "A",
            "links": {"jasper": "https://jasper.ai/?via=ref"},
        }
        assert amap["cta_variant"] == "A"

    def test_primary_partner_can_be_none(self) -> None:
        amap: AffiliateMap = {
            "slug": "some-article",
            "primary_partner": None,
            "cta_variant": "B",
            "links": {},
        }
        assert amap["primary_partner"] is None

    def test_empty_links_valid(self) -> None:
        amap: AffiliateMap = {
            "slug": "slug",
            "primary_partner": None,
            "cta_variant": "A",
            "links": {},
        }
        assert amap["links"] == {}


class TestArticleArtifact:
    def _make_frontmatter(self) -> Frontmatter:
        return {
            "title": "Best AI Tools",
            "description": "Compare the best AI tools in 2026 with pricing and honest reviews.",
            "slug": "best-ai-tools",
            "category": "ai-writing",
            "intent": "comparison",
            "published_at": "2026-05-18",
            "last_reviewed": "2026-05-18",
            "author": "Editorial Team",
            "affiliate_partner": "jasper",
            "schema_type": "Article",
        }

    def _make_artifact(self, qa_overall: str = "PASS") -> ArticleArtifact:
        fm = self._make_frontmatter()
        faq: list[FAQItem] = [{"question": "Q?", "answer": "A."}]
        amap: AffiliateMap = {
            "slug": "best-ai-tools",
            "primary_partner": "jasper",
            "cta_variant": "A",
            "links": {},
        }
        qa = QAResult(overall=qa_overall, checks=[], article_updates={})  # type: ignore[arg-type]
        return {
            "slug": "best-ai-tools",
            "category": "ai-writing",
            "frontmatter": fm,
            "mdx_body": "# Best AI Tools\n\n## Overview\n\nContent here.",
            "faq_json": faq,
            "affiliate_map": amap,
            "qa_result": qa,
        }

    def test_minimal_valid_artifact(self) -> None:
        artifact = self._make_artifact()
        assert artifact["slug"] == "best-ai-tools"

    def test_frontmatter_is_typed(self) -> None:
        artifact = self._make_artifact()
        assert artifact["frontmatter"]["schema_type"] == "Article"

    def test_faq_json_contains_faq_items(self) -> None:
        artifact = self._make_artifact()
        assert artifact["faq_json"][0]["question"] == "Q?"
        assert artifact["faq_json"][0]["answer"] == "A."

    def test_affiliate_map_present(self) -> None:
        artifact = self._make_artifact()
        assert artifact["affiliate_map"]["primary_partner"] == "jasper"

    def test_qa_result_pass(self) -> None:
        artifact = self._make_artifact(qa_overall="PASS")
        assert artifact["qa_result"].overall == "PASS"

    def test_qa_result_fail(self) -> None:
        artifact = self._make_artifact(qa_overall="FAIL")
        assert artifact["qa_result"].overall == "FAIL"

    def test_qa_result_with_checks(self) -> None:
        fm = self._make_frontmatter()
        check = CheckResult(
            name="word_count",
            result="FAIL",
            message="500 words <= 1,200",
            action="regenerate",
        )
        qa = QAResult(
            overall="FAIL", checks=[check], article_updates={"status": "failed"}
        )
        artifact: ArticleArtifact = {
            "slug": "test",
            "category": "ai-writing",
            "frontmatter": fm,
            "mdx_body": "# Test",
            "faq_json": [],
            "affiliate_map": {
                "slug": "test",
                "primary_partner": None,
                "cta_variant": "A",
                "links": {},
            },
            "qa_result": qa,
        }
        assert artifact["qa_result"].checks[0].name == "word_count"
        assert artifact["qa_result"].article_updates["status"] == "failed"
