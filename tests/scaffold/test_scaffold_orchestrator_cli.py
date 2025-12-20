"""
Comprehensive unit tests for scaffold_orchestrator.py CLI script.

Tests cover:
- Command-line argument parsing
- Environment variable handling
- Main execution flow
- Exit codes
- Error handling
- Dry-run mode
- Logging configuration
- Integration with ScaffoldOrchestrator
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
from pathlib import Path
from io import StringIO


# We need to import the CLI module, but it may execute on import
# So we'll patch sys.argv before importing
@pytest.fixture
def cli_module():
    """Import CLI module with patched argv."""
    # Save original argv
    original_argv = sys.argv.copy()
    
    # Set minimal argv to prevent execution
    sys.argv = ['scaffold_orchestrator.py']
    
    # Import the module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "scaffold_orchestrator",
        "scripts/autonomous/scaffold_orchestrator.py"
    )
    module = importlib.util.module_from_spec(spec)
    
    # Restore argv
    sys.argv = original_argv
    
    yield module
    

class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_parse_args_defaults(self):
        """Test parsing with no arguments uses environment defaults."""
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            # Import and get parse_args function
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scaffold_cli",
                "scripts/autonomous/scaffold_orchestrator.py"
            )
            module = importlib.util.module_from_spec(spec)
            
            # Load but don't execute
            spec.loader.exec_module(module)
            
            args = module.parse_args()
            
            # Check defaults are from environment or hardcoded
            assert hasattr(args, 'dry_run')
            assert hasattr(args, 'max_tasks')
            assert hasattr(args, 'max_cost')
            assert hasattr(args, 'max_time')
            assert hasattr(args, 'labels')

    def test_parse_args_dry_run_flag(self):
        """Test --dry-run flag sets dry_run to True."""
        with patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run']):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scaffold_cli",
                "scripts/autonomous/scaffold_orchestrator.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            args = module.parse_args()
            
            assert args.dry_run is True

    def test_parse_args_max_tasks(self):
        """Test --max-tasks argument."""
        with patch('sys.argv', ['scaffold_orchestrator.py', '--max-tasks', '5']):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scaffold_cli",
                "scripts/autonomous/scaffold_orchestrator.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            args = module.parse_args()
            
            assert args.max_tasks == 5

    def test_parse_args_max_cost(self):
        """Test --max-cost argument."""
        with patch('sys.argv', ['scaffold_orchestrator.py', '--max-cost', '3.5']):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scaffold_cli",
                "scripts/autonomous/scaffold_orchestrator.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            args = module.parse_args()
            
            assert args.max_cost == 3.5

    def test_parse_args_max_time(self):
        """Test --max-time argument."""
        with patch('sys.argv', ['scaffold_orchestrator.py', '--max-time', '2.0']):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scaffold_cli",
                "scripts/autonomous/scaffold_orchestrator.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            args = module.parse_args()
            
            assert args.max_time == 2.0

    def test_parse_args_labels(self):
        """Test --labels argument."""
        with patch('sys.argv', ['scaffold_orchestrator.py', '--labels', 'build,test']):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scaffold_cli",
                "scripts/autonomous/scaffold_orchestrator.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            args = module.parse_args()
            
            assert args.labels == 'build,test'

    def test_parse_args_all_arguments(self):
        """Test parsing all arguments together."""
        with patch('sys.argv', [
            'scaffold_orchestrator.py',
            '--dry-run',
            '--max-tasks', '3',
            '--max-cost', '2.5',
            '--max-time', '1.5',
            '--labels', 'build,rivet-pro'
        ]):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "scaffold_cli",
                "scripts/autonomous/scaffold_orchestrator.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            args = module.parse_args()
            
            assert args.dry_run is True
            assert args.max_tasks == 3
            assert args.max_cost == 2.5
            assert args.max_time == 1.5
            assert args.labels == 'build,rivet-pro'


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_env_max_tasks(self):
        """Test MAX_TASKS environment variable."""
        with patch.dict(os.environ, {'MAX_TASKS': '15'}):
            with patch('sys.argv', ['scaffold_orchestrator.py']):
                # Re-import to pick up env var
                import importlib
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check that MAX_TASKS is read from environment
                assert module.MAX_TASKS == 15

    def test_env_dry_run_true(self):
        """Test DRY_RUN=true environment variable."""
        with patch.dict(os.environ, {'DRY_RUN': 'true'}):
            with patch('sys.argv', ['scaffold_orchestrator.py']):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                assert module.DRY_RUN is True

    def test_env_dry_run_false(self):
        """Test DRY_RUN=false environment variable."""
        with patch.dict(os.environ, {'DRY_RUN': 'false'}):
            with patch('sys.argv', ['scaffold_orchestrator.py']):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                assert module.DRY_RUN is False

    def test_env_max_cost(self):
        """Test MAX_COST environment variable."""
        with patch.dict(os.environ, {'MAX_COST': '3.0'}):
            with patch('sys.argv', ['scaffold_orchestrator.py']):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                assert module.MAX_COST == 3.0

    def test_env_max_time_hours(self):
        """Test MAX_TIME_HOURS environment variable."""
        with patch.dict(os.environ, {'MAX_TIME_HOURS': '2.0'}):
            with patch('sys.argv', ['scaffold_orchestrator.py']):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                assert module.MAX_TIME_HOURS == 2.0


class TestMainExecution:
    """Test main() function execution."""

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_main_creates_orchestrator(self, mock_orchestrator_class):
        """Test main() creates ScaffoldOrchestrator instance."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'session_id': 'test-session',
            'dry_run': True,
            'tasks_completed': 1,
            'tasks_failed': 0,
            'total_cost': 0.5,
            'total_duration_sec': 120.0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Call main
                module.main()
                
                # Verify orchestrator was created
                mock_orchestrator_class.assert_called_once()

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_main_calls_run(self, mock_orchestrator_class):
        """Test main() calls orchestrator.run()."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'session_id': 'test-session',
            'dry_run': True,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_cost': 0.0,
            'total_duration_sec': 0.0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Verify run was called
                mock_orch.run.assert_called_once()


class TestExitCodes:
    """Test exit codes for different scenarios."""

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_exit_code_dry_run_success(self, mock_orchestrator_class):
        """Test exit code 0 for successful dry run."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': True,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Dry run should exit 0
                mock_exit.assert_called_with(0)

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_exit_code_tasks_completed(self, mock_orchestrator_class):
        """Test exit code 0 when at least one task completed."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': False,
            'tasks_completed': 2,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Should exit 0 for success
                mock_exit.assert_called_with(0)

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_exit_code_all_failed(self, mock_orchestrator_class):
        """Test exit code 1 when all tasks failed."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': False,
            'tasks_completed': 0,
            'tasks_failed': 3
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Should exit 1 for failure
                mock_exit.assert_called_with(1)

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_exit_code_no_work(self, mock_orchestrator_class):
        """Test exit code 2 when no tasks processed."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': False,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Should exit 2 for no work
                mock_exit.assert_called_with(2)


class TestErrorHandling:
    """Test error handling in main()."""

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_keyboard_interrupt(self, mock_orchestrator_class):
        """Test Ctrl+C handling."""
        mock_orch = Mock()
        mock_orch.run.side_effect = KeyboardInterrupt()
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Should exit 130 for SIGINT
                mock_exit.assert_called_with(130)

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_fatal_error(self, mock_orchestrator_class):
        """Test fatal error handling."""
        mock_orch = Mock()
        mock_orch.run.side_effect = Exception("Fatal error")
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Should exit 1 for fatal error
                mock_exit.assert_called_with(1)


class TestLoggingConfiguration:
    """Test logging setup."""

    def test_log_directory_created(self):
        """Test that logs directory is created."""
        with patch('sys.argv', ['scaffold_orchestrator.py', '--help']):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check LOG_DIR is defined
                assert hasattr(module, 'LOG_DIR')
                assert isinstance(module.LOG_DIR, Path)

    def test_log_file_path_format(self):
        """Test log file path has correct format."""
        with patch('sys.argv', ['scaffold_orchestrator.py', '--help']):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Log file should be in logs directory
                assert str(module.LOG_DIR) in str(module.log_file)
                assert 'scaffold_' in str(module.log_file)
                assert '.log' in str(module.log_file)


class TestLabelParsing:
    """Test label parsing from command line."""

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_labels_parsed_as_list(self, mock_orchestrator_class):
        """Test labels are parsed into list."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': True,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py', '--labels', 'build,test,docs']):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Check orchestrator was called with labels list
                call_args = mock_orchestrator_class.call_args
                assert 'labels' in call_args[1]
                labels = call_args[1]['labels']
                assert labels == ['build', 'test', 'docs']

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_labels_with_spaces(self, mock_orchestrator_class):
        """Test labels with spaces are trimmed."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': True,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py', '--labels', 'build , test , docs']):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Check labels are trimmed
                call_args = mock_orchestrator_class.call_args
                labels = call_args[1]['labels']
                assert labels == ['build', 'test', 'docs']

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_no_labels(self, mock_orchestrator_class):
        """Test when no labels provided."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': True,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Check labels is None
                call_args = mock_orchestrator_class.call_args
                labels = call_args[1]['labels']
                assert labels is None


