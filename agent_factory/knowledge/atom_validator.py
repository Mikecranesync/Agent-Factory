"""
Knowledge Atom Validator

Automated validation for IEEE LOM-compliant knowledge atoms.
Validates schema compliance and quality metrics.

Usage:
    from agent_factory.knowledge.atom_validator import validate_atom_set

    atoms = load_atoms_from_json("atoms.json")
    report = validate_atom_set(atoms)
    print(f"Valid: {report['valid']}/{report['total']}")
"""

from typing import Dict, List, Tuple, Any
import json
import re


class AtomValidationError(Exception):
    """Raised when atom validation fails."""
    pass


def validate_knowledge_atom(atom: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single knowledge atom against IEEE LOM schema and quality metrics.

    Args:
        atom: Dictionary containing knowledge atom data

    Returns:
        Tuple of (is_valid, errors) where errors is list of validation failures

    Example:
        >>> atom = {"atom_id": "pattern:test", "type": "pattern", ...}
        >>> is_valid, errors = validate_knowledge_atom(atom)
        >>> if not is_valid:
        ...     print(f"Validation failed: {errors}")
    """
    errors = []

    # 1. SCHEMA VALIDATION - Required fields
    required_fields = [
        'atom_id', 'type', 'title', 'summary', 'content',
        'atom_type', 'vendor', 'equipment_type', 'source_document',
        'keywords', 'difficulty', 'prereqs', 'code_example'
    ]

    for field in required_fields:
        if field not in atom:
            errors.append(f"Missing required field: {field}")
        elif atom[field] is None:
            errors.append(f"Field '{field}' cannot be null")

    # 2. TYPE VALIDATION
    if 'type' in atom:
        valid_types = ['pattern', 'concept', 'fault', 'procedure', 'best-practice']
        if atom['type'] not in valid_types:
            errors.append(f"Invalid type '{atom['type']}'. Must be one of: {valid_types}")

    if 'atom_type' in atom:
        valid_atom_types = ['pattern', 'concept', 'fault', 'procedure', 'best-practice']
        if atom['atom_type'] not in valid_atom_types:
            errors.append(f"Invalid atom_type '{atom['atom_type']}'. Must be one of: {valid_atom_types}")

    if 'difficulty' in atom:
        valid_difficulties = ['beginner', 'moderate', 'advanced']
        if atom['difficulty'] not in valid_difficulties:
            errors.append(f"Invalid difficulty '{atom['difficulty']}'. Must be one of: {valid_difficulties}")

    # 3. ATOM_ID FORMAT VALIDATION
    if 'atom_id' in atom:
        # Format: type:vendor-pattern-name
        if not re.match(r'^[a-z-]+:[a-z0-9-]+$', atom['atom_id']):
            errors.append(f"Invalid atom_id format '{atom['atom_id']}'. Expected: 'type:vendor-pattern-name'")

    # 4. CONTENT QUALITY VALIDATION
    if 'content' in atom:
        content_len = len(str(atom['content']))
        if content_len < 300:
            errors.append(f"Content too short: {content_len} chars (minimum 300)")
        elif content_len > 5000:
            errors.append(f"Content too long: {content_len} chars (maximum 5000)")

    if 'summary' in atom:
        summary_len = len(str(atom['summary']))
        if summary_len < 50:
            errors.append(f"Summary too short: {summary_len} chars (minimum 50)")
        elif summary_len > 200:
            errors.append(f"Summary too long: {summary_len} chars (maximum 200)")

    if 'title' in atom:
        title_len = len(str(atom['title']))
        if title_len < 10:
            errors.append(f"Title too short: {title_len} chars (minimum 10)")
        elif title_len > 100:
            errors.append(f"Title too long: {title_len} chars (maximum 100)")

    # 5. CODE EXAMPLE VALIDATION
    if 'code_example' in atom:
        code_example = str(atom['code_example'])
        code_len = len(code_example)

        if code_len < 50:
            errors.append(f"Code example too short: {code_len} chars (minimum 50)")

        # Check for code fence markers
        if '```' not in code_example:
            errors.append("Code example missing markdown code fences (```)")

    # 6. KEYWORDS VALIDATION
    if 'keywords' in atom:
        keywords = atom['keywords']
        if not isinstance(keywords, list):
            errors.append(f"Keywords must be a list, got {type(keywords).__name__}")
        elif len(keywords) < 3:
            errors.append(f"Not enough keywords: {len(keywords)} (minimum 3)")
        elif len(keywords) > 15:
            errors.append(f"Too many keywords: {len(keywords)} (maximum 15)")
        else:
            # Check for empty or whitespace-only keywords
            for kw in keywords:
                if not kw or not str(kw).strip():
                    errors.append("Keywords cannot be empty or whitespace")
                    break

    # 7. PREREQUISITES VALIDATION
    if 'prereqs' in atom:
        prereqs = atom['prereqs']
        if not isinstance(prereqs, list):
            errors.append(f"Prerequisites must be a list, got {type(prereqs).__name__}")
        elif len(prereqs) > 10:
            errors.append(f"Too many prerequisites: {len(prereqs)} (maximum 10)")
        else:
            # Check format: concept:name or pattern:name
            for prereq in prereqs:
                if not re.match(r'^[a-z-]+:[a-z0-9-]+$', str(prereq)):
                    errors.append(f"Invalid prerequisite format '{prereq}'. Expected: 'type:name'")
                    break

    # 8. SOURCE DOCUMENT VALIDATION
    if 'source_document' in atom:
        source = str(atom['source_document'])
        if len(source) < 10:
            errors.append(f"Source document too short: {len(source)} chars (minimum 10)")

    # 9. VENDOR AND EQUIPMENT_TYPE VALIDATION
    if 'vendor' in atom:
        vendor = str(atom['vendor'])
        if len(vendor) < 2:
            errors.append(f"Vendor name too short: {len(vendor)} chars (minimum 2)")
        if not re.match(r'^[a-z0-9-]+$', vendor):
            errors.append(f"Invalid vendor format '{vendor}'. Use lowercase with hyphens only")

    if 'equipment_type' in atom:
        equipment = str(atom['equipment_type'])
        if len(equipment) < 2:
            errors.append(f"Equipment type too short: {len(equipment)} chars (minimum 2)")
        if not re.match(r'^[a-z0-9-]+$', equipment):
            errors.append(f"Invalid equipment_type format '{equipment}'. Use lowercase with hyphens only")

    return (len(errors) == 0, errors)


def validate_atom_set(atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate entire set of knowledge atoms and generate quality report.

    Args:
        atoms: List of knowledge atom dictionaries

    Returns:
        Validation report with counts and detailed errors

    Example:
        >>> atoms = load_atoms_from_json("atoms.json")
        >>> report = validate_atom_set(atoms)
        >>> print(f"Valid: {report['valid']}/{report['total']}")
        >>> if report['invalid'] > 0:
        ...     for error in report['errors']:
        ...         print(f"{error['atom_id']}: {error['errors']}")
    """
    report = {
        'total': len(atoms),
        'valid': 0,
        'invalid': 0,
        'errors': [],
        'quality_metrics': {
            'avg_content_length': 0,
            'avg_keywords': 0,
            'avg_prereqs': 0,
            'has_code_examples': 0,
            'type_distribution': {}
        }
    }

    total_content_len = 0
    total_keywords = 0
    total_prereqs = 0
    type_counts = {}

    for atom in atoms:
        # Validate atom
        is_valid, errors = validate_knowledge_atom(atom)

        if is_valid:
            report['valid'] += 1
        else:
            report['invalid'] += 1
            report['errors'].append({
                'atom_id': atom.get('atom_id', 'unknown'),
                'errors': errors
            })

        # Collect quality metrics
        if 'content' in atom:
            total_content_len += len(str(atom['content']))

        if 'keywords' in atom and isinstance(atom['keywords'], list):
            total_keywords += len(atom['keywords'])

        if 'prereqs' in atom and isinstance(atom['prereqs'], list):
            total_prereqs += len(atom['prereqs'])

        if 'code_example' in atom and len(str(atom.get('code_example', ''))) > 50:
            report['quality_metrics']['has_code_examples'] += 1

        if 'type' in atom:
            atom_type = atom['type']
            type_counts[atom_type] = type_counts.get(atom_type, 0) + 1

    # Calculate averages
    if report['total'] > 0:
        report['quality_metrics']['avg_content_length'] = total_content_len // report['total']
        report['quality_metrics']['avg_keywords'] = total_keywords / report['total']
        report['quality_metrics']['avg_prereqs'] = total_prereqs / report['total']
        report['quality_metrics']['type_distribution'] = type_counts

    return report


def load_and_validate_atoms(filepath: str) -> Dict[str, Any]:
    """
    Load atoms from JSON file and validate them.

    Args:
        filepath: Path to JSON file containing knowledge atoms

    Returns:
        Validation report

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON

    Example:
        >>> report = load_and_validate_atoms("data/atoms-core-repos.json")
        >>> if report['invalid'] > 0:
        ...     print(f"WARNING: {report['invalid']} invalid atoms found")
        ...     for error in report['errors']:
        ...         print(f"  {error['atom_id']}: {error['errors']}")
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both formats: {"atoms": [...]} and [...]
    if isinstance(data, dict) and 'atoms' in data:
        atoms = data['atoms']
    elif isinstance(data, list):
        atoms = data
    else:
        raise ValueError(f"Unexpected JSON structure. Expected dict with 'atoms' key or list of atoms")

    return validate_atom_set(atoms)


def print_validation_report(report: Dict[str, Any], verbose: bool = False) -> None:
    """
    Print formatted validation report to console.

    Args:
        report: Validation report from validate_atom_set()
        verbose: If True, show all error details
    """
    print("\n" + "=" * 60)
    print("KNOWLEDGE ATOM VALIDATION REPORT")
    print("=" * 60)

    print(f"\nTotal Atoms: {report['total']}")
    print(f"Valid: {report['valid']} ({100 * report['valid'] // report['total']}%)")
    print(f"Invalid: {report['invalid']} ({100 * report['invalid'] // report['total']}%)")

    print("\n--- Quality Metrics ---")
    metrics = report['quality_metrics']
    print(f"Average Content Length: {metrics['avg_content_length']} chars")
    print(f"Average Keywords per Atom: {metrics['avg_keywords']:.1f}")
    print(f"Average Prerequisites per Atom: {metrics['avg_prereqs']:.1f}")
    print(f"Atoms with Code Examples: {metrics['has_code_examples']} ({100 * metrics['has_code_examples'] // report['total']}%)")

    print("\n--- Type Distribution ---")
    for atom_type, count in metrics['type_distribution'].items():
        print(f"  {atom_type}: {count}")

    if report['invalid'] > 0:
        print(f"\n--- Validation Errors ({report['invalid']} atoms) ---")
        for error_entry in report['errors']:
            print(f"\n{error_entry['atom_id']}:")
            if verbose:
                for error in error_entry['errors']:
                    print(f"  - {error}")
            else:
                print(f"  - {len(error_entry['errors'])} errors (use verbose=True for details)")

    print("\n" + "=" * 60)

    if report['valid'] == report['total']:
        print("[OK] ALL ATOMS VALID - Ready for embedding generation")
    else:
        print(f"[WARN] {report['invalid']} ATOMS NEED FIXES")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    """
    Run validation on atoms-core-repos.json when executed directly.

    Usage:
        poetry run python agent_factory/knowledge/atom_validator.py
    """
    import sys

    filepath = "data/atoms-core-repos.json"

    try:
        report = load_and_validate_atoms(filepath)
        print_validation_report(report, verbose=True)

        # Exit with error code if any atoms are invalid
        sys.exit(0 if report['invalid'] == 0 else 1)

    except FileNotFoundError:
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {filepath}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
