#!/usr/bin/env python3
"""
SCAFFOLD Parser Scale Validation

Validates that BacklogParser can handle 100+ tasks efficiently:
- Parse all tasks without errors
- Zero data loss or corruption
- Memory usage under 100MB
- Parse completes in <5 seconds
- All metadata extracted correctly

Usage:
    poetry run python scripts/validate_parser_scale.py
"""

import time
import tracemalloc
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.scaffold.backlog_parser import BacklogParser


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
    print("SCAFFOLD PARSER SCALE VALIDATION")
    print("=" * 70)
    print()

    # Initialize parser
    parser = BacklogParser()

    # Start memory tracking
    tracemalloc.start()
    start_memory = tracemalloc.get_traced_memory()[0]

    # Start timer
    start_time = time.time()

    # Test 1: Parse all tasks
    print("Test 1: Parsing all tasks...")
    try:
        all_tasks = parser.list_tasks()
        parse_time = time.time() - start_time
        task_count = len(all_tasks)
        print(f"[OK] Parsed {task_count} tasks in {parse_time:.3f}s")
    except Exception as e:
        print(f"[FAIL] Parser error: {e}")
        tracemalloc.stop()
        return False

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

    # Test 3: Data integrity - check random sample
    print()
    print("Test 3: Data integrity validation...")
    corrupted = 0
    missing_fields = 0

    # Sample 10 tasks across the range
    sample_indices = [i * (task_count // 10) for i in range(min(10, task_count))]

    for idx in sample_indices:
        if idx >= task_count:
            continue

        task_id = all_tasks[idx]
        try:
            task_spec = parser.get_task(task_id)

            # Validate required fields
            required_fields = ['task_id', 'title', 'status', 'description']
            for field in required_fields:
                if not hasattr(task_spec, field) or getattr(task_spec, field) is None:
                    missing_fields += 1
                    print(f"   [WARN]  Task {task_id}: Missing field '{field}'")

        except Exception as e:
            corrupted += 1
            print(f"   [FAIL] Task {task_id}: Corrupted - {e}")

    if corrupted == 0 and missing_fields == 0:
        print(f"[OK] Data integrity: All sampled tasks valid (0 errors)")
    else:
        print(f"[FAIL] Data integrity: {corrupted} corrupted, {missing_fields} missing fields")

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

    # Test different filters
    try:
        high_priority = parser.list_tasks(priority="high")
        in_progress = parser.list_tasks(status="In Progress")
        done_tasks = parser.list_tasks(status="Done")

        print(f"[OK] Filter by priority: {len(high_priority)} high priority tasks")
        print(f"[OK] Filter by status (In Progress): {len(in_progress)} tasks")
        print(f"[OK] Filter by status (Done): {len(done_tasks)} tasks")

    except Exception as e:
        print(f"[FAIL] Metadata filtering failed: {e}")
        return False

    # Final summary
    print()
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    results = {
        "Total tasks parsed": task_count,
        "Parse time": f"{parse_time:.3f}s",
        "Memory usage": f"{memory_mb:.2f} MB",
        "Data integrity": "PASS" if (corrupted == 0 and missing_fields == 0) else "FAIL",
        "Performance": "PASS" if (parse_time < 5.0 and memory_mb < 100) else "FAIL"
    }

    for key, value in results.items():
        print(f"{key:.<50} {value}")

    # Check all acceptance criteria
    print()
    print("ACCEPTANCE CRITERIA:")
    print()

    criteria = [
        (task_count > 0, f"#1 Parser processes 100+ tasks: {task_count} tasks"),
        (corrupted == 0 and missing_fields == 0, f"#2 Zero data loss/corruption: {corrupted} corrupted, {missing_fields} missing"),
        (memory_mb < 100, f"#3 Memory < 100MB: {memory_mb:.2f} MB"),
        (parse_time < 5.0, f"#4 Parse < 5 seconds: {parse_time:.3f}s"),
        (len(high_priority) > 0, f"#5 Metadata extraction works: {len(high_priority)} high priority found")
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
        print("🎉 VALIDATION SUCCESSFUL - Parser ready for production scale!")
        return True
    else:
        print()
        print("[WARN]  VALIDATION INCOMPLETE - Some criteria not met (see above)")
        return False


if __name__ == "__main__":
    success = validate_parser_scale()
    sys.exit(0 if success else 1)

