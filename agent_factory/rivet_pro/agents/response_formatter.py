"""
Response Formatter for RIVET Pro Phase 3.

Utilities for post-processing agent responses:
- Extract URLs and links
- Parse safety warnings
- Format citations for Telegram markdown
- Extract action lists
"""

import re
from typing import List, Dict, Any, Tuple


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from response text.

    Args:
        text: Response text containing potential URLs

    Returns:
        List of URLs found in text
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:\'\"]'
    urls = re.findall(url_pattern, text)
    return urls


def extract_safety_warnings(text: str) -> List[str]:
    """
    Extract safety warnings from response text.

    Looks for lines starting with:
    - ⚠️ SAFETY:
    - ⚠️ WARNING:
    - SAFETY NOTE:
    - WARNING:

    Args:
        text: Response text

    Returns:
        List of safety warning messages
    """
    warnings = []

    # Pattern 1: Lines starting with warning emoji + keyword
    pattern1 = r'⚠️\s*(SAFETY|WARNING)[:\-\s]+(.+?)(?=\n|$)'
    matches1 = re.findall(pattern1, text, re.IGNORECASE)
    warnings.extend([match[1].strip() for match in matches1])

    # Pattern 2: Lines starting with SAFETY NOTE: or WARNING:
    pattern2 = r'^(SAFETY NOTE|WARNING)[:\-\s]+(.+?)(?=\n|$)'
    matches2 = re.findall(pattern2, text, re.MULTILINE | re.IGNORECASE)
    warnings.extend([match[1].strip() for match in matches2])

    return warnings


def format_citations_telegram(citations: List[Dict[str, Any]]) -> str:
    """
    Format citations for Telegram markdown.

    Args:
        citations: List of citation dictionaries from agent response

    Returns:
        Formatted citation text for Telegram

    Example output:
        **Sources:**
        [1] SINAMICS G120C Manual - Fault Troubleshooting (sim: 0.92)
        [2] IEC 61508-2 - Diagnostic Coverage (sim: 0.87)
    """
    if not citations:
        return ""

    lines = ["**Sources:**"]

    for i, citation in enumerate(citations, start=1):
        title = citation.get("title", "Unknown")
        source = citation.get("source", "KB")
        similarity = citation.get("similarity", 0.0)

        # Format line
        line = f"[{i}] {title}"

        # Add source if not "Knowledge Base"
        if source and source != "Knowledge Base":
            line += f" - {source}"

        # Add similarity score (only if meaningful)
        if similarity >= 0.5:
            line += f" (sim: {similarity:.2f})"

        lines.append(line)

    return "\n".join(lines)


def extract_action_lists(text: str) -> List[Tuple[int, str]]:
    """
    Extract numbered action lists from response text.

    Finds patterns like:
    1. Check input voltage
    2. Verify wiring connections
    3. Reset fault code

    Args:
        text: Response text

    Returns:
        List of (number, action) tuples
    """
    actions = []

    # Pattern: Lines starting with number followed by period or parenthesis
    pattern = r'^(\d+)[\.\)]\s+(.+?)(?=\n|$)'
    matches = re.findall(pattern, text, re.MULTILINE)

    for match in matches:
        step_num = int(match[0])
        action_text = match[1].strip()
        actions.append((step_num, action_text))

    return actions


def format_for_telegram(text: str, citations: List[Dict[str, Any]]) -> str:
    """
    Format complete response for Telegram markdown.

    Args:
        text: Agent response text
        citations: Citation metadata

    Returns:
        Formatted text ready for Telegram

    Features:
    - Adds citation block at end
    - Preserves markdown formatting
    - Keeps safety warnings prominent
    """
    # Start with original text
    formatted = text

    # Add citations at end if present
    citation_block = format_citations_telegram(citations)
    if citation_block:
        formatted += "\n\n" + citation_block

    return formatted


def highlight_safety_warnings(text: str) -> str:
    """
    Highlight safety warnings in text for better visibility.

    Args:
        text: Response text

    Returns:
        Text with safety warnings highlighted using markdown bold
    """
    # Bold lines starting with ⚠️ or SAFETY/WARNING
    patterns = [
        (r'(⚠️\s*(?:SAFETY|WARNING)[:\-\s]+.+?)(?=\n|$)', r'**\1**'),
        (r'^((?:SAFETY NOTE|WARNING)[:\-\s]+.+?)(?=\n|$)', r'**\1**')
    ]

    highlighted = text
    for pattern, replacement in patterns:
        highlighted = re.sub(pattern, replacement, highlighted, flags=re.MULTILINE | re.IGNORECASE)

    return highlighted
