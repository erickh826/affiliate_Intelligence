from __future__ import annotations

import json
from pathlib import Path

from affiliates import category_has_enabled_program, load_programs


def test_placeholders_are_disabled() -> None:
    programs = load_programs()
    ids = {program.id for program in programs}
    assert {
        "jasper",
        "writesonic",
        "copy_ai",
        "surfer",
        "semrush",
        "ahrefs",
        "elevenlabs",
        "descript",
        "notion",
        "zapier",
    } <= ids
    assert all(not program.enabled for program in programs)
    assert all("YOUR_REF" in program.url for program in programs)


def test_enabled_program_unlocks_its_category(tmp_path: Path) -> None:
    path = tmp_path / "affiliates.json"
    path.write_text(
        json.dumps(
            {
                "programs": [
                    {
                        "id": "surfer",
                        "name": "Surfer SEO",
                        "category": "seo",
                        "url": "https://surferseo.com/?via=real",
                        "promo_code": "SAVE10",
                        "anchor": "Try Surfer SEO",
                        "enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert category_has_enabled_program("seo", path) is True
    assert category_has_enabled_program("ai-writing", path) is False
    assert category_has_enabled_program("ai-code") is False
