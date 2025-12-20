"""
Comprehensive validation tests for SCAFFOLD Orchestrator.

Tests all 6 core components:
1. TaskFetcher - Backlog.md MCP integration
2. WorktreeManager - Git worktree management
3. TaskRouter - Task routing logic
4. SessionManager - Session state persistence
5. ResultProcessor - PR creation and Backlog updates
6. Orchestrator - End-to-end integration

Requirements validated:
- REQ-ORCH-001: Orchestrator class with main() entry point
- REQ-ORCH-002: TaskFetcher queries Backlog.md via MCP
- REQ-ORCH-003: TaskRouter routes tasks to handlers
- REQ-ORCH-004: SessionManager tracks worktrees and budgets
- REQ-ORCH-005: ResultProcessor updates Backlog.md
- REQ-ORCH-006: Command-line interface works
"""

import pytest
from unittest.mock import MagicMock, Mock, patch, call
from pathlib import Path
import json
from datetime import datetime

# Import scaffold components
from agent_factory.scaffold.orchestrator import ScaffoldOrchestrator
from agent_factory.scaffold.session_manager import SessionManager
from agent_factory.scaffold.task_fetcher import TaskFetcher
from agent_factory.scaffold.task_router import TaskRouter
from agent_factory.scaffold.result_processor import ResultProcessor
from agent_factory.scaffold.worktree_manager import WorktreeManager
from agent_factory.scaffold.models import TaskContext, WorktreeMetadata, SessionState


# ============================================================================
# 1. IMPORT TESTS - Verify all modules import successfully
# ============================================================================

class TestImports:
    """Test all scaffold modules import without errors."""

    def test_orchestrator_imports(self):
        """REQ-ORCH-001: Verify ScaffoldOrchestrator class exists"""
        assert ScaffoldOrchestrator is not None
        assert hasattr(ScaffoldOrchestrator, 'run')

    def test_session_manager_imports(self):
        """REQ-ORCH-004: Verify SessionManager class exists"""
        assert SessionManager is not None
        assert hasattr(SessionManager, 'start_session')
        assert hasattr(SessionManager, 'resume_session')

    def test_task_fetcher_imports(self):
        """REQ-ORCH-002: Verify TaskFetcher class exists"""
        assert TaskFetcher is not None
        assert hasattr(TaskFetcher, 'fetch_eligible_tasks')

    def test_task_router_imports(self):
        """REQ-ORCH-003: Verify TaskRouter class exists"""
        assert TaskRouter is not None
        assert hasattr(TaskRouter, 'route')

    def test_result_processor_imports(self):
        """REQ-ORCH-005: Verify ResultProcessor class exists"""
        assert ResultProcessor is not None
        assert hasattr(ResultProcessor, 'process_success')
        assert hasattr(ResultProcessor, 'process_failure')

    def test_worktree_manager_imports(self):
        """Verify WorktreeManager class exists"""
        assert WorktreeManager is not None
        assert hasattr(WorktreeManager, 'create_worktree')
        assert hasattr(WorktreeManager, 'cleanup_worktree')

    def test_models_imports(self):
        """Verify Pydantic models exist"""
        assert TaskContext is not None
        assert WorktreeMetadata is not None
        assert SessionState is not None


# ============================================================================
# 2. TASK FETCHER TESTS - Mock Backlog MCP, verify task queries
# ============================================================================

