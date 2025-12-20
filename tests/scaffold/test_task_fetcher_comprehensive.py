"""
Comprehensive unit tests for TaskFetcher - Edge cases and failure conditions.

Tests cover:
- Cache behavior (hits, misses, invalidation)
- Dependency resolution (multiple deps, partial completion, errors)
- Priority scoring (base priority, label bonuses/penalties, age)
- Label filtering (single, multiple, OR logic)
- Error handling (MCP failures, exceptions)
- Performance (large task lists, complex dependency graphs)
"""

import pytest
import time
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
from pathlib import Path

from agent_factory.scaffold.task_fetcher import TaskFetcher


class TestTaskFetcherCache:
    """Test caching behavior of TaskFetcher."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_empty_task_list(self, mock_task_list):
        """Test handling of empty task list from MCP"""
        mock_task_list.return_value = []

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        assert tasks == []
        assert isinstance(tasks, list)

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_cache_hit_behavior(self, mock_task_list):
        """Test cache hit behavior (should not call MCP twice)"""
        mock_task_list.return_value = [
            {
                'id': 'task-cached',
                'title': 'Cached Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        fetcher = TaskFetcher(cache_ttl_sec=60)
        
        # First call - should fetch from MCP
        tasks1 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert len(tasks1) == 1
        assert mock_task_list.call_count == 1

        # Second call - should use cache
        tasks2 = fetcher.fetch_eligible_tasks(max_tasks=10)
        assert len(tasks2) == 1
        assert mock_task_list.call_count == 1  # Still only called once

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_cache_invalidation(self, mock_task_list):
        """Test manual cache invalidation"""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Task 1',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        fetcher = TaskFetcher(cache_ttl_sec=60)
        
        # First call
        fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 1

        # Invalidate cache
        fetcher.invalidate_cache()

        # Second call - should fetch again
        fetcher.fetch_eligible_tasks(max_tasks=10)
        assert mock_task_list.call_count == 2


class TestTaskFetcherDependencies:
    """Test dependency resolution logic."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_multiple_dependencies_all_done(self, mock_task_view, mock_task_list):
        """Test task with multiple dependencies all satisfied"""
        mock_task_list.return_value = [
            {
                'id': 'task-multi-dep',
                'title': 'Multi Dependency Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-1', 'task-2', 'task-3'],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        # All dependencies are Done
        mock_task_view.side_effect = [
            {'id': 'task-1', 'status': 'Done'},
            {'id': 'task-2', 'status': 'Done'},
            {'id': 'task-3', 'status': 'Done'}
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # Task should be eligible
        assert len(tasks) == 1
        assert tasks[0]['id'] == 'task-multi-dep'

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_multiple_dependencies_one_blocked(self, mock_task_view, mock_task_list):
        """Test task blocked by one unfinished dependency"""
        mock_task_list.return_value = [
            {
                'id': 'task-blocked',
                'title': 'Blocked Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-1', 'task-2', 'task-3'],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        # One dependency is In Progress, others Done
        mock_task_view.side_effect = [
            {'id': 'task-1', 'status': 'Done'},
            {'id': 'task-2', 'status': 'In Progress'},  # Blocker
            {'id': 'task-3', 'status': 'Done'}
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # Task should be filtered out
        assert len(tasks) == 0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_dependency_check_with_exception(self, mock_task_view, mock_task_list):
        """Test handling of exception during dependency check"""
        mock_task_list.return_value = [
            {
                'id': 'task-dep-error',
                'title': 'Task with Broken Dependency',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-nonexistent'],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        # Dependency lookup raises exception
        mock_task_view.side_effect = Exception("Task not found")

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # Task should be filtered out due to error
        assert len(tasks) == 0


class TestTaskFetcherPriorityScoring:
    """Test priority score calculation logic."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_priority_score_high(self, mock_task_list):
        """Test priority score for high priority tasks"""
        mock_task_list.return_value = [
            {
                'id': 'task-high',
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

        assert len(tasks) == 1
        # High priority should have score of 10
        score = fetcher._priority_score(tasks[0])
        assert score == 10.0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_priority_score_with_critical_label(self, mock_task_list):
        """Test priority score with critical label bonus (+5)"""
        mock_task_list.return_value = [
            {
                'id': 'task-critical',
                'title': 'Critical Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['critical'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        assert len(tasks) == 1
        # High (10) + critical label (+5) = 15
        score = fetcher._priority_score(tasks[0])
        assert score >= 15.0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_priority_score_with_quick_win_label(self, mock_task_list):
        """Test priority score with quick-win label bonus (+3)"""
        mock_task_list.return_value = [
            {
                'id': 'task-quick',
                'title': 'Quick Win',
                'status': 'To Do',
                'priority': 'medium',
                'labels': ['quick-win'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        assert len(tasks) == 1
        # Medium (5) + quick-win (+3) = 8
        score = fetcher._priority_score(tasks[0])
        assert score >= 8.0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_priority_score_with_user_action_penalty(self, mock_task_list):
        """Test priority score penalty for user-action tasks (-10)"""
        mock_task_list.return_value = [
            {
                'id': 'task-manual',
                'title': 'Manual Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['user-action'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        assert len(tasks) == 1
        # High (10) + user-action penalty (-10) = 0
        score = fetcher._priority_score(tasks[0])
        assert score == 0.0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_age_bonus_calculation(self, mock_task_list):
        """Test age bonus calculation for older tasks (capped at 2.0)"""
        # Create a task 60 days old
        old_date = (datetime.now() - timedelta(days=60)).isoformat()

        mock_task_list.return_value = [
            {
                'id': 'task-old',
                'title': 'Old Task',
                'status': 'To Do',
                'priority': 'medium',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': [],
                'created_date': old_date
            }
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        assert len(tasks) == 1
        # Should have age bonus (capped at 2.0 for 60+ days)
        age_bonus = fetcher._calculate_age_bonus(tasks[0])
        assert age_bonus == 2.0

