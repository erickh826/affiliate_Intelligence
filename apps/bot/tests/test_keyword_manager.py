from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from keyword_manager import KeywordManager, _DIFFICULTY_MAX, _VOLUME_MIN

_INSERT = (
    "INSERT INTO keywords "
    "(keyword, category, intent, monthly_volume, difficulty, status, slug) "
    "VALUES (?,?,?,?,?,?,?)"
)

_ROWS = [
    # slug                        vol   diff  status
    ("high priority pending",    "ai-writing", "comparison", 5000, 10, "pending",       "high-priority-pending"),
    ("low priority pending",     "ai-writing", "comparison",  200, 40, "pending",       "low-priority-pending"),
    ("needs rewrite kw",         "ai-writing", "comparison", 3000, 20, "needs_rewrite", "needs-rewrite-kw"),
    ("below volume threshold",   "ai-writing", "comparison",   50, 10, "pending",       "below-volume"),
    ("above diff threshold",     "ai-writing", "comparison", 5000, 50, "pending",       "above-diff"),
    ("published kw",             "ai-writing", "comparison", 5000, 10, "published",     "published-kw"),
    ("failed kw",                "ai-writing", "comparison", 5000, 10, "failed",        "failed-kw"),
]


@pytest.fixture()
def mgr(tmp_path: Path) -> Generator[KeywordManager, None, None]:
    km = KeywordManager(tmp_path / "test.db")
    km._conn.executemany(_INSERT, _ROWS)
    km._conn.commit()
    yield km
    km.close()


class TestSelectKeywords:
    def test_normal_mode_includes_pending_and_rewrite(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10)
        # Verify initial selection content, but note status will have changed to 'generating'
        # The returned dicts contain the status AT THE TIME OF SELECT
        statuses = {r["status"] for r in results}
        assert statuses == {"pending", "needs_rewrite"}

    def test_select_updates_status_to_generating(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(1)
        slug = results[0]["slug"]
        row = mgr.get_keyword(slug)
        assert row is not None
        assert row["status"] == "generating"

    def test_excludes_published_and_failed(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10)
        slugs = {r["slug"] for r in results}
        assert "published-kw" not in slugs
        assert "failed-kw" not in slugs

    def test_excludes_below_volume_threshold(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10)
        assert all(r["monthly_volume"] > _VOLUME_MIN for r in results)

    def test_excludes_above_difficulty_threshold(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10)
        assert all(r["difficulty"] < _DIFFICULTY_MAX for r in results)

    def test_force_bypasses_thresholds(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10, force=True)
        slugs = {r["slug"] for r in results}
        assert "below-volume" in slugs
        assert "above-diff" in slugs

    def test_ordered_by_priority_desc(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10)
        scores = [r["priority_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_highest_priority_is_first(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10)
        assert results[0]["slug"] == "high-priority-pending"

    def test_batch_size_respected(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(1)
        assert len(results) == 1

    def test_batch_size_two_returns_two(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(2)
        assert len(results) == 2

    def test_priority_score_formula(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10)
        high = next(r for r in results if r["slug"] == "high-priority-pending")
        expected = 5000 / (10 + 1)
        assert abs(high["priority_score"] - expected) < 0.01

    def test_rewrite_mode_returns_only_needs_rewrite(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10, mode="rewrite")
        assert all(r["status"] == "needs_rewrite" for r in results)
        assert len(results) == 1
        assert results[0]["slug"] == "needs-rewrite-kw"

    def test_rewrite_mode_excludes_pending(self, mgr: KeywordManager) -> None:
        results = mgr.select_keywords(10, mode="rewrite")
        assert not any(r["status"] == "pending" for r in results)

    def test_second_select_excludes_locked_rows(self, mgr: KeywordManager) -> None:
        first = mgr.select_keywords(1)
        second = mgr.select_keywords(10)
        first_slugs = {r["slug"] for r in first}
        second_slugs = {r["slug"] for r in second}
        assert first_slugs.isdisjoint(second_slugs)

    def test_generating_rows_not_reselected(self, mgr: KeywordManager) -> None:
        all_rows = mgr.select_keywords(10)
        assert mgr.select_keywords(10) == []
        assert len(all_rows) > 0

    def test_empty_when_no_selectable_rows(self, tmp_path: Path) -> None:
        km = KeywordManager(tmp_path / "empty.db")
        assert km.select_keywords(10) == []
        km.close()


class TestGetKeyword:
    def test_returns_dict_for_existing_slug(self, mgr: KeywordManager) -> None:
        result = mgr.get_keyword("high-priority-pending")
        assert result is not None
        assert result["slug"] == "high-priority-pending"
        assert result["keyword"] == "high priority pending"

    def test_returns_none_for_missing_slug(self, mgr: KeywordManager) -> None:
        assert mgr.get_keyword("does-not-exist") is None

    def test_returned_dict_has_all_columns(self, mgr: KeywordManager) -> None:
        result = mgr.get_keyword("high-priority-pending")
        assert result is not None
        for col in ("id", "keyword", "category", "intent", "monthly_volume",
                    "difficulty", "status", "slug", "published_at"):
            assert col in result


class TestUpdateStatus:
    def test_updates_pending_to_published(self, mgr: KeywordManager) -> None:
        mgr.update_status("high-priority-pending", "published")
        row = mgr.get_keyword("high-priority-pending")
        assert row is not None
        assert row["status"] == "published"

    def test_published_sets_published_at(self, mgr: KeywordManager) -> None:
        mgr.update_status("high-priority-pending", "published")
        row = mgr.get_keyword("high-priority-pending")
        assert row is not None
        assert row["published_at"] is not None

    def test_published_at_not_overwritten_on_republish(self, mgr: KeywordManager) -> None:
        mgr.update_status("high-priority-pending", "published")
        first_date = mgr.get_keyword("high-priority-pending")["published_at"]  # type: ignore[index]
        mgr.update_status("high-priority-pending", "published")
        second_date = mgr.get_keyword("high-priority-pending")["published_at"]  # type: ignore[index]
        assert first_date == second_date

    def test_updates_to_failed(self, mgr: KeywordManager) -> None:
        mgr.update_status("high-priority-pending", "failed")
        row = mgr.get_keyword("high-priority-pending")
        assert row is not None
        assert row["status"] == "failed"

    def test_updates_to_needs_rewrite(self, mgr: KeywordManager) -> None:
        mgr.update_status("published-kw", "needs_rewrite")
        row = mgr.get_keyword("published-kw")
        assert row is not None
        assert row["status"] == "needs_rewrite"

    def test_needs_rewrite_becomes_selectable(self, mgr: KeywordManager) -> None:
        mgr.update_status("published-kw", "needs_rewrite")
        results = mgr.select_keywords(10)
        slugs = {r["slug"] for r in results}
        assert "published-kw" in slugs

    def test_raises_on_invalid_status(self, mgr: KeywordManager) -> None:
        with pytest.raises(ValueError, match="invalid status"):
            mgr.update_status("high-priority-pending", "unknown")

    def test_failed_not_selected_after_update(self, mgr: KeywordManager) -> None:
        mgr.update_status("high-priority-pending", "failed")
        results = mgr.select_keywords(10)
        slugs = {r["slug"] for r in results}
        assert "high-priority-pending" not in slugs


class TestContextManager:
    def test_context_manager_closes_connection(self, tmp_path: Path) -> None:
        with KeywordManager(tmp_path / "ctx.db") as km:
            assert km.select_keywords(1) == []
