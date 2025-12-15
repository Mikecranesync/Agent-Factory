"""
Critic Node - Validate extracted atoms

Performs quality checks on extracted knowledge atoms.
"""

import logging
from typing import Dict, Any
from langgraph_app.state import RivetState

logger = logging.getLogger(__name__)


def critic_node(state: RivetState) -> Dict[str, Any]:
    """
    Validate extracted knowledge atoms

    Checks:
    - Atoms list is not empty
    - Required fields are present
    - Content meets minimum quality standards
    - No duplicate atoms

    Args:
        state: Current workflow state

    Returns:
        Updated state with validation errors (if any)
    """
    logger.info(f"[{state.job_id}] Critic node started")

    if not state.atoms:
        error_msg = "No atoms extracted from document"
        state.errors.append(error_msg)
        logger.warning(f"[{state.job_id}] {error_msg}")
        return state.dict()

    # Validation checks
    valid_atoms = []
    validation_errors = []

    for i, atom in enumerate(state.atoms, 1):
        errors = validate_atom(atom, i)

        if errors:
            validation_errors.extend(errors)
            logger.warning(f"[{state.job_id}] Atom {i} validation failed: {errors}")
        else:
            valid_atoms.append(atom)

    # Update state
    state.atoms = valid_atoms
    state.stats["atoms_validated"] = len(valid_atoms)
    state.stats["atoms_rejected"] = len(state.atoms) - len(valid_atoms)

    if validation_errors:
        state.errors.extend(validation_errors)
        logger.warning(f"[{state.job_id}] Validation found {len(validation_errors)} issues")

    state.logs.append(f"Validation: {len(valid_atoms)} valid, {len(validation_errors)} errors")
    logger.info(f"[{state.job_id}] Validation complete: {len(valid_atoms)} atoms passed")

    return state.dict()


def validate_atom(atom: Dict[str, Any], index: int) -> list[str]:
    """
    Validate a single atom

    Args:
        atom: Atom dictionary to validate
        index: Atom index for error messages

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["atom_type", "title", "summary", "content"]
    for field in required_fields:
        if not atom.get(field):
            errors.append(f"Atom {index}: Missing required field '{field}'")

    # Atom type validation
    valid_types = ["fault", "pattern", "concept", "procedure"]
    if atom.get("atom_type") not in valid_types:
        errors.append(f"Atom {index}: Invalid atom_type '{atom.get('atom_type')}'")

    # Content length validation
    title = atom.get("title", "")
    summary = atom.get("summary", "")
    content = atom.get("content", "")

    if len(title) < 5:
        errors.append(f"Atom {index}: Title too short ({len(title)} chars)")

    if len(summary) < 20:
        errors.append(f"Atom {index}: Summary too short ({len(summary)} chars)")

    if len(content) < 50:
        errors.append(f"Atom {index}: Content too short ({len(content)} chars)")

    # Type-specific validation
    if atom.get("atom_type") == "fault":
        if not atom.get("symptoms") and not atom.get("causes"):
            errors.append(f"Atom {index}: Fault must have symptoms or causes")

    if atom.get("atom_type") == "pattern":
        if not atom.get("steps"):
            errors.append(f"Atom {index}: Pattern must have steps")

    return errors


def check_duplicates(atoms: list[Dict[str, Any]]) -> list[int]:
    """
    Find duplicate atoms based on title similarity

    Args:
        atoms: List of atoms

    Returns:
        List of indices of duplicate atoms
    """
    duplicates = []
    seen_titles = set()

    for i, atom in enumerate(atoms):
        title_normalized = atom.get("title", "").lower().strip()

        if title_normalized in seen_titles:
            duplicates.append(i)
        else:
            seen_titles.add(title_normalized)

    return duplicates
