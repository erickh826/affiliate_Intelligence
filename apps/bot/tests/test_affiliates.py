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
    affiliates = [program for program in programs if program.type == "affiliate"]
    referrals = {
        program.id: program for program in programs if program.type == "referral"
    }
    assert all(not program.enabled for program in affiliates)
    assert all("YOUR_REF" in program.url for program in affiliates)
    assert referrals["lovable"].enabled is True
    assert referrals["lovable"].url == "https://lovable.dev/invite/U7087MO"
    assert referrals["lovable"].category == "ai-code"
    assert referrals["manus"].enabled is True
    assert referrals["manus"].url == "https://manus.im/invitation/4QB3RCLPTD1A"
    assert "bonus credits" in referrals["manus"].anchor


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
    assert category_has_enabled_program("ai-writing") is False
    assert category_has_enabled_program("ai-code") is True
