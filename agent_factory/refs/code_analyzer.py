"""
code_analyzer.py - Python Code Analysis using AST

Extracts semantic information from Python files:
- Functions and classes
- Imports and dependencies
- Docstrings
- Purpose inference
"""

import ast
from pathlib import Path
from typing import List, Set
from datetime import datetime
from .project_twin import FileNode


class CodeAnalyzer:
    """
    Analyzes Python code to extract semantic information.

    Uses AST parsing to understand:
    - Function and class definitions
    - Import statements
    - Docstrings and comments
    - Call relationships
    """

    def analyze_file(self, file_path: Path) -> FileNode:
        """
        Analyze a Python file and extract information.

        Returns FileNode with:
        - Functions: List of function names
        - Classes: List of class names
        - Imports: What this file imports
        - Dependencies: Files this depends on
        - Docstring: Module docstring

        Args:
            file_path: Path to Python file

        Returns:
            FileNode with extracted information
        """
        # Get file metadata
        stat = file_path.stat()
        file_type = self._infer_file_type(file_path)

        # Create base node
        file_node = FileNode(
            path=file_path,
            file_type=file_type,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            size_bytes=stat.st_size
        )

        # Parse Python files
        if file_type == "python":
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

                file_node.functions = self.extract_functions(tree)
                file_node.classes = self.extract_classes(tree)
                file_node.imports = self.extract_imports(tree)
                file_node.dependencies = self._resolve_dependencies(file_node.imports, file_path)
                file_node.docstring = ast.get_docstring(tree)
                file_node.purpose = self.infer_purpose(file_node)

            except Exception as e:
                # If parsing fails, still return basic file info
                print(f"Warning: Could not parse {file_path}: {e}")

        return file_node

    def extract_functions(self, tree: ast.AST) -> List[str]:
        """
        Extract function definitions from AST.

        Args:
            tree: AST tree

        Returns:
            List of function names
        """
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions

    def extract_classes(self, tree: ast.AST) -> List[str]:
        """
        Extract class definitions from AST.

        Args:
            tree: AST tree

        Returns:
            List of class names
        """
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes

    def extract_imports(self, tree: ast.AST) -> List[str]:
        """
        Extract import statements.

        Args:
            tree: AST tree

        Returns:
            List of imported module names
        """
        imports = []

        for node in ast.walk(tree):
            # import module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            # from module import name
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    def infer_purpose(self, file_node: FileNode) -> str:
        """
        Infer the purpose of a file from its contents.

        Uses heuristics:
        - File name patterns (test_*, config*, setup*)
        - Docstrings
        - Function/class names
        - Import patterns

        Args:
            file_node: FileNode to analyze

        Returns:
            Inferred purpose as string
        """
        file_name = file_node.path.name.lower()
        path_str = str(file_node.path).lower()

        # File name patterns
        if file_name.startswith('test_'):
            return "Test suite"
        if file_name == '__init__.py':
            return "Package initialization"
        if file_name.startswith('config'):
            return "Configuration"
        if file_name in ['setup.py', 'setup.cfg']:
            return "Package setup"
        if 'demo' in file_name or 'example' in file_name:
            return "Demo/Example"

        # Path patterns
        if '/tests/' in path_str or '\\tests\\' in path_str:
            return "Test"
        if '/examples/' in path_str or '\\examples\\' in path_str:
            return "Example/Demo"
        if '/tools/' in path_str or '\\tools\\' in path_str:
            return "Tool implementation"
        if '/schemas/' in path_str or '\\schemas\\' in path_str:
            return "Data schema/model"
        if '/core/' in path_str or '\\core\\' in path_str:
            return "Core functionality"

        # Docstring analysis
        if file_node.docstring:
            doc_lower = file_node.docstring.lower()
            if 'test' in doc_lower:
                return "Test suite"
            if 'config' in doc_lower:
                return "Configuration"
            if 'tool' in doc_lower:
                return "Tool implementation"
            # Return first line of docstring as purpose
            first_line = file_node.docstring.split('\n')[0].strip()
            if first_line and len(first_line) < 100:
                return first_line

        # Class/function name analysis
        if file_node.classes:
            # If has main class matching file name, it's probably that class's module
            stem = file_node.path.stem
            for cls in file_node.classes:
                if cls.lower() == stem.replace('_', '').lower():
                    return f"{cls} class implementation"

        # Generic fallback
        if file_node.functions or file_node.classes:
            return "Module implementation"

        return "Unknown purpose"

    def _infer_file_type(self, file_path: Path) -> str:
        """
        Infer file type from extension.

        Args:
            file_path: Path to file

        Returns:
            File type string
        """
        suffix = file_path.suffix.lower()

        type_map = {
            '.py': 'python',
            '.md': 'markdown',
            '.txt': 'text',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.cfg': 'config',
            '.ini': 'config',
        }

        return type_map.get(suffix, 'unknown')

    def _resolve_dependencies(self, imports: List[str], file_path: Path) -> Set[str]:
        """
        Resolve import statements to file paths within the project.

        Args:
            imports: List of imported module names
            file_path: Path to the file being analyzed

        Returns:
            Set of relative paths to dependency files
        """
        dependencies = set()

        for import_name in imports:
            # Only track local project imports (not external packages)
            if import_name.startswith('agent_factory'):
                # Convert module path to file path
                # e.g., "agent_factory.core.orchestrator" -> "agent_factory/core/orchestrator.py"
                parts = import_name.split('.')
                potential_path = Path(*parts[:-1]) / f"{parts[-1]}.py"
                dependencies.add(str(potential_path))

                # Also check for package import
                # e.g., "agent_factory.core" -> "agent_factory/core/__init__.py"
                package_path = Path(*parts) / "__init__.py"
                dependencies.add(str(package_path))

        return dependencies
