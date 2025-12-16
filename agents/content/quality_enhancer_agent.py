#!/usr/bin/env python3
"""
QualityEnhancerAgent - GPT-4 fallback for expanding short scripts

Responsibilities:
- Check script word count
- If ≥ 400 words → Return as-is (NO LLM CALL)
- If < 400 words → Use GPT-4 to expand content (FALLBACK ONLY)
- Preserve citations and facts
- Track LLM usage and costs

Purpose: Expand scripts ONLY when necessary (last resort)
Cost: ~$0.01 per expansion (only 10-20% of scripts need this)

Based on: Multi-agent content enhancement chain
"""

import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class QualityEnhancerAgent:
    """
    Expand scripts using GPT-4 ONLY if below 400 words.

    This is the LAST agent in the chain - only called when KB queries
    and logic couldn't reach 400-word target.
    """

    def __init__(self):
        """Initialize agent with OpenAI API"""
        self.agent_name = "quality_enhancer_agent"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not found - GPT-4 enhancement disabled")
            self.gpt4_available = False
        else:
            self.gpt4_available = True
            # Import OpenAI only if API key exists
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_api_key)
                logger.info(f"{self.agent_name} initialized with GPT-4")
            except ImportError:
                logger.warning("openai package not installed - GPT-4 enhancement disabled")
                self.gpt4_available = False

    def enhance_if_needed(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance script ONLY if < 400 words using GPT-4.

        Args:
            script: Script dict from ScriptwriterAgent

        Returns:
            Enhanced script (or original if >= 400 words)

        Example:
            >>> enhancer = QualityEnhancerAgent()
            >>> script = {'word_count': 250, 'full_script': '...'}
            >>> enhanced = enhancer.enhance_if_needed(script)
            >>> print(f"Enhanced: {enhanced['llm_enhanced']}")
            >>> print(f"New word count: {enhanced['word_count']}")
        """
        word_count = script.get('word_count', 0)

        # NO LLM if ≥ 400 words
        if word_count >= 400:
            logger.info(f"Script has {word_count} words (≥ 400) - no enhancement needed")
            script['llm_enhanced'] = False
            script['llm_cost'] = 0.0
            return script

        # NO LLM if GPT-4 not available
        if not self.gpt4_available:
            logger.warning(f"Script has {word_count} words but GPT-4 unavailable - returning as-is")
            script['llm_enhanced'] = False
            script['llm_cost'] = 0.0
            script['quality_issues'] = script.get('quality_issues', [])
            script['quality_issues'].append("LLM enhancement unavailable (no API key)")
            return script

        # Need GPT-4 expansion
        gap = 400 - word_count
        logger.info(f"Script has {word_count} words - expanding by ~{gap} words using GPT-4")

        try:
            expanded_script = self._expand_with_gpt4(script, gap)

            # Update script
            script['full_script'] = expanded_script
            script['word_count'] = len(expanded_script.split())
            script['llm_enhanced'] = True
            script['llm_cost'] = 0.01  # Estimated cost per expansion

            logger.info(f"Script expanded from {word_count} to {script['word_count']} words (cost: $0.01)")

            return script

        except Exception as e:
            logger.error(f"GPT-4 expansion failed: {e}")
            # Return original script on error
            script['llm_enhanced'] = False
            script['llm_cost'] = 0.0
            script['quality_issues'] = script.get('quality_issues', [])
            script['quality_issues'].append(f"LLM expansion failed: {str(e)}")
            return script

    def _expand_with_gpt4(self, script: Dict[str, Any], target_words: int) -> str:
        """
        Use GPT-4 to expand script by target_words.

        Preserves citations and factual accuracy.
        """
        current_script = script.get('full_script', '')
        citations = script.get('citations', [])
        topic = script.get('title', 'PLC Tutorial')

        # Build prompt
        prompt = f"""You are an expert PLC programming instructor. Expand this tutorial script by approximately {target_words} words.

RULES:
1. Add educational detail to existing sections (don't change facts or citations)
2. Include practical examples and real-world use cases
3. Add context about why this matters in industrial automation
4. Explain concepts in simple terms for beginners
5. Preserve ALL citations exactly as they appear
6. Don't hallucinate - only expand on existing content
7. Maintain the script's teaching flow (hook → concept → details → recap → CTA)

TOPIC: {topic}

CURRENT SCRIPT ({script.get('word_count', 0)} words):
{current_script}

CITATIONS (MUST PRESERVE):
{chr(10).join(f'- {c}' for c in citations)}

EXPANDED SCRIPT (target: ~{target_words} additional words):"""

        # Call GPT-4
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert industrial automation instructor who creates clear, educational content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,  # ~600 words max
            temperature=0.7
        )

        expanded_script = response.choices[0].message.content.strip()

        # Validate citations preserved
        for citation in citations:
            if citation not in expanded_script:
                logger.warning(f"Citation missing in expanded script: {citation}")
                # Append citations if missing
                expanded_script += f"\n\nSources: {', '.join(citations)}"
                break

        return expanded_script


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with short script
    test_script = {
        'title': 'PLC Basics',
        'word_count': 250,
        'full_script': 'PLCs are industrial computers. They monitor inputs and control outputs. This is a short script that needs expansion.',
        'citations': ['rockwell_manual.pdf (page 5)', 'siemens_guide.pdf (page 12)']
    }

    enhancer = QualityEnhancerAgent()

    # Test 1: Short script (should enhance)
    print("\n" + "=" * 70)
    print("TEST 1: Short Script (250 words) - Should Enhance")
    print("=" * 70)
    result = enhancer.enhance_if_needed(test_script.copy())
    print(f"Enhanced: {result['llm_enhanced']}")
    print(f"Word count: {result['word_count']}")
    print(f"Cost: ${result['llm_cost']}")

    # Test 2: Long script (should NOT enhance)
    long_script = test_script.copy()
    long_script['word_count'] = 450
    print("\n" + "=" * 70)
    print("TEST 2: Long Script (450 words) - Should NOT Enhance")
    print("=" * 70)
    result2 = enhancer.enhance_if_needed(long_script)
    print(f"Enhanced: {result2['llm_enhanced']}")
    print(f"Word count: {result2['word_count']}")
    print(f"Cost: ${result2['llm_cost']}")