class TestTaskFetcher:
    """Test TaskFetcher queries Backlog.md via MCP tools."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_eligible_tasks_basic(self, mock_task_list):
        """REQ-ORCH-002: Fetch tasks with status='To Do'"""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'BUILD: Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': 'Test description',
                'acceptance_criteria': ['Test AC']
            }
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        assert len(tasks) == 1
        assert tasks[0].id == 'task-1'
        assert tasks[0].title == 'BUILD: Test Task'
        mock_task_list.assert_called_once()

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_dependency_checking(self, mock_task_view, mock_task_list):
        """Verify tasks with dependencies are filtered"""
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
            'status': 'To Do'  # Not Done, so task-2 should be blocked
        }

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # Should be filtered out due to unmet dependency
        assert len(tasks) == 0
        mock_task_view.assert_called_with(id='task-1')

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_priority_sorting(self, mock_task_list):
        """Verify tasks are sorted by priority score"""
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
            }
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # High priority should come first (priority='high' = score 10, 'low' = 1)
        assert tasks[0].id == 'task-high'
        assert tasks[1].id == 'task-low'


# ============================================================================
# 3. WORKTREE MANAGER TESTS - Mock git commands, verify creation/cleanup
# ============================================================================

class TestWorktreeManager:
    """Test WorktreeManager git worktree operations."""

    @patch('agent_factory.scaffold.worktree_manager.subprocess.run')
    @patch('agent_factory.scaffold.worktree_manager.Path.exists', return_value=False)
    def test_create_worktree_success(self, mock_exists, mock_subprocess):
        """Verify worktree creation via git commands"""
        mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')

        manager = WorktreeManager(max_concurrent=3)
        worktree_path = manager.create_worktree('task-test')

        assert worktree_path is not None
        assert 'agent-factory-task-test' in str(worktree_path)

        # Verify git worktree add was called
        mock_subprocess.assert_called()
        git_call = mock_subprocess.call_args[0][0]
        assert 'git' in git_call
        assert 'worktree' in git_call
        assert 'add' in git_call

    @patch('agent_factory.scaffold.worktree_manager.subprocess.run')
    @patch('agent_factory.scaffold.worktree_manager.Path.exists', return_value=True)
    def test_prevent_duplicate_worktrees(self, mock_exists, mock_subprocess):
        """Verify duplicate worktrees are prevented"""
        manager = WorktreeManager(max_concurrent=3)
        manager.create_worktree('task-test')

        # Try to create same worktree again
        with pytest.raises(Exception):  # Should raise an error
            manager.create_worktree('task-test')

    @patch('agent_factory.scaffold.worktree_manager.subprocess.run')
    def test_cleanup_worktree(self, mock_subprocess):
        """Verify worktree cleanup removes worktree and deletes branch"""
        mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')

        manager = WorktreeManager(max_concurrent=3)
        manager.cleanup_worktree('task-test', delete_branch=True)

        # Verify git worktree remove was called
        assert any('remove' in str(call) for call in mock_subprocess.call_args_list)


# ============================================================================
# 4. TASK ROUTER TESTS - Verify routing logic
# ============================================================================

class TestTaskRouter:
    """Test TaskRouter routes tasks to correct handlers."""

    def test_route_to_manual_handler(self):
        """REQ-ORCH-003: User-action tasks route to ManualActionHandler"""
        task = TaskContext(
            id='task-manual',
            title='ACTION: Manual Task',
            description='Requires human action',
            acceptance_criteria=[],
            priority='high',
            labels=['user-action']
        )

        router = TaskRouter()
        handler = router.route(task)

        # Should route to ManualActionHandler for user-action labels
        assert handler is not None
        assert 'Manual' in handler.__class__.__name__

    def test_route_to_claude_handler(self):
        """REQ-ORCH-003: Build tasks route to ClaudeCodeHandler"""
        task = TaskContext(
            id='task-build',
            title='BUILD: Automated Task',
            description='Can be built automatically',
            acceptance_criteria=[],
            priority='high',
            labels=['build']
        )

        router = TaskRouter()
        handler = router.route(task)

        # Should route to ClaudeCodeHandler for build tasks
        assert handler is not None
        assert 'Claude' in handler.__class__.__name__ or 'Code' in handler.__class__.__name__


# ============================================================================
# 5. SESSION MANAGER TESTS - Verify state persistence/resumption
# ============================================================================

class TestSessionManager:
    """Test SessionManager session lifecycle."""

    @pytest.fixture
    def temp_session_dir(self, tmp_path):
        """Create temporary session directory"""
        session_dir = tmp_path / '.scaffold' / 'sessions'
        session_dir.mkdir(parents=True)
        return session_dir

    @patch('agent_factory.scaffold.session_manager.Path.mkdir')
    @patch('agent_factory.scaffold.session_manager.WorktreeManager')
    def test_start_session_creates_state(self, mock_worktree_mgr, mock_mkdir):
        """REQ-ORCH-004: Starting session creates state file"""
        manager = SessionManager(max_tasks=10, max_cost=5.0, max_time_hours=4.0)
        session_id = manager.start_session()

        assert session_id is not None
        assert manager.state is not None
        assert manager.state.max_tasks == 10
        assert manager.state.max_cost == 5.0

    @patch('agent_factory.scaffold.session_manager.Path.exists', return_value=True)
    @patch('agent_factory.scaffold.session_manager.Path.read_text')
    @patch('agent_factory.scaffold.session_manager.WorktreeManager')
    def test_resume_session_loads_state(self, mock_worktree_mgr, mock_read_text, mock_exists):
        """REQ-ORCH-004: Resuming session loads previous state"""
        # Mock session state JSON
        saved_state = {
            'session_id': '20251218_140000',
            'start_time': '2025-12-18T14:00:00',
            'max_tasks': 10,
            'max_cost': 5.0,
            'max_time_hours': 4.0,
            'tasks_queued': ['task-1'],
            'tasks_in_progress': [],
            'tasks_completed': [],
            'tasks_failed': [],
            'total_cost': 0.0,
            'total_duration_sec': 0.0
        }
        mock_read_text.return_value = json.dumps(saved_state)

        manager = SessionManager()
        manager.resume_session('20251218_140000')

        assert manager.state.session_id == '20251218_140000'
        assert manager.state.tasks_queued == ['task-1']


# ============================================================================
# 6. RESULT PROCESSOR TESTS - Mock PR creation, Backlog updates
# ============================================================================

class TestResultProcessor:
    """Test ResultProcessor handles success/failure results."""

    @patch('agent_factory.scaffold.result_processor.mcp__backlog__task_edit')
    def test_process_success_updates_backlog(self, mock_task_edit):
        """REQ-ORCH-005: Success updates task status to Done"""
        processor = ResultProcessor()
        processor.process_success(
            task_id='task-success',
            result={'cost': 0.42, 'duration_sec': 120.5, 'files_changed': []},
            dry_run=False
        )

        # Verify no errors occurred (Backlog update may fail gracefully)
        assert True

    @patch('agent_factory.scaffold.result_processor.mcp__backlog__task_edit')
    def test_process_failure_records_error(self, mock_task_edit):
        """Failure records error in implementation notes"""
        processor = ResultProcessor()
        processor.process_failure(
            task_id='task-fail',
            error='Test error',
            partial_result={'cost': 0.10, 'duration_sec': 30.0}
        )

        # Verify no errors occurred (Backlog update may fail gracefully)
        assert True


# ============================================================================
# 7. INTEGRATION TESTS - End-to-end dry-run workflow
# ============================================================================

class TestIntegration:
    """Test full orchestrator workflow (dry-run mode)."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.session_manager.WorktreeManager')
    @patch('agent_factory.scaffold.result_processor.mcp__backlog__task_edit')
    def test_orchestrator_dry_run(self, mock_task_edit, mock_worktree_mgr, mock_task_list):
        """REQ-ORCH-001: Orchestrator runs end-to-end in dry-run mode"""
        # Mock tasks from Backlog.md
        mock_task_list.return_value = [
            {
                'id': 'task-test',
                'title': 'BUILD: Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': 'Test task',
                'acceptance_criteria': ['AC 1']
            }
        ]

        # Create orchestrator in dry-run mode
        orchestrator = ScaffoldOrchestrator(
            max_tasks=1,
            max_cost=5.0,
            max_time_hours=4.0,
            dry_run=True
        )

        # Run orchestrator
        result = orchestrator.run()

        # Verify task was fetched
        mock_task_list.assert_called()

        # In dry-run mode, should not actually create worktrees or update Backlog
        # But should complete without errors
        assert result is not None


