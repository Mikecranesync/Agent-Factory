"""Unit tests for BacklogParser.

Tests the clean wrapper around Backlog.md MCP tools.
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from agent_factory.scaffold.backlog_parser import (
    BacklogParser,
    TaskSpec,
    BacklogParserError
)


# Create fake mcp module for testing
fake_mcp = MagicMock()
sys.modules['mcp'] = fake_mcp


# Fixtures

@pytest.fixture
def mock_mcp_tools():
    """Mock MCP backlog tools."""
    # Reset mocks before each test
    fake_mcp.mcp__backlog__task_list = Mock()
    fake_mcp.mcp__backlog__task_view = Mock()
    fake_mcp.mcp__backlog__task_edit = Mock()

    yield {
        'list': fake_mcp.mcp__backlog__task_list,
        'view': fake_mcp.mcp__backlog__task_view,
        'edit': fake_mcp.mcp__backlog__task_edit
    }

    # Clean up
    fake_mcp.reset_mock()


@pytest.fixture
def sample_task_data():
    """Sample task data matching MCP format."""
    return {
        "id": "task-42",
        "title": "Test Task",
        "description": "Test description",
        "status": "To Do",
        "priority": "high",
        "labels": ["test", "scaffold"],
        "dependencies": ["task-41"],
        "acceptance_criteria": ["Criterion 1", "Criterion 2"],
        "assignee": ["agent"],
        "parent_task_id": None,
        "created_date": "2025-12-18",
        "implementation_notes": "Initial notes"
    }


@pytest.fixture
def parser():
    """BacklogParser instance with MCP available."""
    with patch('agent_factory.scaffold.backlog_parser.BacklogParser._check_mcp_available', return_value=True):
        return BacklogParser()


# TaskSpec Tests

def test_taskspec_from_dict(sample_task_data):
    """Test TaskSpec.from_dict() conversion."""
    task = TaskSpec.from_dict(sample_task_data)

    assert task.task_id == "task-42"
    assert task.title == "Test Task"
    assert task.status == "To Do"
    assert task.priority == "high"
    assert task.labels == ["test", "scaffold"]
    assert task.dependencies == ["task-41"]


def test_taskspec_to_dict(sample_task_data):
    """Test TaskSpec.to_dict() serialization."""
    task = TaskSpec.from_dict(sample_task_data)
    data = task.to_dict()

    assert data["id"] == "task-42"
    assert data["title"] == "Test Task"
    assert data["status"] == "To Do"


def test_taskspec_defaults():
    """Test TaskSpec with minimal data."""
    task = TaskSpec.from_dict({"id": "task-1", "title": "Minimal"})

    assert task.task_id == "task-1"
    assert task.title == "Minimal"
    assert task.description == ""
    assert task.status == "To Do"
    assert task.priority == "medium"
    assert task.labels == []


# BacklogParser Tests

def test_parser_initialization_mcp_available():
    """Test parser initializes when MCP is available."""
    with patch('agent_factory.scaffold.backlog_parser.BacklogParser._check_mcp_available', return_value=True):
        parser = BacklogParser()
        assert parser._mcp_available is True


def test_parser_initialization_mcp_unavailable():
    """Test parser initializes when MCP is unavailable."""
    with patch('agent_factory.scaffold.backlog_parser.BacklogParser._check_mcp_available', return_value=False):
        parser = BacklogParser()
        assert parser._mcp_available is False


def test_list_tasks_basic(parser, mock_mcp_tools, sample_task_data):
    """Test list_tasks() basic functionality."""
    mock_mcp_tools['list'].return_value = [sample_task_data]

    tasks = parser.list_tasks(status="To Do", limit=10)

    assert len(tasks) == 1
    assert tasks[0].task_id == "task-42"
    assert tasks[0].title == "Test Task"

    # Verify MCP was called correctly
    mock_mcp_tools['list'].assert_called_once_with(status="To Do", limit=10)


def test_list_tasks_with_label_filter(parser, mock_mcp_tools, sample_task_data):
    """Test list_tasks() with label filtering."""
    # Create tasks with different labels
    task1 = {**sample_task_data, "id": "task-1", "labels": ["scaffold"]}
    task2 = {**sample_task_data, "id": "task-2", "labels": ["other"]}
    task3 = {**sample_task_data, "id": "task-3", "labels": ["scaffold", "test"]}

    mock_mcp_tools['list'].return_value = [task1, task2, task3]

    # Filter for "scaffold" label
    tasks = parser.list_tasks(labels=["scaffold"])

    assert len(tasks) == 2
    assert tasks[0].task_id == "task-1"
    assert tasks[1].task_id == "task-3"


def test_list_tasks_dependencies_satisfied(parser, mock_mcp_tools, sample_task_data):
    """Test list_tasks() with dependencies_satisfied filter."""
    # Task with satisfied dependencies
    task1 = {**sample_task_data, "id": "task-1", "dependencies": ["task-0"]}

    # Task with unsatisfied dependencies
    task2 = {**sample_task_data, "id": "task-2", "dependencies": ["task-99"]}

    # Task with no dependencies
    task3 = {**sample_task_data, "id": "task-3", "dependencies": []}

    mock_mcp_tools['list'].return_value = [task1, task2, task3]

    # Mock dependency checking (note: uses keyword argument 'id')
    def mock_get_task(id):
        if id == "task-0":
            return {**sample_task_data, "id": "task-0", "status": "Done"}
        elif id == "task-99":
            return {**sample_task_data, "id": "task-99", "status": "To Do"}
        raise Exception("Task not found")

    mock_mcp_tools['view'].side_effect = mock_get_task

    # Filter for satisfied dependencies
    tasks = parser.list_tasks(dependencies_satisfied=True)

    # Should return task-1 (deps Done) and task-3 (no deps)
    assert len(tasks) == 2
    assert tasks[0].task_id == "task-1"
    assert tasks[1].task_id == "task-3"


def test_list_tasks_mcp_unavailable():
    """Test list_tasks() when MCP is unavailable."""
    with patch('agent_factory.scaffold.backlog_parser.BacklogParser._check_mcp_available', return_value=False):
        parser = BacklogParser()
        tasks = parser.list_tasks()

        assert tasks == []


def test_get_task_success(parser, mock_mcp_tools, sample_task_data):
    """Test get_task() successful retrieval."""
    mock_mcp_tools['view'].return_value = sample_task_data

    task = parser.get_task("task-42")

    assert task.task_id == "task-42"
    assert task.title == "Test Task"

    mock_mcp_tools['view'].assert_called_once_with(id="task-42")


def test_get_task_not_found(parser, mock_mcp_tools):
    """Test get_task() when task doesn't exist."""
    mock_mcp_tools['view'].side_effect = Exception("Task not found")

    with pytest.raises(BacklogParserError, match="Failed to get task"):
        parser.get_task("task-999")


