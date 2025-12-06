"""
twin_agent.py - LLM Agent Interface to Project Twin

Provides natural language interface to query project structure and dependencies.
"""

from pathlib import Path
from typing import Optional
from langchain_core.language_models.base import BaseLanguageModel
from langchain.agents import Tool

from .project_twin import ProjectTwin


class TwinAgent:
    """
    Agent that queries the project twin.

    Combines:
    - ProjectTwin (semantic project representation)
    - LLM (natural language understanding)
    - Tools (code analysis, search)

    Can answer:
    - "Where is X defined?"
    - "What depends on Y?"
    - "Show me all authentication files"
    - "Explain how the database connection works"
    """

    def __init__(self, project_twin: ProjectTwin, llm: Optional[BaseLanguageModel] = None):
        """
        Initialize twin agent.

        Args:
            project_twin: ProjectTwin instance
            llm: Language model for natural language queries (optional)
        """
        self.twin = project_twin
        self.llm = llm

        # Create specialized tools
        self.tools = [
            self._create_find_file_tool(),
            self._create_get_dependencies_tool(),
            self._create_search_functions_tool(),
            self._create_explain_file_tool(),
            self._create_list_files_tool(),
        ]

        # Create agent if LLM provided
        self.agent = None
        if llm:
            from agent_factory.core import AgentFactory
            factory = AgentFactory(llm=llm)
            self.agent = factory.create_agent(
                role="Project Twin Assistant",
                tools_list=self.tools,
                system_prompt=self._get_system_prompt()
            )

    def query(self, question: str) -> str:
        """
        Ask the twin a question about the project.

        Args:
            question: Natural language question

        Returns:
            Answer string
        """
        # If we have an LLM agent, use it
        if self.agent:
            try:
                result = self.agent.invoke({"input": question})
                if isinstance(result, dict) and "output" in result:
                    return result["output"]
                return str(result)
            except Exception as e:
                # Fallback to direct twin query
                return self.twin.query(question)
        else:
            # Use twin's built-in query
            return self.twin.query(question)

    def _get_system_prompt(self) -> str:
        """System prompt that gives context about the project."""
        return f"""You are a Project Twin assistant with deep knowledge of this codebase.

Project Information:
- Root: {self.twin.project_root}
- Total files: {len(self.twin.files)}
- Last synced: {self.twin.last_sync}
- Total classes: {len(self.twin.class_map)}
- Total functions: {len(self.twin.function_map)}

You can answer questions about:
- File locations and purposes
- Code dependencies and relationships
- Function and class definitions
- Project structure and patterns

Use your tools to query the project twin and provide accurate, concise answers.
Always cite specific file paths when answering."""

    def _create_find_file_tool(self) -> Tool:
        """Tool: Find files by purpose or name."""
        def find_file(query: str) -> str:
            """Find files matching a purpose or name pattern."""
            files = self.twin.find_files_by_purpose(query)
            if files:
                return f"Found {len(files)} files:\n" + "\n".join(f"- {f}" for f in files)
            return f"No files found matching: {query}"

        return Tool(
            name="find_file",
            description="Find files by purpose, name pattern, or keyword. Example: 'auth', 'test', 'database'",
            func=find_file
        )

    def _create_get_dependencies_tool(self) -> Tool:
        """Tool: Get dependencies of a file."""
        def get_dependencies(file_path: str) -> str:
            """Get dependencies of a specific file."""
            path = Path(file_path)
            deps = self.twin.get_dependencies(path)
            dependents = self.twin.get_dependents(path)

            result = [f"File: {file_path}"]

            if deps:
                result.append(f"\nDependencies ({len(deps)}):")
                result.extend(f"- {d}" for d in deps)
            else:
                result.append("\nNo dependencies")

            if dependents:
                result.append(f"\nDepended upon by ({len(dependents)}):")
                result.extend(f"- {d}" for d in dependents)
            else:
                result.append("\nNo dependents")

            return "\n".join(result)

        return Tool(
            name="get_dependencies",
            description="Get dependencies and dependents of a file. Provide full file path.",
            func=get_dependencies
        )

    def _create_search_functions_tool(self) -> Tool:
        """Tool: Search for functions/classes."""
        def search_functions(query: str) -> str:
            """Search for functions or classes by name."""
            results = []

            # Search classes
            matching_classes = {
                cls: path
                for cls, path in self.twin.class_map.items()
                if query.lower() in cls.lower()
            }

            if matching_classes:
                results.append(f"Classes matching '{query}':")
                for cls, path in matching_classes.items():
                    results.append(f"- {cls} in {path}")

            # Search functions
            matching_functions = {
                func: path
                for func, path in self.twin.function_map.items()
                if query.lower() in func.lower()
            }

            if matching_functions:
                if results:
                    results.append("")  # Empty line separator
                results.append(f"Functions matching '{query}':")
                for func, path in matching_functions.items():
                    results.append(f"- {func} in {path}")

            if not results:
                return f"No classes or functions found matching: {query}"

            return "\n".join(results)

        return Tool(
            name="search_functions",
            description="Search for classes and functions by name. Example: 'Agent', 'create', 'parse'",
            func=search_functions
        )

    def _create_explain_file_tool(self) -> Tool:
        """Tool: Explain what a file does."""
        def explain_file(file_path: str) -> str:
            """Get detailed information about a file."""
            path = Path(file_path)
            return self.twin.get_file_summary(path)

        return Tool(
            name="explain_file",
            description="Get detailed summary of a file including purpose, classes, functions. Provide full file path.",
            func=explain_file
        )

    def _create_list_files_tool(self) -> Tool:
        """Tool: List all files in the twin."""
        def list_files(filter_str: str = "") -> str:
            """List all files, optionally filtered."""
            all_files = list(self.twin.files.keys())

            if filter_str:
                filtered = [f for f in all_files if filter_str.lower() in str(f).lower()]
                if filtered:
                    return f"Files matching '{filter_str}':\n" + "\n".join(f"- {f}" for f in filtered)
                return f"No files matching: {filter_str}"

            # Group by directory
            by_dir = {}
            for file_path in all_files:
                dir_name = file_path.parent if file_path.parent != Path('.') else Path('root')
                if dir_name not in by_dir:
                    by_dir[dir_name] = []
                by_dir[dir_name].append(file_path.name)

            result = [f"Total files: {len(all_files)}\n"]
            for dir_name in sorted(by_dir.keys()):
                result.append(f"{dir_name}/")
                for file_name in sorted(by_dir[dir_name]):
                    result.append(f"  - {file_name}")

            return "\n".join(result)

        return Tool(
            name="list_files",
            description="List all files in the project. Optionally provide a filter string.",
            func=list_files
        )