class TestOrchestratorConfiguration:
    """Test orchestrator is configured correctly."""

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_orchestrator_receives_all_parameters(self, mock_orchestrator_class):
        """Test orchestrator receives all configuration parameters."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': True,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', [
            'scaffold_orchestrator.py',
            '--dry-run',
            '--max-tasks', '5',
            '--max-cost', '2.5',
            '--max-time', '1.5',
            '--labels', 'build'
        ]):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Verify all parameters passed
                call_args = mock_orchestrator_class.call_args
                assert call_args[1]['dry_run'] is True
                assert call_args[1]['max_tasks'] == 5
                assert call_args[1]['max_cost'] == 2.5
                assert call_args[1]['max_time'] == 1.5
                assert call_args[1]['labels'] == ['build']

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_orchestrator_receives_repo_root(self, mock_orchestrator_class):
        """Test orchestrator receives repo_root parameter."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'dry_run': True,
            'tasks_completed': 0,
            'tasks_failed': 0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py']):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Verify repo_root is passed
                call_args = mock_orchestrator_class.call_args
                assert 'repo_root' in call_args[1]
                assert isinstance(call_args[1]['repo_root'], Path)


class TestSummaryOutput:
    """Test summary output formatting."""

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    @patch('builtins.print')
    def test_summary_printed(self, mock_print, mock_orchestrator_class):
        """Test summary is printed after execution."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'session_id': 'test-123',
            'dry_run': True,
            'tasks_queued': 5,
            'tasks_in_progress': 0,
            'tasks_completed': 3,
            'tasks_failed': 2,
            'total_cost': 1.25,
            'total_duration_sec': 180.5
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', ['scaffold_orchestrator.py', '--dry-run']):
            with patch('sys.exit'):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Verify print was called with summary
                assert mock_print.called
                # Check for key summary elements in any print call
                all_prints = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'Session' in all_prints or 'session' in all_prints


class TestIntegration:
    """Integration tests for CLI."""

    @patch('scripts.autonomous.scaffold_orchestrator.ScaffoldOrchestrator')
    def test_full_execution_flow(self, mock_orchestrator_class):
        """Test full execution flow from args to exit."""
        mock_orch = Mock()
        mock_orch.run.return_value = {
            'session_id': 'integration-test',
            'dry_run': False,
            'tasks_queued': 3,
            'tasks_in_progress': 0,
            'tasks_completed': 2,
            'tasks_failed': 1,
            'total_cost': 0.75,
            'total_duration_sec': 240.0
        }
        mock_orchestrator_class.return_value = mock_orch
        
        with patch('sys.argv', [
            'scaffold_orchestrator.py',
            '--max-tasks', '3',
            '--max-cost', '5.0'
        ]):
            with patch('sys.exit') as mock_exit:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "scaffold_cli",
                    "scripts/autonomous/scaffold_orchestrator.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                module.main()
                
                # Verify full flow
                mock_orchestrator_class.assert_called_once()
                mock_orch.run.assert_called_once()
                mock_exit.assert_called_once_with(0)  # Success (tasks completed)