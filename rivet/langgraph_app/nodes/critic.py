"""
Critic node: Validate extracted atoms
"""

import logging
from typing import List, Dict, Any
from langgraph_app.state import RivetState

logger = logging.getLogger(__name__)


def validate_atom(atom: Dict[str, Any]) -> List[str]:
    """
    Validate a single atom

    Args:
        atom: Atom dictionary to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["type", "title", "content"]
    for field in required_fields:
        if field not in atom or not atom[field]:
            errors.append(f"Missing required field: {field}")

    # Valid types
    valid_types = ["fault", "procedure", "concept", "pattern"]
    if atom.get("type") and atom["type"] not in valid_types:
        errors.append(f"Invalid type: {atom['type']} (must be one of {valid_types})")

    # Content length
    if atom.get("content") and len(atom["content"]) < 20:
        errors.append("Content too short (< 20 chars)")

    return errors


def critic_node(state: RivetState) -> RivetState:
    """
    Validate extracted atoms for quality and completeness

    Args:
        state: Current graph state

    Returns:
        Updated state with validation errors if any
    """
    state.logs.append("Starting critique")

    if not state.atoms:
        error_msg = "No atoms to validate"
        logger.warning(f"[{state.job_id}] {error_msg}")
        state.errors.append(error_msg)
        return state

    # Validate each atom
    valid_atoms = []
    validation_errors = []

    for i, atom in enumerate(state.atoms):
        atom_errors = validate_atom(atom)

        if atom_errors:
            validation_errors.extend([f"Atom {i}: {err}" for err in atom_errors])
            logger.warning(f"[{state.job_id}] Atom {i} validation failed: {atom_errors}")
        else:
            valid_atoms.append(atom)

    # Update state
    if validation_errors:
        state.errors.extend(validation_errors)
        logger.warning(
            f"[{state.job_id}] Validation: {len(valid_atoms)}/{len(state.atoms)} atoms valid"
        )

    # Keep only valid atoms
    state.atoms = valid_atoms

    # Log results
    state.logs.append(f"Validated {len(valid_atoms)} atoms")
    if validation_errors:
        state.logs.append(f"Rejected {len(state.atoms) - len(valid_atoms)} invalid atoms")

    logger.info(f"[{state.job_id}] Critique complete: {len(valid_atoms)} valid atoms")

    return state
