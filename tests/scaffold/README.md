# SCAFFOLD Test Suite

Comprehensive test coverage for the SCAFFOLD autonomous development system.

## Test Files

### `test_worktree_manager.py`
Tests for git worktree management:
- Worktree creation and cleanup
- Concurrent worktree limits
- Metadata persistence
- Error handling

### `test_orchestrator_validation.py`
Integration tests for the main orchestrator:
- Component imports and initialization
- TaskFetcher integration with MCP
- WorktreeManager integration
- TaskRouter logic
- SessionManager state tracking
- ResultProcessor Backlog updates
- End-to-end dry-run workflows
- Acceptance criteria validation

### `test_task_fetcher_comprehensive.py` (NEW)
Comprehensive unit tests for TaskFetcher module:
- **Happy path scenarios**: Basic fetching, filtering, sorting
- **Dependency resolution**: Blocking, satisfaction, circular deps
- **Priority scoring**: Base priorities, label bonuses/penalties, age factors
- **Caching**: Cache hits, TTL expiration, invalidation
- **Error handling**: MCP failures, timeouts, malformed data
- **Edge cases**: Empty lists, large datasets, Unicode, None values
- **Security**: SQL injection, XSS, path traversal attempts
- **Performance**: Large dependency chains, many labels
- **Backwards compatibility**: Legacy data formats

**Coverage**: 200+ test cases covering all code paths

### `test_orchestrator_cli.py` (NEW)
Tests for the CLI entry point:
- **Argument parsing**: All CLI flags and options
- **Environment variables**: Configuration via env vars
- **Orchestrator initialization**: Correct parameter passing
- **Exit codes**: Success (0), failure (1), no work (2), interrupt (130)
- **Error handling**: Exceptions, keyboard interrupts
- **Logging**: Log directory creation, file naming
- **Integration**: Full CLI workflows with all options

**Coverage**: 40+ test cases for CLI behavior

## Running Tests

### Run all SCAFFOLD tests
```bash
pytest tests/scaffold/ -v
```

### Run specific test file
```bash
pytest tests/scaffold/test_task_fetcher_comprehensive.py -v
pytest tests/scaffold/test_orchestrator_cli.py -v
pytest tests/scaffold/test_orchestrator_validation.py -v
pytest tests/scaffold/test_worktree_manager.py -v
```

### Run with coverage
```bash
pytest tests/scaffold/ --cov=agent_factory.scaffold --cov=scripts.autonomous --cov-report=html
```

### Run specific test class
```bash
pytest tests/scaffold/test_task_fetcher_comprehensive.py::TestDependencyResolution -v
```

### Run specific test
```bash
pytest tests/scaffold/test_task_fetcher_comprehensive.py::TestDependencyResolution::test_blocks_task_with_unmet_dependencies -v
```

## Test Coverage

### agent_factory/scaffold/task_fetcher.py
- ✅ Initialization (default and custom TTL)
- ✅ fetch_eligible_tasks (happy path, filtering, limits)
- ✅ _dependencies_satisfied (all scenarios)
- ✅ _priority_score (all bonuses/penalties)
- ✅ _calculate_age_bonus (all date scenarios)
- ✅ _get_placeholder_tasks
- ✅ invalidate_cache
- ✅ Error handling (MCP failures, timeouts)
- ✅ Edge cases (empty, large, malformed data)
- ✅ Security (injection attempts)

### scripts/autonomous/scaffold_orchestrator.py
- ✅ parse_args (all argument combinations)
- ✅ Environment variable handling
- ✅ Orchestrator initialization
- ✅ Label parsing
- ✅ Exit code logic
- ✅ Error handling (exceptions, interrupts)
- ✅ Logging configuration
- ✅ Summary printing

### agent_factory/scaffold/orchestrator.py
- ✅ Orchestrator initialization
- ✅ Component integration
- ✅ Task fetching and queuing
- ✅ Dry-run mode
- ✅ Safety limit checking
- ✅ Session management

## Test Statistics

- **Total test files**: 4
- **Total test classes**: 35+
- **Total test cases**: 300+
- **Code coverage**: >90% (target)

## Continuous Integration

Tests run automatically on:
- Every pull request
- Every push to main branch
- Nightly builds

## Contributing

When adding new features to SCAFFOLD:
1. Write tests first (TDD approach)
2. Aim for >80% code coverage
3. Include happy path, edge cases, and error scenarios
4. Add docstrings explaining what each test validates
5. Use descriptive test names that explain the scenario

## Test Patterns

### Mocking MCP Tools
```python
@patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_list')
@patch('agent_factory.scaffold.task_fetcher.mcp__backlog__task_view')
def test_something(self, mock_task_view, mock_task_list):
    mock_task_list.return_value = [...]
    # Test code
```

### Testing CLI
```python
@patch('sys.argv', ['script.py', '--arg', 'value'])
@patch('module.ScaffoldOrchestrator')
def test_cli(self, mock_orch, clean_env):
    # Test code
```

### Testing Error Handling
```python
def test_error_handling(self):
    mock.side_effect = Exception("Error message")
    result = function_under_test()
    assert result == expected_fallback
```

## Known Test Limitations

- MCP tools are always mocked (no real Backlog.md integration)
- Git commands are mocked (no real repository operations)
- File system operations use temporary directories
- Network calls are mocked (no real API calls)

These limitations ensure tests are:
- Fast (< 1 second per test)
- Reliable (no external dependencies)
- Isolated (no side effects)