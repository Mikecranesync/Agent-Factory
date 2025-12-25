# Telegram → Agent Routing Logic

Complete guide for mapping Telegram messages to your multi-agent system.

---

## 🎯 Available Agents in Your System

### Production Agents (Active)
1. **RivetOrchestrator** - Industrial maintenance AI (Routes A/B/C/D)
   - Siemens SME Agent
   - Rockwell SME Agent
   - Generic SME Agent
   - Safety Agent

2. **GapDetector** - Knowledge gap analysis + ingestion triggers

3. **ResearchPipeline** - Forum scraping + document ingestion

4. **TwinAgent** - Codebase analysis + project understanding

5. **AgentFactory** - General-purpose agent builder

### Specialized Agents (Available)
- Data Ingest Agent (FieldEye)
- Agent Editor (CLI)
- Admin Panel Agents (Telegram)

---

## 📋 Routing Patterns (4 Options)

### Pattern 1: Command-Based Routing (Explicit)
**Best for:** Clear separation of agent responsibilities

```python
# File: agent_factory/integrations/telegram/multi_agent_bot.py

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import all your agents
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.refs.twin_agent import TwinAgent
from agent_factory.rivet_pro.research.research_pipeline import ResearchPipeline
from agent_factory.core.database_manager import DatabaseManager

# Initialize agents globally
rivet_orchestrator = None
twin_agent = None
db = None


async def init_agents(app: Application):
    """Initialize all agents on bot startup."""
    global rivet_orchestrator, twin_agent, db

    db = DatabaseManager()
    rivet_orchestrator = RivetOrchestrator(rag_layer=db)
    twin_agent = TwinAgent()

    logger.info("All agents initialized")


# ROUTE 1: /rivet <query> → RivetOrchestrator
async def cmd_rivet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route to industrial maintenance AI."""
    query = ' '.join(context.args) if context.args else update.message.text

    from agent_factory.rivet_pro.models import create_text_request, ChannelType
    request = create_text_request(
        text=query,
        user_id=str(update.effective_user.id),
        channel=ChannelType.TELEGRAM
    )

    result = await rivet_orchestrator.route_query(request)
    await update.message.reply_text(result.text)


# ROUTE 2: /twin <question> → TwinAgent
async def cmd_twin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route to codebase analysis agent."""
    query = ' '.join(context.args) if context.args else update.message.text

    # Twin agent analyzes project structure
    response = await twin_agent.query(query)
    await update.message.reply_text(response)


# ROUTE 3: /research <topic> → ResearchPipeline
async def cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route to research/ingestion pipeline."""
    topic = ' '.join(context.args) if context.args else update.message.text

    # Create intent from topic
    from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType, KBCoverage
    intent = RivetIntent(
        vendor=VendorType.GENERIC,
        equipment_type=EquipmentType.UNKNOWN,
        symptom=topic,
        raw_summary=topic,
        context_source="telegram",
        confidence=0.8,
        kb_coverage=KBCoverage.NONE
    )

    pipeline = ResearchPipeline(db_manager=db)
    result = pipeline.run(intent)

    await update.message.reply_text(
        f"Research triggered!\n\n"
        f"Sources found: {len(result.sources_found)}\n"
        f"Queued for ingestion: {result.sources_queued}\n"
        f"Estimated completion: {result.estimated_completion}"
    )


# ROUTE 4: /code <request> → AgentFactory
async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route to code generation agent."""
    request = ' '.join(context.args) if context.args else update.message.text

    from agent_factory.core.agent_factory import AgentFactory
    factory = AgentFactory()

    # Create a coding agent
    coding_agent = factory.create_agent(
        role="Python Code Generator",
        goal=f"Generate code for: {request}",
        tools_list=[]
    )

    result = coding_agent.invoke({"input": request})
    await update.message.reply_text(f"```python\n{result}\n```", parse_mode="Markdown")


# ROUTE 5: Default (no command) → Intent Detection → Route
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-route based on message intent."""
    text = update.message.text

    # Simple keyword-based routing
    if any(word in text.lower() for word in ['plc', 'motor', 'vfd', 'drive', 'fault', 'error']):
        # Industrial maintenance query → RivetOrchestrator
        await cmd_rivet(update, context)

    elif any(word in text.lower() for word in ['code', 'function', 'class', 'file', 'project']):
        # Codebase question → TwinAgent
        await cmd_twin(update, context)

    elif any(word in text.lower() for word in ['research', 'find', 'scrape', 'ingest']):
        # Research request → ResearchPipeline
        await cmd_research(update, context)

    else:
        # Default → RivetOrchestrator (most common use case)
        await cmd_rivet(update, context)


# Setup bot
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Initialize agents
    app.post_init = init_agents

    # Register command handlers
    app.add_handler(CommandHandler("rivet", cmd_rivet))
    app.add_handler(CommandHandler("twin", cmd_twin))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("code", cmd_code))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))

    # Default message handler (auto-routing)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
```

