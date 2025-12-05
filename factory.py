"""
Factory.py - Constitutional Code Generator

Generated from: specs/factory-v1.0.md
Purpose: Reads markdown specifications and generates PLC-style annotated Python code

This is the meta-system that generates all other components from specs.
Code is disposable. Specs are eternal.

REGENERATION: python factory.py specs/factory-v1.0.md
Constitutional Authority: AGENTS.md Article II
"""

import re
import hashlib
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum

try:
    import typer
    from jinja2 import Environment, FileSystemLoader, Template
    import markdown
except ImportError as e:
    print(f"[FACTORY ERROR] Missing dependency: {e}")
    print("Install with: pip install typer jinja2 markdown")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class Requirement:
    """
    Single requirement from spec.

    Implements: REQ-FAC-008 (Requirement Format)
    Spec: specs/factory-v1.0.md#section-4.2
    """
    id: str                          # REQ-AGENT-NNN format
    section: str                     # Section number (e.g., "2.1")
    description: str                 # What this requirement does
    must_statements: List[str]       # MUST do these things
    must_not_statements: List[str]   # MUST NOT do these things
    should_statements: List[str]     # SHOULD do these things


@dataclass
class CodeBlock:
    """
    Code example from spec.

    Implements: REQ-FAC-009 (Code Block Format)
    """
    language: str                    # python, bash, json, etc.
    content: str                     # Actual code
    section: str                     # Which section it's from
    context: str                     # Surrounding description


@dataclass
class SpecModel:
    """
    Parsed specification representation.

    Implements: REQ-FAC-007 (Required Sections)
    Spec: specs/factory-v1.0.md#section-4.1
    """
    file_path: str
    title: str
    spec_type: str
    status: str
    created: str
    updated: str

    purpose: str                              # Section 1
    requirements: List[Requirement]           # Section 2+
    data_structures: List[CodeBlock]          # Classes, dataclasses
    examples: List[CodeBlock]                 # Usage examples
    dependencies: List[str]                   # External libs
    troubleshooting: Dict[str, str]           # Issue → solution

    # Computed fields
    spec_hash: str = ""
    agent_code: str = ""                      # e.g., "ORCH", "CB", "FAC"


# ═══════════════════════════════════════════════════════════════════════════
# SPEC PARSER
# Implements: REQ-FAC-001 (Spec Parsing)
# ═══════════════════════════════════════════════════════════════════════════


