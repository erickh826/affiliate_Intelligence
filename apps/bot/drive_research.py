from __future__ import annotations

import base64
import binascii
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote

_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
_LIST_URL = "https://www.googleapis.com/drive/v3/files"
_PACKET_EXTENSIONS = (".markdown", ".json", ".md", ".txt")
_SECTION_NAMES = {
    "talking points": "talking_points",
    "key points": "talking_points",
    "verified talking points": "talking_points",
    "facts": "talking_points",
    "sources": "sources",
    "source links": "sources",
    "links": "sources",
    "tools": "tools",
    "tools mentioned": "tools",
    "faq": "faq",
    "faqs": "faq",
    "questions": "faq",
}
_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_URL = re.compile(r"https?://[^\s)>\]]+")


class DriveAccessError(RuntimeError):
    pass


class ResearchPacketError(ValueError):
    pass


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    mime_type: str


@dataclass(frozen=True)
class ResearchPacket:
    filename: str
    keyword: str
    slug: str
    title: str
    talking_points: tuple[str, ...]
    sources: tuple[tuple[str, str], ...]
    facts: tuple[dict[str, str], ...]
    tools: tuple[dict[str, Any], ...]
    faq_seeds: tuple[str, ...]
    affiliate_partner: str
    cta_text: str
    disclosure: str


class DriveCatalog(Protocol):
    def list_files(self) -> list[DriveFile]:
        pass

    def download_text(self, file: DriveFile) -> str:
        pass


class MemoryDriveCatalog:
    def __init__(
        self,
        files: Mapping[str, str],
        *,
        mime_types: Mapping[str, str] | None = None,
    ) -> None:
        self._files = dict(files)
        self._mime_types = dict(mime_types or {})

    def list_files(self) -> list[DriveFile]:
        listed: list[DriveFile] = []
        for name in self._files:
            listed.append(DriveFile(id=name, name=name, mime_type=self._mime_for(name)))
        return listed

    def download_text(self, file: DriveFile) -> str:
        try:
            return self._files[file.name]
        except KeyError as exc:
            raise DriveAccessError(f"Drive file {file.name} is missing") from exc

    def _mime_for(self, name: str) -> str:
        if name in self._mime_types:
            return self._mime_types[name]
        lower = name.lower()
        if lower.endswith(".json"):
            return "application/json"
        if lower.endswith(".txt"):
            return "text/plain"
        return "text/markdown"


def drive_configured() -> bool:
    return bool(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()) and bool(
        os.environ.get("DRIVE_FOLDER_ID", "").strip()
    )


def resolve_drive_catalog() -> DriveCatalog | None:
    if not drive_configured():
        return None
    return GoogleDriveCatalog.from_env()


def parse_service_account_info(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if not text:
        raise DriveAccessError("GOOGLE_SERVICE_ACCOUNT_JSON is empty")
    if not text.startswith("{"):
        try:
            text = base64.b64decode(text, validate=False).decode("utf-8").strip()
        except (binascii.Error, UnicodeError) as exc:
            raise DriveAccessError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not JSON or base64 JSON"
            ) from exc
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DriveAccessError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise DriveAccessError("GOOGLE_SERVICE_ACCOUNT_JSON must be a JSON object")
    if parsed.get("type") != "service_account":
        raise DriveAccessError(
            "GOOGLE_SERVICE_ACCOUNT_JSON must be a service account key"
        )
    email = str(parsed.get("client_email") or "").strip()
    private_key = str(parsed.get("private_key") or "").strip()
    if not email or not private_key:
        raise DriveAccessError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is missing client_email or private_key"
        )
    return parsed


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-")