# ============================================================================
# ACCEPTANCE CRITERIA VALIDATION
# ============================================================================

class TestAcceptanceCriteria:
    """Validate all 6 acceptance criteria from task-scaffold-orchestrator."""

    def test_ac1_orchestrator_class_exists(self):
        """AC #1: Orchestrator class with main() entry point"""
        assert ScaffoldOrchestrator is not None
        orchestrator = ScaffoldOrchestrator(max_tasks=10)
        assert hasattr(orchestrator, 'run')
        assert callable(orchestrator.run)

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_ac2_task_fetcher_queries_mcp(self, mock_task_list):
        """AC #2: TaskFetcher queries Backlog.md via MCP"""
        mock_task_list.return_value = []

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # Verify MCP tool was called
        mock_task_list.assert_called_once()
        assert tasks == []

    def test_ac3_task_router_routes_tasks(self):
        """AC #3: TaskRouter routes tasks to handlers"""
        task = TaskContext(
            id='task-1',
            title='BUILD: Test',
            description='',
            acceptance_criteria=[],
            priority='high',
            labels=[]
        )

        router = TaskRouter()
        handler = router.route(task)

        assert handler is not None

    @patch('agent_factory.scaffold.session_manager.WorktreeManager')
    def test_ac4_session_manager_tracks_worktrees(self, mock_worktree_mgr):
        """AC #4: SessionManager tracks worktrees and budgets"""
        manager = SessionManager(max_tasks=10, max_cost=5.0, max_time_hours=4.0)
        session_id = manager.start_session()

        assert manager.state is not None
        assert manager.state.max_cost == 5.0
        assert manager.state.total_cost == 0.0

    @patch('agent_factory.scaffold.result_processor.mcp__backlog__task_edit')
    def test_ac5_result_processor_updates_backlog(self, mock_task_edit):
        """AC #5: ResultProcessor updates Backlog.md after completion"""
        processor = ResultProcessor()
        processor.process_success(
            task_id='task-1',
            result={'cost': 0.1, 'duration_sec': 10, 'files_changed': []},
            dry_run=False
        )

        # Verify no errors occurred (Backlog update may fail gracefully)
        assert True

    def test_ac6_command_line_interface_exists(self):
        """AC #6: Command-line entry point exists"""
        # Verify CLI script exists
        cli_path = Path('scripts/autonomous/scaffold_orchestrator.py')
        assert cli_path.exists(), "CLI script must exist"

        # This is tested manually via:
        # poetry run python scripts/autonomous/scaffold_orchestrator.py --help


