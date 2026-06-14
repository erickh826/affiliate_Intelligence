from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from research_agent import (
    ResearchAgentError,
    build_research_bundle,
    query_perplexity,
    scrape_serps,
)


class FakeClient:
    def __init__(self, responses: list[Mapping[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def post_json(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout: float,
    ) -> Mapping[str, Any]:
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout}
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def firecrawl_response() -> Mapping[str, Any]:
    return {
        "data": [
            {
                "url": "https://example.com/a",
                "title": "Example A",
                "markdown": "# Intro\nBody text\n## Pricing\nMore text",
            },
            {
                "sourceURL": "https://example.com/b",
                "metadata": {"title": "Example B"},
                "content": "# Overview\nUseful content",
            },
        ]
    }


def perplexity_response() -> Mapping[str, Any]:
    content = {
        "facts": [{"claim": "Tool A costs $20/month", "source": "vendor"}],
        "tools_mentioned": [
            {
                "name": "Tool A",
                "pricing": "$20/month",
                "pros": ["fast"],
                "cons": ["limited exports"],
            }
        ],
        "faq_seeds": ["What is the best AI writing tool?"],
    }
    return {"choices": [{"message": {"content": json.dumps(content)}}]}


def test_scrape_serps_extracts_competitor_records() -> None:
    client = FakeClient([firecrawl_response()])

    results = scrape_serps("best ai writer", api_key="test-key", client=client)

    assert len(results) == 2
    assert results[0]["url"] == "https://example.com/a"
    assert results[0]["title"] == "Example A"
    assert results[0]["headings"] == ["Intro", "Pricing"]
    assert "Body text" in results[0]["body_summary"]


def test_scrape_serps_limits_results() -> None:
    response = {
        "data": [
            {"url": "https://example.com/1", "title": "A", "markdown": "# A"},
            {"url": "https://example.com/2", "title": "B", "markdown": "# B"},
        ]
    }
    client = FakeClient([response])

    results = scrape_serps("keyword", api_key="test-key", client=client, limit=1)

    assert len(results) == 1


def test_scrape_serps_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    with pytest.raises(ResearchAgentError, match="FIRECRAWL_API_KEY"):
        scrape_serps("keyword", client=FakeClient([]))


def test_query_perplexity_extracts_enrichment() -> None:
    client = FakeClient([perplexity_response()])

    result = query_perplexity("best ai writer", api_key="test-key", client=client)

    assert result["facts"] == [{"claim": "Tool A costs $20/month", "source": "vendor"}]
    assert result["tools_mentioned"][0]["name"] == "Tool A"
    assert result["faq_seeds"] == ["What is the best AI writing tool?"]


def test_query_perplexity_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)

    with pytest.raises(ResearchAgentError, match="PERPLEXITY_API_KEY"):
        query_perplexity("keyword", client=FakeClient([]))


def test_build_research_bundle_matches_spec_shape() -> None:
    client = FakeClient([firecrawl_response(), perplexity_response()])

    bundle = build_research_bundle(
        "best ai writer",
        "comparison",
        firecrawl_api_key="firecrawl-key",
        perplexity_api_key="perplexity-key",
        client=client,
    )

    assert bundle["keyword"] == "best ai writer"
    assert bundle["intent"] == "comparison"
    assert bundle["competitors_scraped"][0]["url"] == "https://example.com/a"
    assert bundle["facts"][0]["claim"] == "Tool A costs $20/month"
    assert bundle["tools_mentioned"][0]["pricing"] == "$20/month"
    assert bundle["faq_seeds"] == ["What is the best AI writing tool?"]


def test_retries_external_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient([ResearchAgentError("temporary"), firecrawl_response()])
    sleeps: list[float] = []
    monkeypatch.setattr("research_agent.time.sleep", sleeps.append)

    results = scrape_serps("keyword", api_key="test-key", client=client)

    assert results
    assert len(client.calls) == 2
    assert sleeps == [0.25]


def test_raises_after_retry_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient(
        [
            ResearchAgentError("first"),
            ResearchAgentError("second"),
            ResearchAgentError("third"),
        ]
    )
    monkeypatch.setattr("research_agent.time.sleep", lambda _: None)

    with pytest.raises(ResearchAgentError, match="external research request failed"):
        scrape_serps("keyword", api_key="test-key", client=client)

    assert len(client.calls) == 3


class TestBuildResearchBundleDryRun:
    def test_returns_without_http_calls(self) -> None:
        bundle = build_research_bundle("best ai tools", "comparison", dry_run=True)
        assert bundle["keyword"] == "best ai tools"
        assert bundle["intent"] == "comparison"

    def test_shape_matches_spec(self) -> None:
        bundle = build_research_bundle("best ai tools", "comparison", dry_run=True)
        for key in (
            "keyword",
            "intent",
            "competitors_scraped",
            "facts",
            "tools_mentioned",
            "faq_seeds",
        ):
            assert key in bundle

    def test_competitors_scraped_is_empty(self) -> None:
        bundle = build_research_bundle("kw", "informational", dry_run=True)
        assert bundle["competitors_scraped"] == []

    def test_facts_are_keyword_specific(self) -> None:
        bundle = build_research_bundle("jasper ai", "informational", dry_run=True)
        assert any("jasper ai" in f["claim"].lower() for f in bundle["facts"])

    def test_facts_contain_price_anchors(self) -> None:
        bundle = build_research_bundle("best ai tools", "comparison", dry_run=True)
        full = " ".join(f["claim"] for f in bundle["facts"])
        assert "$" in full

    def test_faq_seeds_non_empty(self) -> None:
        bundle = build_research_bundle("kw", "comparison", dry_run=True)
        assert len(bundle["faq_seeds"]) >= 1

    def test_does_not_require_api_keys(self) -> None:
        bundle = build_research_bundle(
            "test keyword",
            "tutorial",
            dry_run=True,
            firecrawl_api_key=None,
            perplexity_api_key=None,
        )
        assert bundle["keyword"] == "test keyword"
