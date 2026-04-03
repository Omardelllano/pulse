"""Tests for DB auto-cleanup job."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from pulso.engine.cleanup import run_cleanup, CLEANUP_RULES


class TestCleanupRules:
    def test_simulation_cache_ttl_is_48h(self):
        assert CLEANUP_RULES["simulation_cache"]["max_age_hours"] == 48

    def test_simulation_cache_max_entries_is_500(self):
        assert CLEANUP_RULES["simulation_cache"]["max_entries"] == 500

    def test_state_history_max_age_is_30_days(self):
        assert CLEANUP_RULES["state_history"]["max_age_days"] == 30

    def test_rate_limits_max_age_is_2h(self):
        assert CLEANUP_RULES["rate_limits"]["max_age_hours"] == 2


class TestRunCleanup:
    def test_run_cleanup_returns_dict(self):
        """run_cleanup should return counts per table."""
        mock_db = MagicMock()

        # Make queries return empty lists / count 0
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        result = run_cleanup(mock_db)

        assert isinstance(result, dict)
        assert "simulation_cache" in result
        assert "state_history" in result
        assert "rate_limits" in result

    def test_run_cleanup_returns_zero_when_nothing_to_delete(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        result = run_cleanup(mock_db)

        assert result["simulation_cache"] == 0
        assert result["state_history"] == 0
        assert result["rate_limits"] == 0

    def test_cleanup_commits_on_success(self):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query

        run_cleanup(mock_db)

        # commit() should have been called (once per table)
        assert mock_db.commit.call_count >= 3
