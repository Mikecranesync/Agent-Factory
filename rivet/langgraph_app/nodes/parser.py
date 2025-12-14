"""
Parser node: Extract structured atoms from raw text using LLM
"""

import logging
import json
import requests
from typing import List, Dict, Any
from langgraph_app.state import RivetState
from langgraph_app.config import settings

logger = logging.getLogger(__name__)


def call_ollama_llm(prompt: str, model: str = None) -> str:
    """
    Call Ollama LLM for text generation

    Args:
        prompt: Input prompt
        model: Model name (defaults to settings.OLLAMA_LLM_MODEL)

    Returns:
        Generated text
    """
    model = model or settings.OLLAMA_LLM_MODEL

    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for structured extraction
            "num_predict": 2000,
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        logger.error(f"Ollama LLM call failed: {e}")
        raise


def extract_atoms_from_text(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract structured knowledge atoms from raw text using LLM

    Args:
        text: Raw document text
        metadata: Document metadata

    Returns:
        List of structured atoms
    """
    # Limit text length for LLM context
    max_chars = 8000
    if len(text) > max_chars:
        text = text[:max_chars] + "...[truncated]"

    prompt = f"""You are an expert at extracting structured industrial maintenance knowledge from technical documents.

Extract knowledge atoms from the following document. Each atom should be a self-contained piece of knowledge.

Document:
{text}

Extract atoms in JSON format. Each atom should have:
- type: "fault", "procedure", "concept", or "pattern"
- vendor: Equipment vendor (e.g., "Allen-Bradley", "Siemens") if applicable
- product: Product name if applicable
- title: Brief title
- content: Main content
- keywords: List of relevant keywords

Return ONLY a JSON array of atoms, no other text.

Example:
[
  {{
    "type": "fault",
    "vendor": "Allen-Bradley",
    "product": "ControlLogix",
    "title": "Fault Code 0x1234",
    "content": "Fault 0x1234 indicates communication error...",
    "keywords": ["fault", "communication", "controllogix"]
  }}
]

Atoms:"""

    try:
        logger.info("Calling Ollama LLM for atom extraction...")
        response_text = call_ollama_llm(prompt)

        # Try to parse JSON
        # Extract JSON array from response (LLM might add extra text)
        start_idx = response_text.find("[")
        end_idx = response_text.rfind("]") + 1

        if start_idx >= 0 and end_idx > start_idx:
            json_text = response_text[start_idx:end_idx]
            atoms = json.loads(json_text)

            # Validate atoms
            if isinstance(atoms, list):
                # Add metadata to each atom
                for atom in atoms:
                    atom["source_url"] = metadata.get("source_url", "")
                    atom["source_type"] = metadata.get("source_type", "")

                logger.info(f"Extracted {len(atoms)} atoms")
                return atoms
            else:
                logger.error("LLM response was not a JSON array")
                return []
        else:
            logger.error("Could not find JSON array in LLM response")
            return []

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        return []
    except Exception as e:
        logger.error(f"Atom extraction failed: {e}")
        return []


def parser_node(state: RivetState) -> RivetState:
    """
    Parse raw document into structured atoms using LLM

    Args:
        state: Current graph state

    Returns:
        Updated state with atoms populated
    """
    state.logs.append("Starting parsing")

    if not state.raw_document:
        error_msg = "No raw document to parse"
        logger.error(f"[{state.job_id}] {error_msg}")
        state.errors.append(error_msg)
        return state

    try:
        # Extract atoms using LLM
        atoms = extract_atoms_from_text(state.raw_document, state.metadata)

        state.atoms = atoms
        state.atoms_created = len(atoms)

        logger.info(f"[{state.job_id}] Parsed {len(atoms)} atoms")
        state.logs.append(f"Extracted {len(atoms)} atoms")

    except Exception as e:
        error_msg = f"Parsing failed: {str(e)}"
        logger.error(f"[{state.job_id}] {error_msg}")
        state.errors.append(error_msg)

    return state