class SpecParser:
    """
    Parse markdown specifications into structured SpecModel.

    Implements: REQ-FAC-001
    Spec: specs/factory-v1.0.md#section-3.1
    """

    REQ_PATTERN = re.compile(r'\(REQ-([A-Z]+)-(\d+)\)')
    CODE_BLOCK_PATTERN = re.compile(r'```(\w+)\n(.*?)```', re.DOTALL)

    def parse(self, spec_path: str) -> SpecModel:
        """
        Parse markdown spec file into SpecModel.

        Implements: REQ-FAC-001

        Args:
            spec_path: Path to markdown spec file

        Returns:
            Parsed SpecModel with all sections

        Raises:
            FileNotFoundError: If spec file doesn't exist
            ValueError: If required sections missing
        """
        path = Path(spec_path)
        if not path.exists():
            raise FileNotFoundError(f"Spec not found: {spec_path}")

        content = path.read_text(encoding='utf-8')

        # Compute hash for audit trail
        spec_hash = hashlib.sha256(content.encode()).hexdigest()[:12]

        # Extract header metadata
        title, spec_type, status, created, updated = self._parse_header(content)

        # Extract agent code from title (e.g., "Orchestrator" → "ORCH")
        agent_code = self._extract_agent_code(title)

        # Parse main sections
        purpose = self._extract_section(content, "1. PURPOSE") or self._extract_section(content, "## 1. PURPOSE")
        requirements = self._parse_requirements(content)
        data_structures = self._parse_data_structures(content)
        examples = self._parse_examples(content)
        dependencies = self._parse_dependencies(content)
        troubleshooting = self._parse_troubleshooting(content)

        return SpecModel(
            file_path=spec_path,
            title=title,
            spec_type=spec_type,
            status=status,
            created=created,
            updated=updated,
            purpose=purpose,
            requirements=requirements,
            data_structures=data_structures,
            examples=examples,
            dependencies=dependencies,
            troubleshooting=troubleshooting,
            spec_hash=spec_hash,
            agent_code=agent_code
        )

    def _parse_header(self, content: str) -> Tuple[str, str, str, str, str]:
        """Extract header metadata from spec."""
        lines = content.split('\n')

        title = lines[0].replace('#', '').strip() if lines else "Unknown"
        spec_type = self._extract_field(content, "Spec Type")
        status = self._extract_field(content, "Status")
        created = self._extract_field(content, "Created")
        updated = self._extract_field(content, "Last Updated")

        return title, spec_type, status, created, updated

    def _extract_field(self, content: str, field_name: str) -> str:
        """Extract field value from markdown bold text."""
        pattern = rf'\*\*{field_name}\*\*:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""

    def _extract_agent_code(self, title: str) -> str:
        """
        Extract agent code from title.

        Examples:
            "Orchestrator Specification v1.0" → "ORCH"
            "Callbacks (Event System) Specification v1.0" → "CB"
            "Factory.py (Code Generator) Specification v1.0" → "FAC"
        """
        # Remove common words
        words = title.replace("Specification", "").replace("v1.0", "").strip()
        words = re.sub(r'\([^)]*\)', '', words).strip()

        # Take first word
        first_word = words.split()[0] if words.split() else "UNKNOWN"

        # Generate code (first 2-4 letters, uppercase)
        if len(first_word) <= 4:
            return first_word.upper()
        elif first_word.lower() == "orchestrator":
            return "ORCH"
        elif first_word.lower() == "callbacks":
            return "CB"
        elif first_word.lower() == "factory":
            return "FAC"
        else:
            return first_word[:4].upper()

    def _extract_section(self, content: str, section_header: str) -> str:
        """Extract content of a section until next header."""
        pattern = rf'{re.escape(section_header)}\n+(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _parse_requirements(self, content: str) -> List[Requirement]:
        """
        Parse all REQ-* requirements from spec.

        Implements: REQ-FAC-008
        """
        requirements = []

        # Find all requirement sections
        req_sections = re.finditer(r'###\s+([\d.]+)\s+(.+?)\s+\(REQ-([A-Z]+)-(\d+)\)', content)

        for match in req_sections:
            section_num = match.group(1)
            description = match.group(2).strip()
            agent_code = match.group(3)
            req_num = match.group(4)
            req_id = f"REQ-{agent_code}-{req_num}"

            # Extract content after this requirement header
            start_pos = match.end()
            next_header = re.search(r'\n###', content[start_pos:])
            end_pos = start_pos + next_header.start() if next_header else len(content)
            req_content = content[start_pos:end_pos]

            # Parse MUST/MUST NOT/SHOULD statements
            must = re.findall(r'\*\*MUST\*\*\s+(.+?)(?:\n|$)', req_content)
            must_not = re.findall(r'\*\*MUST NOT\*\*\s+(.+?)(?:\n|$)', req_content)
            should = re.findall(r'\*\*SHOULD\*\*\s+(.+?)(?:\n|$)', req_content)

            requirements.append(Requirement(
                id=req_id,
                section=section_num,
                description=description,
                must_statements=must,
                must_not_statements=must_not,
                should_statements=should
            ))

        return requirements

    def _parse_data_structures(self, content: str) -> List[CodeBlock]:
        """Extract data structure definitions from spec."""
        blocks = []

        # Look in "DATA STRUCTURES" section
        ds_section = self._extract_section(content, "## 3. DATA STRUCTURES")
        if not ds_section:
            ds_section = self._extract_section(content, "DATA STRUCTURES")

        # Find code blocks in that section
        for match in self.CODE_BLOCK_PATTERN.finditer(ds_section):
            lang = match.group(1)
            code = match.group(2).strip()

            if lang == 'python':
                blocks.append(CodeBlock(
                    language=lang,
                    content=code,
                    section="3",
                    context="Data Structures"
                ))

        return blocks

    def _parse_examples(self, content: str) -> List[CodeBlock]:
        """Extract usage examples from spec."""
        blocks = []

        # Look in "USAGE EXAMPLES" section
        examples_section = self._extract_section(content, "USAGE EXAMPLES")
        if not examples_section:
            examples_section = self._extract_section(content, "## 10. USAGE EXAMPLES")

        for match in self.CODE_BLOCK_PATTERN.finditer(examples_section):
            lang = match.group(1)
            code = match.group(2).strip()

            blocks.append(CodeBlock(
                language=lang,
                content=code,
                section="10",
                context="Usage Examples"
            ))

        return blocks

    def _parse_dependencies(self, content: str) -> List[str]:
        """Extract dependency list from spec."""
        deps = []

        # Look in DEPENDENCIES section
        dep_section = self._extract_section(content, "DEPENDENCIES")
        if not dep_section:
            dep_section = self._extract_section(content, "## 9. DEPENDENCIES")

        # Extract library names from markdown lists
        for line in dep_section.split('\n'):
            if line.strip().startswith('-') and '**' in line:
                # Format: - **library**: description
                lib_match = re.search(r'\*\*([^*]+)\*\*', line)
                if lib_match:
                    deps.append(lib_match.group(1).strip())

        return deps

    def _parse_troubleshooting(self, content: str) -> Dict[str, str]:
        """Extract troubleshooting issues and solutions."""
        issues = {}

        # Look in TROUBLESHOOTING section
        ts_section = self._extract_section(content, "TROUBLESHOOTING")
        if not ts_section:
            ts_section = self._extract_section(content, "## 11. TROUBLESHOOTING")

        # Parse "**Issue**: description" followed by "- Solution: fix"
        current_issue = None
        for line in ts_section.split('\n'):
            if line.startswith('**Issue**:'):
                current_issue = line.replace('**Issue**:', '').strip()
            elif current_issue and 'Solution:' in line:
                solution = line.split('Solution:')[-1].strip()
                issues[current_issue] = solution
                current_issue = None

        return issues


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATOR
# Implements: REQ-FAC-012 (Spec Validation)
# ═══════════════════════════════════════════════════════════════════════════


