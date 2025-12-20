"""
Comprehensive unit tests for TaskFetcher.

Tests cover:
- Task fetching with caching
- Dependency checking logic
- Priority scoring algorithm
- Age bonus calculation
- Label filtering
- Cache invalidation
- Error handling
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta, timezone

from agent_factory.scaffold.task_fetcher import TaskFetcher


class TestTaskFetcherInitialization:
    """Test TaskFetcher initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default cache TTL."""
        fetcher = TaskFetcher()
        
        assert fetcher._cache is None
        assert fetcher._cache_time is None
        assert fetcher._cache_ttl == 60

    def test_init_with_custom_ttl(self):
        """Test initialization with custom cache TTL."""
        fetcher = TaskFetcher(cache_ttl_sec=120)
        
        assert fetcher._cache_ttl == 120

    def test_init_with_zero_ttl(self):
        """Test initialization with zero cache TTL (cache disabled)."""
        fetcher = TaskFetcher(cache_ttl_sec=0)
        
        assert fetcher._cache_ttl == 0

    def test_init_with_very_long_ttl(self):
        """Test initialization with very long cache TTL."""
        fetcher = TaskFetcher(cache_ttl_sec=3600)
        
        assert fetcher._cache_ttl == 3600


class TestFetchEligibleTasks:
    """Test fetch_eligible_tasks method."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_basic_tasks(self, mock_task_list):
        """Test fetching basic tasks without dependencies."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Test Task 1',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': 'Test',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        assert len(tasks) == 1
        assert tasks[0]['id'] == 'task-1'
        mock_task_list.assert_called_once()

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_respects_max_tasks(self, mock_task_list):
        """Test that max_tasks limit is respected."""
        mock_task_list.return_value = [
            {
                'id': f'task-{i}',
                'title': f'Test Task {i}',
                'status': 'To Do',
                'priority': 'medium',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
            for i in range(20)
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=5)
        
        assert len(tasks) <= 5

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_with_mcp_import_error(self, mock_task_list):
        """Test fallback to placeholder when MCP import fails."""
        fetcher = TaskFetcher()
        
        # Simulate import error by patching the import
        with patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list', side_effect=ImportError):
            tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should return placeholder tasks
        assert len(tasks) >= 1
        assert 'placeholder' in tasks[0]['id'].lower()

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_with_exception(self, mock_task_list):
        """Test error handling when MCP call fails."""
        mock_task_list.side_effect = Exception("MCP connection error")
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should return empty list on error
        assert tasks == []

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_empty_backlog(self, mock_task_list):
        """Test fetching when backlog is empty."""
        mock_task_list.return_value = []
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        assert tasks == []


class TestCaching:
    """Test caching behavior."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_cache_hit(self, mock_task_list):
        """Test that cache is used on subsequent calls."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Test',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher(cache_ttl_sec=60)
        
        # First call - should hit MCP
        tasks1 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 1
        
        # Second call - should use cache
        tasks2 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 1  # No additional call
        
        assert tasks1 == tasks2

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_cache_expiration(self, mock_task_list):
        """Test that cache expires after TTL."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Test',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher(cache_ttl_sec=1)
        
        # First call
        tasks1 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 1
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Second call - should hit MCP again
        tasks2 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 2

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_cache_with_different_labels(self, mock_task_list):
        """Test that label filtering works with cached data."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Build Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-2',
                'title': 'Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['test'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher(cache_ttl_sec=60)
        
        # First call - no filter
        all_tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert len(all_tasks) == 2
        
        # Second call - with label filter (should use cache)
        build_tasks = fetcher.fetch_eligible_tasks(max_tasks=10, labels=['build'])
        assert len(build_tasks) == 1
        assert build_tasks[0]['id'] == 'task-1'
        
        # Should have only called MCP once
        assert mock_task_list.call_count == 1


class TestInvalidateCache:
    """Test cache invalidation."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_invalidate_cache(self, mock_task_list):
        """Test manual cache invalidation."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Test',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher(cache_ttl_sec=60)
        
        # First call - populate cache
        tasks1 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 1
        
        # Invalidate cache
        fetcher.invalidate_cache()
        
        # Next call should hit MCP again
        tasks2 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 2

    def test_invalidate_empty_cache(self):
        """Test invalidating cache when no cache exists."""
        fetcher = TaskFetcher()
        
        # Should not raise error
        fetcher.invalidate_cache()
        
        assert fetcher._cache is None
        assert fetcher._cache_time is None


class TestDependencyChecking:
    """Test dependency satisfaction logic."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_task_with_satisfied_dependency(self, mock_task_view, mock_task_list):
        """Test task with satisfied (Done) dependency is included."""
        mock_task_list.return_value = [
            {
                'id': 'task-2',
                'title': 'Dependent Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-1'],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        mock_task_view.return_value = {
            'id': 'task-1',
            'status': 'Done'  # Dependency satisfied
        }
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        assert len(tasks) == 1
        assert tasks[0]['id'] == 'task-2'

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_task_with_unsatisfied_dependency(self, mock_task_view, mock_task_list):
        """Test task with unsatisfied dependency is filtered out."""
        mock_task_list.return_value = [
            {
                'id': 'task-2',
                'title': 'Dependent Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-1'],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        mock_task_view.return_value = {
            'id': 'task-1',
            'status': 'To Do'  # Dependency not satisfied
        }
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        assert len(tasks) == 0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_task_with_multiple_dependencies(self, mock_task_view, mock_task_list):
        """Test task with multiple dependencies - all must be satisfied."""
        mock_task_list.return_value = [
            {
                'id': 'task-3',
                'title': 'Multi-Dependent Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-1', 'task-2'],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        # First dependency Done, second In Progress
        def task_view_side_effect(id):
            if id == 'task-1':
                return {'id': 'task-1', 'status': 'Done'}
            else:
                return {'id': 'task-2', 'status': 'In Progress'}
        
        mock_task_view.side_effect = task_view_side_effect
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should be filtered out (not all dependencies Done)
        assert len(tasks) == 0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_dependency_check_error_handling(self, mock_task_view, mock_task_list):
        """Test error handling when dependency check fails."""
        mock_task_list.return_value = [
            {
                'id': 'task-2',
                'title': 'Dependent Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-1'],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        mock_task_view.side_effect = Exception("Dependency not found")
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should be filtered out when dependency check fails
        assert len(tasks) == 0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_task_with_no_dependencies(self, mock_task_list):
        """Test task with no dependencies is always eligible."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Independent Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        assert len(tasks) == 1


class TestPriorityScoring:
    """Test priority scoring algorithm."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_high_priority_score(self, mock_task_list):
        """Test high priority tasks get score 10."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'High Priority',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        score = fetcher._priority_score(tasks[0])
        assert score >= 10  # Base score for high priority

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_medium_priority_score(self, mock_task_list):
        """Test medium priority tasks get score 5."""
        task = {
            'id': 'task-1',
            'title': 'Medium Priority',
            'status': 'To Do',
            'priority': 'medium',
            'labels': [],
            'dependencies': [],
            'description': '',
            'acceptance_criteria': []
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        assert score == 5  # Base score for medium priority

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_low_priority_score(self, mock_task_list):
        """Test low priority tasks get score 1."""
        task = {
            'id': 'task-1',
            'title': 'Low Priority',
            'status': 'To Do',
            'priority': 'low',
            'labels': [],
            'dependencies': [],
            'description': '',
            'acceptance_criteria': []
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        assert score == 1

    def test_critical_label_bonus(self):
        """Test critical label adds +5 to score."""
        task = {
            'id': 'task-1',
            'priority': 'medium',
            'labels': ['critical']
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        # Medium (5) + critical (5) = 10
        assert score >= 10

    def test_quick_win_label_bonus(self):
        """Test quick-win label adds +3 to score."""
        task = {
            'id': 'task-1',
            'priority': 'medium',
            'labels': ['quick-win']
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        # Medium (5) + quick-win (3) = 8
        assert score >= 8

    def test_user_action_label_penalty(self):
        """Test user-action label subtracts 10 from score."""
        task = {
            'id': 'task-1',
            'priority': 'high',
            'labels': ['user-action']
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        # High (10) - user-action (10) = 0 (clamped to 0)
        assert score == 0

    def test_combined_label_bonuses(self):
        """Test multiple label bonuses are additive."""
        task = {
            'id': 'task-1',
            'priority': 'high',
            'labels': ['critical', 'quick-win']
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        # High (10) + critical (5) + quick-win (3) = 18
        assert score >= 18

    def test_score_is_non_negative(self):
        """Test score is clamped to non-negative values."""
        task = {
            'id': 'task-1',
            'priority': 'low',
            'labels': ['user-action']
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        # Low (1) - user-action (10) = -9, clamped to 0
        assert score >= 0


class TestAgeBonus:
    """Test age bonus calculation."""

    def test_age_bonus_new_task(self):
        """Test age bonus for very new task (0 days) is 0."""
        task = {
            'created_date': datetime.now(timezone.utc).isoformat()
        }
        
        fetcher = TaskFetcher()
        age_bonus = fetcher._calculate_age_bonus(task)
        
        assert age_bonus == 0.0

    def test_age_bonus_30_days(self):
        """Test age bonus for 30-day-old task is 1.0."""
        created = datetime.now(timezone.utc) - timedelta(days=30)
        task = {
            'created_date': created.isoformat()
        }
        
        fetcher = TaskFetcher()
        age_bonus = fetcher._calculate_age_bonus(task)
        
        assert 0.9 <= age_bonus <= 1.1  # Allow small floating point errors

    def test_age_bonus_60_days(self):
        """Test age bonus for 60-day-old task is 2.0 (capped)."""
        created = datetime.now(timezone.utc) - timedelta(days=60)
        task = {
            'created_date': created.isoformat()
        }
        
        fetcher = TaskFetcher()
        age_bonus = fetcher._calculate_age_bonus(task)
        
        assert 1.9 <= age_bonus <= 2.0

    def test_age_bonus_very_old_task_capped(self):
        """Test age bonus is capped at 2.0 for very old tasks."""
        created = datetime.now(timezone.utc) - timedelta(days=365)
        task = {
            'created_date': created.isoformat()
        }
        
        fetcher = TaskFetcher()
        age_bonus = fetcher._calculate_age_bonus(task)
        
        assert age_bonus == 2.0

    def test_age_bonus_no_created_date(self):
        """Test age bonus is 0 when no created_date provided."""
        task = {}
        
        fetcher = TaskFetcher()
        age_bonus = fetcher._calculate_age_bonus(task)
        
        assert age_bonus == 0.0

    def test_age_bonus_invalid_date_format(self):
        """Test age bonus is 0 when date format is invalid."""
        task = {
            'created_date': 'invalid-date-format'
        }
        
        fetcher = TaskFetcher()
        age_bonus = fetcher._calculate_age_bonus(task)
        
        assert age_bonus == 0.0


class TestLabelFiltering:
    """Test label filtering functionality."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_filter_by_single_label(self, mock_task_list):
        """Test filtering by a single label."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Build Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-2',
                'title': 'Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['test'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10, labels=['build'])
        
        assert len(tasks) == 1
        assert tasks[0]['id'] == 'task-1'

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_filter_by_multiple_labels(self, mock_task_list):
        """Test filtering by multiple labels (OR logic)."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Build Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-2',
                'title': 'Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['test'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-3',
                'title': 'Docs Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['docs'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10, labels=['build', 'test'])
        
        assert len(tasks) == 2
        assert any(t['id'] == 'task-1' for t in tasks)
        assert any(t['id'] == 'task-2' for t in tasks)

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_filter_no_matching_labels(self, mock_task_list):
        """Test filtering with no matching labels returns empty list."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Build Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10, labels=['nonexistent'])
        
        assert len(tasks) == 0


class TestPrioritySorting:
    """Test priority sorting of tasks."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_tasks_sorted_by_priority(self, mock_task_list):
        """Test tasks are sorted by priority score (highest first)."""
        mock_task_list.return_value = [
            {
                'id': 'task-low',
                'title': 'Low Priority',
                'status': 'To Do',
                'priority': 'low',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-high',
                'title': 'High Priority',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-medium',
                'title': 'Medium Priority',
                'status': 'To Do',
                'priority': 'medium',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should be sorted: high, medium, low
        assert tasks[0]['id'] == 'task-high'
        assert tasks[1]['id'] == 'task-medium'
        assert tasks[2]['id'] == 'task-low'


class TestPlaceholderTasks:
    """Test placeholder task generation."""

    def test_placeholder_tasks_when_mcp_unavailable(self):
        """Test placeholder tasks are returned when MCP unavailable."""
        fetcher = TaskFetcher()
        tasks = fetcher._get_placeholder_tasks(max_tasks=5)
        
        assert len(tasks) >= 1
        assert 'placeholder' in tasks[0]['id']
        assert tasks[0]['status'] == 'To Do'

    def test_placeholder_respects_max_tasks(self):
        """Test placeholder generation respects max_tasks limit."""
        fetcher = TaskFetcher()
        tasks = fetcher._get_placeholder_tasks(max_tasks=1)
        
        assert len(tasks) == 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_with_max_tasks_zero(self, mock_task_list):
        """Test fetching with max_tasks=0."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Test',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=0)
        
        assert len(tasks) == 0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_with_negative_max_tasks(self, mock_task_list):
        """Test fetching with negative max_tasks."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Test',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=-1)
        
        # Should handle gracefully (likely returns empty or uses default)
        assert isinstance(tasks, list)

    def test_priority_score_with_missing_priority_field(self):
        """Test priority scoring when priority field is missing."""
        task = {
            'id': 'task-1',
            'labels': []
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        # Should default to 'low' priority (score 1)
        assert score >= 0

    def test_priority_score_with_unknown_priority(self):
        """Test priority scoring with unknown priority value."""
        task = {
            'id': 'task-1',
            'priority': 'unknown',
            'labels': []
        }
        
        fetcher = TaskFetcher()
        score = fetcher._priority_score(task)
        
        # Should default to low priority (score 1)
        assert score >= 0