def parse_research_packet(text: str, *, filename: str) -> ResearchPacket:
    body = text.lstrip("\ufeff").strip()
    if filename.lower().endswith(".json") or body.startswith("{"):
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ResearchPacketError(f"{filename} is not valid JSON") from exc
        if isinstance(parsed, dict):
            packet = _packet_from_json(parsed, filename)
            _require_substance(packet)
            return packet
        if filename.lower().endswith(".json"):
            raise ResearchPacketError(f"{filename} must be a JSON object")
    packet = _packet_from_markdown(body, filename)
    _require_substance(packet)
    return packet


def load_matching_packet(
    catalog: DriveCatalog,
    *,
    slug: str,
    keyword: str,
) -> ResearchPacket | None:
    ranked: list[tuple[int, DriveFile]] = []
    for file in catalog.list_files():
        rank = _match_rank(file, slug=slug, keyword=keyword)
        if rank is not None:
            ranked.append((rank, file))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    errors: list[str] = []
    for _rank, file in ranked:
        try:
            packet = parse_research_packet(
                catalog.download_text(file),
                filename=file.name,
            )
        except ResearchPacketError as exc:
            errors.append(str(exc))
            continue
        if not _packet_identity_ok(packet, slug=slug, keyword=keyword):
            errors.append(f"{file.name} does not match {slug or keyword}")
            continue
        return packet
    detail = "; ".join(errors) if errors else "no usable packet"
    raise ResearchPacketError(
        f"Drive research file matched {slug or keyword} but could not be used: {detail}"
    )


def bundle_from_packet(
    packet: ResearchPacket,
    *,
    keyword: str,
    intent: str,
) -> dict[str, Any]:
    sources: list[tuple[str, str]] = [
        (title, url)
        for title, url in packet.sources
        if url.startswith(("http://", "https://"))
    ]
    seen = {url for _title, url in sources}
    for fact in packet.facts:
        source = str(fact.get("source") or "").strip()
        if source.startswith(("http://", "https://")) and source not in seen:
            sources.append((source, source))
            seen.add(source)
    facts: list[dict[str, str]] = []
    known: set[str] = set()
    for fact in packet.facts:
        claim = str(fact.get("claim") or "").strip()
        if not claim or claim in known:
            continue
        facts.append({"claim": claim, "source": str(fact.get("source") or "").strip()})
        known.add(claim)
    default_source = sources[0][1] if sources else ""
    for point in packet.talking_points:
        text = point.strip()
        if text and text not in known:
            facts.append({"claim": text, "source": default_source})
            known.add(text)
    return {
        "keyword": keyword,
        "intent": intent,
        "competitors_scraped": [
            {
                "url": url,
                "title": title or url,
                "headings": [],
                "body_summary": "",
            }
            for title, url in sources
        ],
        "facts": facts,
        "tools_mentioned": [dict(tool) for tool in packet.tools],
        "faq_seeds": list(packet.faq_seeds),
        "title": packet.title,
        "cta_text": packet.cta_text,
        "disclosure": packet.disclosure,
        "affiliate_partner": packet.affiliate_partner,
        "research_source": "drive",
        "drive_file": packet.filename,
    }