class SpecValidator:
    """
    Validate spec format and completeness.

    Implements: REQ-FAC-012
    Spec: specs/factory-v1.0.md#section-6.1
    """

    REQUIRED_SECTIONS = [
        "PURPOSE",
        "REQUIREMENTS",
        "DATA STRUCTURES",
        "DEPENDENCIES",
        "USAGE EXAMPLES"
    ]

    def validate(self, spec: SpecModel) -> Tuple[bool, List[str]]:
        """
        Validate spec compliance.

        Args:
            spec: Parsed SpecModel to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required sections
        if not spec.purpose:
            errors.append("Missing section: PURPOSE")

        if not spec.requirements:
            errors.append("Missing section: REQUIREMENTS (no REQ-* found)")

        if not spec.data_structures:
            errors.append("Missing section: DATA STRUCTURES")

        if not spec.dependencies:
            errors.append("Missing section: DEPENDENCIES")

        if not spec.examples:
            errors.append("Missing section: USAGE EXAMPLES")

        # Check requirement format
        for req in spec.requirements:
            if not req.id.startswith('REQ-'):
                errors.append(f"Invalid requirement ID: {req.id}")

            if not req.must_statements and not req.must_not_statements:
                errors.append(f"{req.id}: No MUST/MUST NOT statements")

        # Check for duplicate requirement IDs
        req_ids = [r.id for r in spec.requirements]
        duplicates = [rid for rid in req_ids if req_ids.count(rid) > 1]
        if duplicates:
            errors.append(f"Duplicate requirement IDs: {set(duplicates)}")

        return (len(errors) == 0, errors)


# ═══════════════════════════════════════════════════════════════════════════
# CLI APPLICATION
# Implements: REQ-FAC-004 (CLI Interface)
# ═══════════════════════════════════════════════════════════════════════════


app = typer.Typer(help="Constitutional Code Generator - Generate code from specs")


@app.command()
def generate(
    spec_file: str = typer.Argument(..., help="Path to spec file (e.g., specs/orchestrator-v1.0.md)"),
    output_dir: str = typer.Option(".", help="Output directory for generated code"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    Generate code and tests from specification file.

    Implements: REQ-FAC-018 (Generate from Spec File)
    """
    try:
        # Parse spec
        parser = SpecParser()
        spec = parser.parse(spec_file)

        if verbose:
            print(f"[FACTORY] Parsed: {spec.title}")
            print(f"[FACTORY] Requirements: {len(spec.requirements)}")

        # Validate spec
        validator = SpecValidator()
        is_valid, errors = validator.validate(spec)

        if not is_valid:
            print("[FACTORY ERROR] Spec validation failed:")
            for error in errors:
                print(f"  - {error}")
            raise typer.Exit(1)

        if verbose:
            print("[FACTORY] Validation: PASSED")

        # TODO: Generate code (Phase 2)
        print(f"[FACTORY] Code generation not yet implemented")
        print(f"[FACTORY] Spec parsed successfully: {spec.agent_code}")
        print(f"[FACTORY] Found {len(spec.requirements)} requirements")

    except Exception as e:
        print(f"[FACTORY ERROR] {e}")
        raise typer.Exit(1)


