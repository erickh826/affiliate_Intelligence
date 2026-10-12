from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self

from category_weights import (
    choose_keywords,
    count_live_articles,
    load_weight_config,
)
from db_setup import DB_PATH, init_db

_VOLUME_MIN = 100
_DIFFICULTY_MAX = 45
_VALID_STATUSES = frozenset(
    {"pending", "published", "needs_rewrite", "failed", "generating", "draft"}
)


class KeywordManager:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._conn = init_db(db_path)
        self._conn.row_factory = sqlite3.Row
        self.last_weight_mode = "even"

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def select_keywords(
        self,
        batch_size: int,
        mode: str = "normal",
        force: bool = False,
        *,
        published_counts: Mapping[str, int] | None = None,
        weights_path: Path | None = None,
        content_root: Path | None = None,
    ) -> list[dict[str, Any]]:
        if mode == "rewrite":
            statuses: tuple[str, ...] = ("needs_rewrite",)
        else:
            statuses = ("pending", "needs_rewrite")

        placeholders = ",".join("?" * len(statuses))

        filter_clause = ""
        if not force:
            filter_clause = (
                f"AND monthly_volume > {_VOLUME_MIN} AND difficulty < {_DIFFICULTY_MAX}"
            )

        with self._conn:
            fetched = self._conn.execute(
                f"""
                SELECT *,
                       CAST(monthly_volume AS REAL) / (difficulty + 1) AS priority_score
                FROM   keywords
                WHERE  status IN ({placeholders})
                {filter_clause}
                ORDER  BY priority_score DESC
                """,
                statuses,
            ).fetchall()
            candidates = [dict(row) for row in fetched]
            if mode == "rewrite":
                self.last_weight_mode = "rewrite"
                chosen = candidates[:batch_size]
            else:
                counts = (
                    dict(published_counts)
                    if published_counts is not None
                    else count_live_articles(content_root)
                )
                config = load_weight_config(weights_path)
                chosen, self.last_weight_mode = choose_keywords(
                    candidates,
                    batch_size,
                    published_counts=counts,
                    config=config,
                )

            slugs = [row["slug"] for row in chosen]
            if slugs:
                slug_placeholders = ",".join("?" * len(slugs))
                self._conn.execute(
                    f"UPDATE keywords SET status = 'generating' WHERE slug IN ({slug_placeholders})",
                    slugs,
                )

        return chosen

    def get_keyword(self, slug: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM keywords WHERE slug = ?", (slug,)
        ).fetchone()
        return dict(row) if row else None

    def update_status(self, slug: str, status: str) -> None:
        if status not in _VALID_STATUSES:
            raise ValueError(f"invalid status: {status!r}")
        if status == "published":
            self._conn.execute(
                """
                UPDATE keywords
                SET    status       = ?,
                       published_at = COALESCE(published_at, date('now'))
                WHERE  slug = ?
                """,
                (status, slug),
            )
        else:
            self._conn.execute(
                "UPDATE keywords SET status = ? WHERE slug = ?", (status, slug)
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