def test_get_task_mcp_unavailable():
    """Test get_task() when MCP is unavailable."""
    with patch('agent_factory.scaffold.backlog_parser.BacklogParser._check_mcp_available', return_value=False):
        parser = BacklogParser()

        with pytest.raises(BacklogParserError, match="MCP not available"):
            parser.get_task("task-42")


def test_update_status_success(parser, mock_mcp_tools):
    """Test update_status() successful update."""
    result = parser.update_status("task-42", "In Progress")

    assert result is True

    mock_mcp_tools['edit'].assert_called_once_with(
        id="task-42",
        status="In Progress"
    )


def test_update_status_invalid_status(parser):
    """Test update_status() with invalid status."""
    with pytest.raises(BacklogParserError, match="Invalid status"):
        parser.update_status("task-42", "Invalid Status")


def test_update_status_valid_statuses(parser, mock_mcp_tools):
    """Test update_status() accepts all valid statuses."""
    valid_statuses = ["To Do", "In Progress", "Done"]

    for status in valid_statuses:
        parser.update_status("task-42", status)

    assert mock_mcp_tools['edit'].call_count == 3


def test_update_status_mcp_error(parser, mock_mcp_tools):
    """Test update_status() when MCP edit fails."""
    mock_mcp_tools['edit'].side_effect = Exception("MCP error")

    with pytest.raises(BacklogParserError, match="Failed to update status"):
        parser.update_status("task-42", "Done")


def test_add_notes_append(parser, mock_mcp_tools, sample_task_data):
    """Test add_notes() appending to existing notes."""
    mock_mcp_tools['view'].return_value = sample_task_data

    result = parser.add_notes("task-42", "New note", append=True)

    assert result is True

    # Verify edit was called with appended notes
    call_args = mock_mcp_tools['edit'].call_args
    assert call_args[1]['id'] == "task-42"
    assert "Initial notes" in call_args[1]['implementation_notes']
    assert "New note" in call_args[1]['implementation_notes']


