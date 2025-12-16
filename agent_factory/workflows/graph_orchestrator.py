"""
Graph Orchestrator - LangGraph-based Multi-Agent Workflows

Implements advanced agent collaboration using LangGraph's StateGraph.
Agents pass context to each other, share discoveries, and build on
previous work for remarkable results.

Key Features:
- Shared state across agent pipeline
- Conditional routing based on quality gates
- Automatic retries with context from failures
- Visual workflow debugging support
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class AgentState(TypedDict):
    """
    Shared state that flows through the agent workflow.

    Each agent reads from and writes to this state, enabling
    context sharing and collaborative problem-solving.

    Attributes:
        query: Original user query
        context: Accumulated context from all agents (append-only list)
        findings: Discoveries made by each agent
        current_step: Which agent is currently processing
        final_answer: The complete response to return to user
        errors: Any errors encountered during workflow
        quality_score: Current quality assessment (0.0-1.0)
        retry_count: Number of retries attempted
        metadata: Additional workflow metadata
    """
    query: str
    context: Annotated[List[str], operator.add]  # Accumulate context from all agents
    findings: Dict[str, Any]  # {agent_name: discoveries}
    current_step: str
    final_answer: str
    errors: List[str]
    quality_score: float
    retry_count: int
    metadata: Dict[str, Any]


class GraphOrchestrator:
    """
    Advanced multi-agent orchestrator using LangGraph.

    Coordinates multiple specialized agents in workflows where:
    - Agents pass context to each other
    - Quality gates prevent bad answers
    - Failed attempts teach subsequent retries
    - Visual debugging of agent workflows

    Example:
        >>> orch = GraphOrchestrator()
        >>> workflow = orch.create_research_workflow(agents)
        >>> result = workflow.invoke({"query": "What is a PLC?"})
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize graph orchestrator.

        Args:
            verbose: Print workflow progress to console
        """
        self.verbose = verbose

    def _log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(f"[GraphOrchestrator] {message}")

    def create_research_workflow(
        self,
        agents: Dict[str, Any],
        quality_threshold: float = 0.7,
        max_retries: int = 2
    ) -> Any:
        """
        Create a research workflow with quality gates.

        Workflow:
        1. Planner: Decides what to research
        2. Researcher: Finds information
        3. Analyzer: Evaluates quality
        4. Writer: Formats final answer

        Quality gate after analyzer:
        - If quality_score > threshold → proceed to writer
        - Else → retry research with context from failure

        Args:
            agents: Dict of agent names to agent executors
            quality_threshold: Minimum quality score to proceed (0.0-1.0)
            max_retries: Maximum number of research retries

        Returns:
            Compiled LangGraph workflow

        Example:
            >>> agents = {
            ...     "planner": planner_agent,
            ...     "researcher": research_agent,
            ...     "analyzer": analysis_agent,
            ...     "writer": writer_agent
            ... }
            >>> workflow = orch.create_research_workflow(agents)
            >>> result = workflow.invoke({
            ...     "query": "How does a PLC scan cycle work?",
            ...     "context": [],
            ...     "findings": {},
            ...     "errors": [],
            ...     "retry_count": 0
            ... })
        """
        workflow = StateGraph(AgentState)

        # Node implementations
        def plan_research(state: AgentState) -> AgentState:
            """
            Planning agent decides what to research.

            Updates state with:
            - Research plan
            - Context about what needs to be found
            """
            self._log(f"Planning research for: {state['query']}")

            planner = agents.get("planner")
            if not planner:
                state["errors"].append("Planner agent not found")
                state["final_answer"] = "Error: Planning agent not configured"
                return state

            try:
                # Invoke planner with query
                result = planner.invoke({"input": state["query"]})
                output = result.get("output", str(result))

                # Update state
                state["context"].append(f"Research Plan: {output}")
                state["findings"]["plan"] = output
                state["current_step"] = "planner"

                self._log(f"Research plan created")

            except Exception as e:
                self._log(f"Planning failed: {e}")
                state["errors"].append(f"Planning error: {str(e)}")

            return state

        def execute_research(state: AgentState) -> AgentState:
            """
            Research agent finds information.

            Uses context from:
            - Original query
            - Research plan
            - Previous failed attempts (if any)
            """
            self._log(f"Executing research (attempt {state.get('retry_count', 0) + 1})")

            researcher = agents.get("researcher")
            if not researcher:
                state["errors"].append("Researcher agent not found")
                state["final_answer"] = "Error: Research agent not configured"
                return state

            try:
                # Build enhanced query with context
                context_str = "\n".join(state.get("context", []))
                enhanced_query = f"""
Original Query: {state['query']}

Research Context:
{context_str}

Previous Attempts: {state.get('retry_count', 0)}
                """.strip()

                # Invoke researcher
                result = researcher.invoke({"input": enhanced_query})
                output = result.get("output", str(result))

                # Update state
                state["context"].append(f"Research Findings: {output}")
                state["findings"]["research"] = output
                state["current_step"] = "researcher"

                self._log(f"Research completed")

            except Exception as e:
                self._log(f"Research failed: {e}")
                state["errors"].append(f"Research error: {str(e)}")

            return state

        def analyze_findings(state: AgentState) -> AgentState:
            """
            Analyzer agent evaluates research quality.

            Produces:
            - Quality score (0.0-1.0)
            - Feedback for improvement (if quality low)
            """
            self._log("Analyzing research quality")

            analyzer = agents.get("analyzer")
            if not analyzer:
                # No analyzer = assume quality is good
                state["quality_score"] = 0.9
                state["findings"]["analysis"] = "No analysis performed (analyzer not configured)"
                return state

            try:
                # Build analysis prompt with findings
                research_findings = state.get("findings", {}).get("research", "No findings")

                analysis_query = f"""
