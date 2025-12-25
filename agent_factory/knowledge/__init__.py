"""
Knowledge Atom Management

This package provides tools for creating, validating, and managing knowledge atoms.

Modules:
    atom_validator: Validation for IEEE LOM-compliant knowledge atoms
"""

from .atom_validator import (
    validate_knowledge_atom,
    validate_atom_set,
    load_and_validate_atoms,
    print_validation_report,
    AtomValidationError
)

__all__ = [
    'validate_knowledge_atom',
    'validate_atom_set',
    'load_and_validate_atoms',
    'print_validation_report',
    'AtomValidationError'
]