---

### Pattern 2: Intent-Based Routing (Smart)
**Best for:** Natural conversation flow (no commands needed)

```python
# File: agent_factory/integrations/telegram/intent_router.py

import re
from typing import Tuple, Optional
from enum import Enum


class AgentIntent(str, Enum):
    """Detected user intents."""
    INDUSTRIAL_MAINTENANCE = "industrial_maintenance"
    CODE_ANALYSIS = "code_analysis"
    RESEARCH_INQUIRY = "research_inquiry"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"


class IntentRouter:
    """Detect user intent and route to appropriate agent."""

    # Intent detection patterns
    PATTERNS = {
        AgentIntent.INDUSTRIAL_MAINTENANCE: [
            r'\b(plc|vfd|drive|motor|hmi|scada)\b',
            r'\b(fault|error|alarm|code|F\d{3,5})\b',
            r'\b(siemens|rockwell|allen.bradley|mitsubishi|omron)\b',
            r'\b(troubleshoot|diagnose|repair|fix)\b',
        ],
        AgentIntent.CODE_ANALYSIS: [
            r'\b(code|function|class|method|file|directory)\b',
            r'\b(python|javascript|java|c\+\+)\b',
            r'\b(bug|debug|refactor|implement)\b',
            r'\bwhere.*(defined|implemented|located)\b',
        ],
        AgentIntent.RESEARCH_INQUIRY: [
            r'\b(research|find|search|scrape|ingest)\b',
            r'\b(documentation|manual|datasheet|spec)\b',
            r'\b(forum|stackoverflow|reddit)\b',
        ],
    }

    def detect_intent(self, text: str) -> Tuple[AgentIntent, float]:
        """
        Detect user intent from message text.

        Returns:
            (intent, confidence) where confidence is 0-1
        """
        text_lower = text.lower()
        scores = {}

        # Score each intent
        for intent, patterns in self.PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matches += 1

            # Confidence = % of patterns matched
            confidence = matches / len(patterns) if patterns else 0
            scores[intent] = confidence

        # Return highest scoring intent
        if scores:
            best_intent = max(scores, key=scores.get)
            best_confidence = scores[best_intent]

            if best_confidence > 0.3:  # Threshold
                return (best_intent, best_confidence)

        # Default to general question
        return (AgentIntent.GENERAL_QUESTION, 0.5)

    async def route(self, text: str, update: Update) -> str:
        """
        Route message to appropriate agent based on detected intent.

        Returns:
            Agent response text
        """
        intent, confidence = self.detect_intent(text)

        logger.info(f"Intent detected: {intent.value} (confidence: {confidence:.2f})")

        # Route to appropriate agent
        if intent == AgentIntent.INDUSTRIAL_MAINTENANCE:
            return await self._route_to_rivet(text, update)

        elif intent == AgentIntent.CODE_ANALYSIS:
            return await self._route_to_twin(text, update)

        elif intent == AgentIntent.RESEARCH_INQUIRY:
            return await self._route_to_research(text, update)

        else:
            # Default: RivetOrchestrator (most versatile)
            return await self._route_to_rivet(text, update)

    async def _route_to_rivet(self, text: str, update: Update) -> str:
        """Route to RivetOrchestrator."""
        # Same as Pattern 1 cmd_rivet
        pass

    async def _route_to_twin(self, text: str, update: Update) -> str:
        """Route to TwinAgent."""
        # Same as Pattern 1 cmd_twin
        pass

    async def _route_to_research(self, text: str, update: Update) -> str:
        """Route to ResearchPipeline."""
        # Same as Pattern 1 cmd_research
        pass


# Usage in bot
intent_router = IntentRouter()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-route based on intent detection."""
    text = update.message.text
    response = await intent_router.route(text, update)
    await update.message.reply_text(response)
```

