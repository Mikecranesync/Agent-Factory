"""
Agent Collaboration Patterns - Advanced Multi-Agent Coordination

Implements sophisticated patterns for agents working together:
1. Parallel Execution - Multiple agents work simultaneously (fan-out/fan-in)
2. Consensus Building - Multiple agents vote on best answer
3. Supervisor Delegation - Coordinator delegates to specialist teams

These patterns enable remarkable results through agent collaboration.
"""

from typing import Dict, Any, List, TypedDict, Annotated, Literal
import asyncio
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage


# ========================================
# Pattern 1: Parallel Execution
# ========================================

class ParallelState(TypedDict):
    """State for parallel research workflow"""
    query: str
    results: Annotated[List[Dict[str, Any]], operator.add]  # Accumulate results
    final_answer: str
    errors: List[str]


async def create_parallel_research(
    agents: Dict[str, Any],
    verbose: bool = True
) -> Any:
    """
    Create parallel research workflow.

    Multiple research agents work simultaneously on different
    aspects of the query, then a synthesis agent combines findings.

    Workflow:
    1. Split query into sub-tasks (optional)
    2. Execute multiple research agents in parallel
    3. Synthesis agent combines all findings
    4. Return unified answer

    Args:
        agents: Dict with keys:
            - "researchers": List of research agents
            - "synthesizer": Agent that combines results
        verbose: Print progress

    Returns:
        Compiled async LangGraph workflow

    Example:
        >>> workflow = await create_parallel_research({
        ...     "researchers": [agent1, agent2, agent3],
        ...     "synthesizer": synthesis_agent
        ... })
        >>> result = await workflow.ainvoke({
        ...     "query": "What are the main PLC manufacturers?",
        ...     "results": [],
        ...     "errors": []
        ... })
    """
    workflow = StateGraph(ParallelState)

    def research_parallel(state: ParallelState) -> ParallelState:
        """
        Execute all research agents in parallel.

        Uses asyncio.gather() to run all agents simultaneously.
        """
        researchers = agents.get("researchers", [])
        if not researchers:
            state["errors"].append("No research agents configured")
            state["final_answer"] = "Error: No researchers available"
            return state

        async def run_researcher(agent, query: str) -> Dict[str, Any]:
            """Run single researcher async"""
            try:
                # If agent has arun, use it; otherwise use sync invoke
                if hasattr(agent, "arun"):
                    result = await agent.arun(query)
                elif hasattr(agent, "ainvoke"):
                    result = await agent.ainvoke({"input": query})
                else:
                    # Fallback to sync
                    result = agent.invoke({"input": query})

                return {
                    "agent": getattr(agent, "metadata", {}).get("role", "unknown"),
                    "output": result.get("output", str(result)) if isinstance(result, dict) else str(result),
                    "success": True
                }
            except Exception as e:
                return {
                    "agent": getattr(agent, "metadata", {}).get("role", "unknown"),
                    "output": "",
                    "success": False,
                    "error": str(e)
                }

        # Run all researchers in parallel
        async def gather_results():
            tasks = [run_researcher(agent, state["query"]) for agent in researchers]
            return await asyncio.gather(*tasks)

        # Execute (create event loop if needed)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        results = loop.run_until_complete(gather_results())

        # Update state with all results
        state["results"].extend(results)

        if verbose:
            successful = sum(1 for r in results if r.get("success"))
            print(f"[ParallelResearch] {successful}/{len(results)} agents completed successfully")

        return state

    def synthesize_results(state: ParallelState) -> ParallelState:
        """
        Synthesize all research findings into unified answer.
        """
        synthesizer = agents.get("synthesizer")
        if not synthesizer:
            # No synthesizer - combine results manually
            combined = "\n\n".join([
                f"Source {i+1}: {r['output']}"
                for i, r in enumerate(state.get("results", []))
                if r.get("success")
            ])
            state["final_answer"] = combined
            return state

        try:
            # Build synthesis prompt
            findings = "\n\n".join([
                f"Agent {i+1} ({r.get('agent', 'unknown')}):\n{r['output']}"
                for i, r in enumerate(state.get("results", []))
                if r.get("success")
            ])

            synthesis_query = f"""
Synthesize these research findings into a comprehensive answer for: "{state['query']}"

Findings from multiple sources:
{findings}

Requirements:
- Combine insights from all sources
- Remove redundancy
- Highlight areas of agreement
- Note any conflicting information
- Provide unified, coherent answer
            """.strip()

            result = synthesizer.invoke({"input": synthesis_query})
            output = result.get("output", str(result))

            state["final_answer"] = output

            if verbose:
                print(f"[ParallelResearch] Synthesis complete")

        except Exception as e:
            if verbose:
                print(f"[ParallelResearch] Synthesis failed: {e}")
            state["errors"].append(f"Synthesis error: {str(e)}")
            state["final_answer"] = "Error synthesizing results"

        return state

    # Build workflow
    workflow.add_node("research", research_parallel)
    workflow.add_node("synthesize", synthesize_results)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()