def test_add_notes_replace(parser, mock_mcp_tools):
    """Test add_notes() replacing existing notes."""
    result = parser.add_notes("task-42", "Replacement notes", append=False)

    assert result is True

    mock_mcp_tools['edit'].assert_called_once_with(
        id="task-42",
        implementation_notes="Replacement notes"
    )


def test_add_notes_no_existing_notes(parser, mock_mcp_tools, sample_task_data):
    """Test add_notes() when task has no existing notes."""
    task_data = {**sample_task_data, "implementation_notes": None}
    mock_mcp_tools['view'].return_value = task_data

    result = parser.add_notes("task-42", "First note", append=True)

    assert result is True

    # Should just contain new note
    call_args = mock_mcp_tools['edit'].call_args
    assert call_args[1]['implementation_notes'] == "First note"


def test_add_notes_mcp_unavailable():
    """Test add_notes() when MCP is unavailable."""
    with patch('agent_factory.scaffold.backlog_parser.BacklogParser._check_mcp_available', return_value=False):
        parser = BacklogParser()

        with pytest.raises(BacklogParserError, match="MCP not available"):
            parser.add_notes("task-42", "Note")


def test_check_mcp_available():
    """Test _check_mcp_available() detection."""
    # MCP should be available (we injected fake_mcp module)
    parser = BacklogParser()
    assert parser._mcp_available is True

    # Test when import fails
    original_modules = sys.modules.copy()
    try:
        # Remove mcp module temporarily
        if 'mcp' in sys.modules:
            del sys.modules['mcp']

        # Force re-check
        parser2 = BacklogParser()
        assert parser2._mcp_available is False
    finally:
        # Restore modules
        sys.modules.update(original_modules)


def test_are_dependencies_satisfied_all_done(parser, mock_mcp_tools, sample_task_data):
    """Test _are_dependencies_satisfied() when all deps are Done."""
    task = TaskSpec.from_dict({
        **sample_task_data,
        "dependencies": ["task-1", "task-2"]
    })

    # Mock both dependencies as Done
    mock_mcp_tools['view'].return_value = {**sample_task_data, "status": "Done"}

    result = parser._are_dependencies_satisfied(task)

    assert result is True
    assert mock_mcp_tools['view'].call_count == 2


def test_are_dependencies_satisfied_some_pending(parser, mock_mcp_tools, sample_task_data):
    """Test _are_dependencies_satisfied() when some deps are pending."""
    task = TaskSpec.from_dict({
        **sample_task_data,
        "dependencies": ["task-1", "task-2"]
    })

    # Mock task-1 as Done, task-2 as To Do
    def mock_view(id):
        if id == "task-1":
            return {**sample_task_data, "status": "Done"}
        else:
            return {**sample_task_data, "status": "To Do"}

    mock_mcp_tools['view'].side_effect = mock_view

    result = parser._are_dependencies_satisfied(task)

    assert result is False


def test_are_dependencies_satisfied_no_dependencies(parser, sample_task_data):
    """Test _are_dependencies_satisfied() when task has no dependencies."""
    task = TaskSpec.from_dict({**sample_task_data, "dependencies": []})

    result = parser._are_dependencies_satisfied(task)

    assert result is True


def test_are_dependencies_satisfied_error_handling(parser, mock_mcp_tools, sample_task_data):
    """Test _are_dependencies_satisfied() handles errors gracefully."""
    task = TaskSpec.from_dict({
        **sample_task_data,
        "dependencies": ["task-999"]
    })

    # Mock error fetching dependency
    mock_mcp_tools['view'].side_effect = Exception("Task not found")

    result = parser._are_dependencies_satisfied(task)

    # Should return False on error
    assert result is False


# Integration Tests

def test_full_workflow(parser, mock_mcp_tools, sample_task_data):
    """Test complete workflow: list → get → update → add notes."""
    # Setup mocks
    mock_mcp_tools['list'].return_value = [sample_task_data]
    mock_mcp_tools['view'].return_value = sample_task_data

    # 1. List tasks
    tasks = parser.list_tasks(status="To Do")
    assert len(tasks) == 1

    # 2. Get task details
    task = parser.get_task("task-42")
    assert task.task_id == "task-42"

    # 3. Update status
    parser.update_status("task-42", "In Progress")

    # 4. Add notes
    parser.add_notes("task-42", "Started implementation")

    # Verify all MCP calls
    assert mock_mcp_tools['list'].call_count == 1
    assert mock_mcp_tools['view'].call_count == 2  # get_task + add_notes
    assert mock_mcp_tools['edit'].call_count == 2  # update_status + add_notes