---

### Pattern 3: Hybrid Routing (Commands + Auto-Intent)
**Best for:** Power users (commands) + casual users (auto-routing)

```python
# File: agent_factory/integrations/telegram/hybrid_bot.py

"""
Hybrid routing bot:
- Commands: /rivet, /twin, /research → Explicit routing
- No command: Auto-detect intent → Smart routing
- Fallback: RivetOrchestrator (default)
"""

from agent_factory.integrations.telegram.intent_router import IntentRouter

intent_router = IntentRouter()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Hybrid routing logic:
    1. Check if command was used (handled by CommandHandler)
    2. If no command, detect intent and route automatically
    """
    text = update.message.text

    # Auto-route based on intent
    response = await intent_router.route(text, update)

    # Send response
    await update.message.reply_text(response)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # EXPLICIT ROUTING: Commands (optional, for power users)
    app.add_handler(CommandHandler("rivet", cmd_rivet))
    app.add_handler(CommandHandler("twin", cmd_twin))
    app.add_handler(CommandHandler("research", cmd_research))
    app.add_handler(CommandHandler("code", cmd_code))

    # AUTO-ROUTING: No command (for casual users)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
```

**Usage:**
```
User: "Siemens G120 fault F0003"
→ Auto-routes to RivetOrchestrator (industrial intent detected)

User: /twin Where is the database manager defined?
→ Explicit route to TwinAgent (command used)

User: "Find Siemens drive manuals"
→ Auto-routes to ResearchPipeline (research intent detected)
```

---

### Pattern 4: Multi-Agent Orchestrator (Advanced)
**Best for:** Complex queries requiring multiple agents

```python
# File: agent_factory/integrations/telegram/multi_agent_orchestrator.py

from typing import List, Dict
from dataclasses import dataclass


@dataclass
class AgentResponse:
    """Response from a single agent."""
    agent_name: str
    response: str
    confidence: float
    processing_time: float


class MultiAgentOrchestrator:
    """
    Orchestrates multiple agents for a single query.
    - Parallel execution
    - Response aggregation
    - Confidence-based selection
    """

    def __init__(self):
        self.agents = {
            'rivet': RivetOrchestrator(rag_layer=db),
            'twin': TwinAgent(),
            'research': ResearchPipeline(db_manager=db),
        }

    async def query_all_agents(self, text: str) -> List[AgentResponse]:
        """
        Query all agents in parallel and collect responses.

        Returns:
            List of AgentResponse objects
        """
        tasks = []

        # Spawn parallel tasks
        for agent_name, agent in self.agents.items():
            task = self._query_agent(agent_name, agent, text)
            tasks.append(task)

        # Wait for all agents to respond
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        responses = [r for r in results if isinstance(r, AgentResponse)]

        return responses

    async def _query_agent(
        self, agent_name: str, agent, text: str
    ) -> AgentResponse:
        """Query a single agent and measure performance."""
        start = time.time()

        try:
            if agent_name == 'rivet':
                from agent_factory.rivet_pro.models import create_text_request, ChannelType
                request = create_text_request(text=text, user_id="test", channel=ChannelType.TELEGRAM)
                result = await agent.route_query(request)
                response = result.text
                confidence = result.confidence

            elif agent_name == 'twin':
                response = await agent.query(text)
                confidence = 0.7  # Twin agent doesn't return confidence

            elif agent_name == 'research':
                # Research pipeline is synchronous
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, agent.run, text)
                response = f"Found {len(result.sources_found)} sources"
                confidence = 0.6

            processing_time = time.time() - start

            return AgentResponse(
                agent_name=agent_name,
                response=response,
                confidence=confidence,
                processing_time=processing_time
            )

        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            return AgentResponse(
                agent_name=agent_name,
                response=f"Error: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start
            )

    async def select_best_response(
        self, responses: List[AgentResponse]
    ) -> AgentResponse:
        """
        Select best response based on confidence scores.

        Strategy:
        - Highest confidence wins
        - Tie-breaker: Fastest response time
        """
        if not responses:
            return AgentResponse(
                agent_name="fallback",
                response="No agents could process this query.",
                confidence=0.0,
                processing_time=0.0
            )

        # Sort by confidence (desc), then by processing time (asc)
        sorted_responses = sorted(
            responses,
            key=lambda r: (r.confidence, -r.processing_time),
            reverse=True
        )

        return sorted_responses[0]

    async def orchestrate(self, text: str) -> str:
        """
        Main orchestration logic.

        1. Query all agents in parallel
        2. Select best response
        3. Return formatted result
        """
        # Query all agents
        responses = await self.query_all_agents(text)

        # Select best
        best = await self.select_best_response(responses)

        # Format response
        formatted = (
            f"{best.response}\n\n"
            f"_Agent: {best.agent_name} | "
            f"Confidence: {best.confidence:.0%} | "
            f"Time: {best.processing_time:.1f}s_"
        )

        return formatted


# Usage in bot
orchestrator = MultiAgentOrchestrator()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route to multi-agent orchestrator."""
    text = update.message.text
    response = await orchestrator.orchestrate(text)
    await update.message.reply_text(response, parse_mode="Markdown")
```

