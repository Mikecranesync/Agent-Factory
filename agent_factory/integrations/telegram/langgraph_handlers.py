"""
LangGraph Telegram Handlers - Multi-Agent Workflows in Telegram

Provides Telegram commands for advanced multi-agent workflows with full observability:
- /research <query> - Research → Analyze → Write pipeline with quality gates
- /consensus <query> - Multiple agents vote on best answer
- /analyze <query> - Supervisor routes to specialist teams

All workflows are traced with LangFuse for full observability.
Users receive results + trace links to see detailed execution.

Commands:
    /research What is a PLC? - Run research workflow
    /consensus Best PLC for beginners? - 3 agents + judge
    /analyze PLC troubleshooting guide - Supervisor delegation
"""

import os
import asyncio
from typing import Optional
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.workflows import (
    create_research_workflow,
    create_consensus_workflow,
    create_supervisor_workflow
)
from agent_factory.observability import LangFuseTracker


class LangGraphHandlers:
    """
    Telegram handlers for LangGraph multi-agent workflows.

    Enables users to run sophisticated multi-agent workflows
    directly from Telegram with full observability.
    """

    def __init__(self):
        """Initialize handlers with agent factory and tracker"""
        self.factory = AgentFactory()

        # Try to initialize LangFuse tracker
        try:
            self.tracker = LangFuseTracker()
            self.observability_enabled = True
        except ValueError:
            # LangFuse not configured - workflows still work, just no traces
            self.tracker = None
            self.observability_enabled = False

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /research <query> - Run research workflow with quality gates.

        Workflow: Planner → Researcher → Analyzer → Writer
        Quality gate: Retries if quality < 0.7

        Example:
            /research What is a PLC and what are the main manufacturers?
        """
        user_id = str(update.effective_user.id)
        query = " ".join(context.args) if context.args else ""

        if not query:
            await update.message.reply_text(
                "❌ *Usage:* `/research <your question>`\n\n"
                "*Example:*\n"
                "`/research What is a PLC?`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send initial message
        status_msg = await update.message.reply_text(
            "🔄 *Running Research Workflow*\n\n"
            f"Query: _{query}_\n\n"
            "Step 1/4: Planning research strategy...",
            parse_mode=ParseMode.MARKDOWN
        )

        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        try:
            # Get LangFuse callback if available
            callback = None
            if self.observability_enabled:
                session_id = f"telegram_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                callback = self.tracker.get_callback(session_id=session_id, user_id=user_id)

            # Create agents with optional callback
            callbacks = [callback] if callback else []

            planner = self.factory.create_agent(
                role="Research Planner",
                goal="Decide what to research",
                backstory="Expert at breaking down complex questions",
                verbose=False,
                callbacks=callbacks
            )

            # Update status
            await status_msg.edit_text(
                "🔄 *Running Research Workflow*\n\n"
                f"Query: _{query}_\n\n"
                "Step 1/4: Planning research strategy ✅\n"
                "Step 2/4: Finding information...",
                parse_mode=ParseMode.MARKDOWN
            )

            researcher = self.factory.create_agent(
                role="Researcher",
                goal="Find accurate information",
                backstory="Skilled at finding reliable sources",
                verbose=False,
                callbacks=callbacks
            )

            # Update status
            await status_msg.edit_text(
                "🔄 *Running Research Workflow*\n\n"
                f"Query: _{query}_\n\n"
                "Step 1/4: Planning research strategy ✅\n"
                "Step 2/4: Finding information ✅\n"
                "Step 3/4: Analyzing quality...",
                parse_mode=ParseMode.MARKDOWN
            )

            analyzer = self.factory.create_agent(
                role="Quality Analyzer",
                goal="Evaluate research quality",
                backstory="Critical thinker who ensures accuracy",
                verbose=False,
                callbacks=callbacks
            )

            writer = self.factory.create_agent(
                role="Technical Writer",
                goal="Create clear answers",
                backstory="Technical writer who explains simply",
                verbose=False,
                callbacks=callbacks
            )

            # Create and execute workflow
            workflow = create_research_workflow(
                agents={
                    "planner": planner,
                    "researcher": researcher,
                    "analyzer": analyzer,
                    "writer": writer
                },
                quality_threshold=0.7,
                max_retries=2,
                verbose=False
            )

            # Execute workflow
            start_time = datetime.now()
            result = workflow.invoke({
                "query": query,
                "context": [],
                "findings": {},
                "errors": [],
                "retry_count": 0,
                "quality_score": 0.0,
                "current_step": "",
                "final_answer": "",
                "metadata": {}
            })
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Update status - analyzing
            quality_score = result.get("quality_score", 0.0)
            await status_msg.edit_text(
                "🔄 *Running Research Workflow*\n\n"
                f"Query: _{query}_\n\n"
                "Step 1/4: Planning research strategy ✅\n"
                "Step 2/4: Finding information ✅\n"
                f"Step 3/4: Analyzing quality (Score: {quality_score:.2f}) ✅\n"
                "Step 4/4: Writing answer...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Small delay for effect
            await asyncio.sleep(0.5)

            # Final update
            final_answer = result.get("final_answer", "No answer generated")
            retry_count = result.get("retry_count", 0)

            # Build response
            response = (
                "✅ *Research Workflow Complete*\n\n"
                f"*Answer:*\n{final_answer}\n\n"
                f"*Quality Score:* {quality_score:.2f}/1.0\n"
                f"*Processing Time:* {duration:.1f}s\n"
                f"*Retries:* {retry_count}"
            )

            # Add trace link if available
            if self.observability_enabled and self.tracker:
                self.tracker.flush()
                trace_link = self.tracker.get_trace_link()
                if trace_link:
                    response += f"\n\n📊 [View Detailed Trace]({trace_link})"

            await status_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            await status_msg.edit_text(
                f"❌ *Workflow Failed*\n\n"
                f"Error: {str(e)}\n\n"
                "Please try again or contact support.",
                parse_mode=ParseMode.MARKDOWN
            )

    async def handle_consensus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /consensus <query> - Run consensus workflow (3 agents + judge).

        Workflow: 3 solvers generate answers → Judge picks best

        Example:
            /consensus What is the best PLC for beginners?
        """
        user_id = str(update.effective_user.id)
        query = " ".join(context.args) if context.args else ""

        if not query:
            await update.message.reply_text(
                "❌ *Usage:* `/consensus <your question>`\n\n"
                "*Example:*\n"
                "`/consensus Best PLC for beginners?`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send initial message
        status_msg = await update.message.reply_text(
            "🔄 *Running Consensus Workflow*\n\n"
            f"Query: _{query}_\n\n"
            "Generating 3 candidate answers...",
            parse_mode=ParseMode.MARKDOWN
        )

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        try:
            # Get LangFuse callback if available
            callback = None
            if self.observability_enabled:
                session_id = f"telegram_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                callback = self.tracker.get_callback(session_id=session_id, user_id=user_id)

            callbacks = [callback] if callback else []

            # Create 3 solver agents with different perspectives
            solver1 = self.factory.create_agent(
                role="Technical Expert",
                goal="Provide technically accurate answers",
                backstory="Deep technical knowledge",
                verbose=False,
                callbacks=callbacks
            )

            solver2 = self.factory.create_agent(
                role="Practical Expert",
                goal="Provide practical answers",
                backstory="Focuses on real-world applications",
                verbose=False,
                callbacks=callbacks
            )

            solver3 = self.factory.create_agent(
                role="Teaching Expert",
                goal="Provide clear educational answers",
                backstory="Explains complex topics simply",
                verbose=False,
                callbacks=callbacks
            )

            judge = self.factory.create_agent(
                role="Judge",
                goal="Pick the best answer",
                backstory="Expert evaluator of answer quality",
                verbose=False,
                callbacks=callbacks
            )

            # Update status
            await status_msg.edit_text(
                "🔄 *Running Consensus Workflow*\n\n"
                f"Query: _{query}_\n\n"
                "Generating 3 candidate answers ✅\n"
                "Judge evaluating answers...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Create and execute workflow
            workflow = create_consensus_workflow(
                agents={
                    "solvers": [solver1, solver2, solver3],
                    "judge": judge
                },
                consensus_method="judge",
                verbose=False
            )

            start_time = datetime.now()
            result = workflow.invoke({
                "query": query,
                "candidate_answers": [],
                "scores": {},
                "final_answer": "",
                "consensus_method": "judge"
            })
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Build response
            final_answer = result.get("final_answer", "No answer selected")

            response = (
                "✅ *Consensus Reached*\n\n"
                f"*Best Answer (selected by judge):*\n{final_answer}\n\n"
                f"*Processing Time:* {duration:.1f}s\n"
                f"*Candidates Evaluated:* 3"
            )

            # Add trace link if available
            if self.observability_enabled and self.tracker:
                self.tracker.flush()
                trace_link = self.tracker.get_trace_link()
                if trace_link:
                    response += f"\n\n📊 [View All 3 Answers + Judge Decision]({trace_link})"

            await status_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            await status_msg.edit_text(
                f"❌ *Workflow Failed*\n\n"
                f"Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )

    async def handle_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /analyze <query> - Run supervisor workflow (routes to specialists).

        Workflow: Supervisor analyzes query → Delegates to specialist teams

        Example:
            /analyze Create a PLC troubleshooting guide
        """
        user_id = str(update.effective_user.id)
        query = " ".join(context.args) if context.args else ""

        if not query:
            await update.message.reply_text(
                "❌ *Usage:* `/analyze <your task>`\n\n"
                "*Example:*\n"
                "`/analyze Create PLC troubleshooting guide`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send initial message
        status_msg = await update.message.reply_text(
            "🔄 *Running Supervisor Workflow*\n\n"
            f"Task: _{query}_\n\n"
            "Supervisor analyzing task...",
            parse_mode=ParseMode.MARKDOWN
        )

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        try:
            # Get LangFuse callback if available
            callback = None
            if self.observability_enabled:
                session_id = f"telegram_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                callback = self.tracker.get_callback(session_id=session_id, user_id=user_id)

            callbacks = [callback] if callback else []

            # Create supervisor and specialist teams
            supervisor = self.factory.create_agent(
                role="Workflow Supervisor",
                goal="Analyze tasks and delegate to specialists",
                backstory="Expert coordinator",
                verbose=False,
                callbacks=callbacks
            )

            research_team = self.factory.create_agent(
                role="Research Team",
                goal="Find information",
                backstory="Skilled researchers",
                verbose=False,
                callbacks=callbacks
            )

            analysis_team = self.factory.create_agent(
                role="Analysis Team",
                goal="Analyze data and provide insights",
                backstory="Data analysts",
                verbose=False,
                callbacks=callbacks
            )

            coding_team = self.factory.create_agent(
                role="Coding Team",
                goal="Write and explain code",
                backstory="Software engineers",
                verbose=False,
                callbacks=callbacks
            )

            # Update status
            await status_msg.edit_text(
                "🔄 *Running Supervisor Workflow*\n\n"
                f"Task: _{query}_\n\n"
                "Supervisor analyzing task ✅\n"
                "Delegating to specialist teams...",
                parse_mode=ParseMode.MARKDOWN
            )

            # Create and execute workflow
            workflow = create_supervisor_workflow(
                agents={
                    "supervisor": supervisor,
                    "teams": {
                        "research": research_team,
                        "analysis": analysis_team,
                        "coding": coding_team
                    }
                },
                verbose=False
            )

            start_time = datetime.now()
            result = workflow.invoke({
                "query": query,
                "supervisor_decision": {},
                "delegated_results": [],
                "final_answer": ""
            })
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Build response
            final_answer = result.get("final_answer", "No results")
            decision = result.get("supervisor_decision", {})
            teams_used = ", ".join(decision.get("teams", []))

            response = (
                "✅ *Analysis Complete*\n\n"
                f"*Results:*\n{final_answer}\n\n"
                f"*Teams Used:* {teams_used or 'N/A'}\n"
                f"*Processing Time:* {duration:.1f}s"
            )

            # Add trace link if available
            if self.observability_enabled and self.tracker:
                self.tracker.flush()
                trace_link = self.tracker.get_trace_link()
                if trace_link:
                    response += f"\n\n📊 [View Supervisor Decision + Team Results]({trace_link})"

            await status_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            await status_msg.edit_text(
                f"❌ *Workflow Failed*\n\n"
                f"Error: {str(e)}",
                parse_mode=ParseMode.MARKDOWN
            )
