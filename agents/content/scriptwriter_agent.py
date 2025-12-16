#!/usr/bin/env python3
"""
ScriptwriterAgent - Write video scripts from knowledge atoms

Responsibilities:
- Transform atom content into narration\n- Add personality markers ([enthusiastic], [cautionary])\n- Include visual cues (show diagram, highlight code)\n- Cite atom sources in script\n- Generate recap quiz question

Schedule: On-demand (triggered by orchestrator)
Dependencies: Supabase, agent_factory.memory
Output: Updates Supabase tables, logs to agent_status

Based on: docs/AGENT_ORGANIZATION.md Section 4
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from agent_factory.memory.storage import SupabaseMemoryStorage

logger = logging.getLogger(__name__)


class ScriptwriterAgent:
    """
    Write video scripts from knowledge atoms

    Write video scripts from knowledge atoms\n\nThis agent is part of the Content Team.
    """

    def __init__(self):
        """Initialize agent with Supabase connection"""
        self.storage = SupabaseMemoryStorage()
        self.agent_name = "scriptwriter_agent"
        self._register_status()

    def _register_status(self):
        """Register agent in agent_status table"""
        try:
            self.storage.client.table("agent_status").upsert({
                "agent_name": self.agent_name,
                "status": "idle",
                "last_heartbeat": datetime.now().isoformat(),
                "tasks_completed_today": 0,
                "tasks_failed_today": 0
            }).execute()
            logger.info(f"{self.agent_name} registered")
        except Exception as e:
            logger.error(f"Failed to register {self.agent_name}: {e}")

    def _send_heartbeat(self):
        """Update heartbeat in agent_status table"""
        try:
            self.storage.client.table("agent_status") \
                .update({"last_heartbeat": datetime.now().isoformat()}) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method called by orchestrator.

        Args:
            payload: Job payload from agent_jobs table

        Returns:
            Dict with status, result/error

        Example:
            >>> agent = ScriptwriterAgent()
            >>> result = agent.run({"task": "process"})
            >>> assert result["status"] == "success"
        """
        try:
            self._send_heartbeat()
            self._update_status("running")

            # TODO: Implement agent logic
            result = self._process(payload)

            self._update_status("completed")
            return {"status": "success", "result": result}

        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}")
            self._update_status("error", str(e))
            return {"status": "error", "error": str(e)}

    def _process(self, payload: Dict[str, Any]) -> Any:
        """Agent-specific processing logic"""
        # TODO: Implement in subclass or concrete agent
        raise NotImplementedError("Agent must implement _process()")

    def _update_status(self, status: str, error_message: Optional[str] = None):
        """Update agent status in database"""
        try:
            update_data = {"status": status}
            if error_message:
                update_data["error_message"] = error_message

            self.storage.client.table("agent_status") \
                .update(update_data) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    def query_atoms(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query Supabase for relevant atoms by topic using keyword search.

        Prioritizes educational content (concept, procedure, fault, pattern atoms)
        and filters out specification/reference atoms that don't narrate well.

        Args:
            topic: Topic keyword to search for in atom titles/content
            limit: Maximum number of atoms to return (default: 5)

        Returns:
            List of atom dictionaries from Supabase, filtered for narration quality

        Example:
            >>> agent = ScriptwriterAgent()
            >>> atoms = agent.query_atoms("motor control", limit=3)
            >>> print(len(atoms))
            3
        """
        try:
            # Preferred atom types for video scripts (good for narration)
            preferred_types = ['concept', 'procedure', 'fault', 'pattern']

            # Try to get all matching atoms (including specifications)
            all_results = self.storage.client.table('knowledge_atoms') \
                .select('*') \
                .or_(f'title.ilike.%{topic}%,summary.ilike.%{topic}%,content.ilike.%{topic}%') \
                .limit(limit * 3) \
                .execute()

            # Sort atoms by preference (preferred types first, then others)
            preferred_atoms = [a for a in all_results.data if a.get('atom_type') in preferred_types]
            other_atoms = [a for a in all_results.data if a.get('atom_type') not in preferred_types]

            # Combine: preferred first, then others
            combined = preferred_atoms + other_atoms

            # Return up to limit
            result_atoms = combined[:limit]

            logger.info(f"Query '{topic}' returned {len(result_atoms)} atoms ({len(preferred_atoms)} preferred, {len(other_atoms)} other)")
            return result_atoms

        except Exception as e:
            logger.error(f"Failed to query atoms for topic '{topic}': {e}")
            return []

    def generate_script(self, topic: str, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate video script from knowledge atoms using templates.

        Args:
            topic: Video topic/title
            atoms: List of atoms retrieved from query_atoms()

        Returns:
            Dictionary with script structure:
            {
                'title': str,
                'hook': str,
                'intro': str,
                'sections': List[Dict],
                'summary': str,
                'cta': str,
                'citations': List[str],
                'word_count': int
            }

        Example:
            >>> atoms = agent.query_atoms("PLC basics")
            >>> script = agent.generate_script("Introduction to PLCs", atoms)
            >>> print(script['word_count'])
            450
        """
        if not atoms:
            raise ValueError("No atoms provided for script generation")

        # Extract key information from atoms
        primary_atom = atoms[0]
        supporting_atoms = atoms[1:] if len(atoms) > 1 else []

        # Generate hook (first 10 seconds - grab attention)
        hook = self._generate_hook(topic, primary_atom)

        # Generate intro (establish credibility)
        intro = self._generate_intro(topic, primary_atom)

        # Generate main content sections
        sections = self._generate_sections(primary_atom, supporting_atoms)

        # Generate summary/recap
        summary = self._generate_summary(topic, primary_atom)

        # Generate call-to-action
        cta = self._generate_cta()

        # Collect citations
        citations = self._extract_citations(atoms)

        # Combine all parts
        full_script = f"{hook}\n\n{intro}\n\n"
        for section in sections:
            full_script += f"{section['content']}\n\n"
        full_script += f"{summary}\n\n{cta}"

        # Calculate word count
        word_count = len(full_script.split())

        # Build script dictionary
        script = {
            'title': topic,
            'hook': hook,
            'intro': intro,
            'sections': sections,
            'summary': summary,
            'cta': cta,
            'citations': citations,
            'full_script': full_script,
            'word_count': word_count,
            'estimated_duration_seconds': word_count // 2.5,  # ~150 words/minute
            'quality_score': 0,
            'quality_issues': []
        }

        # Validate script quality
        script = self._validate_script(script)

        return script

    def _generate_hook(self, topic: str, atom: Dict[str, Any]) -> str:
        """Generate attention-grabbing hook (first 10 seconds)"""
        difficulty = atom.get('difficulty', 'beginner')

        if difficulty == 'beginner':
            return f"Ever wondered how {topic.lower()} works? Let me break it down in simple terms."
        elif difficulty == 'intermediate':
            return f"Ready to level up your {topic.lower()} skills? Here's what you need to know."
        else:
            return f"Let's dive deep into {topic.lower()}. This is advanced stuff, so pay attention."

    def _generate_intro(self, topic: str, atom: Dict[str, Any]) -> str:
        """Generate intro with credibility and context"""
        manufacturer = atom.get('manufacturer', '').replace('_', ' ').title()
        atom_type = atom.get('atom_type', 'concept')

        intro = f"Today we're covering {topic}. "

        if manufacturer:
            intro += f"This is based on official {manufacturer} documentation, "
        else:
            intro += f"This is based on industry-standard documentation, "

        intro += f"so you're getting accurate, reliable information. "

        if atom_type == 'procedure':
            intro += "I'll walk you through the exact steps you need to follow."
        elif atom_type == 'concept':
            intro += "I'll explain the core concepts and how they work."
        elif atom_type == 'pattern':
            intro += "I'll show you the pattern and when to use it."
        else:
            intro += "Let's get started."

        return intro

    def _generate_sections(self, primary_atom: Dict[str, Any], supporting_atoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate main content sections from atoms"""
        sections = []

        # Primary section from main atom
        primary_section = {
            'title': primary_atom.get('title', 'Main Content'),
            'content': self._format_atom_content(primary_atom),
            'source': primary_atom.get('source_document', 'Official documentation')
        }
        sections.append(primary_section)

        # Supporting sections
        for atom in supporting_atoms[:2]:  # Max 2 supporting atoms to keep video concise
            section = {
                'title': atom.get('title', 'Additional Information'),
                'content': self._format_atom_content(atom),
                'source': atom.get('source_document', 'Official documentation')
            }
            sections.append(section)

        return sections

    def _format_atom_content(self, atom: Dict[str, Any]) -> str:
        """
        Format atom content for TEACHING narration (not data dumps).

        Handles different atom types intelligently:
        - concept: Explain the idea in plain language with detail
        - procedure: Walk through steps conversationally
        - specification: Explain what the specs mean, not raw tables
        - pattern: Show when/why to use it
        - fault: Explain symptoms and fixes

        Returns 100-200 words per section for 3-5 minute videos.
        """
        atom_type = atom.get('atom_type', 'concept')
        title = atom.get('title', '')
        summary = atom.get('summary', '')
        content = atom.get('content', '')

        # STRATEGY: Combine summary + relevant content for richer narration
        # Filter out tables/raw data that don't narrate well

        if atom_type == 'concept':
            # Explain the concept in detail (summary + first paragraphs of content)
            narration = summary if summary else ""

            # Add more detail from content if available
            if content and not content.startswith('Table'):
                # Extract first 2-3 sentences from content (skip table metadata)
                content_sentences = [s.strip() + '.' for s in content.split('.') if s.strip() and 'Table' not in s and 'rows' not in s and 'columns' not in s]
                if content_sentences:
                    additional_detail = ' '.join(content_sentences[:3])
                    if additional_detail and additional_detail not in narration:
                        narration += f" {additional_detail}"

        elif atom_type == 'procedure':
            # Extract steps and make them conversational with context
            narration = f"{summary} " if summary else ""
            narration += "Here's the step-by-step process. [pause] "

            if 'step' in content.lower():
                # Parse step-by-step format
                lines = content.split('\n')
                steps = [l.strip() for l in lines if l.strip() and ('step' in l.lower() or (l[0].isdigit() and ':' in l))]
                if steps:
                    for i, step in enumerate(steps[:8], 1):  # Max 8 steps for video
                        # Clean step text (remove "Step 1:", just keep action)
                        step_text = step.split(':', 1)[-1].strip() if ':' in step else step
                        narration += f"Step {i}: {step_text}. [pause] "
                else:
                    # No explicit steps, use full content
                    if content and not content.startswith('Table'):
                        narration += content[:400]  # First 400 chars
            else:
                # No steps found, use summary + content
                if content and not content.startswith('Table'):
                    narration += content[:400]

        elif atom_type == 'pattern':
            # Explain the pattern, when to use it, and example
            narration = f"{summary} " if summary else f"{title}. "

            # Add context about when to use
            if 'when' not in narration.lower() and 'use' not in narration.lower():
                narration += "This pattern is commonly used in industrial automation when you need reliable, repeatable control logic. "

            # Add implementation detail if available
            if content and not content.startswith('Table') and len(content) > 50:
                content_clean = ' '.join([s.strip() for s in content.split('\n') if s.strip() and 'Table' not in s])
                if content_clean:
                    narration += content_clean[:300]

        elif atom_type == 'fault':
            # Explain problem, symptoms, and solution
            narration = f"{summary} " if summary else f"Let's troubleshoot {title.lower()}. "

            # Add diagnostic steps from content
            if content and 'symptom' in content.lower() or 'cause' in content.lower():
                narration += content[:400]
            elif content and not content.startswith('Table'):
                # Generic troubleshooting approach
                narration += f"Here's how to diagnose this issue. {content[:300]}"

        elif atom_type == 'specification':
            # SMART HANDLING: Extract meaningful content from specifications
            # Don't just say "Table with X rows" - explain what the specs cover
            narration = ""

            # Use title to frame the specification
            if title and not title.startswith('Specification'):
                narration = f"Let's look at the specifications for {title.lower()}. "

            # Try to use summary if available (usually better than raw content for specs)
            if summary and not summary.startswith('Table with'):
                narration += f"{summary} "

            # Add context about what these specifications cover
            if 'technical' not in narration.lower() and 'specification' not in narration.lower():
                narration += "The technical documentation provides detailed specifications including electrical ratings, operating parameters, and performance characteristics. "

            # Extract any non-table content (actual meaningful text)
            if content and not content.startswith('Table'):
                # Look for actual sentences (not table metadata)
                sentences = [s.strip() + '.' for s in content.split('.') if s.strip() and len(s.strip()) > 20 and 'rows' not in s and 'columns' not in s]
                if sentences:
                    narration += ' '.join(sentences[:2]) + " "

            # Add practical guidance
            narration += "Check the official documentation for the complete specification tables - they're essential for system design and component selection."

        else:
            # Default: Use summary + content intelligently
            narration = summary if summary else ""
            if content and not content.startswith('Table') and 'rows' not in content[:50]:
                content_clean = content.replace('\n', ' ')
                if content_clean and content_clean not in narration:
                    narration += f" {content_clean[:300]}"

        # Clean up for narration
        narration = ' '.join(narration.split())  # Remove excess whitespace

        # Remove markdown tables (they don't narrate well)
        if '|' in narration and '---' in narration:
            # This is a markdown table, skip it
            narration = f"{title}. This involves several technical parameters - check the official documentation for the complete reference tables and specifications."

        # Limit length (max 250 words per section for better pacing)
        # Longer sections = more educational value
        words = narration.split()
        if len(words) > 250:
            narration = ' '.join(words[:250])
            # Add natural ending
            if not narration.endswith('.'):
                # Find last complete sentence
                last_period = narration.rfind('.')
                if last_period > 0:
                    narration = narration[:last_period + 1]
                else:
                    narration += '.'

        # Ensure minimum quality (at least 30 words)
        if len(words) < 30:
            narration += f" For more details on {title.lower()}, refer to the official documentation which provides comprehensive coverage of all aspects."

        return narration

    def _generate_summary(self, topic: str, atom: Dict[str, Any]) -> str:
        """Generate recap/summary"""
        summary = f"So to recap: {topic} is "

        # Use atom summary as base
        atom_summary = atom.get('summary', '')
        if atom_summary:
            # Take first sentence
            first_sentence = atom_summary.split('.')[0] + '.'
            summary += first_sentence.lower()

        summary += " Remember, this information comes from official documentation, "
        summary += "so you can trust it's accurate and up-to-date."

        return summary

    def _generate_cta(self) -> str:
        """Generate call-to-action"""
        return ("If you found this helpful, hit that like button and subscribe for more PLC tutorials. "
                "Drop a comment if you have questions - I read every single one. "
                "See you in the next video!")

    def _extract_citations(self, atoms: List[Dict[str, Any]]) -> List[str]:
        """Extract source citations from atoms"""
        citations = []
        for atom in atoms:
            source_doc = atom.get('source_document', '')
            source_pages = atom.get('source_pages', [])

            if source_doc:
                citation = source_doc
                if source_pages:
                    citation += f" (pages {', '.join(map(str, source_pages))})"
                citations.append(citation)

        return list(set(citations))  # Remove duplicates

    def _validate_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate script quality and assign quality score.

        Quality criteria:
        - Minimum 400 words (target: 450-600 for 3-5 min video)
        - No raw table text ("Table with X rows...")
        - At least 2 citations
        - Proper structure (hook, intro, sections, summary, CTA)

        Returns:
            Updated script dict with quality_score (0-100) and quality_issues list
        """
        issues = []
        score = 100  # Start perfect, deduct points

        word_count = script['word_count']
        full_text = script['full_script']

        # Check 1: Minimum word count (CRITICAL)
        if word_count < 400:
            issues.append(f"Script too short: {word_count} words (minimum: 400)")
            score -= 30  # Major penalty
        elif word_count < 450:
            issues.append(f"Script short: {word_count} words (target: 450-600)")
            score -= 10  # Minor penalty

        # Check 2: Maximum word count
        if word_count > 800:
            issues.append(f"Script too long: {word_count} words (max: 800)")
            score -= 10

        # Check 3: Raw table text (CRITICAL)
        if 'Table with' in full_text and 'rows' in full_text:
            issues.append("Contains raw table metadata (not narration-ready)")
            score -= 25  # Major penalty

        # Check 4: Citations
        citation_count = len(script['citations'])
        if citation_count < 2:
            issues.append(f"Too few citations: {citation_count} (minimum: 2)")
            score -= 15

        # Check 5: Section count
        section_count = len(script['sections'])
        if section_count < 2:
            issues.append(f"Too few sections: {section_count} (minimum: 2)")
            score -= 10

        # Check 6: Placeholder text
        if 'TODO' in full_text.upper() or 'PLACEHOLDER' in full_text.upper():
            issues.append("Contains placeholder text")
            score -= 20

        # Ensure score doesn't go below 0
        score = max(0, score)

        # Update script with validation results
        script['quality_score'] = score
        script['quality_issues'] = issues

        # Log validation results
        if issues:
            logger.warning(f"Script quality issues (score: {score}/100): {', '.join(issues)}")
        else:
            logger.info(f"Script passed validation (score: {score}/100)")

        return script

    def transform_atom_to_script(self, *args, **kwargs):
        """
        [DEPRECATED] Use generate_script() instead.

        This method is kept for backwards compatibility.
        """
        raise NotImplementedError("Use generate_script() instead of transform_atom_to_script")

    def add_personality_markers(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add personality markers for voice production guidance.

        Markers guide voice tone/emotion:
        - [enthusiastic] - excited, energetic delivery
        - [cautionary] - careful, warning tone
        - [explanatory] - clear, teaching tone
        - [emphasize] - stress this point
        - [pause] - brief pause for effect

        Args:
            script: Script dictionary from generate_script()

        Returns:
            Updated script with personality markers added to text

        Example:
            >>> script = agent.generate_script("PLC Basics", atoms)
            >>> marked_script = agent.add_personality_markers(script)
            >>> print(marked_script['hook'])
            '[enthusiastic] Ever wondered how plcs work? [pause] Let me break it down!'
        """
        # Add markers to hook (always enthusiastic)
        script['hook'] = f"[enthusiastic] {script['hook']}"

        # Add markers to intro (explanatory tone)
        script['intro'] = f"[explanatory] {script['intro']}"

        # Add markers to sections based on content
        for section in script['sections']:
            content = section['content']

            # Add cautionary markers for warning/error content
            if any(word in content.lower() for word in ['warning', 'error', 'fault', 'danger', 'caution']):
                content = f"[cautionary] {content}"

            # Add emphasize markers for important points
            if any(word in content.lower() for word in ['important', 'critical', 'must', 'required']):
                content = content.replace('important', '[emphasize] important')
                content = content.replace('Important', '[emphasize] Important')
                content = content.replace('critical', '[emphasize] critical')
                content = content.replace('Critical', '[emphasize] Critical')

            # Add pause after key phrases
            content = content.replace('. ', '. [pause] ')

            section['content'] = content

        # Add markers to summary (reflective, calm)
        script['summary'] = f"[explanatory] {script['summary']}"

        # Add markers to CTA (enthusiastic, encouraging)
        script['cta'] = f"[enthusiastic] {script['cta']}"

        # Rebuild full_script with markers
        full_script = f"{script['hook']}\n\n{script['intro']}\n\n"
        for section in script['sections']:
            full_script += f"{section['content']}\n\n"
        full_script += f"{script['summary']}\n\n{script['cta']}"

        script['full_script'] = full_script

        return script

    def add_visual_cues(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add visual cues for video production guidance.

        Cues guide visual elements:
        - [show title: TEXT] - Display title card
        - [show diagram: DESC] - Display diagram/image
        - [highlight: TEXT] - Highlight specific text
        - [show code: LANG] - Display code snippet
        - [show table] - Display table/data

        Args:
            script: Script dictionary from generate_script()

        Returns:
            Updated script with visual cues added

        Example:
            >>> script = agent.generate_script("PLC Basics", atoms)
            >>> visual_script = agent.add_visual_cues(script)
        """
        # Add title card cue at beginning
        script['hook'] = f"[show title: {script['title']}] {script['hook']}"

        # Add visual cues based on content type
        for section in script['sections']:
            content = section['content']
            atom_type = section.get('type', '')

            # Add diagram cue for concepts
            if 'diagram' in content.lower() or 'figure' in content.lower():
                content = f"[show diagram: {section['title']}] {content}"

            # Add code cue for programming content
            if any(word in content.lower() for word in ['code', 'programming', 'ladder', 'function']):
                content = f"[show code: ladder_logic] {content}"

            # Add table cue for specifications
            if 'table' in content.lower() or atom_type == 'specification':
                content = f"[show table] {content}"

            # Add citation visual at end of section
            source = section.get('source', '')
            if source:
                content += f" [show citation: {source}]"

            section['content'] = content

        # Rebuild full_script with visual cues
        full_script = f"{script['hook']}\n\n{script['intro']}\n\n"
        for section in script['sections']:
            full_script += f"{section['content']}\n\n"
        full_script += f"{script['summary']}\n\n{script['cta']}"

        script['full_script'] = full_script

        return script

    def include_visual_cues(self, *args, **kwargs):
        """
        [DEPRECATED] Use add_visual_cues() instead.

        This method is kept for backwards compatibility.
        """
        raise NotImplementedError("Use add_visual_cues() instead of include_visual_cues")

    def cite_sources(self, *args, **kwargs):
        """
        Cite atom sources in script

        TODO: Implement cite_sources logic

        Args:
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            TODO: Define return type

        Raises:
            NotImplementedError: Not yet implemented
        """
        # TODO: Implement cite_sources
        raise NotImplementedError("cite_sources not yet implemented")

    def generate_quiz_question(self, *args, **kwargs):
        """
        Generate recap quiz question

        TODO: Implement generate_quiz_question logic

        Args:
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            TODO: Define return type

        Raises:
            NotImplementedError: Not yet implemented
        """
        # TODO: Implement generate_quiz_question
        raise NotImplementedError("generate_quiz_question not yet implemented")

    def generate_script_with_chain(self, topic: str, use_llm_fallback: bool = True) -> Dict[str, Any]:
        """
        Generate video script using multi-agent chain (KB-first, LLM fallback).

        This is the NEW recommended method that:
        1. Uses ContentResearcherAgent for KB queries (10-15 atoms vs 5)
        2. Uses ContentEnricherAgent for structured outline (400+ word targets)
        3. Uses ScriptwriterAgent template-based generation (pure logic)
        4. Uses QualityEnhancerAgent ONLY if < 400 words (GPT-4 fallback)

        Expected cost: ~$0.002/script (vs $0.01 if using GPT-4 for everything)
        Expected quality: 450+ words, 80% won't need LLM

        Args:
            topic: Video topic/title
            use_llm_fallback: Whether to use GPT-4 for < 400 word scripts (default: True)

        Returns:
            Dictionary with script structure (same as generate_script())

        Example:
            >>> agent = ScriptwriterAgent()
            >>> script = agent.generate_script_with_chain("Introduction to PLCs")
            >>> print(f"Word count: {script['word_count']}")
            >>> print(f"LLM enhanced: {script['llm_enhanced']}")
            >>> print(f"Cost: ${script['llm_cost']}")
        """
        try:
            import sys
            from pathlib import Path

            # Add project root to path for imports
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))

            from agents.content.content_researcher_agent import ContentResearcherAgent
            from agents.content.content_enricher_agent import ContentEnricherAgent
            from agents.content.quality_enhancer_agent import QualityEnhancerAgent

            logger.info(f"Starting multi-agent chain for topic: '{topic}'")

            # AGENT 1: ContentResearcherAgent ($0 - pure KB queries)
            logger.info("AGENT 1: Researching topic with KB queries...")
            researcher = ContentResearcherAgent()
            research = researcher.research_topic(topic)

            total_atoms = sum(len(v) for v in research.values())
            logger.info(f"Research complete: {total_atoms} atoms found")

            # AGENT 2: ContentEnricherAgent ($0 - pure logic)
            logger.info("AGENT 2: Creating structured outline...")
            enricher = ContentEnricherAgent()
            outline = enricher.create_outline(research, topic)

            logger.info(f"Outline complete: {len(outline['sections'])} sections, {outline['total_target_words']} target words")

            # AGENT 3: ScriptwriterAgent ($0 - template-based generation)
            logger.info("AGENT 3: Generating script from outline...")
            script = self._generate_script_from_outline(outline)

            logger.info(f"Script generated: {script['word_count']} words, quality score: {script['quality_score']}/100")

            # AGENT 4: QualityEnhancerAgent ($0.01 if needed - GPT-4 fallback)
            if use_llm_fallback:
                logger.info("AGENT 4: Checking if LLM enhancement needed...")
                enhancer = QualityEnhancerAgent()
                script = enhancer.enhance_if_needed(script)

                if script.get('llm_enhanced'):
                    logger.info(f"Script enhanced with GPT-4: {script['word_count']} words (cost: ${script['llm_cost']})")
                else:
                    logger.info(f"No LLM enhancement needed (cost: $0)")
            else:
                script['llm_enhanced'] = False
                script['llm_cost'] = 0.0
                logger.info("LLM fallback disabled (cost: $0)")

            logger.info(f"Multi-agent chain complete: {script['word_count']} words, quality: {script['quality_score']}/100, cost: ${script.get('llm_cost', 0)}")

            return script

        except Exception as e:
            logger.error(f"Multi-agent chain failed: {e}")
            # Fallback to original single-agent method
            logger.warning("Falling back to original generate_script() method")
            atoms = self.query_atoms(topic, limit=5)
            return self.generate_script(topic, atoms)

    def _generate_script_from_outline(self, outline: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate script from ContentEnricherAgent outline (template-based).

        This is the template-based generation method that uses the structured
        outline from ContentEnricherAgent to create a narration-ready script.

        Args:
            outline: Outline dict from ContentEnricherAgent.create_outline()

        Returns:
            Script dictionary (same format as generate_script())
        """
        topic = outline['topic']
        sections_outline = outline['sections']

        # Generate script parts
        hook = self._generate_hook_from_outline(topic, sections_outline)
        intro = self._generate_intro_from_outline(topic, sections_outline)
        sections = self._generate_sections_from_outline(sections_outline)
        summary = self._generate_summary_from_outline(topic, sections_outline)
        cta = self._generate_cta()

        # Collect citations from all atoms in outline
        citations = []
        for section in sections_outline:
            for atom in section.get('atoms', []):
                source_doc = atom.get('source_document', '')
                if source_doc and source_doc not in citations:
                    citations.append(source_doc)

        # Combine all parts
        full_script = f"{hook}\n\n{intro}\n\n"
        for section in sections:
            full_script += f"{section['content']}\n\n"
        full_script += f"{summary}\n\n{cta}"

        # Calculate word count
        word_count = len(full_script.split())

        # Build script dictionary
        script = {
            'title': topic,
            'hook': hook,
            'intro': intro,
            'sections': sections,
            'summary': summary,
            'cta': cta,
            'citations': citations,
            'full_script': full_script,
            'word_count': word_count,
            'estimated_duration_seconds': word_count // 2.5,  # ~150 words/minute
            'quality_score': 0,
            'quality_issues': []
        }

        # Validate script quality
        script = self._validate_script(script)

        return script

    def _generate_hook_from_outline(self, topic: str, sections: List[Dict[str, Any]]) -> str:
        """Generate hook from outline (uses first atom's difficulty)"""
        if sections and sections[0].get('atoms'):
            first_atom = sections[0]['atoms'][0]
            return self._generate_hook(topic, first_atom)
        else:
            # Default hook
            return f"Ever wondered how {topic.lower()} works? Let me break it down in simple terms."

    def _generate_intro_from_outline(self, topic: str, sections: List[Dict[str, Any]]) -> str:
        """Generate intro from outline (uses first atom)"""
        if sections and sections[0].get('atoms'):
            first_atom = sections[0]['atoms'][0]
            return self._generate_intro(topic, first_atom)
        else:
            # Default intro
            return f"Today we're covering {topic}. This is based on industry-standard documentation, so you're getting accurate, reliable information. Let's get started."

    def _generate_sections_from_outline(self, sections_outline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate script sections from outline sections.

        Each outline section has:
        - type: section type (prerequisite, concept, example, etc.)
        - title: section title
        - atoms: list of atoms for this section
        - target_words: target word count

        We'll combine all atoms in each section into cohesive narration.
        """
        script_sections = []

        for outline_section in sections_outline:
            section_type = outline_section.get('type', 'concept')
            section_title = outline_section.get('title', 'Content')
            atoms = outline_section.get('atoms', [])
            target_words = outline_section.get('target_words', 100)

            if not atoms:
                continue

            # Combine content from all atoms in this section
            section_content = ""

            # Add section introduction based on type
            if section_type == 'prerequisite':
                section_content += "Before we dive in, you should understand: "
            elif section_type == 'concept':
                section_content += f"Let's understand {section_title.lower()}. "
            elif section_type == 'example':
                section_content += "Here's a practical example. "
            elif section_type == 'procedure':
                section_content += "Here's the step-by-step process. "
            elif section_type == 'troubleshooting':
                section_content += "Let's look at common issues you might encounter. "

            # Format each atom and combine
            for atom in atoms:
                atom_content = self._format_atom_content(atom)
                section_content += f"{atom_content} "

            # Ensure we hit target word count (add more detail if needed)
            current_words = len(section_content.split())
            if current_words < target_words and atoms:
                # Add more context from atoms
                for atom in atoms:
                    content = atom.get('content', '')
                    if content and 'Table' not in content:
                        # Add more detail
                        additional = content[:300]
                        section_content += f" {additional}"
                        break

            # Build section dict
            script_section = {
                'title': section_title,
                'content': section_content.strip(),
                'type': section_type,
                'source': atoms[0].get('source_document', 'Official documentation') if atoms else ''
            }

            script_sections.append(script_section)

        return script_sections

    def _generate_summary_from_outline(self, topic: str, sections: List[Dict[str, Any]]) -> str:
        """Generate summary from outline (uses first atom)"""
        if sections and sections[0].get('atoms'):
            first_atom = sections[0]['atoms'][0]
            return self._generate_summary(topic, first_atom)
        else:
            # Default summary
            return f"So to recap: {topic} is an important concept in industrial automation. Remember, this information comes from official documentation, so you can trust it's accurate and up-to-date."

