"""Comprehensive tests for SCAFFOLD Orchestrator CLI.

Tests cover:
- Command-line argument parsing
- Environment variable handling
- Orchestrator initialization
- Integration with orchestrator module
- Exit codes
- Error handling
- Logging configuration
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

# Add scripts to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_orchestrator():
    """Mock ScaffoldOrchestrator class."""
    with patch('agent_factory.scaffold.orchestrator.ScaffoldOrchestrator') as mock:
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test_session',
            'dry_run': False,
            'tasks_queued': 5,
            'tasks_in_progress': 0,
            'tasks_completed': 3,
            'tasks_failed': 2,
            'total_cost': 1.23,
            'total_duration_sec': 456.7
        }
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def clean_env():
    """Clean environment variables before each test."""
    env_vars = ['MAX_TASKS', 'MAX_CONCURRENT', 'MAX_COST', 'MAX_TIME_HOURS', 'DRY_RUN']
    old_values = {}
    
    for var in env_vars:
        old_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore
    for var, value in old_values.items():
        if value is not None:
            os.environ[var] = value


# ============================================================================
# ARGUMENT PARSING TESTS
# ============================================================================

class TestArgumentParsing:
    """Test command-line argument parsing."""

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    def test_default_arguments(self, clean_env):
        """Test default values when no arguments provided."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.dry_run == False
        assert args.max_tasks == 10
        assert args.max_concurrent == 3
        assert args.max_cost == 5.0
        assert args.max_time == 4.0
        assert args.labels is None

    @patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run'])
    def test_dry_run_flag(self, clean_env):
        """Test --dry-run flag."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.dry_run == True

    @patch('sys.argv', ['scaffold_orchestrator.py', '--max-tasks', '5'])
    def test_max_tasks_argument(self, clean_env):
        """Test --max-tasks argument."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.max_tasks == 5

    @patch('sys.argv', ['scaffold_orchestrator.py', '--max-concurrent', '2'])
    def test_max_concurrent_argument(self, clean_env):
        """Test --max-concurrent argument."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.max_concurrent == 2

    @patch('sys.argv', ['scaffold_orchestrator.py', '--max-cost', '3.5'])
    def test_max_cost_argument(self, clean_env):
        """Test --max-cost argument."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.max_cost == 3.5

    @patch('sys.argv', ['scaffold_orchestrator.py', '--max-time', '2.5'])
    def test_max_time_argument(self, clean_env):
        """Test --max-time argument."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.max_time == 2.5

    @patch('sys.argv', ['scaffold_orchestrator.py', '--labels', 'build,rivet-pro'])
    def test_labels_argument(self, clean_env):
        """Test --labels argument."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.labels == 'build,rivet-pro'

    @patch('sys.argv', [
        'scaffold_orchestrator.py',
        '--dry-run',
        '--max-tasks', '3',
        '--max-cost', '2.0',
        '--labels', 'test'
    ])
    def test_combined_arguments(self, clean_env):
        """Test multiple arguments combined."""
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        assert args.dry_run == True
        assert args.max_tasks == 3
        assert args.max_cost == 2.0
        assert args.labels == 'test'


# ============================================================================
# ENVIRONMENT VARIABLE TESTS
# ============================================================================

class TestEnvironmentVariables:
    """Test environment variable handling."""

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    def test_max_tasks_from_env(self, clean_env):
        """Test MAX_TASKS environment variable."""
        os.environ['MAX_TASKS'] = '15'
        
        # Re-import to pick up env var
        import importlib
        import scripts.autonomous.scaffold_orchestrator as orch_module
        importlib.reload(orch_module)
        
        from scripts.autonomous.scaffold_orchestrator import MAX_TASKS
        assert MAX_TASKS == 15

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    def test_dry_run_from_env(self, clean_env):
        """Test DRY_RUN environment variable."""
        os.environ['DRY_RUN'] = 'true'
        
        import importlib
        import scripts.autonomous.scaffold_orchestrator as orch_module
        importlib.reload(orch_module)
        
        from scripts.autonomous.scaffold_orchestrator import DRY_RUN
        assert DRY_RUN == True

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    def test_max_cost_from_env(self, clean_env):
        """Test MAX_COST environment variable."""
        os.environ['MAX_COST'] = '8.5'
        
        import importlib
        import scripts.autonomous.scaffold_orchestrator as orch_module
        importlib.reload(orch_module)
        
        from scripts.autonomous.scaffold_orchestrator import MAX_COST
        assert MAX_COST == 8.5

    @patch('sys.argv', ['scaffold_orchestrator.py', '--max-tasks', '5'])
    def test_cli_argument_overrides_env(self, clean_env):
        """Test CLI argument overrides environment variable."""
        os.environ['MAX_TASKS'] = '20'
        
        from scripts.autonomous.scaffold_orchestrator import parse_args
        
        args = parse_args()
        
        # CLI arg should override env var
        assert args.max_tasks == 5


# ============================================================================
# ORCHESTRATOR INITIALIZATION TESTS
# ============================================================================