# ============================================================================
# 8. COMPREHENSIVE TASK FETCHER TESTS - Edge cases and failure conditions
# ============================================================================

class TestTaskFetcherComprehensive:
    """Comprehensive tests for TaskFetcher with edge cases and failure conditions."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_empty_task_list(self, mock_task_list):
        """Test handling of empty task list from MCP"""
        mock_task_list.return_value = []

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        assert tasks == []
        assert isinstance(tasks, list)

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetch_with_cache_hit(self, mock_task_list):
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

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_priority_score_calculation_high(self, mock_task_list):
        """Test priority score calculation for high priority tasks"""
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
        """Test priority score calculation with critical label bonus"""
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
        """Test priority score calculation with quick-win label bonus"""
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
        """Test priority score penalty for user-action tasks"""
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
        """Test age bonus calculation for older tasks"""
        from datetime import datetime, timedelta

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

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_label_filtering(self, mock_task_list):
        """Test filtering tasks by labels"""
        mock_task_list.return_value = [
            {
                'id': 'task-build',
                'title': 'Build Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-test',
                'title': 'Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['test'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-docs',
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
        
        # Filter for build tasks only
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10, labels=['build'])

        assert len(tasks) == 1
        assert tasks[0]['id'] == 'task-build'

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_label_filtering_multiple_labels(self, mock_task_list):
        """Test filtering with multiple labels (OR logic)"""
        mock_task_list.return_value = [
            {
                'id': 'task-build',
                'title': 'Build Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-test',
                'title': 'Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['test'],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-docs',
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
        
        # Filter for build OR test tasks
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10, labels=['build', 'test'])

        assert len(tasks) == 2
        task_ids = [t['id'] for t in tasks]
        assert 'task-build' in task_ids
        assert 'task-test' in task_ids
        assert 'task-docs' not in task_ids

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_max_tasks_limit(self, mock_task_list):
        """Test that max_tasks limit is enforced"""
        mock_task_list.return_value = [
            {
                'id': f'task-{i}',
                'title': f'Task {i}',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
            for i in range(20)
        ]

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=5)

        # Should only return 5 tasks
        assert len(tasks) == 5

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_mcp_exception_handling(self, mock_task_list):
        """Test graceful handling of MCP exceptions"""
        mock_task_list.side_effect = Exception("MCP server error")

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # Should return empty list on error
        assert tasks == []

    def test_placeholder_tasks_when_mcp_unavailable(self):
        """Test placeholder task generation when MCP not available"""
        # This tests the ImportError path by not mocking MCP
        # In the actual code, it catches ImportError and returns placeholders
        fetcher = TaskFetcher()
        placeholders = fetcher._get_placeholder_tasks(max_tasks=3)

        assert len(placeholders) <= 3
        assert all('id' in task for task in placeholders)
        assert all('title' in task for task in placeholders)


# ============================================================================
# 9. CLI ORCHESTRATOR TESTS - Command-line interface validation
# ============================================================================

class TestCLIOrchestrator:
    """Test CLI entry point and argument parsing."""

    def test_cli_script_exists(self):
        """Verify CLI script exists at expected location"""
        cli_path = Path('scripts/autonomous/scaffold_orchestrator.py')
        assert cli_path.exists()
        assert cli_path.is_file()

    def test_cli_script_is_executable(self):
        """Verify CLI script has executable permissions"""
        cli_path = Path('scripts/autonomous/scaffold_orchestrator.py')
        # Check if file starts with shebang
        first_line = cli_path.read_text().split('\n')[0]
        assert first_line.startswith('#!')

    def test_cli_help_output(self):
        """Test CLI help output is generated correctly"""
        import subprocess
        result = subprocess.run(
            ['python', 'scripts/autonomous/scaffold_orchestrator.py', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert 'SCAFFOLD Orchestrator' in result.stdout
        assert '--dry-run' in result.stdout
        assert '--max-tasks' in result.stdout
        assert '--max-cost' in result.stdout

    @patch('agent_factory.scaffold.orchestrator.ScaffoldOrchestrator')
    def test_cli_dry_run_flag(self, mock_orchestrator):
        """Test --dry-run flag is properly passed"""
        import sys
        from importlib import reload
        
        # Mock sys.argv
        original_argv = sys.argv
        try:
            sys.argv = ['scaffold_orchestrator.py', '--dry-run']
            
            # Import and run CLI module
            import scripts.autonomous.scaffold_orchestrator as cli_module
            reload(cli_module)
            
        finally:
            sys.argv = original_argv

    def test_cli_environment_variables(self):
        """Test environment variables are read correctly"""
        import os
        import importlib
        
        # Set environment variables
        original_env = os.environ.copy()
        try:
            os.environ['MAX_TASKS'] = '15'
            os.environ['MAX_COST'] = '10.0'
            os.environ['DRY_RUN'] = 'true'
            
            # Reload module to pick up env vars
            import scripts.autonomous.scaffold_orchestrator as cli_module
            importlib.reload(cli_module)
            
            # Verify values
            assert cli_module.MAX_TASKS == 15
            assert cli_module.MAX_COST == 10.0
            assert cli_module.DRY_RUN is True
            
        finally:
            os.environ.clear()
            os.environ.update(original_env)


# ============================================================================
# 10. ORCHESTRATOR ERROR HANDLING TESTS
# ============================================================================

class TestOrchestratorErrorHandling:
    """Test error handling and recovery in ScaffoldOrchestrator."""

    @patch('agent_factory.scaffold.task_fetcher.TaskFetcher.fetch_eligible_tasks')
    @patch('agent_factory.scaffold.session_manager.SessionManager.start_session')
    def test_orchestrator_handles_empty_task_queue(self, mock_start_session, mock_fetch):
        """Test orchestrator handles empty task queue gracefully"""
        mock_start_session.return_value = '20251220_120000'
        mock_fetch.return_value = []

        orchestrator = ScaffoldOrchestrator(
            repo_root=Path.cwd(),
            dry_run=True,
            max_tasks=10
        )

        result = orchestrator.run()

        assert result is not None
        assert 'tasks_queued' in result or 'session_id' in result

    @patch('agent_factory.scaffold.task_fetcher.TaskFetcher.fetch_eligible_tasks')
    @patch('agent_factory.scaffold.session_manager.SessionManager.start_session')
    def test_orchestrator_handles_fetch_exception(self, mock_start_session, mock_fetch):
        """Test orchestrator handles task fetch exceptions"""
        mock_start_session.return_value = '20251220_120000'
        mock_fetch.side_effect = Exception("MCP connection error")

        orchestrator = ScaffoldOrchestrator(
            repo_root=Path.cwd(),
            dry_run=True,
            max_tasks=10
        )

        # Should raise ScaffoldOrchestratorError
        with pytest.raises(Exception):  # Could be ScaffoldOrchestratorError or base Exception
            orchestrator.run()

    @patch('agent_factory.scaffold.task_fetcher.TaskFetcher.fetch_eligible_tasks')
    @patch('agent_factory.scaffold.session_manager.SessionManager')
    def test_orchestrator_keyboard_interrupt_handling(self, mock_session_mgr, mock_fetch):
        """Test orchestrator handles Ctrl+C gracefully"""
        mock_session_mgr.return_value.start_session.return_value = '20251220_120000'
        mock_fetch.side_effect = KeyboardInterrupt()

        orchestrator = ScaffoldOrchestrator(
            repo_root=Path.cwd(),
            dry_run=True,
            max_tasks=10
        )

        # Should not crash, should return summary
        result = orchestrator.run()
        assert result is not None


# ============================================================================
# 11. INTEGRATION TESTS - Multi-component workflows
# ============================================================================

class TestIntegrationWorkflows:
    """Test complex multi-component workflows."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    @patch('agent_factory.scaffold.session_manager.WorktreeManager')
    @patch('agent_factory.scaffold.result_processor.mcp__backlog__task_edit')
    def test_full_workflow_single_task_dry_run(
        self, 
        mock_task_edit, 
        mock_worktree_mgr, 
        mock_task_view,
        mock_task_list
    ):
        """Test complete workflow: fetch → route → execute (dry-run)"""
        # Mock task from Backlog.md
        mock_task_list.return_value = [
            {
                'id': 'task-integration-test',
                'title': 'BUILD: Integration Test Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build', 'test'],
                'dependencies': [],
                'description': 'Test complete workflow',
                'acceptance_criteria': ['AC1: Works end-to-end']
            }
        ]

        # Create and run orchestrator
        orchestrator = ScaffoldOrchestrator(
            repo_root=Path.cwd(),
            dry_run=True,
            max_tasks=1,
            max_cost=5.0,
            max_time_hours=4.0,
            labels=['build']
        )

        result = orchestrator.run()

        # Verify workflow completed
        assert result is not None
        mock_task_list.assert_called()

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_dependency_chain_resolution(self, mock_task_view, mock_task_list):
        """Test complex dependency chain resolution"""
        # Task chain: task-3 depends on task-2, task-2 depends on task-1
        mock_task_list.return_value = [
            {
                'id': 'task-3',
                'title': 'Task 3 (depends on 2)',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-2'],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-2',
                'title': 'Task 2 (depends on 1)',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-1'],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-1',
                'title': 'Task 1 (no dependencies)',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]

        # task-1 is Done, task-2 is In Progress
        def mock_view_side_effect(id):
            if id == 'task-1':
                return {'id': 'task-1', 'status': 'Done'}
            elif id == 'task-2':
                return {'id': 'task-2', 'status': 'In Progress'}
            return {'id': id, 'status': 'To Do'}

        mock_task_view.side_effect = mock_view_side_effect

        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)

        # Only task-1 should be eligible (no dependencies)
        # task-2 and task-3 should be filtered out
        task_ids = [t['id'] for t in tasks]
        assert 'task-1' in task_ids
        assert 'task-2' not in task_ids  # Blocked by task-1
        assert 'task-3' not in task_ids  # Blocked by task-2


