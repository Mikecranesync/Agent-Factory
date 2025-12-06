"""
test_project_twin.py - Tests for Project Twin (Phase 5)

Tests:
- FileNode and ProjectTwin data structures
- CodeAnalyzer parsing
- KnowledgeGraph operations
- TwinAgent queries
"""

import sys
from pathlib import Path
from datetime import datetime
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from agent_factory.refs import (
    FileNode,
    ProjectTwin,
    CodeAnalyzer,
    KnowledgeGraph,
    TwinAgent,
)


# ============================================================================
# FileNode Tests
# ============================================================================


def test_file_node_creation():
    """Test FileNode dataclass creation."""
    node = FileNode(
        path=Path("test.py"),
        file_type="python",
        last_modified=datetime.now(),
        size_bytes=1024,
    )

    assert node.path == Path("test.py")
    assert node.file_type == "python"
    assert node.size_bytes == 1024
    assert node.functions == []
    assert node.classes == []


def test_file_node_with_metadata():
    """Test FileNode with semantic metadata."""
    node = FileNode(
        path=Path("agent.py"),
        file_type="python",
        last_modified=datetime.now(),
        size_bytes=2048,
        functions=["create_agent", "run_agent"],
        classes=["Agent", "AgentConfig"],
        imports=["langchain", "pydantic"],
        docstring="Agent implementation module",
        purpose="Agent creation and execution",
    )

    assert len(node.functions) == 2
    assert len(node.classes) == 2
    assert "langchain" in node.imports
    assert node.purpose == "Agent creation and execution"


# ============================================================================
# CodeAnalyzer Tests
# ============================================================================


def test_code_analyzer_extract_functions():
    """Test extracting function definitions."""
    import ast

    code = """
def hello():
    pass

def world():
    pass

class Test:
    def method(self):
        pass
"""

    tree = ast.parse(code)
    analyzer = CodeAnalyzer()
    functions = analyzer.extract_functions(tree)

    assert "hello" in functions
    assert "world" in functions
    assert "method" in functions  # Methods are also functions


def test_code_analyzer_extract_classes():
    """Test extracting class definitions."""
    import ast

    code = """
class Agent:
    pass

class Tool:
    pass
"""

    tree = ast.parse(code)
    analyzer = CodeAnalyzer()
    classes = analyzer.extract_classes(tree)

    assert "Agent" in classes
    assert "Tool" in classes


def test_code_analyzer_extract_imports():
    """Test extracting import statements."""
    import ast

    code = """
import os
import sys
from pathlib import Path
from typing import Dict, List
from agent_factory.core import AgentFactory
"""

    tree = ast.parse(code)
    analyzer = CodeAnalyzer()
    imports = analyzer.extract_imports(tree)

    assert "os" in imports
    assert "sys" in imports
    assert "pathlib" in imports
    assert "typing" in imports
    assert "agent_factory.core" in imports


def test_code_analyzer_analyze_file():
    """Test full file analysis."""
    # Create temporary Python file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''"""Test module docstring."""

class TestClass:
    """Test class."""
    def test_method(self):
        pass

def test_function():
    """Test function."""
    pass
