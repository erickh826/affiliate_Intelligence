from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any, Protocol


class ResearchAgentError(RuntimeError):
    pass


class HTTPClient(Protocol):
    def post_json(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout: float,
    ) -> Mapping[str, Any]:
        pass


class UrlLibHTTPClient:
    def post_json(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout: float,
    ) -> Mapping[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **dict(headers)},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8")
            except Exception:
                pass
            raise ResearchAgentError(
                f"HTTP {exc.code} {exc.reason}: {error_body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ResearchAgentError(str(exc)) from exc

        data = json.loads(body)
        if not isinstance(data, dict):
            raise ResearchAgentError("expected JSON object response")
        return data


def scrape_serps(
    keyword: str,
    *,
    api_key: str | None = None,
    client: HTTPClient | None = None,
    limit: int = 5,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    key = api_key or os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        raise ResearchAgentError("FIRECRAWL_API_KEY is required")

    http = client or UrlLibHTTPClient()
    payload = {
        "query": keyword,
        "sources": ["web"],
        "categories": [],
        "limit": min(limit, 10),
        "scrapeOptions": {
            "onlyMainContent": True,
            "formats": [],
        },
    }
    headers = {"Authorization": f"Bearer {key}"}
    data = _retry(
        lambda: http.post_json(
            "https://api.firecrawl.dev/v2/search",
            headers,
            payload,
            timeout,
        )
    )
    raw_results = _extract_firecrawl_results(data)

    return [_competitor_from_result(result) for result in raw_results[:limit]]


def query_perplexity(
    keyword: str,
    *,
    api_key: str | None = None,
    client: HTTPClient | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    key = api_key or os.environ.get("PERPLEXITY_API_KEY")
    if not key:
        raise ResearchAgentError("PERPLEXITY_API_KEY is required")

    http = client or UrlLibHTTPClient()
    headers = {"Authorization": f"Bearer {key}"}
    payload = {
        "model": "sonar-deep-research",
        "messages": [
            {"role": "system", "content": "Extract factual data only. No opinions."},
            {
                "role": "user",
                "content": (
                    f"Research '{keyword}':\n"
                    "1. Top 5 tools with pricing\n"
                    "2. Market statistics with sources\n"
                    "3. Common user complaints\n"
                    "4. Expert recommendations\n\n"
                    "Return JSON with facts, tools_mentioned, and faq_seeds."
                ),
            },
        ],
    }
    data = _retry(
        lambda: http.post_json(
            "https://api.perplexity.ai/chat/completions",
            headers,
            payload,
            timeout,
        )
    )
    content = _extract_message_content(data)
    return _parse_perplexity_content(content)


def build_research_bundle(
    keyword: str,
    intent: str,
    *,
    dry_run: bool = False,
    firecrawl_api_key: str | None = None,
    perplexity_api_key: str | None = None,
    client: HTTPClient | None = None,
) -> dict[str, Any]:
    if dry_run:
        return {
            "keyword": keyword,
            "intent": intent,
            "competitors_scraped": [],
            "facts": [
                {
                    "claim": f"{keyword} pricing starts at $0 for free plans.",
                    "source": "example.com",
                },
                {
                    "claim": f"Leading {keyword} tools cost $49/month for professional plans.",
                    "source": "example.com",
                },
                {
                    "claim": f"{keyword} is used by over 10,000 teams worldwide.",
                    "source": "example.com",
                },
            ],
            "tools_mentioned": [],
            "faq_seeds": [
                f"What is the best {keyword}?",
                f"How much does {keyword} cost?",
            ],
        }
    competitors = scrape_serps(keyword, api_key=firecrawl_api_key, client=client)
    enrichment = query_perplexity(keyword, api_key=perplexity_api_key, client=client)
    return {
        "keyword": keyword,
        "intent": intent,
        "competitors_scraped": competitors,
        "facts": enrichment["facts"],
        "tools_mentioned": enrichment["tools_mentioned"],
        "faq_seeds": enrichment["faq_seeds"],
    }


def _retry(
    operation: Callable[[], Mapping[str, Any]],
    *,
    attempts: int = 3,
    base_delay: float = 0.25,
) -> Mapping[str, Any]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except (ResearchAgentError, OSError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt == attempts - 1:
                break
            time.sleep(base_delay * (2**attempt))
    detail = str(last_error) if last_error is not None else "unknown error"
    raise ResearchAgentError(
        f"external research request failed: {detail}"
    ) from last_error


def _competitor_from_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ResearchAgentError("Firecrawl result must be an object")

    body = _first_text(result, ("markdown", "content", "text", "description"))
    metadata = result.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    title = str(result.get("title") or metadata.get("title") or "")
    return {
        "url": str(result.get("url") or result.get("sourceURL") or ""),
        "title": title,
        "headings": _extract_headings(body),
        "body_summary": _summarize_body(body),
    }


def _extract_firecrawl_results(response: Mapping[str, Any]) -> list[Any]:
    data = response.get("data")
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("results", "web", "organic", "items", "documents"):
            candidate = data.get(key)
            if isinstance(candidate, list):
                return candidate

    for key in ("results", "web", "organic", "items", "documents"):
        candidate = response.get(key)
        if isinstance(candidate, list):
            return candidate

    raise ResearchAgentError(
        "Firecrawl response did not include a results list"
    )


def _first_text(source: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _extract_headings(body: str) -> list[str]:
    headings = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            headings.append(stripped.lstrip("#").strip())
    return headings


def _summarize_body(body: str, limit: int = 500) -> str:
    normalized = " ".join(body.split())
    return normalized[:limit]


def _extract_message_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ResearchAgentError("Perplexity response missing choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ResearchAgentError("Perplexity choice must be an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ResearchAgentError("Perplexity response missing message")
    content = message.get("content")
    if not isinstance(content, str):
        raise ResearchAgentError("Perplexity response missing content")
    return content


def _parse_perplexity_content(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    return {
        "facts": _list_of_dicts(parsed.get("facts")),
        "tools_mentioned": _list_of_dicts(parsed.get("tools_mentioned")),
        "faq_seeds": _list_of_strings(parsed.get("faq_seeds")),
    }


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]