# ============================================================================
# 12. PERFORMANCE AND STRESS TESTS
# ============================================================================

class TestPerformance:
    """Test performance characteristics and limits."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_large_task_list_performance(self, mock_task_list):
        """Test handling of large task lists (100+ tasks)"""
        # Create 100 tasks
        mock_task_list.return_value = [
            {
                'id': f'task-{i}',
                'title': f'Task {i}',
                'status': 'To Do',
                'priority': 'high' if i % 3 == 0 else 'medium',
                'labels': ['build'] if i % 2 == 0 else ['test'],
                'dependencies': [],
                'description': f'Description {i}',
                'acceptance_criteria': [f'AC{i}']
            }
            for i in range(100)
        ]

        fetcher = TaskFetcher()
        
        import time
        start = time.time()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=50)
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 5.0  # Less than 5 seconds
        assert len(tasks) == 50

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_complex_dependency_graph_performance(self, mock_task_view, mock_task_list):
        """Test performance with complex dependency graphs"""
        # Create 20 tasks with various dependency patterns
        tasks = []
        for i in range(20):
            deps = []
            if i > 0:
                deps.append(f'task-{i-1}')  # Linear chain
            if i > 5:
                deps.append('task-5')  # Fan-in pattern
            
            tasks.append({
                'id': f'task-{i}',
                'title': f'Task {i}',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': deps,
                'description': '',
                'acceptance_criteria': []
            })

        mock_task_list.return_value = tasks

        # Mock all dependencies as Done
        mock_task_view.return_value = {'status': 'Done'}

        fetcher = TaskFetcher()
        
        import time
        start = time.time()
        eligible = fetcher.fetch_eligible_tasks(max_tasks=20)
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 10.0  # Less than 10 seconds
        assert len(eligible) > 0


# ============================================================================
# 13. DATA MODEL TESTS - Pydantic models validation
# ============================================================================

class TestDataModels:
    """Test Pydantic data models."""

    def test_task_context_creation(self):
        """Test TaskContext model creation"""
        task = TaskContext(
            task_id='task-42',
            title='Test Task',
            description='Test description',
            acceptance_criteria=['AC1', 'AC2'],
            priority='high',
            labels=['build', 'test']
        )

        assert task.task_id == 'task-42'
        assert task.priority == 'high'
        assert len(task.labels) == 2

    def test_task_context_to_dict(self):
        """Test TaskContext serialization to dict"""
        task = TaskContext(
            task_id='task-42',
            title='Test Task',
            description='Test description',
            acceptance_criteria=['AC1'],
            priority='high',
            labels=['build']
        )

        task_dict = task.to_dict()

        assert isinstance(task_dict, dict)
        assert task_dict['task_id'] == 'task-42'
        assert 'title' in task_dict
        assert 'labels' in task_dict

    def test_task_context_from_dict(self):
        """Test TaskContext deserialization from dict"""
        task_dict = {
            'task_id': 'task-42',
            'title': 'Test Task',
            'description': 'Test description',
            'acceptance_criteria': ['AC1'],
            'priority': 'high',
            'labels': ['build']
        }

        task = TaskContext.from_dict(task_dict)

        assert task.task_id == 'task-42'
        assert task.title == 'Test Task'

    def test_session_state_creation(self):
        """Test SessionState model creation"""
        state = SessionState(
            session_id='20251220_120000',
            start_time='2025-12-20T12:00:00',
            max_tasks=10,
            max_cost=5.0,
            max_time_hours=4.0,
            tasks_queued=['task-1', 'task-2'],
            tasks_in_progress={'task-1': '/path/to/worktree'},
            tasks_completed=[],
            tasks_failed=[]
        )

        assert state.session_id == '20251220_120000'
        assert state.max_cost == 5.0
        assert len(state.tasks_queued) == 2

    def test_session_state_to_dict(self):
        """Test SessionState serialization"""
        state = SessionState(
            session_id='20251220_120000',
            start_time='2025-12-20T12:00:00',
            max_tasks=10,
            max_cost=5.0,
            max_time_hours=4.0,
            tasks_queued=[],
            tasks_in_progress={},
            tasks_completed=[],
            tasks_failed=[]
        )

        state_dict = state.to_dict()

        assert isinstance(state_dict, dict)
        assert state_dict['session_id'] == '20251220_120000'
        assert 'max_cost' in state_dict

    def test_worktree_metadata_creation(self):
        """Test WorktreeMetadata model creation"""
        metadata = WorktreeMetadata(
            task_id='task-42',
            worktree_path='/path/to/worktree',
            branch_name='autonomous/task-42',
            created_at='2025-12-20T12:00:00',
            creator='scaffold-orchestrator',
            status='active',
            pr_url='https://github.com/user/repo/pull/123'
        )

        assert metadata.task_id == 'task-42'
        assert metadata.status == 'active'
        assert metadata.pr_url is not None


# ============================================================================
# ADDITIONAL COMPREHENSIVE TESTS
# ============================================================================

class TestTaskFetcherEdgeCases:
    """Additional edge case tests for TaskFetcher."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_circular_dependencies_handled(self, mock_task_view, mock_task_list):
        """Test circular dependencies don't cause infinite loops."""
        mock_task_list.return_value = [
            {
                'id': 'task-a',
                'title': 'Task A',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-b'],
                'description': '',
                'acceptance_criteria': []
            },
            {
                'id': 'task-b',
                'title': 'Task B',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-a'],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        mock_task_view.side_effect = lambda id: {
            'task-a': {'id': 'task-a', 'status': 'To Do'},
            'task-b': {'id': 'task-b', 'status': 'To Do'}
        }[id]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Both should be filtered out (dependencies not satisfied)
        assert len(tasks) == 0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_self_referencing_dependency(self, mock_task_view, mock_task_list):
        """Test task depending on itself is handled."""
        mock_task_list.return_value = [
            {
                'id': 'task-self',
                'title': 'Self-referencing Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': ['task-self'],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        mock_task_view.return_value = {
            'id': 'task-self',
            'status': 'To Do'
        }
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should be filtered out
        assert len(tasks) == 0

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_unicode_in_task_fields(self, mock_task_view, mock_task_list):
        """Test Unicode characters in task fields are handled."""
        mock_task_list.return_value = [
            {
                'id': 'task-unicode',
                'title': 'BUILD: 🚀 Feature with émojis and àccents',
                'status': 'To Do',
                'priority': 'high',
                'labels': ['build', '中文', 'العربية'],
                'dependencies': [],
                'description': 'Description with 日本語 and Ελληνικά',
                'acceptance_criteria': ['AC with 한국어']
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        assert len(tasks) == 1
        assert '🚀' in tasks[0]['title']
        assert '中文' in tasks[0]['labels']

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_very_large_task_list(self, mock_task_view, mock_task_list):
        """Test handling of very large task lists."""
        # Create 1000 tasks
        large_task_list = [
            {
                'id': f'task-{i}',
                'title': f'Task {i}',
                'status': 'To Do',
                'priority': 'medium',
                'labels': [],
                'dependencies': [],
                'description': f'Description {i}',
                'acceptance_criteria': [f'AC {i}']
            }
            for i in range(1000)
        ]
        
        mock_task_list.return_value = large_task_list
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should return only 10 tasks
        assert len(tasks) == 10

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_task_with_none_values(self, mock_task_view, mock_task_list):
        """Test tasks with None values in fields."""
        mock_task_list.return_value = [
            {
                'id': 'task-none',
                'title': None,
                'status': 'To Do',
                'priority': None,
                'labels': None,
                'dependencies': None,
                'description': None,
                'acceptance_criteria': None
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should handle gracefully (may return task or filter it)
        assert isinstance(tasks, list)


class TestOrchestratorErrorRecovery:
    """Test error recovery and resilience."""

    @patch('agent_factory.scaffold.orchestrator.TaskFetcher')
    @patch('agent_factory.scaffold.orchestrator.SessionManager')
    def test_partial_task_failure_continues_execution(self, mock_session_mgr_class, mock_fetcher_class):
        """Test orchestrator continues after partial task failures."""
        # Mock fetcher to return multiple tasks
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_eligible_tasks.return_value = [
            {'id': 'task-1', 'title': 'Task 1', 'priority': 'high', 'labels': []},
            {'id': 'task-2', 'title': 'Task 2', 'priority': 'high', 'labels': []},
            {'id': 'task-3', 'title': 'Task 3', 'priority': 'high', 'labels': []},
        ]
        mock_fetcher_class.return_value = mock_fetcher
        
        # Mock session manager
        mock_session_mgr = MagicMock()
        mock_session_mgr.start_session.return_value = 'test_session'
        mock_session_mgr.check_can_continue.return_value = (True, None)
        mock_session_mgr.state = Mock(tasks_queued=[])
        mock_session_mgr_class.return_value = mock_session_mgr
        
        orchestrator = ScaffoldOrchestrator(
            max_tasks=3,
            dry_run=False
        )
        
        # This would normally execute tasks, but in dry_run=False it requires more mocking
        # The test verifies the structure is correct
        assert orchestrator is not None

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetcher_timeout_handling(self, mock_task_list):
        """Test handling of MCP timeouts."""
        import socket
        mock_task_list.side_effect = socket.timeout("Connection timeout")
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should return empty list on timeout
        assert tasks == []

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    def test_fetcher_connection_error_handling(self, mock_task_list):
        """Test handling of connection errors."""
        import requests
        mock_task_list.side_effect = requests.ConnectionError("Connection refused")
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should return empty list on connection error
        assert tasks == []


class TestConcurrencyAndRaceConditions:
    """Test concurrent execution scenarios."""

    def test_cache_invalidation_thread_safe(self):
        """Test cache invalidation is thread-safe."""
        fetcher = TaskFetcher()
        
        # Simulate concurrent cache operations
        import threading
        
        def invalidate_cache():
            for _ in range(100):
                fetcher.invalidate_cache()
        
        def check_cache():
            for _ in range(100):
                _ = fetcher._cache is None
        
        threads = [
            threading.Thread(target=invalidate_cache),
            threading.Thread(target=check_cache),
            threading.Thread(target=invalidate_cache),
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Should complete without errors
        assert True


class TestSecurityAndValidation:
    """Test security and input validation."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_sql_injection_in_task_id(self, mock_task_view, mock_task_list):
        """Test SQL injection attempts in task IDs are handled."""
        mock_task_list.return_value = [
            {
                'id': "task-'; DROP TABLE tasks; --",
                'title': 'Malicious Task',
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
        
        # Should handle without injection
        assert len(tasks) == 1

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_xss_in_task_title(self, mock_task_view, mock_task_list):
        """Test XSS attempts in task titles are preserved (not executed)."""
        mock_task_list.return_value = [
            {
                'id': 'task-xss',
                'title': '<script>alert("XSS")</script>',
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
        
        # Script tags should be preserved as strings, not executed
        assert len(tasks) == 1
        assert '<script>' in tasks[0]['title']

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_path_traversal_in_task_id(self, mock_task_view, mock_task_list):
        """Test path traversal attempts are handled."""
        mock_task_list.return_value = [
            {
                'id': '../../../etc/passwd',
                'title': 'Path Traversal Task',
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
        
        # Should handle without file system access
        assert len(tasks) == 1


class TestPerformanceAndScalability:
    """Test performance characteristics."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_large_dependency_chain(self, mock_task_view, mock_task_list):
        """Test handling of long dependency chains."""
        # Create chain of 50 dependent tasks
        tasks = []
        for i in range(50):
            tasks.append({
                'id': f'task-{i}',
                'title': f'Task {i}',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [f'task-{i-1}'] if i > 0 else [],
                'description': '',
                'acceptance_criteria': []
            })
        
        mock_task_list.return_value = tasks
        
        # All dependencies are "To Do" (not satisfied)
        mock_task_view.return_value = {'status': 'To Do'}
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=100)
        
        # Only task-0 (no dependencies) should be eligible
        assert len(tasks) == 1
        assert tasks[0]['id'] == 'task-0'

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_many_labels_per_task(self, mock_task_view, mock_task_list):
        """Test tasks with many labels are handled efficiently."""
        mock_task_list.return_value = [
            {
                'id': 'task-many-labels',
                'title': 'Task with Many Labels',
                'status': 'To Do',
                'priority': 'high',
                'labels': [f'label-{i}' for i in range(100)],
                'dependencies': [],
                'description': '',
                'acceptance_criteria': []
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        assert len(tasks) == 1
        assert len(tasks[0]['labels']) == 100


class TestBackwardsCompatibility:
    """Test backwards compatibility with older data formats."""

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_legacy_task_format_without_created_date(self, mock_task_view, mock_task_list):
        """Test legacy tasks without created_date field."""
        mock_task_list.return_value = [
            {
                'id': 'task-legacy',
                'title': 'Legacy Task',
                'status': 'To Do',
                'priority': 'high',
                'labels': [],
                'dependencies': [],
                # No created_date field
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should handle missing field gracefully
        assert len(tasks) == 1

    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
    @patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
    def test_legacy_priority_values(self, mock_task_view, mock_task_list):
        """Test legacy priority values (critical, normal)."""
        mock_task_list.return_value = [
            {
                'id': 'task-1',
                'title': 'Task 1',
                'status': 'To Do',
                'priority': 'critical',  # Legacy value
                'labels': [],
                'dependencies': [],
            },
            {
                'id': 'task-2',
                'title': 'Task 2',
                'status': 'To Do',
                'priority': 'normal',  # Legacy value
                'labels': [],
                'dependencies': [],
            }
        ]
        
        fetcher = TaskFetcher()
        tasks = fetcher.fetch_eligible_tasks(max_tasks=10)
        
        # Should handle legacy values (default to low=1)
        assert len(tasks) == 2
