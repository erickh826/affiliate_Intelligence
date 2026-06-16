from __future__ import annotations

import re
from pathlib import Path

from db_setup import DB_PATH, init_db

# (keyword, category, intent, monthly_volume, difficulty, affiliate_partner)
_SEED: list[tuple[str, str, str, int, int, str | None]] = [
    # ai-writing — comparison
    ("best ai writing tools 2026", "ai-writing", "comparison", 8100, 32, "jasper"),
    ("jasper ai vs writesonic", "ai-writing", "comparison", 2400, 28, "jasper"),
    ("copy ai vs jasper", "ai-writing", "comparison", 1900, 25, "jasper"),
    ("writesonic vs copy ai", "ai-writing", "comparison", 1600, 22, "writesonic"),
    ("best ai copywriting tools", "ai-writing", "comparison", 3200, 33, "jasper"),
    ("surfer seo vs clearscope", "ai-writing", "comparison", 1200, 30, "surfer"),
    (
        "jasper ai vs chatgpt for writing",
        "ai-writing",
        "comparison",
        4400,
        38,
        "jasper",
    ),
    ("ai email writer tools comparison", "ai-writing", "comparison", 2800, 27, None),
    # ai-writing — informational
    ("writesonic review 2026", "ai-writing", "informational", 2200, 30, "writesonic"),
    ("jasper ai review 2026", "ai-writing", "informational", 4400, 35, "jasper"),
    ("copy ai review 2026", "ai-writing", "informational", 1900, 25, None),
    ("surfer seo review 2026", "ai-writing", "informational", 3300, 30, "surfer"),
    (
        "ai writing tools for bloggers",
        "ai-writing",
        "informational",
        2100,
        28,
        "jasper",
    ),
    (
        "best ai tools for content marketing",
        "ai-writing",
        "informational",
        4500,
        40,
        "jasper",
    ),
    # ai-writing — tutorial
    ("how to use jasper ai", "ai-writing", "tutorial", 1800, 20, "jasper"),
    ("how to use surfer seo", "ai-writing", "tutorial", 1100, 22, "surfer"),
    ("how to write seo articles with ai", "ai-writing", "tutorial", 2600, 30, "jasper"),
    # ai-image — comparison
    ("best ai image generators 2026", "ai-image", "comparison", 9200, 38, None),
    ("midjourney vs dall-e 3", "ai-image", "comparison", 5400, 32, None),
    ("stable diffusion vs midjourney", "ai-image", "comparison", 4100, 34, None),
    ("adobe firefly vs midjourney", "ai-image", "comparison", 2200, 30, None),
    ("best ai image upscalers", "ai-image", "comparison", 2400, 22, None),
    # ai-image — informational
    ("midjourney review 2026", "ai-image", "informational", 6600, 40, None),
    ("dall-e 3 review 2026", "ai-image", "informational", 3300, 28, None),
    ("ai art generators for beginners", "ai-image", "informational", 3100, 25, None),
    # ai-image — tutorial
    ("how to use midjourney", "ai-image", "tutorial", 8800, 35, None),
    ("how to create ai art for free", "ai-image", "tutorial", 5500, 30, None),
    ("stable diffusion setup guide", "ai-image", "tutorial", 3200, 28, None),
    # ai-video — comparison
    ("best ai video generators 2026", "ai-video", "comparison", 5500, 35, None),
    ("descript vs riverside", "ai-video", "comparison", 1800, 25, None),
    ("elevenlabs vs murf ai", "ai-video", "comparison", 1600, 24, "elevenlabs"),
    (
        "ai voice cloning tools comparison",
        "ai-video",
        "comparison",
        2900,
        28,
        "elevenlabs",
    ),
    ("best text to video ai tools", "ai-video", "comparison", 4200, 36, None),
    ("synthesia vs heygen", "ai-video", "comparison", 2300, 28, None),
    # ai-video — informational
    ("runway ml review 2026", "ai-video", "informational", 2700, 30, None),
    ("elevenlabs review 2026", "ai-video", "informational", 3900, 32, "elevenlabs"),
    ("descript review 2026", "ai-video", "informational", 2500, 26, None),
    # ai-video — tutorial
    ("how to use descript", "ai-video", "tutorial", 2100, 22, None),
    ("how to make ai videos for youtube", "ai-video", "tutorial", 6100, 33, None),
    (
        "elevenlabs voice cloning tutorial",
        "ai-video",
        "tutorial",
        2200,
        20,
        "elevenlabs",
    ),
    # ai-code — comparison
    ("best ai coding assistants 2026", "ai-code", "comparison", 7200, 37, None),
    ("github copilot vs cursor", "ai-code", "comparison", 4800, 35, None),
    ("tabnine vs github copilot", "ai-code", "comparison", 2200, 28, None),
    ("ai code review tools comparison", "ai-code", "comparison", 3100, 30, None),
    # ai-code — informational
    ("cursor ai review 2026", "ai-code", "informational", 5100, 32, None),
    ("github copilot review 2026", "ai-code", "informational", 4300, 38, None),
    ("codeium review 2026", "ai-code", "informational", 2100, 22, None),
    ("best ai tools for developers 2026", "ai-code", "informational", 4600, 40, None),
    # ai-code — tutorial
    ("how to use github copilot", "ai-code", "tutorial", 5500, 30, None),
    ("how to use cursor ai", "ai-code", "tutorial", 3400, 25, None),
    ("cursor ai setup guide for vscode", "ai-code", "tutorial", 2200, 20, None),
    # ai-productivity — comparison
    (
        "best ai productivity tools 2026",
        "ai-productivity",
        "comparison",
        6600,
        35,
        None,
    ),
    ("notion ai vs chatgpt", "ai-productivity", "comparison", 3200, 30, None),
    (
        "best ai meeting assistants 2026",
        "ai-productivity",
        "comparison",
        3400,
        30,
        None,
    ),
    ("best ai scheduling tools", "ai-productivity", "comparison", 2600, 28, None),
    # ai-productivity — informational
    ("notion ai review 2026", "ai-productivity", "informational", 4800, 33, None),
    ("otter ai review 2026", "ai-productivity", "informational", 2800, 28, None),
    ("reclaim ai review 2026", "ai-productivity", "informational", 1500, 20, None),
    ("ai tools for solopreneurs", "ai-productivity", "informational", 3200, 32, None),
    (
        "zapier ai features explained",
        "ai-productivity",
        "informational",
        2100,
        25,
        None,
    ),
    # ai-productivity — tutorial
    ("how to use notion ai", "ai-productivity", "tutorial", 3500, 25, None),
    ("otter ai setup guide", "ai-productivity", "tutorial", 1200, 18, None),
]


def _to_slug(keyword: str) -> str:
    slug = keyword.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug


def seed(db_path: Path = DB_PATH) -> int:
    conn = init_db(db_path)
    rows = [
        (kw, cat, intent, vol, diff, _to_slug(kw), partner)
        for kw, cat, intent, vol, diff, partner in _SEED
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO keywords
            (keyword, category, intent, monthly_volume, difficulty, slug, affiliate_partner)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    inserted = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    conn.close()
    return inserted


if __name__ == "__main__":
    count = seed()
    print(f"seed_complete rows={count}")
