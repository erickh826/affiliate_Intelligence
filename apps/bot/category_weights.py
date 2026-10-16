from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS_PATH = _PROJECT_ROOT / "monetisation" / "category_weights.json"
DEFAULT_CONTENT_ROOT = _PROJECT_ROOT / "apps" / "web" / "content"


@dataclass(frozen=True)
class WeightConfig:
    published_target: int
    focus_categories: tuple[str, ...]
    categories: tuple[str, ...]
    focus_weights: dict[str, int]
    even_weights: dict[str, int]


def _weight_map(raw: object, categories: tuple[str, ...]) -> dict[str, int]:
    source = raw if isinstance(raw, dict) else {}
    weights: dict[str, int] = {}
    for category in categories:
        value = source.get(category, 0)
        weights[category] = int(value) if isinstance(value, int | float) else 0
    return weights


def load_weight_config(path: Path | None = None) -> WeightConfig:
    config_path = path or DEFAULT_WEIGHTS_PATH
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("category weight config must be an object")
    categories_raw = raw.get("categories", [])
    focus_raw = raw.get("focus_categories", [])
    if not isinstance(categories_raw, list) or not categories_raw:
        raise ValueError("category weight config needs categories")
    categories = tuple(str(category) for category in categories_raw)
    focus = (
        tuple(str(category) for category in focus_raw)
        if isinstance(focus_raw, list)
        else ()
    )
    target = raw.get("published_target", 10)
    published_target = int(target) if isinstance(target, int | float) else 10
    return WeightConfig(
        published_target=published_target,
        focus_categories=focus,
        categories=categories,
        focus_weights=_weight_map(raw.get("focus_weights"), categories),
        even_weights=_weight_map(raw.get("even_weights"), categories),
    )


def mdx_is_draft(text: str) -> bool:
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    for line in text[3:end].splitlines():
        if not line.startswith("draft:"):
            continue
        value = line.split(":", 1)[1].strip().strip("\"'").lower()
        return value in {"true", "yes", "1"}
    return False


def _frontmatter_category(text: str, fallback: str) -> str:
    if not text.startswith("---"):
        return fallback
    end = text.find("\n---", 3)
    if end == -1:
        return fallback
    for line in text[3:end].splitlines():
        if not line.startswith("category:"):
            continue
        value = line.split(":", 1)[1].strip().strip("\"'")
        return value or fallback
    return fallback


def count_live_articles(content_root: Path | None = None) -> dict[str, int]:
    root = content_root or DEFAULT_CONTENT_ROOT
    counts: Counter[str] = Counter()
    if not root.exists():
        return {}
    for path in root.rglob("*.mdx"):
        if path.parent.name == "faq":
            continue
        text = path.read_text(encoding="utf-8")
        if mdx_is_draft(text):
            continue
        category = _frontmatter_category(text, path.parent.name)
        counts[category] += 1
    return dict(counts)


def weight_mode(published_counts: dict[str, int], config: WeightConfig) -> str:
    for category in config.focus_categories:
        if published_counts.get(category, 0) < config.published_target:
            return "focus"
    return "even"


def allocate_slots(
    batch_size: int,
    weights: dict[str, int],
    order: tuple[str, ...] | list[str],
) -> dict[str, int]:
    active = [(category, weights.get(category, 0)) for category in order]
    active = [(category, weight) for category, weight in active if weight > 0]
    total = sum(weight for _, weight in active)
    if batch_size <= 0 or total <= 0:
        return {}
    raw = [(category, batch_size * weight / total) for category, weight in active]
    slots = {category: int(value) for category, value in raw}
    remainder = batch_size - sum(slots.values())
    fractional = sorted(
        (
            (value - int(value), index, category)
            for index, (category, value) in enumerate(raw)
        ),
        key=lambda item: (-item[0], item[1]),
    )
    for _, _, category in fractional[:remainder]:
        slots[category] += 1
    return slots


def choose_keywords(
    rows: list[dict[str, Any]],
    batch_size: int,
    *,
    published_counts: dict[str, int],
    config: WeightConfig,
) -> tuple[list[dict[str, Any]], str]:
    mode = weight_mode(published_counts, config)
    weights = config.focus_weights if mode == "focus" else config.even_weights
    slots = allocate_slots(batch_size, weights, config.categories)
    by_category: dict[str, list[dict[str, Any]]] = {
        category: [] for category in config.categories
    }
    for row in rows:
        category = str(row.get("category") or "")
        if category in by_category:
            by_category[category].append(row)
    chosen: list[dict[str, Any]] = []
    for category in config.categories:
        pool = by_category[category]
        take = slots.get(category, 0)
        chosen.extend(pool[:take])
        by_category[category] = pool[take:]
    if len(chosen) < batch_size:
        rest: list[dict[str, Any]] = []
        for category in config.categories:
            rest.extend(by_category[category])
        rest.sort(key=lambda row: float(row.get("priority_score") or 0), reverse=True)
        chosen.extend(rest[: batch_size - len(chosen)])
    chosen.sort(key=lambda row: float(row.get("priority_score") or 0), reverse=True)
    return chosen[:batch_size], mode