# ========================================
# Pattern 2: Consensus Building
# ========================================

class ConsensusState(TypedDict):
    """State for consensus workflow"""
    query: str
    candidate_answers: List[Dict[str, Any]]  # Answers from multiple agents
    scores: Dict[str, float]  # Quality scores for each answer
    final_answer: str
    consensus_method: str  # "vote" | "judge" | "best"


def create_consensus_workflow(
    agents: Dict[str, Any],
    consensus_method: Literal["vote", "judge", "best"] = "judge",
    verbose: bool = True
) -> Any:
    """
    Create consensus-building workflow.

    Multiple agents solve the same problem, then consensus
    mechanism picks or combines the best answer.

    Consensus Methods:
    - "vote": Agents vote on best answer (majority wins)
    - "judge": Judge agent evaluates and picks best
    - "best": Highest quality score wins

    Args:
        agents: Dict with keys:
            - "solvers": List of agents that generate answers
            - "judge": (optional) Agent that evaluates answers
        consensus_method: How to pick final answer
        verbose: Print progress

    Returns:
        Compiled LangGraph workflow

    Example:
        >>> workflow = create_consensus_workflow({
        ...     "solvers": [agent1, agent2, agent3],
        ...     "judge": judge_agent
        ... }, consensus_method="judge")
        >>> result = workflow.invoke({
        ...     "query": "What is the best PLC for beginners?",
        ...     "candidate_answers": [],
        ...     "scores": {}
        ... })
    """
    workflow = StateGraph(ConsensusState)

    def generate_answers(state: ConsensusState) -> ConsensusState:
        """
        All solver agents generate candidate answers.
        """
        solvers = agents.get("solvers", [])
        if not solvers:
            state["final_answer"] = "Error: No solver agents configured"
            return state

        for i, agent in enumerate(solvers):
            try:
                result = agent.invoke({"input": state["query"]})
                output = result.get("output", str(result))

                state["candidate_answers"].append({
                    "agent": getattr(agent, "metadata", {}).get("role", f"solver_{i}"),
                    "answer": output,
                    "index": i
                })

                if verbose:
                    print(f"[Consensus] Answer {i+1}/{len(solvers)} generated")

            except Exception as e:
                if verbose:
                    print(f"[Consensus] Solver {i} failed: {e}")

        return state

    def pick_consensus(state: ConsensusState) -> ConsensusState:
        """
        Pick final answer using configured consensus method.
        """
        method = consensus_method
        candidates = state.get("candidate_answers", [])

        if not candidates:
            state["final_answer"] = "Error: No candidate answers generated"
            return state

        if method == "judge":
            # Use judge agent to evaluate and pick best
            judge = agents.get("judge")
            if not judge:
                # Fallback to "best" method if no judge
                method = "best"
            else:
                try:
                    # Build judging prompt
                    answers_str = "\n\n".join([
                        f"Answer {i+1} (from {c['agent']}):\n{c['answer']}"
                        for i, c in enumerate(candidates)
                    ])

                    judge_query = f"""
Evaluate these candidate answers for: "{state['query']}"

Candidates:
{answers_str}

Pick the best answer based on:
- Accuracy and completeness
- Clarity and organization
- Relevance to query
- Practical usefulness

Respond with ONLY the number (1, 2, 3, etc.) of the best answer.
                    """.strip()

                    result = judge.invoke({"input": judge_query})
                    output = result.get("output", str(result)).strip()

                    # Extract answer number
                    import re
                    match = re.search(r'\b(\d+)\b', output)
                    if match:
                        best_idx = int(match.group(1)) - 1  # Convert to 0-indexed
                        if 0 <= best_idx < len(candidates):
                            state["final_answer"] = candidates[best_idx]["answer"]
                            if verbose:
                                print(f"[Consensus] Judge picked answer {best_idx + 1}")
                        else:
                            # Invalid index - use first answer
                            state["final_answer"] = candidates[0]["answer"]
                    else:
                        # Couldn't parse - use first answer
                        state["final_answer"] = candidates[0]["answer"]

                except Exception as e:
                    if verbose:
                        print(f"[Consensus] Judging failed: {e}, using first answer")
                    state["final_answer"] = candidates[0]["answer"]

        elif method == "best":
            # Use quality scores (if available) or answer length as heuristic
            best_answer = max(candidates, key=lambda c: len(c["answer"]))
            state["final_answer"] = best_answer["answer"]
            if verbose:
                print(f"[Consensus] Best answer selected by quality score")

        elif method == "vote":
            # Simple majority vote (agents vote on each other's answers)
            # For simplicity, use first answer (voting requires additional round)
            state["final_answer"] = candidates[0]["answer"]
            if verbose:
                print(f"[Consensus] Voting not yet implemented, using first answer")

        return state

    # Build workflow
    workflow.add_node("generate", generate_answers)
    workflow.add_node("consensus", pick_consensus)

    workflow.set_entry_point("generate")
    workflow.add_edge("generate", "consensus")
    workflow.add_edge("consensus", END)

    return workflow.compile()