Evaluate the quality of these research findings for the query: "{state['query']}"

Research Findings:
{research_findings}

Provide:
1. Quality score (0.0-1.0)
2. What's good
3. What's missing
4. Suggestions for improvement
                """.strip()

                # Invoke analyzer
                result = analyzer.invoke({"input": analysis_query})
                output = result.get("output", str(result))

                # Extract quality score (simple heuristic - look for "score: X.X" in output)
                import re
                score_match = re.search(r'score:?\s*(\d+\.?\d*)', output.lower())
                if score_match:
                    quality_score = float(score_match.group(1))
                    if quality_score > 1.0:  # Normalize if given as percentage
                        quality_score = quality_score / 100.0
                else:
                    # No score found - use default based on output length
                    quality_score = min(len(output) / 500.0, 1.0)

                # Update state
                state["context"].append(f"Quality Analysis: {output}")
                state["findings"]["analysis"] = output
                state["quality_score"] = quality_score
                state["current_step"] = "analyzer"

                self._log(f"Analysis complete (quality: {quality_score:.2f})")

            except Exception as e:
                self._log(f"Analysis failed: {e}")
                state["errors"].append(f"Analysis error: {str(e)}")
                state["quality_score"] = 0.5  # Default to medium quality

            return state

        def write_answer(state: AgentState) -> AgentState:
            """
            Writer agent formats final answer.

            Combines:
            - Original query
            - Research findings
            - Analysis insights
            - Quality improvements
            """
            self._log("Writing final answer")

            writer = agents.get("writer")
            if not writer:
                # No writer = return research findings directly
                state["final_answer"] = state.get("findings", {}).get("research", "No answer available")
                return state

            try:
                # Build comprehensive writing prompt
                context_str = "\n\n".join(state.get("context", []))

                writing_query = f"""
Create a comprehensive answer to this query: "{state['query']}"

Available Context:
{context_str}

Requirements:
- Clear and well-structured
- Cite sources from research
- Address all aspects of the query
- Professional tone
                """.strip()

                # Invoke writer
                result = writer.invoke({"input": writing_query})
                output = result.get("output", str(result))

                # Update state
                state["final_answer"] = output
                state["current_step"] = "writer"

                self._log("Final answer written")

            except Exception as e:
                self._log(f"Writing failed: {e}")
                state["errors"].append(f"Writing error: {str(e)}")
                state["final_answer"] = "Error generating final answer"

            return state

        # Add nodes to workflow
        workflow.add_node("planner", plan_research)
        workflow.add_node("researcher", execute_research)
        workflow.add_node("analyzer", analyze_findings)
        workflow.add_node("writer", write_answer)

        # Define workflow edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "analyzer")

        # Conditional edge after analyzer (quality gate)
        def should_retry(state: AgentState) -> Literal["writer", "researcher", "end"]:
            """
            Decide whether to proceed to writer or retry research.

            Logic:
            - If quality >= threshold → proceed to writer
            - Elif retry_count < max_retries → retry research
            - Else → end (max retries exceeded, use what we have)
            """
            quality = state.get("quality_score", 0.0)
            retry_count = state.get("retry_count", 0)

            if quality >= quality_threshold:
                return "writer"
            elif retry_count < max_retries:
                state["retry_count"] = retry_count + 1
                state["context"].append(
                    f"Quality below threshold ({quality:.2f} < {quality_threshold}). Retrying research..."
                )
                return "researcher"
            else:
                # Max retries exceeded - write answer with what we have
                state["context"].append(
                    f"Max retries ({max_retries}) exceeded. Proceeding with available information..."
                )
                return "writer"

        workflow.add_conditional_edges(
            "analyzer",
            should_retry,
            {
                "writer": "writer",
                "researcher": "researcher"
            }
        )

        workflow.add_edge("writer", END)

        # Compile and return
        return workflow.compile()


# Convenience function for creating research workflow
def create_research_workflow(
    agents: Dict[str, Any],
    quality_threshold: float = 0.7,
    max_retries: int = 2,
    verbose: bool = True
) -> Any:
    """
    Create a research workflow with quality gates.

    Convenience function that creates GraphOrchestrator
    and builds research workflow.

    Args:
        agents: Dict of {agent_name: agent_executor}
        quality_threshold: Minimum quality to proceed (0.0-1.0)
        max_retries: Maximum research retries
        verbose: Print workflow progress

    Returns:
        Compiled LangGraph workflow ready to invoke

    Example:
        >>> workflow = create_research_workflow({
        ...     "planner": planner_agent,
        ...     "researcher": research_agent,
        ...     "analyzer": analysis_agent,
        ...     "writer": writer_agent
        ... })
        >>> result = workflow.invoke({
        ...     "query": "Explain PLC scan cycle",
        ...     "context": [],
        ...     "findings": {},
        ...     "errors": [],
        ...     "retry_count": 0,
        ...     "quality_score": 0.0,
        ...     "current_step": "",
        ...     "final_answer": "",
        ...     "metadata": {}
        ... })
        >>> print(result["final_answer"])
    """
    orch = GraphOrchestrator(verbose=verbose)
    return orch.create_research_workflow(
        agents=agents,
        quality_threshold=quality_threshold,
        max_retries=max_retries
    )
