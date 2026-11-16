from __future__ import annotations

from typing import Any

EDITORIAL_FACTS: dict[str, list[dict[str, str]]] = {
    "manus ai review": [
        {
            "claim": (
                "Manus paused new subscriptions in some regions since August 2026."
            ),
            "source": "editorial",
        }
    ],
}


def editorial_facts_for(keyword: str) -> list[dict[str, str]]:
    return [dict(item) for item in EDITORIAL_FACTS.get(keyword.strip().lower(), [])]


def is_editorial_fact(fact: object) -> bool:
    return isinstance(fact, dict) and str(fact.get("source") or "") == "editorial"


def merge_editorial_facts(keyword: str, facts: list[Any]) -> list[Any]:
    extra = editorial_facts_for(keyword)
    if not extra:
        return list(facts)
    seen = {
        str(item.get("claim") or "").strip() for item in facts if isinstance(item, dict)
    }
    prefix = [item for item in extra if item["claim"] not in seen]
    return prefix + list(facts)