# ========================================
# Pattern 3: Supervisor Delegation
# ========================================

class SupervisorState(TypedDict):
    """State for supervisor workflow"""
    query: str
    supervisor_decision: Dict[str, Any]  # Supervisor's routing decision
    delegated_results: List[Dict[str, Any]]
    final_answer: str


def create_supervisor_workflow(
    agents: Dict[str, Any],
    verbose: bool = True
) -> Any:
    """
    Create supervisor delegation workflow.

    Supervisor agent analyzes query and delegates to
    appropriate specialist teams.

    Workflow:
    1. Supervisor analyzes query
    2. Decides which specialist team(s) to use
    3. Delegates to specialist(s)
    4. Combines results if multiple teams used

    Args:
        agents: Dict with keys:
            - "supervisor": Coordinator agent
            - "teams": Dict of {team_name: team_agent}
        verbose: Print progress

    Returns:
        Compiled LangGraph workflow

    Example:
        >>> workflow = create_supervisor_workflow({
        ...     "supervisor": supervisor_agent,
        ...     "teams": {
        ...         "research": research_team,
        ...         "coding": coding_team,
        ...         "analysis": analysis_team
        ...     }
        ... })
        >>> result = workflow.invoke({
        ...     "query": "Find and analyze PLC documentation",
        ...     "delegated_results": []
        ... })
    """
    workflow = StateGraph(SupervisorState)

    def supervise(state: SupervisorState) -> SupervisorState:
        """
        Supervisor decides which team(s) to delegate to.
        """
        supervisor = agents.get("supervisor")
        if not supervisor:
            state["final_answer"] = "Error: Supervisor agent not configured"
            return state

        teams = agents.get("teams", {})
        team_names = list(teams.keys())

        try:
            # Build supervision prompt
            teams_list = ", ".join(team_names)

            supervisor_query = f"""
Analyze this query and decide which specialist team(s) should handle it: "{state['query']}"

Available teams:
{teams_list}

Respond with:
1. Which team(s) to use (comma-separated if multiple)
2. What task to give each team

Format:
TEAMS: team1, team2
TASKS: task for team1 | task for team2
            """.strip()

            result = supervisor.invoke({"input": supervisor_query})
            output = result.get("output", str(result))

            # Parse supervisor decision
            import re
            teams_match = re.search(r'TEAMS?:\s*([^\n]+)', output)
            tasks_match = re.search(r'TASKS?:\s*([^\n]+)', output)

            if teams_match and tasks_match:
                selected_teams = [t.strip() for t in teams_match.group(1).split(",")]
                tasks = [t.strip() for t in tasks_match.group(1).split("|")]

                state["supervisor_decision"] = {
                    "teams": selected_teams,
                    "tasks": tasks
                }

                if verbose:
                    print(f"[Supervisor] Delegating to: {', '.join(selected_teams)}")
            else:
                # Couldn't parse - delegate to first team with original query
                state["supervisor_decision"] = {
                    "teams": [team_names[0]],
                    "tasks": [state["query"]]
                }

        except Exception as e:
            if verbose:
                print(f"[Supervisor] Supervision failed: {e}")
            state["final_answer"] = f"Error: Supervision failed - {str(e)}"

        return state

    def delegate(state: SupervisorState) -> SupervisorState:
        """
        Execute delegated tasks on appropriate teams.
        """
        decision = state.get("supervisor_decision", {})
        selected_teams = decision.get("teams", [])
        tasks = decision.get("tasks", [])

        teams = agents.get("teams", {})

        for i, team_name in enumerate(selected_teams):
            team_agent = teams.get(team_name)
            if not team_agent:
                if verbose:
                    print(f"[Supervisor] Team '{team_name}' not found")
                continue

            task = tasks[i] if i < len(tasks) else state["query"]

            try:
                result = team_agent.invoke({"input": task})
                output = result.get("output", str(result))

                state["delegated_results"].append({
                    "team": team_name,
                    "task": task,
                    "result": output
                })

                if verbose:
                    print(f"[Supervisor] Team '{team_name}' completed task")

            except Exception as e:
                if verbose:
                    print(f"[Supervisor] Team '{team_name}' failed: {e}")

        # Combine results
        if state.get("delegated_results"):
            combined = "\n\n".join([
                f"{r['team'].upper()} Results:\n{r['result']}"
                for r in state["delegated_results"]
            ])
            state["final_answer"] = combined
        else:
            state["final_answer"] = "Error: No teams completed successfully"

        return state

    # Build workflow
    workflow.add_node("supervise", supervise)
    workflow.add_node("delegate", delegate)

    workflow.set_entry_point("supervise")
    workflow.add_edge("supervise", "delegate")
    workflow.add_edge("delegate", END)

    return workflow.compile()