class GoogleDriveCatalog:
    def __init__(
        self,
        session: Any,
        *,
        folder_id: str,
        timeout: float = 30.0,
    ) -> None:
        self._session = session
        self._folder_id = folder_id
        self._timeout = timeout

    @classmethod
    def from_env(cls) -> GoogleDriveCatalog:
        info = parse_service_account_info(
            os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        )
        folder_id = os.environ.get("DRIVE_FOLDER_ID", "").strip()
        if not folder_id:
            raise DriveAccessError("DRIVE_FOLDER_ID is empty")
        try:
            from google.auth.transport.requests import AuthorizedSession
            from google.oauth2 import service_account
        except ImportError as exc:
            raise DriveAccessError("google-auth is not installed") from exc
        try:
            credentials = service_account.Credentials.from_service_account_info(
                info,
                scopes=[_DRIVE_SCOPE],
            )
            session = AuthorizedSession(credentials)
        except Exception as exc:
            raise DriveAccessError("could not load the Google service account") from exc
        return cls(session, folder_id=folder_id)

    def list_files(self) -> list[DriveFile]:
        files: list[DriveFile] = []
        page_token = ""
        for _page in range(20):
            params = {
                "q": self._folder_query(),
                "fields": "nextPageToken, files(id, name, mimeType)",
                "pageSize": "1000",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            }
            if page_token:
                params["pageToken"] = page_token
            payload = self._get_json(_LIST_URL, params)
            raw_files = payload.get("files", [])
            if not isinstance(raw_files, list):
                raise DriveAccessError("Drive file list did not include files")
            for item in raw_files:
                if not isinstance(item, dict):
                    continue
                file_id = str(item.get("id") or "").strip()
                name = str(item.get("name") or "").strip()
                if not file_id or not name:
                    continue
                files.append(
                    DriveFile(
                        id=file_id,
                        name=name,
                        mime_type=str(item.get("mimeType") or ""),
                    )
                )
            page_token = str(payload.get("nextPageToken") or "").strip()
            if not page_token:
                break
        return files

    def download_text(self, file: DriveFile) -> str:
        file_id = quote(file.id, safe="")
        if file.mime_type == "application/vnd.google-apps.document":
            url = f"{_LIST_URL}/{file_id}/export"
            params = {"mimeType": "text/plain"}
        else:
            url = f"{_LIST_URL}/{file_id}"
            params = {"alt": "media", "supportsAllDrives": "true"}
        return self._get_text(url, params)

    def _folder_query(self) -> str:
        safe_id = self._folder_id.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{safe_id}' in parents and trashed = false"

    def _get_json(self, url: str, params: Mapping[str, str]) -> dict[str, Any]:
        response = self._session.get(url, params=dict(params), timeout=self._timeout)
        self._raise_for_status(response)
        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise DriveAccessError("Drive API returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise DriveAccessError("Drive API returned invalid JSON")
        return payload

    def _get_text(self, url: str, params: Mapping[str, str]) -> str:
        response = self._session.get(url, params=dict(params), timeout=self._timeout)
        self._raise_for_status(response)
        text = getattr(response, "text", None)
        if isinstance(text, str):
            return text
        content = getattr(response, "content", b"")
        if isinstance(content, bytes):
            try:
                return content.decode("utf-8")
            except UnicodeError as exc:
                raise DriveAccessError("Drive file is not UTF-8 text") from exc
        raise DriveAccessError("Drive file response was empty")

    def _raise_for_status(self, response: Any) -> None:
        status = int(getattr(response, "status_code", 0) or 0)
        if status >= 400:
            raise DriveAccessError(f"Drive API HTTP {status}")


def _packet_from_json(data: Mapping[str, Any], filename: str) -> ResearchPacket:
    affiliate = data.get("affiliate")
    if not isinstance(affiliate, dict):
        affiliate = {}
    talking_points, fact_rows = _json_points(data.get("talking_points"))
    if not talking_points and not fact_rows:
        talking_points, fact_rows = _json_points(data.get("talkingPoints"))
    extra_points, extra_facts = _json_points(data.get("facts"))
    talking_points.extend(extra_points)
    fact_rows.extend(extra_facts)
    tools_raw = data.get("tools_mentioned")
    if not isinstance(tools_raw, list):
        tools_raw = data.get("tools")
    return ResearchPacket(
        filename=filename,
        keyword=_first_text(data, ("keyword",)),
        slug=_first_text(data, ("slug",)),
        title=_first_text(data, ("title",)),
        talking_points=tuple(talking_points),
        sources=tuple(_json_sources(data.get("sources") or data.get("source_links"))),
        facts=tuple(fact_rows),
        tools=tuple(_json_tools(tools_raw)),
        faq_seeds=tuple(_json_faqs(data.get("faq_seeds") or data.get("faqs"))),
        affiliate_partner=(
            _first_text(data, ("affiliate_partner", "partner"))
            or _first_text(affiliate, ("partner", "id"))
        ),
        cta_text=(
            _first_text(data, ("cta", "cta_text"))
            or _first_text(affiliate, ("cta", "cta_text", "wording"))
        ),
        disclosure=(
            _first_text(data, ("disclosure",))
            or _first_text(affiliate, ("disclosure",))
        ),
    )


def _packet_from_markdown(text: str, filename: str) -> ResearchPacket:
    meta, body = _frontmatter(text)
    sections = _split_sections(body)
    talking = _bullets(sections.get("talking_points", ""))
    if not talking:
        talking = _bullets(sections.get("preamble", ""))
    sources = _sources_from_text(sections.get("sources", ""))
    if not sources:
        sources = _sources_from_text(body)
    preamble = sections.get("preamble", "")
    disclosure = meta.get("disclosure") or _labeled_line(preamble, "disclosure")
    cta_text = meta.get("cta") or meta.get("cta_text") or _labeled_line(preamble, "cta")
    return ResearchPacket(
        filename=filename,
        keyword=meta.get("keyword", ""),
        slug=meta.get("slug", ""),
        title=meta.get("title", ""),
        talking_points=tuple(talking),
        sources=tuple(sources),
        facts=(),
        tools=tuple(_markdown_tools(sections.get("tools", ""))),
        faq_seeds=tuple(_bullets(sections.get("faq", ""))),
        affiliate_partner=meta.get("affiliate_partner", ""),
        cta_text=cta_text,
        disclosure=disclosure,
    )


def _require_substance(packet: ResearchPacket) -> None:
    claims = [point.strip() for point in packet.talking_points if point.strip()]
    claims.extend(
        str(fact.get("claim") or "").strip()
        for fact in packet.facts
        if str(fact.get("claim") or "").strip()
    )
    urls = [
        url for _title, url in packet.sources if url.startswith(("http://", "https://"))
    ]
    urls.extend(
        str(fact.get("source") or "").strip()
        for fact in packet.facts
        if str(fact.get("source") or "").strip().startswith(("http://", "https://"))
    )
    if not claims:
        raise ResearchPacketError(
            f"{packet.filename} needs at least one talking point or fact"
        )
    if not urls:
        raise ResearchPacketError(
            f"{packet.filename} needs at least one http(s) source link"
        )


def _match_rank(file: DriveFile, *, slug: str, keyword: str) -> int | None:
    if not _is_readable(file):
        return None
    stem = slugify(_file_stem(file.name))
    targets = {slugify(slug), slugify(keyword)}
    targets.discard("")
    if stem not in targets:
        return None
    rank = 100 if slug and stem == slugify(slug) else 80
    lower = file.name.lower()
    if lower.endswith(".json") or file.mime_type == "application/json":
        rank += 3
    elif lower.endswith((".md", ".markdown")):
        rank += 1
    return rank


def _packet_identity_ok(packet: ResearchPacket, *, slug: str, keyword: str) -> bool:
    targets = {slugify(slug), slugify(keyword)}
    targets.discard("")
    slug_ok = not packet.slug or slugify(packet.slug) in targets
    keyword_ok = not packet.keyword or (
        packet.keyword.strip().lower() == keyword.strip().lower()
        or slugify(packet.keyword) in targets
    )
    return slug_ok and keyword_ok


def _is_readable(file: DriveFile) -> bool:
    lower = file.name.lower()
    if any(lower.endswith(ext) for ext in _PACKET_EXTENSIONS):
        return True
    mime = file.mime_type.lower()
    return mime.startswith("text/") or mime in {
        "application/json",
        "application/vnd.google-apps.document",
    }


def _file_stem(name: str) -> str:
    lower = name.lower()
    for ext in _PACKET_EXTENSIONS:
        if lower.endswith(ext):
            return name[: -len(ext)]
    return name


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}, text
    meta: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = _unquote(value.strip())
    return meta, "\n".join(lines[end + 1 :])


