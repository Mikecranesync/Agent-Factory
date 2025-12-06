"""
project_twin.py - Digital Twin of Software Project

Maintains semantic representation of project structure, dependencies, and state.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime


@dataclass
class FileNode:
    """Represents a file in the project twin."""
    path: Path
    file_type: str  # "python", "markdown", "config", etc.
    last_modified: datetime
    size_bytes: int

    # Semantic information
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)

    # Documentation
    docstring: Optional[str] = None
    comments: List[str] = field(default_factory=list)

    # Metadata
    purpose: Optional[str] = None  # What this file does
    related_files: List[Path] = field(default_factory=list)


@dataclass
class ProjectTwin:
    """
    Digital twin of a software project.

    Maintains a semantic representation of:
    - File structure and relationships
    - Code dependencies
    - Documentation and patterns
    - Project state and history
    """
    project_root: Path
    files: Dict[Path, FileNode] = field(default_factory=dict)
    last_sync: Optional[datetime] = None

    # Knowledge graph
    file_graph: Dict[Path, Set[Path]] = field(default_factory=dict)  # path -> dependencies
    function_map: Dict[str, Path] = field(default_factory=dict)  # function_name -> file
    class_map: Dict[str, Path] = field(default_factory=dict)  # class_name -> file

    def sync(self, include_patterns: List[str] = None, exclude_patterns: List[str] = None) -> None:
        """
        Sync twin with actual project files.

        Scans project directory and updates twin representation.

        Args:
            include_patterns: Glob patterns to include (e.g., ["*.py", "*.md"])
            exclude_patterns: Glob patterns to exclude (e.g., ["**/tests/**"])
        """
        from .code_analyzer import CodeAnalyzer
        from .knowledge_graph import KnowledgeGraph

        # Default patterns
        if include_patterns is None:
            include_patterns = ["*.py"]
        if exclude_patterns is None:
            exclude_patterns = ["**/__pycache__/**", "**/.*", "**/*.pyc"]

        # Collect files
        files_to_analyze = []
        for pattern in include_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    # Check exclusions
                    excluded = False
                    for excl_pattern in exclude_patterns:
                        if file_path.match(excl_pattern):
                            excluded = True
                            break
                    if not excluded:
                        files_to_analyze.append(file_path)

        # Analyze each file
        analyzer = CodeAnalyzer()
        for file_path in files_to_analyze:
            try:
                file_node = analyzer.analyze_file(file_path)
                relative_path = file_path.relative_to(self.project_root)
                self.files[relative_path] = file_node

                # Update maps
                for func in file_node.functions:
                    self.function_map[func] = relative_path
                for cls in file_node.classes:
                    self.class_map[cls] = relative_path

            except Exception as e:
                # Skip files that can't be analyzed
                print(f"Warning: Could not analyze {file_path}: {e}")
                continue

        # Build knowledge graph
        graph = KnowledgeGraph()
        for file_path, file_node in self.files.items():
            graph.add_file(file_path, file_node.dependencies)

        self.file_graph = graph.graph
        self.last_sync = datetime.now()

    def query(self, question: str) -> str:
        """
        Answer questions about the project.

        Examples:
            - "What files handle authentication?"
            - "Where is the User class defined?"
            - "What depends on database.py?"

        Args:
            question: Natural language question about the project

        Returns:
            Answer as string
        """
        question_lower = question.lower()

        # Pattern: "where is <name> defined?" or "where is <name>?"
        if "where is" in question_lower:
            # Extract potential class/function name
            parts = question_lower.split("where is")
            if len(parts) > 1:
                name = parts[1].replace("?", "").replace("defined", "").strip()

                # Check class map
                for cls_name, file_path in self.class_map.items():
                    if name in cls_name.lower():
                        return f"{cls_name} class is defined in {file_path}"

                # Check function map
                for func_name, file_path in self.function_map.items():
                    if name in func_name.lower():
                        return f"{func_name} function is defined in {file_path}"

        # Pattern: "what depends on <file>?"
        if "depends on" in question_lower or "what depends" in question_lower:
            # Extract file name
            for file_path in self.files.keys():
                if str(file_path) in question:
                    dependents = self.get_dependents(file_path)
                    if dependents:
                        return f"Files that depend on {file_path}:\n" + "\n".join(f"- {dep}" for dep in dependents)
                    else:
                        return f"No files depend on {file_path}"

        return f"I don't have enough information to answer: {question}"

    def find_files_by_purpose(self, purpose: str) -> List[Path]:
        """
        Find files that serve a specific purpose.

        Args:
            purpose: Purpose keyword (e.g., "auth", "database", "test")

        Returns:
            List of file paths matching the purpose
        """
        matches = []
        purpose_lower = purpose.lower()

        for file_path, file_node in self.files.items():
            # Check file name
            if purpose_lower in str(file_path).lower():
                matches.append(file_path)
                continue

            # Check inferred purpose
            if file_node.purpose and purpose_lower in file_node.purpose.lower():
                matches.append(file_path)
                continue

            # Check docstring
            if file_node.docstring and purpose_lower in file_node.docstring.lower():
                matches.append(file_path)
                continue

        return matches

    def get_dependencies(self, file_path: Path) -> Set[Path]:
        """
        Get all dependencies of a file.

        Args:
            file_path: Path to the file

        Returns:
            Set of file paths this file depends on
        """
        from .knowledge_graph import KnowledgeGraph

        if file_path not in self.files:
            return set()

        return self.files[file_path].dependencies

    def get_dependents(self, file_path: Path) -> Set[Path]:
        """
        Get all files that depend on this file.

        Args:
            file_path: Path to the file

        Returns:
            Set of file paths that depend on this file
        """
        dependents = set()

        for other_path, other_node in self.files.items():
            if file_path in other_node.dependencies or str(file_path) in other_node.dependencies:
                dependents.add(other_path)

        return dependents

    def get_file_summary(self, file_path: Path) -> str:
        """
        Get human-readable summary of a file.

        Args:
            file_path: Path to the file

        Returns:
            Summary string
        """
        if file_path not in self.files:
            return f"File not found: {file_path}"

        file_node = self.files[file_path]
        lines = [
            f"File: {file_path}",
            f"Type: {file_node.file_type}",
            f"Size: {file_node.size_bytes} bytes",
            f"Last modified: {file_node.last_modified}",
        ]

        if file_node.purpose:
            lines.append(f"Purpose: {file_node.purpose}")

        if file_node.docstring:
            lines.append(f"\n{file_node.docstring}")

        if file_node.classes:
            lines.append(f"\nClasses: {', '.join(file_node.classes)}")

        if file_node.functions:
            lines.append(f"Functions: {', '.join(file_node.functions)}")

        if file_node.dependencies:
            lines.append(f"\nDependencies: {', '.join(str(d) for d in file_node.dependencies)}")

        return "\n".join(lines)