---

## 🎨 Choosing the Right Pattern

| Pattern | Best For | Complexity | User Experience |
|---------|----------|------------|-----------------|
| **Command-Based** | Clear separation, power users | Low | Explicit (must know commands) |
| **Intent-Based** | Natural conversation | Medium | Seamless (no commands) |
| **Hybrid** | Both power + casual users | Medium | Flexible |
| **Multi-Agent** | Complex queries, best answer | High | Intelligent |

---

## 🚀 Quick Start: Implement Pattern 3 (Hybrid)

**Step 1:** Create intent router
```bash
# File: agent_factory/integrations/telegram/intent_router.py
# Copy Pattern 2 code above
```

**Step 2:** Update orchestrator_bot.py
```python
# Add to imports
from agent_factory.integrations.telegram.intent_router import IntentRouter

# Initialize
intent_router = IntentRouter()

# Replace handle_message with hybrid routing
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    response = await intent_router.route(text, update)
    await update.message.reply_text(response)
```

**Step 3:** Test
```
# Auto-routing (no command)
"Siemens G120 F0003 fault" → Routes to RivetOrchestrator

# Explicit routing (command)
/twin "Where is database manager?" → Routes to TwinAgent
```

---

## 📊 Routing Decision Tree

```
Telegram Message
      │
      ├─ Has Command? (/rivet, /twin, etc.)
      │   └─ YES → Route to specified agent
      │
      └─ NO Command
          │
          ├─ Detect Intent
          │   │
          │   ├─ Industrial keywords? → RivetOrchestrator
          │   ├─ Code keywords? → TwinAgent
          │   ├─ Research keywords? → ResearchPipeline
          │   └─ Unknown → Default (RivetOrchestrator)
          │
          └─ Execute routing
              │
              ├─ Success → Return response
              └─ Error → Fallback agent
```

---

## 🔧 Production Configuration

**Environment Variables:**
```bash
# .env
ORCHESTRATOR_BOT_TOKEN=<your_bot_token>

# Agent-specific configs
RIVET_ENABLED=true
TWIN_ENABLED=true
RESEARCH_ENABLED=true

# Routing settings
DEFAULT_AGENT=rivet
INTENT_CONFIDENCE_THRESHOLD=0.3
MULTI_AGENT_MODE=false  # Enable Pattern 4
```

**Settings:**
```python
# agent_factory/integrations/telegram/config.py

class BotConfig:
    """Telegram bot routing configuration."""

    # Which agents are enabled
    ENABLED_AGENTS = {
        'rivet': True,
        'twin': True,
        'research': True,
        'code': False,  # Disabled by default
    }

    # Default agent when intent unclear
    DEFAULT_AGENT = 'rivet'

    # Intent detection threshold (0-1)
    INTENT_THRESHOLD = 0.3

    # Multi-agent mode (query all agents)
    MULTI_AGENT_MODE = False

    # Response timeout (seconds)
    AGENT_TIMEOUT = 30
```

