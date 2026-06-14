from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from db_setup import DB_PATH, init_db

_VOLUME_MIN = 100
_DIFFICULTY_MAX = 45
_VALID_STATUSES = frozenset({"pending", "published", "needs_rewrite", "failed", "generating"})


class KeywordManager:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._conn = init_db(db_path)
        self._conn.row_factory = sqlite3.Row

    def __enter__(self) -> KeywordManager:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def select_keywords(
        self, batch_size: int, mode: str = "normal", force: bool = False
    ) -> list[dict[str, Any]]:
        if mode == "rewrite":
            statuses: tuple[str, ...] = ("needs_rewrite",)
        else:
            statuses = ("pending", "needs_rewrite")

        placeholders = ",".join("?" * len(statuses))

        filter_clause = ""
        if not force:
            filter_clause = f"AND monthly_volume > {_VOLUME_MIN} AND difficulty < {_DIFFICULTY_MAX}"

        # Atomic select-and-lock
        with self._conn:
            rows = self._conn.execute(
                f"""
                SELECT *,
                       CAST(monthly_volume AS REAL) / (difficulty + 1) AS priority_score
                FROM   keywords
                WHERE  status IN ({placeholders})
                {filter_clause}
                ORDER  BY priority_score DESC
                LIMIT  ?
                """,
                (*statuses, batch_size),
            ).fetchall()

            slugs = [row["slug"] for row in rows]
            if slugs:
                slug_placeholders = ",".join("?" * len(slugs))
                self._conn.execute(
                    f"UPDATE keywords SET status = 'generating' WHERE slug IN ({slug_placeholders})",
                    slugs,
                )

        return [dict(row) for row in rows]

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
