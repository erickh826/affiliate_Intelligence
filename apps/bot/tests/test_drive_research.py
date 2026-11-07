from __future__ import annotations

import base64
import json

import pytest

from drive_research import (
    DriveAccessError,
    DriveFile,
    GoogleDriveCatalog,
    MemoryDriveCatalog,
    ResearchPacketError,
    bundle_from_packet,
    load_matching_packet,
    parse_research_packet,
    parse_service_account_info,
    slugify,
)

_MARKDOWN = """---
keyword: best ai writing tools
slug: best-ai-writing-tools
title: "Best AI Writing Tools in 2026"
affiliate_partner: jasper
cta: Compare Jasper plans
disclosure: This article contains affiliate links. We may earn a commission.
---

## Talking points

- Jasper Pro is $69 per month when billed monthly.

## Sources

- [Jasper pricing](https://www.jasper.ai/pricing)

## Tools

### Jasper
- Pricing: $69/month
- Pros: brand voice, templates
- Cons: costly for solo use

## FAQ

- How much does Jasper cost?
"""


def test_slugify_matches_keyword_filename() -> None:
    assert slugify("best ai writing tools") == "best-ai-writing-tools"


def test_parse_markdown_packet() -> None:
    packet = parse_research_packet(_MARKDOWN, filename="best-ai-writing-tools.md")

    assert packet.keyword == "best ai writing tools"
    assert packet.slug == "best-ai-writing-tools"
    assert packet.title == "Best AI Writing Tools in 2026"
    assert packet.talking_points == (
        "Jasper Pro is $69 per month when billed monthly.",
    )
    assert packet.sources == (("Jasper pricing", "https://www.jasper.ai/pricing"),)
    assert packet.tools[0]["name"] == "Jasper"
    assert packet.tools[0]["pros"] == ["brand voice", "templates"]
    assert packet.faq_seeds == ("How much does Jasper cost?",)
    assert packet.affiliate_partner == "jasper"
    assert packet.cta_text == "Compare Jasper plans"
    assert "affiliate links" in packet.disclosure


def test_parse_json_packet_nested_affiliate() -> None:
    payload = {
        "keyword": "jasper ai review",
        "slug": "jasper-ai-review-2026",
        "title": "Jasper AI Review 2026",
        "talking_points": ["Jasper Pro is $69 per month."],
        "sources": [{"title": "Pricing", "url": "https://www.jasper.ai/pricing"}],
        "faq_seeds": ["How much does Jasper cost?"],
        "affiliate": {
            "partner": "jasper",
            "cta": "Start Jasper",
            "disclosure": "Referral links may earn credits.",
        },
    }

    packet = parse_research_packet(
        json.dumps(payload),
        filename="jasper-ai-review-2026.json",
    )

    assert packet.affiliate_partner == "jasper"
    assert packet.cta_text == "Start Jasper"
    assert packet.disclosure == "Referral links may earn credits."
    bundle = bundle_from_packet(
        packet, keyword="jasper ai review", intent="informational"
    )
    assert bundle["research_source"] == "drive"
    assert bundle["facts"][0]["claim"] == "Jasper Pro is $69 per month."
    assert bundle["competitors_scraped"][0]["url"] == "https://www.jasper.ai/pricing"
    assert bundle["cta_text"] == "Start Jasper"


def test_parse_plain_heading_without_hashes() -> None:
    text = (
        "Talking points\n"
        "- Copy.ai has a free plan.\n"
        "Sources\n"
        "https://www.copy.ai/prices"
    )

    packet = parse_research_packet(text, filename="copy-ai.txt")

    assert packet.talking_points == ("Copy.ai has a free plan.",)
    assert packet.sources[0][1] == "https://www.copy.ai/prices"


def test_packet_requires_a_source_link() -> None:
    with pytest.raises(ResearchPacketError, match="source link"):
        parse_research_packet(
            json.dumps(
                {
                    "slug": "best-ai-writing-tools",
                    "talking_points": ["Jasper costs $69."],
                }
            ),
            filename="best-ai-writing-tools.json",
        )


