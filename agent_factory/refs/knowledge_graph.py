"""
knowledge_graph.py - Project Dependency Graph

Builds and queries a graph of file relationships using NetworkX.
"""

from pathlib import Path
from typing import Dict, Set, List, Optional
import networkx as nx


class KnowledgeGraph:
    """
    Graph representation of project structure.

    Nodes: Files
    Edges: Dependencies (imports, calls, references)

    Enables queries like:
    - What depends on this?
    - What's the dependency chain?
    - Find circular dependencies
    - Identify central files (most imported)
    """

    def __init__(self):
        """Initialize empty directed graph."""
        self.graph: nx.DiGraph = nx.DiGraph()
        self._file_nodes: Set[Path] = set()

    def add_file(self, file_path: Path, dependencies: Set[str]) -> None:
        """
        Add a file and its dependencies to the graph.

        Args:
            file_path: Path to the file
            dependencies: Set of file paths this file depends on
        """
        # Add file as node if not exists
        if file_path not in self._file_nodes:
            self.graph.add_node(file_path)
            self._file_nodes.add(file_path)

        # Add dependencies as edges
        for dep in dependencies:
            dep_path = Path(dep) if not isinstance(dep, Path) else dep

            # Add dependency node if not exists
            if dep_path not in self._file_nodes:
                self.graph.add_node(dep_path)
                self._file_nodes.add(dep_path)

            # Add edge: file_path depends on dep_path
            self.graph.add_edge(file_path, dep_path)

    def get_dependencies(self, file_path: Path, recursive: bool = False) -> Set[Path]:
        """
        Get direct or transitive dependencies.

        Args:
            file_path: Path to the file
            recursive: If True, get all transitive dependencies

        Returns:
            Set of file paths this file depends on
        """
        if file_path not in self.graph:
            return set()

        if not recursive:
            # Direct dependencies (successors in directed graph)
            return set(self.graph.successors(file_path))
        else:
            # Transitive dependencies (all reachable nodes)
            try:
                return set(nx.descendants(self.graph, file_path))
            except nx.NetworkXError:
                return set()

    def get_dependents(self, file_path: Path, recursive: bool = False) -> Set[Path]:
        """
        Get files that depend on this file.

        Args:
            file_path: Path to the file
            recursive: If True, get all transitive dependents

        Returns:
            Set of file paths that depend on this file
        """
        if file_path not in self.graph:
            return set()

        if not recursive:
            # Direct dependents (predecessors in directed graph)
            return set(self.graph.predecessors(file_path))
        else:
            # Transitive dependents (all nodes that can reach this one)
            try:
                return set(nx.ancestors(self.graph, file_path))
            except nx.NetworkXError:
                return set()

    def find_path(self, from_file: Path, to_file: Path) -> Optional[List[Path]]:
        """
        Find dependency path between two files.

        Args:
            from_file: Starting file
            to_file: Target file

        Returns:
            List of file paths forming the dependency chain, or None if no path exists
        """
        if from_file not in self.graph or to_file not in self.graph:
            return None

        try:
            return nx.shortest_path(self.graph, from_file, to_file)
        except nx.NetworkXNoPath:
            return None

    def find_circular_dependencies(self) -> List[List[Path]]:
        """
        Find circular dependency cycles.

        Returns:
            List of cycles, where each cycle is a list of file paths
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except Exception:
            return []

    def get_central_files(self, top_n: int = 10, method: str = 'degree') -> List[tuple[Path, float]]:
        """
        Get most-depended-on files.

        Args:
            top_n: Number of files to return
            method: Centrality method ('degree', 'pagerank', 'betweenness')

        Returns:
            List of (file_path, centrality_score) tuples, sorted by score descending
        """
        if not self.graph.nodes():
            return []

        centrality: Dict[Path, float] = {}

        if method == 'degree':
            # In-degree: how many files import this file
            centrality = dict(self.graph.in_degree())

        elif method == 'pagerank':
            # PageRank: importance based on who imports it and their importance
            try:
                centrality = nx.pagerank(self.graph)
            except Exception:
                # Fallback to degree if PageRank fails
                centrality = dict(self.graph.in_degree())

        elif method == 'betweenness':
            # Betweenness: how often this file appears in dependency paths
            try:
                centrality = nx.betweenness_centrality(self.graph)
            except Exception:
                centrality = dict(self.graph.in_degree())

        # Sort by centrality score descending
        sorted_files = sorted(
            centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_files[:top_n]

    def get_orphan_files(self) -> Set[Path]:
        """
        Get files with no dependencies and no dependents.

        Returns:
            Set of isolated file paths
        """
        orphans = set()

        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)

            if in_degree == 0 and out_degree == 0:
                orphans.add(node)

        return orphans

    def get_leaf_files(self) -> Set[Path]:
        """
        Get files that have no dependencies (but may be depended upon).

        Returns:
            Set of leaf file paths
        """
        leaves = set()

        for node in self.graph.nodes():
            if self.graph.out_degree(node) == 0:
                leaves.add(node)

        return leaves

    def get_root_files(self) -> Set[Path]:
        """
        Get files that nothing depends on (but may depend on others).

        Returns:
            Set of root file paths
        """
        roots = set()

        for node in self.graph.nodes():
            if self.graph.in_degree(node) == 0:
                roots.add(node)

        return roots

    def export_dot(self, output_path: Path) -> None:
        """
        Export graph to DOT format for visualization.

        Args:
            output_path: Path to output .dot file
        """
        try:
            nx.drawing.nx_pydot.write_dot(self.graph, output_path)
        except Exception as e:
            print(f"Warning: Could not export DOT file: {e}")

    def get_stats(self) -> dict:
        """
        Get graph statistics.

        Returns:
            Dictionary with graph metrics
        """
        stats = {
            'total_files': self.graph.number_of_nodes(),
            'total_dependencies': self.graph.number_of_edges(),
            'orphan_files': len(self.get_orphan_files()),
            'leaf_files': len(self.get_leaf_files()),
            'root_files': len(self.get_root_files()),
            'circular_dependencies': len(self.find_circular_dependencies()),
        }

        # Average dependencies per file
        if stats['total_files'] > 0:
            stats['avg_dependencies'] = stats['total_dependencies'] / stats['total_files']
        else:
            stats['avg_dependencies'] = 0.0

        return stats
