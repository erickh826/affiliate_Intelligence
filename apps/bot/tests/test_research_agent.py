from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from drive_research import DriveAccessError, MemoryDriveCatalog
from research_agent import (
    ResearchAgentError,
    ResearchSession,
    ResearchUnavailable,
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
            {
                "method": "POST",
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout": timeout,
            }
        )
        return self._next_response()

    def get_json(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> Mapping[str, Any]:
        self.calls.append(
            {"method": "GET", "url": url, "headers": headers, "timeout": timeout}
        )
        return self._next_response()

    def _next_response(self) -> Mapping[str, Any]:
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


def research_payload() -> dict[str, Any]:
    return {
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


def perplexity_response() -> Mapping[str, Any]:
    content = json.dumps(research_payload())
    return {
        "id": "resp_test",
        "status": "completed",
        "output_text": content,
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": content}],
            }
        ],
    }


def test_scrape_serps_extracts_competitor_records() -> None:
    client = FakeClient([firecrawl_response()])

    results = scrape_serps("best ai writer", api_key="test-key", client=client)

    assert len(results) == 2
    assert results[0]["url"] == "https://example.com/a"
    assert results[0]["title"] == "Example A"
    assert results[0]["headings"] == ["Intro", "Pricing"]
    assert "Body text" in results[0]["body_summary"]
    payload = client.calls[0]["payload"]
    assert payload["sources"] == ["web"]
    assert payload["scrapeOptions"]["formats"] == ["markdown"]
    assert client.calls[0]["url"] == "https://api.firecrawl.dev/v2/search"


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


def test_scrape_serps_accepts_v2_nested_results() -> None:
    response = {
        "success": True,
        "data": {
            "web": [
                {
                    "url": "https://example.com/v2",
                    "title": "V2 Result",
                    "markdown": "# Intro\nDetails",
                }
            ]
        },
    }
    client = FakeClient([response])

    results = scrape_serps("keyword", api_key="test-key", client=client)

    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/v2"
    assert results[0]["title"] == "V2 Result"


def test_scrape_serps_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    with pytest.raises(ResearchAgentError, match="FIRECRAWL_API_KEY"):
        scrape_serps("keyword", client=FakeClient([]))


def test_query_perplexity_extracts_enrichment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PERPLEXITY_PRESET", raising=False)
    monkeypatch.delenv("PERPLEXITY_MODEL", raising=False)
    client = FakeClient([perplexity_response()])

    result = query_perplexity("best ai writer", api_key="test-key", client=client)

    assert result["facts"] == [{"claim": "Tool A costs $20/month", "source": "vendor"}]
    assert result["tools_mentioned"][0]["name"] == "Tool A"
    assert result["faq_seeds"] == ["What is the best AI writing tool?"]
    payload = client.calls[0]["payload"]
    assert client.calls[0]["url"] == "https://api.perplexity.ai/v1/agent"
    assert payload["preset"] == "high"
    assert payload["background"] is True
    assert payload["response_format"]["type"] == "json_schema"


def test_query_perplexity_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)

    with pytest.raises(ResearchAgentError, match="PERPLEXITY_API_KEY"):
        query_perplexity("keyword", client=FakeClient([]))


def test_build_research_bundle_matches_spec_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("DRIVE_FOLDER_ID", raising=False)
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

    def test_manus_review_includes_subscription_pause(self) -> None:
        bundle = build_research_bundle("manus ai review", "informational", dry_run=True)
        assert bundle["facts"][0]["claim"] == (
            "Manus paused new subscriptions in some regions since August 2026."
        )
        assert bundle["facts"][0]["source"] == "editorial"

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


def test_query_perplexity_polls_background_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = json.dumps(research_payload())
    client = FakeClient(
        [
            {"id": "resp_1", "status": "in_progress"},
            {"id": "resp_1", "status": "completed", "output_text": content},
        ]
    )
    monkeypatch.setattr("research_agent.time.sleep", lambda *_args, **_kwargs: None)

    result = query_perplexity(
        "best ai writer",
        api_key="test-key",
        client=client,
        max_wait=5,
        poll_interval=0,
    )

    assert result["facts"][0]["claim"] == "Tool A costs $20/month"
    assert client.calls[0]["method"] == "POST"
    assert client.calls[1]["method"] == "GET"
    assert client.calls[1]["url"] == "https://api.perplexity.ai/v1/agent/resp_1"


def test_query_perplexity_parses_fenced_json() -> None:
    fenced = "```json\n" + json.dumps(research_payload()) + "\n```"
    client = FakeClient(
        [{"id": "resp_fenced", "status": "completed", "output_text": fenced}]
    )

    result = query_perplexity("keyword", api_key="test-key", client=client)

    assert result["tools_mentioned"][0]["name"] == "Tool A"


def test_query_perplexity_maps_retired_sonar_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PERPLEXITY_MODEL", "sonar-deep-research")
    monkeypatch.delenv("PERPLEXITY_PRESET", raising=False)
    client = FakeClient([perplexity_response()])

    query_perplexity("keyword", api_key="test-key", client=client)

    assert client.calls[0]["payload"]["preset"] == "high"


