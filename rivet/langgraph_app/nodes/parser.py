"""
Parser Node - Extract structured atoms using LLM

Uses Ollama LLM to parse raw document text into knowledge atoms.
"""

import logging
import json
import requests
from typing import Dict, Any, List
from langgraph_app.state import RivetState, KnowledgeAtom
from langgraph_app.config import settings

logger = logging.getLogger(__name__)


def parser_node(state: RivetState) -> Dict[str, Any]:
    """
    Parse raw document into structured knowledge atoms using LLM

    Calls Ollama LLM with schema-constrained prompt to extract:
    - Faults (error codes, symptoms, causes, fixes)
    - Patterns (procedures, configurations)
    - Concepts (definitions, explanations)

    Args:
        state: Current workflow state

    Returns:
        Updated state with atoms populated
    """
    logger.info(f"[{state.job_id}] Parser node started")

    if not state.raw_document:
        state.errors.append("No raw document to parse")
        return state.dict()

    # Chunk document if too large (LLM context limits)
    chunks = chunk_document(state.raw_document, max_chars=4000)
    logger.info(f"[{state.job_id}] Split into {len(chunks)} chunks")

    all_atoms = []

    for i, chunk in enumerate(chunks, 1):
        logger.info(f"[{state.job_id}] Processing chunk {i}/{len(chunks)}")

        try:
            atoms = extract_atoms_from_chunk(chunk, state.metadata)
            all_atoms.extend(atoms)
            state.logs.append(f"Chunk {i}: extracted {len(atoms)} atoms")

        except Exception as e:
            error_msg = f"Chunk {i} parsing failed: {str(e)}"
            state.errors.append(error_msg)
            logger.error(f"[{state.job_id}] {error_msg}")

    state.atoms = all_atoms
    state.stats["total_atoms"] = len(all_atoms)
    state.logs.append(f"Total atoms extracted: {len(all_atoms)}")

    logger.info(f"[{state.job_id}] Parsing complete: {len(all_atoms)} atoms")

    return state.dict()


def chunk_document(text: str, max_chars: int = 4000) -> List[str]:
    """
    Split document into chunks for LLM processing

    Args:
        text: Full document text
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    chunks = []
    current_chunk = []
    current_length = 0

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        para_length = len(para)

        if current_length + para_length > max_chars and current_chunk:
            # Save current chunk and start new one
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_length = para_length
        else:
            current_chunk.append(para)
            current_length += para_length

    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def extract_atoms_from_chunk(chunk: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract knowledge atoms from text chunk using Ollama LLM

    Args:
        chunk: Text to parse
        metadata: Document metadata

    Returns:
        List of atom dictionaries
    """
    prompt = build_extraction_prompt(chunk, metadata)

    try:
        # Call Ollama API
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"  # Request JSON output
            },
            timeout=settings.TIMEOUT_SECONDS
        )
        response.raise_for_status()

        result = response.json()
        generated_text = result.get("response", "")

        # Parse JSON response
        atoms_data = json.loads(generated_text)

        # Validate against schema
        if isinstance(atoms_data, dict) and "atoms" in atoms_data:
            atoms = atoms_data["atoms"]
        elif isinstance(atoms_data, list):
            atoms = atoms_data
        else:
            logger.warning(f"Unexpected LLM response format: {type(atoms_data)}")
            return []

        # Validate each atom
        validated_atoms = []
        for atom_dict in atoms:
            try:
                # Add metadata
                atom_dict["source_url"] = metadata.get("source_url")

                # Validate with Pydantic
                atom = KnowledgeAtom(**atom_dict)
                validated_atoms.append(atom.dict())

            except Exception as e:
                logger.warning(f"Atom validation failed: {e}")

        return validated_atoms

    except requests.RequestException as e:
        logger.error(f"Ollama API error: {e}")
        return []

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return []


def build_extraction_prompt(text: str, metadata: Dict[str, Any]) -> str:
    """
    Build prompt for LLM extraction

    Args:
        text: Text to analyze
        metadata: Document metadata

    Returns:
        Structured prompt
    """
    return f"""Extract knowledge atoms from this industrial/PLC documentation.

DOCUMENT METADATA:
Vendor: {metadata.get('vendor', 'unknown')}
Product: {metadata.get('product', 'unknown')}

TEXT TO ANALYZE:
{text[:2000]}

EXTRACTION RULES:
1. Identify knowledge atoms of these types:
   - fault: Error codes with symptoms, causes, fixes
   - pattern: Programming patterns, procedures, configurations
   - concept: Definitions, explanations, theory

2. For each atom, extract:
   - atom_type: (fault|pattern|concept)
   - title: Clear descriptive title
   - summary: 1-2 sentence summary
   - content: Full detailed content
   - keywords: List of search keywords

3. For faults, also extract:
   - code: Error/fault code
   - symptoms: Observable symptoms list
   - causes: Possible causes list
   - fixes: Remediation steps list

4. For patterns, also extract:
   - pattern_type: Type of pattern
   - steps: Implementation steps list
   - prerequisites: Prerequisites list

OUTPUT FORMAT (JSON):
{{
  "atoms": [
    {{
      "atom_type": "fault",
      "title": "Motor Overcurrent Fault",
      "summary": "Motor trips on excessive current draw",
      "content": "...",
      "code": "F0010",
      "symptoms": ["Motor stops", "Alarm flashing"],
      "causes": ["Jam", "Short"],
      "fixes": ["Check wiring", "Test motor"],
      "keywords": ["motor", "overcurrent", "fault"]
    }}
  ]
}}

Extract all atoms from the text above. Return valid JSON only.
"""