''')
        temp_path = Path(f.name)

    try:
        analyzer = CodeAnalyzer()
        file_node = analyzer.analyze_file(temp_path)

        assert file_node.file_type == "python"
        assert "TestClass" in file_node.classes
        assert "test_function" in file_node.functions
        assert "test_method" in file_node.functions
        assert file_node.docstring == "Test module docstring."

    finally:
        os.unlink(temp_path)


def test_code_analyzer_infer_purpose_test_file():
    """Test purpose inference for test files."""
    node = FileNode(
        path=Path("test_agent.py"),
        file_type="python",
        last_modified=datetime.now(),
        size_bytes=1024,
    )

    analyzer = CodeAnalyzer()
    purpose = analyzer.infer_purpose(node)

    assert "test" in purpose.lower()


def test_code_analyzer_infer_purpose_init_file():
    """Test purpose inference for __init__.py."""
    node = FileNode(
        path=Path("agent_factory/__init__.py"),
        file_type="python",
        last_modified=datetime.now(),
        size_bytes=512,
    )

    analyzer = CodeAnalyzer()
    purpose = analyzer.infer_purpose(node)

    assert "package initialization" in purpose.lower()


# ============================================================================
# KnowledgeGraph Tests
# ============================================================================


def test_knowledge_graph_creation():
    """Test KnowledgeGraph initialization."""
    graph = KnowledgeGraph()

    assert graph.graph is not None
    assert len(graph._file_nodes) == 0


def test_knowledge_graph_add_file():
    """Test adding files to knowledge graph."""
    graph = KnowledgeGraph()

    file_a = Path("a.py")
    file_b = Path("b.py")

    # a.py depends on b.py
    graph.add_file(file_a, {str(file_b)})

    assert file_a in graph._file_nodes
    assert file_b in graph._file_nodes


def test_knowledge_graph_get_dependencies():
    """Test getting direct dependencies."""
    graph = KnowledgeGraph()

    file_a = Path("a.py")
    file_b = Path("b.py")
    file_c = Path("c.py")

    # a depends on b and c
    graph.add_file(file_a, {str(file_b), str(file_c)})

    deps = graph.get_dependencies(file_a, recursive=False)

    assert file_b in deps
    assert file_c in deps
    assert len(deps) == 2


def test_knowledge_graph_get_dependents():
    """Test getting files that depend on a file."""
    graph = KnowledgeGraph()

    file_a = Path("a.py")
    file_b = Path("b.py")

    # a depends on b
    graph.add_file(file_a, {str(file_b)})

    dependents = graph.get_dependents(file_b, recursive=False)

    assert file_a in dependents


def test_knowledge_graph_find_path():
    """Test finding dependency path between files."""
    graph = KnowledgeGraph()

    file_a = Path("a.py")
    file_b = Path("b.py")
    file_c = Path("c.py")

    # a -> b -> c
    graph.add_file(file_a, {str(file_b)})
    graph.add_file(file_b, {str(file_c)})

    path = graph.find_path(file_a, file_c)

    assert path is not None
    assert file_a in path
    assert file_c in path


def test_knowledge_graph_get_stats():
    """Test graph statistics."""
    graph = KnowledgeGraph()

    file_a = Path("a.py")
    file_b = Path("b.py")

    graph.add_file(file_a, {str(file_b)})

    stats = graph.get_stats()

    assert stats['total_files'] >= 2
    assert stats['total_dependencies'] >= 1
    assert 'avg_dependencies' in stats


# ============================================================================
# ProjectTwin Tests
# ============================================================================


def test_project_twin_creation():
    """Test ProjectTwin initialization."""
    twin = ProjectTwin(project_root=Path.cwd())

    assert twin.project_root == Path.cwd()
    assert len(twin.files) == 0
    assert twin.last_sync is None


def test_project_twin_sync():
    """Test syncing twin with project."""
    # Create temporary project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create some Python files
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def helper(): pass")

        # Create twin and sync
        twin = ProjectTwin(project_root=tmp_path)
        twin.sync(include_patterns=["*.py"])

        assert len(twin.files) == 2
        assert twin.last_sync is not None


def test_project_twin_find_files_by_purpose():
    """Test finding files by purpose."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create files
        (tmp_path / "test_main.py").write_text("def test(): pass")
        (tmp_path / "config.py").write_text("CONFIG = {}")

        twin = ProjectTwin(project_root=tmp_path)
        twin.sync(include_patterns=["*.py"])

        # Find test files
        test_files = twin.find_files_by_purpose("test")
        assert len(test_files) > 0


def test_project_twin_get_dependencies():
    """Test getting file dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create file with import
        (tmp_path / "main.py").write_text("from agent_factory.core import AgentFactory")

        twin = ProjectTwin(project_root=tmp_path)
        twin.sync(include_patterns=["*.py"])

        main_path = Path("main.py")
        if main_path in twin.files:
            deps = twin.get_dependencies(main_path)
            assert isinstance(deps, set)


def test_project_twin_query_where_is():
    """Test 'where is' queries."""
    twin = ProjectTwin(project_root=Path.cwd())

    # Manually add test data
    file_node = FileNode(
        path=Path("test.py"),
        file_type="python",
        last_modified=datetime.now(),
        size_bytes=1024,
        classes=["TestClass"],
    )

    twin.files[Path("test.py")] = file_node
    twin.class_map["TestClass"] = Path("test.py")

    result = twin.query("Where is TestClass defined?")

    assert "TestClass" in result
    assert "test.py" in result


def test_project_twin_get_file_summary():
    """Test getting file summary."""
    twin = ProjectTwin(project_root=Path.cwd())

    file_node = FileNode(
        path=Path("agent.py"),
        file_type="python",
        last_modified=datetime.now(),
        size_bytes=2048,
        functions=["create_agent"],
        classes=["Agent"],
        purpose="Agent implementation",
    )

    twin.files[Path("agent.py")] = file_node

    summary = twin.get_file_summary(Path("agent.py"))

    assert "agent.py" in summary
    assert "Agent" in summary
    assert "create_agent" in summary


# ============================================================================
# TwinAgent Tests
# ============================================================================


def test_twin_agent_creation_without_llm():
    """Test TwinAgent creation without LLM."""
    twin = ProjectTwin(project_root=Path.cwd())
    twin_agent = TwinAgent(project_twin=twin)

    assert twin_agent.twin == twin
    assert len(twin_agent.tools) == 5  # 5 tools defined
    assert twin_agent.agent is None  # No agent without LLM


def test_twin_agent_query_without_llm():
    """Test querying without LLM (falls back to twin.query)."""
    twin = ProjectTwin(project_root=Path.cwd())

    # Add test data
    file_node = FileNode(
        path=Path("test.py"),
        file_type="python",
        last_modified=datetime.now(),
        size_bytes=1024,
        classes=["MyClass"],
    )

    twin.files[Path("test.py")] = file_node
    twin.class_map["MyClass"] = Path("test.py")

    twin_agent = TwinAgent(project_twin=twin)
    result = twin_agent.query("Where is MyClass defined?")

    assert "MyClass" in result


def test_twin_agent_tools():
    """Test that TwinAgent creates expected tools."""
    twin = ProjectTwin(project_root=Path.cwd())
    twin_agent = TwinAgent(project_twin=twin)

    tool_names = [tool.name for tool in twin_agent.tools]

    assert "find_file" in tool_names
    assert "get_dependencies" in tool_names
    assert "search_functions" in tool_names
    assert "explain_file" in tool_names
    assert "list_files" in tool_names


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_twin_workflow():
    """Test complete twin workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create project structure
        (tmp_path / "main.py").write_text('''
"""Main module."""
from utils import helper

class MainClass:
    """Main class."""
    def run(self):
        helper()
''')

        (tmp_path / "utils.py").write_text('''
"""Utility functions."""
def helper():
    """Helper function."""
    pass
''')

        # Create and sync twin
        twin = ProjectTwin(project_root=tmp_path)
        twin.sync(include_patterns=["*.py"])

        # Verify sync
        assert len(twin.files) == 2
        assert len(twin.class_map) >= 1

        # Test queries
        result = twin.query("Where is MainClass defined?")
        assert "MainClass" in result

        # Test dependencies
        main_file = Path("main.py")
        if main_file in twin.files:
            summary = twin.get_file_summary(main_file)
            assert "Main module" in summary or "main.py" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
