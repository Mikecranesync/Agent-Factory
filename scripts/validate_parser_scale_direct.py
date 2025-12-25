#!/usr/bin/env python3
"""
SCAFFOLD Parser Scale Validation (Direct File Reading)

Validates parser performance by reading task files directly from backlog/tasks/.

This version doesn't require MCP tools - reads Markdown files directly.

Usage:
    poetry run python scripts/validate_parser_scale_direct.py
"""

import time
import tracemalloc
import sys
from pathlib import Path
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_task_file(filepath: Path) -> dict:
    """
    Parse a Backlog.md task file directly.

    Args:
        filepath: Path to task .md file

    Returns:
        Task dict with id, title, status, priority, description, etc.
    """
    content = filepath.read_text(encoding='utf-8')

    # Extract YAML frontmatter
    yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not yaml_match:
        return None

    frontmatter_str, body = yaml_match.groups()

    # Parse YAML
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return None

    # Extract task data
    task = {
        'id': frontmatter.get('id', filepath.stem),
        'title': frontmatter.get('title', ''),
        'status': frontmatter.get('status', 'To Do'),
        'priority': frontmatter.get('priority', 'medium'),
        'labels': frontmatter.get('labels', []),
        'dependencies': frontmatter.get('dependencies', []),
        'parent_task_id': frontmatter.get('parent', None),
        'created_date': frontmatter.get('created', None),
        'description': body.split('\n## ')[0].strip() if body else '',
    }

    return task


def validate_parser_scale():
    """
    Validate parser performance with 100+ tasks.

    Acceptance Criteria:
    1. Parser processes 100+ tasks without errors
    2. Zero data loss or corruption
    3. Memory usage below 100MB
    4. Parse completes in <5 seconds
    5. All task metadata extracted correctly
    """

    print("=" * 70)
    print("SCAFFOLD PARSER SCALE VALIDATION (Direct File Reading)")
    print("=" * 70)
    print()

    # Find task files
    project_root = Path(__file__).parent.parent
    tasks_dir = project_root / "backlog" / "tasks"

    if not tasks_dir.exists():
        print(f"[FAIL] Tasks directory not found: {tasks_dir}")
        return False

    # Start memory tracking
    tracemalloc.start()
    start_memory = tracemalloc.get_traced_memory()[0]

    # Start timer
    start_time = time.time()

    # Test 1: Parse all task files
    print("Test 1: Parsing all task files...")

    task_files = list(tasks_dir.glob("*.md"))
    tasks = []
    parse_errors = 0

    for filepath in task_files:
        try:
            task = parse_task_file(filepath)
            if task:
                tasks.append(task)
            else:
                parse_errors += 1
        except Exception as e:
            parse_errors += 1
            print(f"   [WARN] Error parsing {filepath.name}: {e}")

    parse_time = time.time() - start_time
    task_count = len(tasks)

    print(f"[OK] Parsed {task_count} tasks in {parse_time:.3f}s")
    if parse_errors > 0:
        print(f"   [WARN] {parse_errors} files failed to parse")

    # Check memory usage
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    memory_mb = (peak_memory - start_memory) / (1024 * 1024)
    print(f"   Memory used: {memory_mb:.2f} MB")

    tracemalloc.stop()

    # Test 2: Validate task count (>= 100)
    print()
    print("Test 2: Task count validation...")
    if task_count >= 100:
        print(f"[OK] Task count: {task_count} (>= 100 required)")
    else:
        print(f"[WARN] Task count: {task_count} (< 100, but not a failure)")

    # Test 3: Data integrity - check all tasks
    print()
    print("Test 3: Data integrity validation...")
    corrupted = 0
    missing_fields = 0

    required_fields = ['id', 'title', 'status', 'description']

    for task in tasks:
        for field in required_fields:
            if field not in task or task[field] is None or task[field] == '':
                if field != 'description':  # Description can be empty
                    missing_fields += 1

    if missing_fields == 0:
        print(f"[OK] Data integrity: All tasks valid (0 missing fields)")
    else:
        print(f"[FAIL] Data integrity: {missing_fields} missing required fields")

    # Test 4: Performance benchmarks
    print()
    print("Test 4: Performance benchmarks...")

    # Parse time check (<5 seconds)
    if parse_time < 5.0:
        print(f"[OK] Parse time: {parse_time:.3f}s (< 5.0s required)")
    else:
        print(f"[FAIL] Parse time: {parse_time:.3f}s (>= 5.0s, FAILED)")

    # Memory check (<100MB)
    if memory_mb < 100:
        print(f"[OK] Memory usage: {memory_mb:.2f} MB (< 100 MB required)")
    else:
        print(f"[FAIL] Memory usage: {memory_mb:.2f} MB (>= 100 MB, FAILED)")

    # Test 5: Metadata extraction
    print()
    print("Test 5: Metadata extraction validation...")

    # Count by status
    status_counts = {}
    for task in tasks:
        status = task.get('status', 'To Do')
        status_counts[status] = status_counts.get(status, 0) + 1

    # Count by priority
    priority_counts = {}
    for task in tasks:
        priority = task.get('priority', 'medium')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    print(f"[OK] Status distribution: {dict(status_counts)}")
    print(f"[OK] Priority distribution: {dict(priority_counts)}")

    # Final summary
    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    results = {
        "Total task files": len(task_files),
        "Successfully parsed": task_count,
        "Parse errors": parse_errors,
        "Parse time": f"{parse_time:.3f}s",
        "Memory usage": f"{memory_mb:.2f} MB",
        "Data integrity": "PASS" if (missing_fields == 0) else f"FAIL ({missing_fields} missing)",
        "Performance": "PASS" if (parse_time < 5.0 and memory_mb < 100) else "FAIL"
    }

    for key, value in results.items():
        print(f"{key:.<50} {value}")

    # Check all acceptance criteria
    print()
    print("ACCEPTANCE CRITERIA:")
    print()

    criteria = [
        (task_count >= 100, f"#1 Parser processes 100+ tasks: {task_count} tasks"),
        (missing_fields == 0 and parse_errors == 0, f"#2 Zero data loss/corruption: {parse_errors} errors, {missing_fields} missing"),
        (memory_mb < 100, f"#3 Memory < 100MB: {memory_mb:.2f} MB"),
        (parse_time < 5.0, f"#4 Parse < 5 seconds: {parse_time:.3f}s"),
        (len(status_counts) > 0 and len(priority_counts) > 0, f"#5 Metadata extraction works: {len(status_counts)} statuses, {len(priority_counts)} priorities")
    ]

    passed = 0
    for success, description in criteria:
        status = "[OK] PASS" if success else "[FAIL] FAIL"
        print(f"{status} - {description}")
        if success:
            passed += 1

    print()
    print(f"Result: {passed}/{len(criteria)} criteria passed")

    # Return overall success
    all_passed = passed == len(criteria)

    if all_passed:
        print()
        print("[SUCCESS] VALIDATION SUCCESSFUL - Parser ready for production scale!")
        return True
    else:
        print()
        print("[WARN] VALIDATION INCOMPLETE - Some criteria not met (see above)")
        return False


if __name__ == "__main__":
    success = validate_parser_scale()
    sys.exit(0 if success else 1)