@app.command()
def validate(
    spec_path: str = typer.Argument(..., help="Path to spec file or directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    Validate specification format without generating code.

    Implements: REQ-FAC-020 (Spec Validation)
    """
    path = Path(spec_path)

    if path.is_file():
        specs = [path]
    elif path.is_dir():
        specs = list(path.glob("*.md"))
    else:
        print(f"[FACTORY ERROR] Path not found: {spec_path}")
        raise typer.Exit(1)

    parser = SpecParser()
    validator = SpecValidator()

    total = len(specs)
    passed = 0

    print(f"[FACTORY] Validating {total} spec(s)...")

    for spec_file in specs:
        try:
            spec = parser.parse(str(spec_file))
            is_valid, errors = validator.validate(spec)

            if is_valid:
                print(f"  [OK] {spec_file.name}")
                passed += 1
            else:
                print(f"  [FAIL] {spec_file.name}")
                for error in errors:
                    print(f"      - {error}")
        except Exception as e:
            print(f"  [FAIL] {spec_file.name}")
            print(f"      - Parse error: {e}")

    print(f"\n[FACTORY] Result: {passed}/{total} valid")

    if passed < total:
        raise typer.Exit(1)


@app.command()
def info(
    spec_file: str = typer.Argument(..., help="Path to spec file")
):
    """Show detailed information about a specification."""
    parser = SpecParser()
    spec = parser.parse(spec_file)

    print(f"\nSpec: {spec.title}")
    print(f"Type: {spec.spec_type}")
    print(f"Status: {spec.status}")
    print(f"Hash: {spec.spec_hash}")
    print(f"\nRequirements: {len(spec.requirements)}")
    for req in spec.requirements:
        print(f"  - {req.id}: {req.description}")
    print(f"\nData Structures: {len(spec.data_structures)}")
    print(f"Examples: {len(spec.examples)}")
    print(f"Dependencies: {', '.join(spec.dependencies) if spec.dependencies else 'None'}")


if __name__ == "__main__":
    app()