class TestOrchestratorInitialization:
    """Test orchestrator initialization from CLI."""

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_creates_orchestrator_with_defaults(self, mock_orch_class, clean_env):
        """Test orchestrator created with default parameters."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test', 'dry_run': False,
            'tasks_queued': 0, 'tasks_in_progress': 0,
            'tasks_completed': 0, 'tasks_failed': 0,
            'total_cost': 0.0, 'total_duration_sec': 0.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify orchestrator was created
        mock_orch_class.assert_called_once()
        call_args = mock_orch_class.call_args
        
        assert call_args.kwargs['dry_run'] == False
        assert call_args.kwargs['max_tasks'] == 10
        assert call_args.kwargs['labels'] is None

    @patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run', '--max-tasks', '3'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_creates_orchestrator_with_custom_params(self, mock_orch_class, clean_env):
        """Test orchestrator created with custom parameters."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test', 'dry_run': True,
            'tasks_queued': 0, 'tasks_in_progress': 0,
            'tasks_completed': 0, 'tasks_failed': 0,
            'total_cost': 0.0, 'total_duration_sec': 0.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit):
            main()
        
        call_args = mock_orch_class.call_args
        
        assert call_args.kwargs['dry_run'] == True
        assert call_args.kwargs['max_tasks'] == 3

    @patch('sys.argv', ['scaffold_orchestrator.py', '--labels', 'build,test'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_parses_labels_correctly(self, mock_orch_class, clean_env):
        """Test label parsing from comma-separated string."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test', 'dry_run': False,
            'tasks_queued': 0, 'tasks_in_progress': 0,
            'tasks_completed': 0, 'tasks_failed': 0,
            'total_cost': 0.0, 'total_duration_sec': 0.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit):
            main()
        
        call_args = mock_orch_class.call_args
        
        assert call_args.kwargs['labels'] == ['build', 'test']


# ============================================================================
# EXIT CODE TESTS
# ============================================================================

class TestExitCodes:
    """Test exit codes for different scenarios."""

    @patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_dry_run_exits_zero(self, mock_orch_class, clean_env):
        """Test dry-run mode exits with code 0."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test',
            'dry_run': True,
            'tasks_queued': 5,
            'tasks_in_progress': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_cost': 0.0,
            'total_duration_sec': 0.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_success_exits_zero(self, mock_orch_class, clean_env):
        """Test successful execution exits with code 0."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test',
            'dry_run': False,
            'tasks_queued': 3,
            'tasks_in_progress': 0,
            'tasks_completed': 3,
            'tasks_failed': 0,
            'total_cost': 1.5,
            'total_duration_sec': 300.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_all_failures_exits_one(self, mock_orch_class, clean_env):
        """Test all tasks failed exits with code 1."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test',
            'dry_run': False,
            'tasks_queued': 3,
            'tasks_in_progress': 0,
            'tasks_completed': 0,
            'tasks_failed': 3,
            'total_cost': 0.5,
            'total_duration_sec': 100.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_no_tasks_exits_two(self, mock_orch_class, clean_env):
        """Test no tasks processed exits with code 2."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'test',
            'dry_run': False,
            'tasks_queued': 0,
            'tasks_in_progress': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_cost': 0.0,
            'total_duration_sec': 0.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_keyboard_interrupt_exits_130(self, mock_orch_class, clean_env):
        """Test KeyboardInterrupt (Ctrl+C) exits with code 130."""
        mock_instance = MagicMock()
        mock_instance.run.side_effect = KeyboardInterrupt()
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 130

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_exception_exits_one(self, mock_orch_class, clean_env):
        """Test uncaught exception exits with code 1."""
        mock_instance = MagicMock()
        mock_instance.run.side_effect = Exception("Test error")
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1


# ============================================================================
# LOGGING TESTS
# ============================================================================

class TestLogging:
    """Test logging configuration."""

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    def test_log_directory_created(self, clean_env, tmp_path, monkeypatch):
        """Test logs directory is created."""
        monkeypatch.chdir(tmp_path)
        
        # Import module to trigger log directory creation
        import importlib
        import scripts.autonomous.scaffold_orchestrator as orch_module
        importlib.reload(orch_module)
        
        from scripts.autonomous.scaffold_orchestrator import LOG_DIR
        
        assert LOG_DIR.exists()
        assert LOG_DIR.is_dir()

    @patch('sys.argv', ['scaffold_orchestrator.py'])
    def test_log_file_has_timestamp(self, clean_env):
        """Test log file name includes timestamp."""
        from scripts.autonomous.scaffold_orchestrator import log_file
        
        assert 'scaffold_' in str(log_file)
        assert '.log' in str(log_file)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test realistic end-to-end CLI scenarios."""

    @patch('sys.argv', [
        'scaffold_orchestrator.py',
        '--dry-run',
        '--max-tasks', '5',
        '--max-cost', '3.0',
        '--labels', 'build,test'
    ])
    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_full_cli_workflow(self, mock_orch_class, clean_env, capsys):
        """Test complete CLI workflow with all options."""
        mock_instance = MagicMock()
        mock_instance.run.return_value = {
            'session_id': 'session_12345',
            'dry_run': True,
            'tasks_queued': 5,
            'tasks_in_progress': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_cost': 0.0,
            'total_duration_sec': 0.0
        }
        mock_orch_class.return_value = mock_instance
        
        from scripts.autonomous.scaffold_orchestrator import main
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        # Verify orchestrator was called correctly
        call_args = mock_orch_class.call_args
        assert call_args.kwargs['dry_run'] == True
        assert call_args.kwargs['max_tasks'] == 5
        assert call_args.kwargs['max_cost'] == 3.0
        assert call_args.kwargs['labels'] == ['build', 'test']
        
        # Verify exit code
        assert exc_info.value.code == 0
        
        # Verify summary was printed
        captured = capsys.readouterr()
        assert 'Session ID: session_12345' in captured.out
        assert 'Tasks Queued: 5' in captured.out