def _split_sections(body: str) -> dict[str, str]:
    current = "preamble"
    buckets: dict[str, list[str]] = {current: []}
    for line in body.splitlines():
        name = _section_name(line)
        if name and not line.lstrip().startswith(("-", "*", "•")):
            current = name
            buckets.setdefault(current, [])
            continue
        buckets.setdefault(current, []).append(line)
    return {key: "\n".join(lines).strip() for key, lines in buckets.items()}


def _section_name(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or len(stripped) > 48 or ":" in stripped:
        return None
    cleaned = re.sub(r"^#+\s*", "", stripped)
    if cleaned.startswith("#"):
        return None
    key = re.sub(r"[^a-z0-9]+", " ", cleaned.lower()).strip()
    return _SECTION_NAMES.get(key)


def _bullets(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "• ")):
            items.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s+", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped).strip())
    return [item for item in items if item]


def _sources_from_text(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for title, url in _MD_LINK.findall(text):
        cleaned = url.rstrip(".,")
        if cleaned not in seen:
            seen.add(cleaned)
            found.append((title.strip(), cleaned))
    for url in _URL.findall(text):
        cleaned = url.rstrip(".,")
        if cleaned not in seen:
            seen.add(cleaned)
            found.append((cleaned, cleaned))
    return found


def _markdown_tools(text: str) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        if line.startswith("### "):
            if current and str(current.get("name") or "").strip():
                tools.append(current)
            current = {
                "name": line[4:].strip(),
                "pricing": "",
                "pros": [],
                "cons": [],
            }
            continue
        if current is None:
            continue
        item = line.strip().lstrip("-* ").strip()
        lower = item.lower()
        if lower.startswith("pricing:"):
            current["pricing"] = item.split(":", 1)[1].strip()
        elif lower.startswith("pros:"):
            current["pros"] = _csv_list(item.split(":", 1)[1])
        elif lower.startswith("cons:"):
            current["cons"] = _csv_list(item.split(":", 1)[1])
    if current and str(current.get("name") or "").strip():
        tools.append(current)
    return tools


def _labeled_line(text: str, label: str) -> str:
    prefix = f"{label.lower()}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(prefix):
            return stripped.split(":", 1)[1].strip()
    return ""


def _json_points(value: Any) -> tuple[list[str], list[dict[str, str]]]:
    points: list[str] = []
    facts: list[dict[str, str]] = []
    if not isinstance(value, list):
        return points, facts
    for item in value:
        if isinstance(item, str) and item.strip():
            points.append(item.strip())
        elif isinstance(item, dict):
            claim = str(item.get("claim") or item.get("text") or "").strip()
            if not claim:
                continue
            source = str(item.get("source") or "").strip()
            points.append(claim)
            facts.append({"claim": claim, "source": source})
    return points, facts


def _json_sources(value: Any) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return _sources_from_text(value)
    if not isinstance(value, list):
        return []
    found: list[tuple[str, str]] = []
    for item in value:
        if isinstance(item, str):
            found.extend(_sources_from_text(item))
            continue
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("link") or item.get("href") or "").strip()
        title = str(item.get("title") or item.get("name") or url).strip()
        if url.startswith(("http://", "https://")):
            found.append((title, url))
    return found


def _json_tools(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    tools: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        tools.append(
            {
                "name": name,
                "pricing": str(item.get("pricing") or "").strip(),
                "pros": _string_list(item.get("pros")),
                "cons": _string_list(item.get("cons")),
            }
        )
    return tools


def _json_faqs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    faqs: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            faqs.append(item.strip())
        elif isinstance(item, dict):
            question = str(item.get("question") or item.get("q") or "").strip()
            if question:
                faqs.append(question)
    return faqs


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _csv_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _first_text(data: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
