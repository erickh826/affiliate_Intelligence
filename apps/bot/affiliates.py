from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AFFILIATES_PATH = _PROJECT_ROOT / "monetisation" / "affiliates.json"


@dataclass(frozen=True)
class AffiliateProgram:
    id: str
    name: str
    category: str
    url: str
    promo_code: str
    anchor: str
    enabled: bool


def _as_bool(value: object) -> bool:
    return value is True


def load_programs(path: Path | None = None) -> list[AffiliateProgram]:
    config_path = path or DEFAULT_AFFILIATES_PATH
    if not config_path.exists():
        return []
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    entries = raw.get("programs", []) if isinstance(raw, dict) else []
    if not isinstance(entries, list):
        return []
    programs: list[AffiliateProgram] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        program_id = str(entry.get("id") or "").strip()
        category = str(entry.get("category") or "").strip()
        if not program_id or not category:
            continue
        programs.append(
            AffiliateProgram(
                id=program_id,
                name=str(entry.get("name") or program_id).strip() or program_id,
                category=category,
                url=str(entry.get("url") or "").strip(),
                promo_code=str(entry.get("promo_code") or "").strip(),
                anchor=str(entry.get("anchor") or "").strip(),
                enabled=_as_bool(entry.get("enabled")),
            )
        )
    return programs


def program_is_active(program: AffiliateProgram) -> bool:
    return program.enabled and program.url.startswith(("http://", "https://"))


def category_has_enabled_program(category: str, path: Path | None = None) -> bool:
    return any(
        program.category == category and program_is_active(program)
        for program in load_programs(path)
    )