def test_load_matching_packet_prefers_json_and_rejects_mismatch() -> None:
    catalog = MemoryDriveCatalog(
        {
            "best-ai-writing-tools.md": _MARKDOWN,
            "best-ai-writing-tools.json": json.dumps(
                {
                    "slug": "best-ai-writing-tools",
                    "keyword": "best ai writing tools",
                    "talking_points": ["JSON point."],
                    "sources": ["https://example.com/json"],
                    "cta": "Use the JSON offer",
                }
            ),
            "other-topic.md": _MARKDOWN.replace(
                "best-ai-writing-tools",
                "other-topic",
            ),
            "notes.pdf": "not research",
        }
    )

    packet = load_matching_packet(
        catalog,
        slug="best-ai-writing-tools",
        keyword="best ai writing tools",
    )

    assert packet is not None
    assert packet.filename.endswith(".json")
    assert packet.cta_text == "Use the JSON offer"
    assert (
        load_matching_packet(catalog, slug="missing-slug", keyword="missing keyword")
        is None
    )


def test_contradicting_packet_is_rejected() -> None:
    catalog = MemoryDriveCatalog(
        {
            "best-ai-writing-tools.json": json.dumps(
                {
                    "slug": "someone-else",
                    "talking_points": ["Wrong article."],
                    "sources": ["https://example.com/wrong"],
                }
            )
        }
    )

    with pytest.raises(ResearchPacketError, match="does not match"):
        load_matching_packet(
            catalog,
            slug="best-ai-writing-tools",
            keyword="best ai writing tools",
        )


def test_service_account_json_accepts_raw_and_base64() -> None:
    info = {
        "type": "service_account",
        "client_email": "bot@example.iam.gserviceaccount.com",
        "private_key": "test-private-key",
    }
    raw = json.dumps(info)
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")

    assert parse_service_account_info(raw)["client_email"] == info["client_email"]
    assert parse_service_account_info(encoded)["private_key"] == "test-private-key"


def test_service_account_json_rejects_user_credentials() -> None:
    with pytest.raises(DriveAccessError, match="service account"):
        parse_service_account_info(json.dumps({"type": "authorized_user"}))


class _Response:
    def __init__(
        self, payload: dict[str, object] | None = None, text: str = ""
    ) -> None:
        self.status_code = 200
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict[str, object]:
        return self._payload


class _Session:
    def __init__(self, pages: list[dict[str, object]], body: str) -> None:
        self.pages = pages
        self.body = body
        self.calls: list[dict[str, object]] = []

    def get(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> _Response:
        self.calls.append({"url": url, "params": params or {}, "timeout": timeout})
        if "alt" in (params or {}) or url.endswith("/export"):
            return _Response(text=self.body)
        return _Response(payload=self.pages.pop(0))


def test_google_drive_catalog_lists_and_downloads() -> None:
    session = _Session(
        pages=[
            {
                "files": [
                    {
                        "id": "file-1",
                        "name": "best-ai-writing-tools.md",
                        "mimeType": "text/markdown",
                    }
                ]
            }
        ],
        body="Talking points\n- Jasper is $69.\nSources\nhttps://www.jasper.ai/pricing\n",
    )
    catalog = GoogleDriveCatalog(session, folder_id="folder'id")

    files = catalog.list_files()
    text = catalog.download_text(files[0])

    assert files == [
        DriveFile(
            id="file-1",
            name="best-ai-writing-tools.md",
            mime_type="text/markdown",
        )
    ]
    assert "Jasper is $69." in text
    params = session.calls[0]["params"]
    assert isinstance(params, dict)
    assert params["q"] == "'folder\\'id' in parents and trashed = false"
    assert session.calls[1]["url"] == "https://www.googleapis.com/drive/v3/files/file-1"


def test_google_drive_catalog_exports_docs() -> None:
    session = _Session(
        pages=[{"files": []}],
        body="exported",
    )
    catalog = GoogleDriveCatalog(session, folder_id="folder")

    text = catalog.download_text(
        DriveFile(
            id="doc-1",
            name="best-ai-writing-tools",
            mime_type="application/vnd.google-apps.document",
        )
    )

    assert text == "exported"
    assert str(session.calls[0]["url"]).endswith("/export")
