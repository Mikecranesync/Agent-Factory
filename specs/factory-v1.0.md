# Factory.py (Code Generator) Specification v1.0

**Spec Type**: Meta-System (Generates All Other Components)
**Constitutional Authority**: AGENTS.md Article II (Claude Code CLI Mandate)
**Status**: APPROVED
**Created**: 2025-12-05
**Last Updated**: 2025-12-05

---

## 1. PURPOSE

Factory.py is the code generation engine that reads markdown specifications and produces PLC-style annotated Python code with corresponding tests.

**Design Goal**: Enable non-programmers to maintain agent systems by editing English specs, then regenerating code automatically.

**Analogy**: Like a compiler - turns high-level specs (source) into executable code (binary), maintaining perfect traceability.

---

## 2. CONSTITUTIONAL MANDATE (Article II)

Factory.py MUST implement the exact workflow specified in AGENTS.md:

```
1. READ AGENTS.md FIRST ← Confirm constitutional compliance
2. Extract user intent → Write/review SPEC.md
3. Generate annotated code.py (PLC-style)
4. Generate tests.py (spec compliance)
5. Show regeneration instructions
```

**Response Structure Mandate**:
```
SPEC GENERATED: [agent-name]-v1.0.md
[full spec content]

CODE GENERATED: [agent-name].py
[PLC-style annotated code]

TESTS GENERATED: test_[agent-name].py
[spec validation tests]

REGENERATION:
Run: python factory.py specs/[agent-name]-v1.0.md
```

---

## 3. REQUIREMENTS

### 3.1 Spec Parsing (REQ-FAC-001)

**MUST** parse markdown specification files and extract:
- **Requirements** (REQ-* identifiers with descriptions)
- **Data structures** (classes, dataclasses, type definitions)
- **Behaviors** (MUST/MUST NOT statements)
- **Examples** (code blocks marked with language)
- **Troubleshooting** (common issues and solutions)
- **Dependencies** (external libraries, internal modules)