def _drive_packet(filename: str = "best-ai-writing-tools.json") -> str:
    return json.dumps(
        {
            "keyword": "best ai writing tools",
            "slug": "best-ai-writing-tools",
            "title": "Best AI Writing Tools in 2026",
            "talking_points": ["Jasper Pro is $69 per month."],
            "sources": [
                {"title": "Jasper pricing", "url": "https://www.jasper.ai/pricing"}
            ],
            "tools_mentioned": [
                {
                    "name": "Jasper",
                    "pricing": "$69/month",
                    "pros": ["brand voice"],
                    "cons": ["price"],
                }
            ],
            "faq_seeds": ["How much does Jasper cost?"],
            "affiliate": {
                "partner": "jasper",
                "cta": "Compare Jasper plans",
                "disclosure": "This article contains affiliate links.",
            },
        }
    )


def test_drive_packet_skips_perplexity_and_firecrawl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    client = FakeClient([])
    catalog = MemoryDriveCatalog({"best-ai-writing-tools.json": _drive_packet()})

    bundle = build_research_bundle(
        "best ai writing tools",
        "comparison",
        slug="best-ai-writing-tools",
        client=client,
        drive=catalog,
    )

    assert client.calls == []
    assert bundle["research_source"] == "drive"
    assert bundle["facts"][0]["source"] == "https://www.jasper.ai/pricing"
    assert bundle["cta_text"] == "Compare Jasper plans"
    assert bundle["disclosure"] == "This article contains affiliate links."
    assert bundle["tools_mentioned"][0]["name"] == "Jasper"


def test_missing_packet_skips_when_perplexity_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("DRIVE_FOLDER_ID", raising=False)
    client = FakeClient([firecrawl_response()])

    with pytest.raises(ResearchUnavailable, match="PERPLEXITY_API_KEY is unset"):
        build_research_bundle(
            "best ai writing tools",
            "comparison",
            slug="best-ai-writing-tools",
            firecrawl_api_key="firecrawl-key",
            client=client,
            drive=MemoryDriveCatalog({}),
        )

    assert client.calls == []


def test_perplexity_quota_skips_and_blocks_the_rest_of_the_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("DRIVE_FOLDER_ID", raising=False)
    session = ResearchSession()
    quota = ResearchAgentError(
        'HTTP 401 Unauthorized: {"error":{"type":"insufficient_quota"}}'
    )
    first = FakeClient([firecrawl_response(), quota])

    with pytest.raises(ResearchUnavailable, match="insufficient_quota"):
        build_research_bundle(
            "best ai writing tools",
            "comparison",
            slug="best-ai-writing-tools",
            firecrawl_api_key="firecrawl-key",
            perplexity_api_key="test-key",
            client=first,
            drive=MemoryDriveCatalog({}),
            session=session,
        )

    assert session.perplexity_blocked is True
    assert len(first.calls) == 2
    second = FakeClient([firecrawl_response(), perplexity_response()])
    with pytest.raises(ResearchUnavailable, match="insufficient_quota"):
        build_research_bundle(
            "jasper ai review",
            "informational",
            slug="jasper-ai-review-2026",
            firecrawl_api_key="firecrawl-key",
            perplexity_api_key="test-key",
            client=second,
            drive=MemoryDriveCatalog({}),
            session=session,
        )

    assert second.calls == []


def test_drive_outage_skips_without_calling_perplexity() -> None:
    class BrokenCatalog:
        def __init__(self) -> None:
            self.calls = 0

        def list_files(self) -> list[object]:
            self.calls += 1
            raise DriveAccessError("Drive API HTTP 403")

        def download_text(self, file: object) -> str:
            raise AssertionError(file)

    session = ResearchSession()
    catalog = BrokenCatalog()
    client = FakeClient([perplexity_response()])
    with pytest.raises(ResearchUnavailable, match="Drive API HTTP 403"):
        build_research_bundle(
            "best ai writing tools",
            "comparison",
            slug="best-ai-writing-tools",
            perplexity_api_key="test-key",
            client=client,
            drive=catalog,
            session=session,
        )
    with pytest.raises(ResearchUnavailable, match="could not be read"):
        build_research_bundle(
            "jasper ai review",
            "informational",
            slug="jasper-ai-review-2026",
            perplexity_api_key="test-key",
            client=client,
            drive=catalog,
            session=session,
        )

    assert catalog.calls == 1
    assert client.calls == []


def test_query_perplexity_does_not_retry_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("research_agent.time.sleep", lambda *_args, **_kwargs: None)
    client = FakeClient(
        [
            ResearchAgentError("HTTP 401 insufficient_quota"),
            perplexity_response(),
        ]
    )

    with pytest.raises(ResearchAgentError, match="insufficient_quota"):
        query_perplexity("keyword", api_key="test-key", client=client)

    assert len(client.calls) == 1


def test_query_perplexity_preset_env_overrides_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PERPLEXITY_MODEL", "sonar-deep-research")
    monkeypatch.setenv("PERPLEXITY_PRESET", "low")
    client = FakeClient([perplexity_response()])

    query_perplexity("keyword", api_key="test-key", client=client)

    assert client.calls[0]["payload"]["preset"] == "low"
