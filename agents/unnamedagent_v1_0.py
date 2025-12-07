"""
========================================================================
UNNAMEDAGENT - v1.0
========================================================================

STATUS: DRAFT
CREATED: 2025-12-06
LAST UPDATED: 2025-12-06
OWNER: mike

PURPOSE:
    Discovers high-value market opportunities for selling apps, agents, and
    digital products by analyzing market trends, competitive landscapes,
    customer pain points, and emerging niches. Provides actionable insights
    on where to build and how to position products for maximum market fit.

---

SCOPE:
    In Scope:
        - Search and analyze market trends across tech, AI, automation
        - Identify customer pain points and unmet needs
        - Research competitor products, pricing, positioning
        - Find emerging niches with low competition, high demand
        - Analyze social media, forums, communities for signals
        - Evaluate market size, growth potential, monetization
        - Research successful launches, extract patterns
        - Identify ideal customer profiles and segments
        - Track industry news, funding, market movements
        - Provide specific recommendations with validation data

    Out of Scope:
        - Financial investment decisions or financial advice
        - Access proprietary databases or paid research
        - Guarantee revenue outcomes or ROI predictions
        - Illegal competitive intelligence or espionage
        - Access private company data or confidential info
        - Execute trades, purchases, or transactions
        - Provide legal advice on market entry or IP
        - Auto-build or deploy products based on findings


INVARIANTS:
    1. Evidence-Based:: All claims backed by verifiable sources and data
    2. Ethical Research:: Never recommend exploitative practices or dark patterns
    3. Transparency:: Always disclose when information is uncertain
    4. User Focus:: Prioritize opportunities solving real customer problems
    5. Timeliness:: Focus on current market conditions (data < 6 months old)
    6. Actionability:: Every insight includes specific next steps
    7. Cost Awareness:: API usage must stay under $0.50 per query
    8. Response Speed:: Initial findings < 60s, deep analysis < 5 minutes


WARNING:
    This file is AUTO-GENERATED from specs/unnamedagent-v1.0.md
    Do not edit manually - changes will be overwritten.
    To modify behavior, update the spec and regenerate.

========================================================================
"""

import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core.agent_factory import AgentFactory
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ====================================================================
# DATA MODELS - Pydantic Schemas
# ====================================================================

from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    answer: str = Field(..., description="Agent response")
    confidence: float = Field(..., ge=0.0, le=1.0)

def create_agent(llm_provider: str = "openai", model_name: str = "gpt-4"):
    """
    PURPOSE: Create and configure the UnnamedAgent agent

    WHAT THIS DOES:
        1. Initialize AgentFactory with specified LLM
        2. Load required tools
        3. Create agent with system prompt and tools
        4. Return configured agent

    INPUTS:
        llm_provider (str): LLM provider (openai, anthropic, google)
        model_name (str): Model name (gpt-4, claude-3-sonnet, etc.)

    OUTPUTS:
        Configured agent ready to invoke

    INVARIANTS:
        1. Evidence-Based:: All claims backed by verifiable sources
        2. Ethical Research:: Never recommend exploitative practices
        3. Transparency:: Always disclose uncertainty
        4. User Focus:: Prioritize real customer problems
        5. Timeliness:: Current market conditions (data < 6 months)
        6. Actionability:: Every insight includes next steps
        7. Cost Awareness:: API usage < $0.50 per query
        8. Response Speed:: Initial < 60s, deep analysis < 5min

    """
    # Initialize factory
    factory = AgentFactory(
        default_llm_provider=llm_provider,
        default_model=model_name,
        verbose=False
    )

    # Load tools - FULL POWER MODE
    from agent_factory.tools.research_tools import get_research_tools
    from agent_factory.tools.coding_tools import get_coding_tools

    # Research tools with AI-powered Tavily search
    tools = get_research_tools(
        include_wikipedia=True,
        include_duckduckgo=True,
        include_tavily=True,  # AI-optimized search - ENABLED!
        include_time=True
    )

    # Add file/code tools for competitive analysis
    tools.extend(get_coding_tools(
        include_read=True,      # Read competitor code, docs
        include_write=True,     # Save research reports
        include_list=True,      # Browse directories
        include_git=True,       # Analyze git repos
        include_search=True,    # Search file contents
        base_dir="."
    ))


    # System prompt from spec
    system_prompt = """You are a Market Research Specialist that discovers high-value opportunities for selling apps, agents, and digital products.

Your mission: Analyze market trends, competitive landscapes, customer pain points, and emerging niches. Provide actionable insights on where to build and how to position products for maximum market fit and revenue potential.

RULES (Must never be violated):
1. Evidence-Based: All claims must be backed by verifiable sources and data
2. Ethical Research: Never recommend exploitative practices or dark patterns
3. Transparency: Always disclose when information is uncertain or based on limited data
4. User Focus: Prioritize opportunities that solve real customer problems, not just profit
5. Timeliness: Focus on current market conditions (data < 6 months old when possible)
6. Actionability: Every insight must include specific next steps or validation methods
7. Cost Awareness: Keep API usage under $0.50 per research query
8. Response Speed: Deliver initial findings within 60 seconds

When analyzing markets, always provide:
- Specific niches with market size estimates
- Customer pain points and willingness to pay
- Competition analysis (low/medium/high)
- Concrete validation steps (interviews, MVP timeline, pricing tests)
- Realistic revenue projections with MRR estimates
- Source citations for all market claims"""

    # Create agent with higher iteration limit for complex research
    agent = factory.create_agent(
        role="Market Research Specialist",
        tools_list=tools,
        system_prompt=system_prompt,
        response_schema=AgentResponse,
        max_iterations=25,  # Higher limit for multi-step research tasks
        max_execution_time=300,  # 5 minutes timeout
        metadata={
            "spec_version": "v1.0",
            "spec_file": "bob-1.md",
            "status": "DRAFT",
            "agent_name": "Bob (Market Research Dominator)",
        }
    )

    return agent

def main():
    """
    PURPOSE: Demo function showing agent usage

    WHAT THIS DOES:
        1. Create agent
        2. Run example query
        3. Display response
    """
    print("=" * 72)
    print("BOB - MARKET RESEARCH DOMINATOR")
    print("=" * 72)
    print("\nCreating Market Research Agent...")
    agent = create_agent()

    print("\n[DEMO QUERY] Finding market opportunities...")
    query = "Find 3 underserved niches in the AI agent marketplace that have high willingness to pay but low competition"
    result = agent.invoke({"input": query})

    print(f"\n[QUERY]")
    print(f"{query}\n")
    print(f"[RESPONSE]")
    print(f"{result.get('output', result)}")


if __name__ == "__main__":
    main()