**Parsing Strategy**:
- Read markdown file line-by-line
- Identify sections by headers (## Section Name)
- Extract REQ-* requirements with regex: `(REQ-[A-Z]+-\d+)`
- Parse code blocks: ` ```python ... ``` `
- Build internal spec representation (dict/dataclass)

### 3.2 PLC-Style Code Generation (REQ-FAC-002)

**MUST** generate Python code following Article IV (Commenting Mandate):

**Every function MUST have rung header**:
```python
═══════════════════════════════════════════════════════════════
RUNG X: [Clear purpose in 1 line]
Spec: specs/[agent]-vX.Y.md#section-Y
Inputs: [explicit types]
Outputs: [explicit types]
Troubleshooting: [first 3 things to check]
═══════════════════════════════════════════════════════════════
def rung_x_function(input: Type) -> OutputType:
    # INLINE: What this line does (1 sentence max)
    result = do_something(input)

    # ASSERT: Safety check (PLC interlock equivalent)
    assert condition, "PLC-style error message"

    return result
```

**Code Generation Rules**:
1. Module docstring references spec file
2. All imports organized (stdlib → external → internal)
3. Type hints on all functions
4. Each requirement (REQ-*) maps to 1+ functions
5. Rung headers link back to spec section
6. Inline comments explain non-obvious logic
7. Assert statements validate inputs/state
8. Error messages cite spec requirements

### 3.3 Test Generation (REQ-FAC-003)

**MUST** generate pytest tests that validate spec compliance:

**Test Structure**:
```python
"""
Tests for [agent-name]
Generated from: specs/[agent-name]-vX.Y.md
"""

class Test[RequirementID]:
    """Tests for REQ-[AGENT]-XXX: [requirement description]"""

    def test_[specific_behavior](self):
        """
        Validates: specs/[agent]-vX.Y.md#section-Y
        Requirement: REQ-[AGENT]-XXX
        """
        # Arrange
        # Act
        # Assert
```

**Test Coverage Requirements**:
- Every REQ-* has at least 1 test
- Every MUST statement validated
- Every MUST NOT statement validated
- Error cases explicitly tested
- Examples from spec used as test cases

### 3.4 CLI Interface (REQ-FAC-004)

**MUST** provide command-line interface with these commands:

**Generate from natural language**:
```bash
python factory.py "build email triage agent" --spec-only-first
# Outputs: specs/email-triage-v1.0.md
# User reviews/edits spec
# Then runs: python factory.py specs/email-triage-v1.0.md
```

**Generate from existing spec**:
```bash
python factory.py specs/orchestrator-v1.0.md
# Outputs: code/orchestrator.py + tests/test_orchestrator.py
```

**Regenerate all**:
```bash
python factory.py --full-regen
# Reads all specs/*.md
# Regenerates all code/* and tests/*
# Reports changes (git diff summary)
```

**Validate specs**:
```bash
python factory.py --validate specs/
# Checks all specs for required sections
# Verifies REQ-* format consistency
# Reports missing/invalid specs
```

**Show regeneration instructions**:
```bash
python factory.py --howto [agent-name]
# Displays exact commands to regenerate specific agent
```

### 3.5 Constitutional Enforcement (REQ-FAC-005)

**MUST** enforce AGENTS.md Article V (Anti-Sycophancy Clauses):

**SY-73 Enforcement**: Never compliment, cite conflicts
```python
# If user asks to change working code without spec update:
print("CONSTITUTIONAL VIOLATION: Article I")
print("Code NEVER supersedes specs.")
print("Update specs/[agent]-vX.Y.md first, then regenerate.")
sys.exit(1)
```

**SY-40 Enforcement**: Demand clarity
```python
# If spec is vague or incomplete:
print("SPEC INCOMPLETE: Section [X] requirements unclear")
print("Required: Explicit MUST/MUST NOT statements")
print("Add REQ-* identifiers for all behaviors")
sys.exit(1)
```

**PLC-1 Enforcement**: Input validation
```python
# Generated code MUST include:
assert input_value is not None, "PLC INTERLOCK: Input cannot be None"
assert len(items) > 0, "PLC INTERLOCK: Empty list rejected"
```

**PLC-2 Enforcement**: Explicit error handling
```python
# Every external call wrapped in try/except:
try:
    result = external_service()
except SpecificError as e:
    # Troubleshooting: Check [spec reference]
    raise AgentError(f"Failed: {e}") from e
```

### 3.6 Audit Trail (REQ-FAC-006)

**MUST** maintain traceability:

**Generated code header**:
```python
"""
Generated from: specs/orchestrator-v1.0.md
Generated on: 2025-12-05 14:32:00 UTC
Generator: factory.py v1.0
Spec SHA256: a3f5e9d8c2b1...

REGENERATION:
Run: python factory.py specs/orchestrator-v1.0.md

WARNING: Manual edits will be overwritten on regeneration.
         Update the spec instead.
"""
```

**Git integration**:
```python
# After generation, factory.py suggests:
print("COMMIT RECOMMENDATION:")
print("git add specs/ code/ tests/")
print("git commit -m 'Regenerated from specs/orchestrator-v1.0.md'")
print("git tag orchestrator-v1.0")
```

---

## 4. INPUT SPEC FORMAT

### 4.1 Required Sections (REQ-FAC-007)

**Every spec file MUST contain** (validation enforced):

1. **Header**: Title, type, authority, status, dates
2. **PURPOSE**: 1-2 paragraphs describing what and why
3. **REQUIREMENTS**: Numbered REQ-* items with MUST/MUST NOT
4. **DATA STRUCTURES**: Classes, types, schemas
5. **BEHAVIORAL SPECIFICATIONS**: How things work
6. **ERROR HANDLING**: Required error cases
7. **TESTING REQUIREMENTS**: What tests must validate
8. **DEPENDENCIES**: External and internal
9. **USAGE EXAMPLES**: Working code snippets
10. **TROUBLESHOOTING**: Common issues and solutions

**Optional Sections**:
- Performance Requirements
- Configuration
- Future Enhancements
- Spec Version History

### 4.2 Requirement Format (REQ-FAC-008)

**Standard format**:
```
### X.Y Section Name (REQ-AGENT-NNN)

**MUST** do something specific and testable.

**MUST NOT** do something that would break requirements.

**SHOULD** optionally do something (not enforced).
```

**Requirement ID format**:
- Pattern: `REQ-[AGENT]-[NNN]`
- AGENT: 2-4 letter code (ORCH, CB, FAC, etc.)
- NNN: Sequential 3-digit number (001, 002, ...)
- Example: REQ-ORCH-001, REQ-CB-014

### 4.3 Code Block Format (REQ-FAC-009)

**Spec examples become test cases**:
```markdown
### Usage Example

```python
# This code block will be extracted and used in tests
factory = AgentFactory()
agent = factory.create_agent(role="Test", tools_list=[])
assert agent is not None
```
```

**Factory.py extracts**:
- Language tag (python, bash, json)
- Code content (exact, preserving indentation)
- Surrounding context (section name, description)

---

## 5. CODE GENERATION ALGORITHM

### 5.1 Generation Pipeline (REQ-FAC-010)

**Phase 1: Parse Spec**
```
Read markdown file
↓
Extract sections (headers, content)
↓
Parse requirements (REQ-* items)
↓
Parse data structures (code blocks)
↓
Parse examples (usage snippets)
↓
Build SpecModel (internal representation)
```

**Phase 2: Plan Code**
```
Group requirements by functional area
↓
Identify core classes/functions needed
↓
Map REQ-* to implementation units
↓
Determine import dependencies
↓
Generate function signatures
```

**Phase 3: Generate Code**
```
Write module docstring (with spec reference)
↓
Write imports (organized by type)
↓
Write data structures (from spec section)
↓
Write functions (one per requirement group)
↓
Add rung headers (link to spec sections)
↓
Add inline comments (explain logic)
↓
Add assertions (validate inputs/state)
↓
Format code (black/isort)
```

**Phase 4: Generate Tests**
```
Create test class per requirement
↓
Create test method per MUST statement
↓
Use spec examples as test cases
↓
Add docstrings (cite spec sections)
↓
Format tests (pytest style)
```

**Phase 5: Output Files**
```
Write code/[agent].py
Write tests/test_[agent].py
Write REGENERATION.md (instructions)
Print summary to console
```

### 5.2 Template System (REQ-FAC-011)

**Use Jinja2 templates** for code generation:

**code_template.py.j2**:
```python
"""
Generated from: {{ spec_file }}
Generated on: {{ timestamp }}
Spec SHA256: {{ spec_hash }}

REGENERATION: python factory.py {{ spec_file }}
"""

{% for import in imports %}
{{ import }}
{% endfor %}

{% for dataclass in dataclasses %}
═══════════════════════════════════════════════════════════════
RUNG {{ loop.index }}: {{ dataclass.purpose }}
Spec: {{ spec_file }}#section-{{ dataclass.section }}
Inputs: {{ dataclass.inputs }}
Outputs: {{ dataclass.name }}
═══════════════════════════════════════════════════════════════
@dataclass
class {{ dataclass.name }}:
    {% for field in dataclass.fields %}
    {{ field.name }}: {{ field.type }}  # {{ field.description }}
    {% endfor %}
{% endfor %}

# ... more templates ...
```

**test_template.py.j2**:
```python
"""
Tests for {{ agent_name }}
Generated from: {{ spec_file }}
"""
import pytest
from {{ module_path }} import {{ classes }}

{% for requirement in requirements %}
class Test{{ requirement.id }}:
    """{{ requirement.description }}"""

    {% for test_case in requirement.test_cases %}
    def test_{{ test_case.name }}(self):
        """
        Validates: {{ spec_file }}#{{ requirement.section }}
        Requirement: {{ requirement.id }}
        """
        {{ test_case.code | indent(8) }}
    {% endfor %}
{% endfor %}
```

---

## 6. VALIDATION & ENFORCEMENT

### 6.1 Spec Validation (REQ-FAC-012)

**Before generating code, factory.py MUST validate**:
- All required sections present
- At least one REQ-* identifier exists
- REQ-* IDs are unique
- Code blocks have language tags
- Data structures are valid Python syntax
- Examples are runnable (syntax check)
- Dependencies listed are installable

**Validation failure** → Exit with error, cite missing/invalid section

### 6.2 Code Quality Enforcement (REQ-FAC-013)

**Generated code MUST pass**:
- Python syntax check (`ast.parse()`)
- Type hint validation (`mypy --strict`)
- Style check (`black --check`, `isort --check`)
- Linting (`ruff check`)

**If quality check fails** → Report error, suggest spec fix

### 6.3 Test Coverage Enforcement (REQ-FAC-014)

**Generated tests MUST**:
- Cover every REQ-* requirement (1:1 mapping)
- Include at least one assertion per test
- Run without errors (`pytest --collect-only`)
- Have descriptive names (`test_[requirement]_[behavior]`)

**Coverage report**:
```
SPEC COVERAGE:
✓ REQ-ORCH-001: 3 tests
✓ REQ-ORCH-002: 2 tests
✗ REQ-ORCH-003: 0 tests ← ERROR: No tests generated

BLOCKING: Cannot proceed without full coverage
UPDATE: Add test cases for REQ-ORCH-003 in spec
```

---

## 7. REGENERATION WORKFLOW

### 7.1 Spec-First Development (REQ-FAC-015)

**The constitutional workflow**:

```
Step 1: Update spec
$ vim specs/orchestrator-v1.0.md
# Add new requirement: REQ-ORCH-014
# Describe behavior in MUST statements

Step 2: Validate spec
$ python factory.py --validate specs/orchestrator-v1.0.md
VALIDATION: ✓ All required sections present
VALIDATION: ✓ 14 requirements found
VALIDATION: ✓ Syntax valid

Step 3: Regenerate code
$ python factory.py specs/orchestrator-v1.0.md
GENERATING: code/orchestrator.py
GENERATING: tests/test_orchestrator.py
CHANGES: +45 lines, +2 functions, +3 tests

Step 4: Review diff
$ git diff code/orchestrator.py
# Review generated changes
# Verify rung headers link to new requirement

Step 5: Run tests
$ pytest tests/test_orchestrator.py -v
✓ 14/14 tests pass

Step 6: Commit
$ git add specs/ code/ tests/
$ git commit -m "feat: Add REQ-ORCH-014 routing cache"
$ git tag orchestrator-v1.1
```

### 7.2 Handling Manual Edits (REQ-FAC-016)

**If user manually edits generated code**:

```
$ python factory.py specs/orchestrator-v1.0.md

WARNING: code/orchestrator.py was manually modified
Last generated: 2025-12-05 10:00:00
Last modified: 2025-12-05 11:30:00

CONFLICT: Manual edits will be OVERWRITTEN
OPTIONS:
1. Cancel (preserve manual edits)
2. Backup manual edits, then regenerate
3. Force regenerate (lose manual edits)

Choice [1/2/3]: _
```

**Best practice**: Never manual edit, always update spec

---

## 8. CLI COMMAND SPECIFICATIONS

### 8.1 Generate from Natural Language (REQ-FAC-017)

```bash
python factory.py "build email triage agent that filters spam" --spec-only-first
```

**Behavior**:
1. Parse natural language intent
2. Use LLM to generate initial spec (using spec template)
3. Save as `specs/email-triage-v1.0.md`
4. Print: "SPEC CREATED: Review and edit, then run: python factory.py specs/email-triage-v1.0.md"

**LLM Prompt Template**:
```
You are a spec writer. Convert this intent into a formal specification:

Intent: {{ user_input }}

Output a markdown spec following this template:
[spec_template.md contents]

Requirements must be:
- Specific and testable (MUST/MUST NOT statements)
- Numbered with REQ-* identifiers
- Linked to data structures and behaviors
```

### 8.2 Generate from Spec File (REQ-FAC-018)

```bash
python factory.py specs/orchestrator-v1.0.md
```

**Behavior**:
1. Validate spec format
2. Parse requirements, data structures, examples
3. Generate `code/orchestrator.py` with PLC annotations
4. Generate `tests/test_orchestrator.py` with spec validation
5. Print summary:
   ```
   GENERATED: code/orchestrator.py (350 lines, 12 functions)
   GENERATED: tests/test_orchestrator.py (180 lines, 14 tests)

   NEXT STEPS:
   1. Review generated code
   2. Run: pytest tests/test_orchestrator.py
   3. Commit: git add specs/ code/ tests/
   ```

### 8.3 Full Regeneration (REQ-FAC-019)

```bash
python factory.py --full-regen
```

**Behavior**:
1. Find all specs/*.md files
2. For each spec:
   - Validate format
   - Regenerate code/[agent].py
   - Regenerate tests/test_[agent].py
3. Print change summary:
   ```
   REGENERATED: 5 agents
   ✓ orchestrator: No changes
   ✓ callbacks: No changes
   ✓ email-triage: +20 lines (new requirement added)
   ✗ spam-filter: FAILED (spec invalid, see specs/spam-filter-v1.0.md:45)
   ✓ scheduler: +5 lines (docstring updated)

   NEXT: Review diffs, run tests, commit
   ```

### 8.4 Spec Validation (REQ-FAC-020)

```bash
python factory.py --validate specs/
```

**Behavior**:
1. Find all specs/*.md in directory
2. Validate each spec:
   - Required sections present
   - REQ-* format correct
   - Code blocks valid syntax
   - Dependencies listed
3. Report validation results:
   ```
   VALIDATING: 5 specs
   ✓ specs/orchestrator-v1.0.md
   ✓ specs/callbacks-v1.0.md
   ✗ specs/email-triage-v1.0.md
     ERROR: Missing section "TESTING REQUIREMENTS"
     ERROR: REQ-EMAIL-005 has no description
   ✓ specs/spam-filter-v1.0.md
   ✓ specs/scheduler-v1.0.md

   RESULT: 3/5 valid, 2 need fixes
   ```

---

## 9. DEPENDENCIES

### 9.1 Required Libraries (REQ-FAC-021)

**Core**:
- **jinja2**: Template rendering for code generation
- **python-markdown**: Parsing markdown specs
- **click** or **typer**: CLI framework
- **pyyaml**: Configuration files

**Code Quality**:
- **black**: Code formatting
- **isort**: Import sorting
- **ruff**: Fast linting
- **mypy**: Type checking

**Testing**:
- **pytest**: Test runner
- **coverage**: Test coverage

**Optional**:
- **anthropic** or **openai**: LLM for natural language → spec
- **git**: Audit trail and diff reporting

### 9.2 Python Version (REQ-FAC-022)

**Minimum**: Python 3.10 (for match/case, better type hints)

**Generated code compatibility**: Python 3.10+ (uses modern features)

---

## 10. ERROR HANDLING

### 10.1 Required Error Cases (REQ-FAC-023)

**MUST** handle gracefully:
1. Spec file not found → Clear error with path checked
2. Invalid markdown syntax → Report line number
3. Missing required section → Cite AGENTS.md Article reference
4. Invalid REQ-* format → Show correct format
5. Code generation failure → Preserve partial output, report error
6. Test generation failure → Skip tests, generate code only
7. Template rendering error → Show template file and line
8. Manual edit conflict → Prompt user for resolution

**Error Message Format**:
```
[FACTORY ERROR] {error_type}
File: {spec_file}:{line_number}
Issue: {description}
Fix: {suggested_action}
Ref: AGENTS.md Article {X}
```

---

## 11. CONFIGURATION

### 11.1 factory.config.yaml (REQ-FAC-024)

**Optional config file for customization**:

```yaml
# Factory.py Configuration

# Paths
specs_dir: specs/
code_dir: code/
tests_dir: tests/
templates_dir: factory_templates/

# Code Generation
language: python
style:
  formatter: black
  line_length: 100
  sort_imports: isort

# Validation
strict_mode: true  # Block on any validation error
require_tests: true  # Must generate tests
min_coverage: 100  # Require 100% REQ-* coverage

# LLM (for natural language → spec)
llm_provider: anthropic  # or openai
llm_model: claude-3-5-sonnet-20241022
llm_api_key_env: ANTHROPIC_API_KEY

# Output
verbose: false
show_diff: true
auto_format: true
```

---

## 12. TESTING REQUIREMENTS

### 12.1 Factory.py Self-Tests (REQ-FAC-025)

**MUST** have comprehensive test suite:

**Unit Tests**:
- Spec parsing (extract sections, requirements, code blocks)
- Template rendering (Jinja2 output correctness)
- Validation logic (detect missing/invalid sections)
- CLI commands (each subcommand)
- Error handling (all error cases)

**Integration Tests**:
- End-to-end: Spec → Code → Tests (roundtrip)
- Full regeneration (multiple specs)
- Spec validation (detect real errors)
- Git integration (commit suggestions)

**Meta Test**:
- Factory.py regenerates ITSELF from specs/factory-v1.0.md
- Generated factory.py must be identical to source
- **Ultimate constitutional test**: The generator can regenerate itself

---

## 13. USAGE EXAMPLES

### 13.1 Initial Setup

```bash
# Clone agent factory repo
git clone https://github.com/user/agent-factory.git
cd agent-factory

# Install factory.py dependencies
pip install -r factory-requirements.txt

# Verify installation
python factory.py --version
# Output: factory.py v1.0 (constitutional code generator)
```

### 13.2 Creating First Agent

```bash
# Step 1: Generate spec from natural language
python factory.py "build calendar agent that manages meetings" --spec-only-first

# Output: SPEC CREATED: specs/calendar-v1.0.md

# Step 2: Review and edit spec
vim specs/calendar-v1.0.md
# Add specific requirements, data structures

# Step 3: Validate spec
python factory.py --validate specs/calendar-v1.0.md
# Output: ✓ VALID

# Step 4: Generate code and tests
python factory.py specs/calendar-v1.0.md
# Output: GENERATED: code/calendar.py, tests/test_calendar.py

# Step 5: Run tests
pytest tests/test_calendar.py -v
# Output: ✓ 10/10 tests pass

# Step 6: Commit
git add specs/ code/ tests/
git commit -m "feat: Add calendar agent v1.0"
```

### 13.3 Updating Existing Agent

```bash
# Step 1: Edit spec (add new requirement)
vim specs/calendar-v1.0.md
# Increment version to v1.1
# Add REQ-CAL-011: Support recurring meetings

# Rename spec file
mv specs/calendar-v1.0.md specs/calendar-v1.1.md

# Step 2: Regenerate
python factory.py specs/calendar-v1.1.md

# Step 3: Review changes
git diff code/calendar.py
# Shows new functions, rung headers, tests

# Step 4: Test
pytest tests/test_calendar.py -v
# Output: ✓ 11/11 tests pass (new test added)

# Step 5: Commit
git add specs/ code/ tests/
git commit -m "feat: Add recurring meetings (REQ-CAL-011)"
git tag calendar-v1.1
```

---

## 14. TROUBLESHOOTING

### Common Issues

**Issue**: factory.py fails with "Invalid spec format"
- Check: All required sections present (see 4.1)
- Check: REQ-* identifiers follow format (REQ-AGENT-NNN)
- Solution: Run `python factory.py --validate specs/` for details

**Issue**: Generated code has syntax errors
- Check: Spec code blocks are valid Python
- Check: Data structures have complete type hints
- Solution: Test spec examples manually before generation

**Issue**: Tests don't validate requirement
- Check: Spec has concrete MUST statements (not vague)
- Check: Usage examples demonstrate expected behavior
- Solution: Add explicit test cases to spec

**Issue**: Regeneration overwrites manual fixes
- Check: Did you edit code/* directly? (forbidden)
- Check: Spec contains the fix you made manually?
- Solution: ALWAYS edit spec first, then regenerate

**Issue**: LLM generates poor specs from natural language
- Check: Intent description too vague
- Check: LLM model not configured (factory.config.yaml)
- Solution: Provide more detailed intent, or write spec manually

---

## 15. FUTURE ENHANCEMENTS (Out of Scope v1.0)

- Multi-language support (TypeScript, Go, Rust)
- Visual spec editor (GUI for non-technical users)
- Spec diff tool (compare spec versions)
- Incremental regeneration (only changed requirements)
- IDE integration (VS Code extension)
- CI/CD hooks (auto-regenerate on spec commits)
- Spec testing (dry-run generation without writing files)
- Parallel generation (multiple agents at once)

---

## 16. SPEC COMPLIANCE VALIDATION

### 16.1 Acceptance Criteria

This specification is considered **implemented** when:

1. All REQ-FAC-* requirements pass tests
2. Factory.py can regenerate itself from this spec
3. Factory.py generates orchestrator.py matching existing prototype
4. Factory.py generates callbacks.py matching existing prototype
5. All generated code follows PLC rung annotation standard
6. CLI commands work as specified
7. Constitutional enforcement blocks non-spec code

### 16.2 Meta-Test (The Ultimate Validation)

```bash
# The factory must regenerate itself:
python factory.py specs/factory-v1.0.md

# Output: code/factory.py

# Compare to source:
diff factory.py code/factory.py

# If identical (or only trivial formatting diffs):
# ✓ CONSTITUTIONAL COMPLIANCE ACHIEVED
# The system is self-regenerating and self-documenting
```

### 16.3 Spec Version History

- **v1.0** (2025-12-05): Initial specification for constitutional code generator

---

**END OF SPECIFICATION**

*This is the most critical spec - it defines how all other specs become code. The factory regenerates everything, including itself.*
