from __future__ import annotations

import json
from pathlib import Path

from category_weights import (
    allocate_slots,
    choose_keywords,
    count_live_articles,
    load_weight_config,
    weight_mode,
)
from keyword_manager import KeywordManager


def _config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "published_target": 10,
                "focus_categories": ["ai-writing", "seo"],
                "categories": [
                    "ai-writing",
                    "seo",
                    "ai-video",
                    "ai-productivity",
                    "ai-code",
                ],
                "focus_weights": {
                    "ai-writing": 45,
                    "seo": 45,
                    "ai-video": 4,
                    "ai-productivity": 3,
                    "ai-code": 3,
                },
                "even_weights": {
                    "ai-writing": 1,
                    "seo": 1,
                    "ai-video": 1,
                    "ai-productivity": 1,
                    "ai-code": 1,
                },
            }
        ),
        encoding="utf-8",
    )


def _row(slug: str, category: str, volume: int = 1000) -> dict[str, object]:
    return {
        "slug": slug,
        "category": category,
        "priority_score": volume / 11,
        "status": "pending",
    }


def test_focus_mode_until_each_target_is_met(tmp_path: Path) -> None:
    path = tmp_path / "weights.json"
    _config(path)
    config = load_weight_config(path)
    assert weight_mode({"ai-writing": 10, "seo": 9}, config) == "focus"
    assert weight_mode({"ai-writing": 10, "seo": 10}, config) == "even"
    assert weight_mode({}, config) == "focus"


def test_focus_batch_comes_mostly_from_writing_and_seo(tmp_path: Path) -> None:
    path = tmp_path / "weights.json"
    _config(path)
    config = load_weight_config(path)
    rows = []
    for category in config.categories:
        for index in range(4):
            rows.append(_row(f"{category}-{index}", category, volume=5000 - index))
    chosen, mode = choose_keywords(
        rows, 5, published_counts={"ai-writing": 1, "seo": 0}, config=config
    )
    mix: dict[str, int] = {}
    for row in chosen:
        mix[str(row["category"])] = mix.get(str(row["category"]), 0) + 1
    assert mode == "focus"
    assert mix["ai-writing"] + mix["seo"] >= 4
    assert sum(mix.values()) == 5


def test_even_batch_rotates_across_categories(tmp_path: Path) -> None:
    path = tmp_path / "weights.json"
    _config(path)
    config = load_weight_config(path)
    rows = [_row(category, category) for category in config.categories]
    counts = {category: 10 for category in config.focus_categories}
    chosen, mode = choose_keywords(rows, 5, published_counts=counts, config=config)
    assert mode == "even"
    assert {row["category"] for row in chosen} == set(config.categories)


def test_allocate_slots_uses_largest_remainder() -> None:
    slots = allocate_slots(
        5,
        {"ai-writing": 45, "seo": 45, "ai-code": 10},
        ["ai-writing", "seo", "ai-code"],
    )
    assert sum(slots.values()) == 5
    assert slots["ai-writing"] >= 2
    assert slots["seo"] >= 2


def test_live_article_count_ignores_drafts(tmp_path: Path) -> None:
    writing = tmp_path / "ai-writing"
    seo = tmp_path / "seo"
    writing.mkdir()
    seo.mkdir()
    (writing / "live.mdx").write_text(
        "---\ncategory: ai-writing\ndraft: false\n---\n",
        encoding="utf-8",
    )
    (writing / "held.mdx").write_text(
        "---\ncategory: ai-writing\ndraft: true\n---\n",
        encoding="utf-8",
    )
    (seo / "also-live.mdx").write_text(
        "---\ncategory: seo\n---\n",
        encoding="utf-8",
    )
    assert count_live_articles(tmp_path) == {"ai-writing": 1, "seo": 1}


def test_selector_logs_focus_mix(tmp_path: Path) -> None:
    weights = tmp_path / "weights.json"
    _config(weights)
    km = KeywordManager(tmp_path / "keywords.db")
    rows = []
    for category in ("ai-writing", "seo", "ai-video", "ai-productivity", "ai-code"):
        for index in range(3):
            rows.append(
                (
                    f"{category} keyword {index}",
                    category,
                    "comparison",
                    2000 - index,
                    20,
                    "pending",
                    f"{category}-{index}",
                )
            )
    km._conn.executemany(
        "INSERT INTO keywords "
        "(keyword, category, intent, monthly_volume, difficulty, status, slug) "
        "VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    km._conn.commit()
    selected = km.select_keywords(
        5,
        published_counts={"ai-writing": 0, "seo": 0},
        weights_path=weights,
        content_root=tmp_path / "empty-content",
    )
    mix: dict[str, int] = {}
    for row in selected:
        mix[str(row["category"])] = mix.get(str(row["category"]), 0) + 1
    assert km.last_weight_mode == "focus"
    assert len(selected) == 5
    assert mix.get("ai-writing", 0) + mix.get("seo", 0) >= 4
    km.close()