---

## 📝 Complete Example: Hybrid Bot

```python
# File: agent_factory/integrations/telegram/smart_bot.py

"""
Smart Telegram Bot with Hybrid Routing
- Commands: /rivet, /twin, /research (explicit)
- No command: Auto-intent detection (smart)
- Fallback: RivetOrchestrator (default)
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Your agents
from agent_factory.core.orchestrator import RivetOrchestrator
from agent_factory.refs.twin_agent import TwinAgent
from agent_factory.rivet_pro.research.research_pipeline import ResearchPipeline
from agent_factory.core.database_manager import DatabaseManager
from agent_factory.rivet_pro.models import create_text_request, ChannelType

# Intent router
from agent_factory.integrations.telegram.intent_router import IntentRouter

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("ORCHESTRATOR_BOT_TOKEN")

# Global agents
db = None
rivet = None
twin = None
research = None
intent_router = None


async def init_agents(app: Application):
    """Initialize all agents on startup."""
    global db, rivet, twin, research, intent_router

    db = DatabaseManager()
    rivet = RivetOrchestrator(rag_layer=db)
    twin = TwinAgent()
    research = ResearchPipeline(db_manager=db)
    intent_router = IntentRouter(rivet=rivet, twin=twin, research=research)

    logger.info("All agents initialized successfully")


# COMMAND HANDLERS (Explicit routing)

async def cmd_rivet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explicitly route to RivetOrchestrator."""
    query = ' '.join(context.args) if context.args else "No query provided"

    request = create_text_request(
        text=query,
        user_id=str(update.effective_user.id),
        channel=ChannelType.TELEGRAM
    )

    result = await rivet.route_query(request)
    await update.message.reply_text(result.text)


async def cmd_twin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explicitly route to TwinAgent."""
    query = ' '.join(context.args) if context.args else "No query provided"
    response = await twin.query(query)
    await update.message.reply_text(response)


async def cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explicitly route to ResearchPipeline."""
    topic = ' '.join(context.args) if context.args else "No topic provided"

    # Run research in background
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, research.run, topic)

    await update.message.reply_text(
        f"Research complete!\n"
        f"Sources found: {len(result.sources_found)}\n"
        f"Queued: {result.sources_queued}\n"
        f"Status: {result.status}"
    )


# AUTO-ROUTING (Intent-based)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Auto-route based on intent detection.
    Falls back to RivetOrchestrator if intent unclear.
    """
    text = update.message.text

    # Use intent router to auto-detect and route
    response = await intent_router.route(text, update)

    await update.message.reply_text(response)


# HELP COMMANDS

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message."""
    await update.message.reply_text(
        "**Smart Multi-Agent Bot**\n\n"
        "I can help with:\n"
        "• Industrial maintenance (PLC, VFD, motors)\n"
        "• Code analysis (files, functions, bugs)\n"
        "• Research (documentation, manuals)\n\n"
        "**Commands (optional):**\n"
        "/rivet <query> - Industrial AI\n"
        "/twin <query> - Code analysis\n"
        "/research <topic> - Document search\n\n"
        "Or just ask naturally - I'll figure it out!",
        parse_mode="Markdown"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message."""
    await cmd_start(update, context)


# MAIN

def main():
    """Run the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Initialize agents on startup
    app.post_init = init_agents

    # Command handlers (explicit routing)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("rivet", cmd_rivet))
    app.add_handler(CommandHandler("twin", cmd_twin))
    app.add_handler(CommandHandler("research", cmd_research))

    # Message handler (auto-routing)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    logger.info("Bot started - Hybrid routing active")
    app.run_polling()


if __name__ == "__main__":
    main()
```

---

## 🎯 Summary

**Your routing options:**

1. **Command-Based** → Simple, explicit, user controls routing
2. **Intent-Based** → Smart, automatic, seamless UX
3. **Hybrid** → Best of both (recommended ✅)
4. **Multi-Agent** → Advanced, parallel execution, best answer

**Recommended:** Start with **Pattern 3 (Hybrid)** - gives users flexibility while being smart about defaults.

---

Let me know which pattern you want to implement, and I'll help you set it up!
