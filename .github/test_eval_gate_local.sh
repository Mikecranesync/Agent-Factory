#!/bin/bash
set -e

echo "=== LOCAL CI GATE TEST ==="
echo

# Check prerequisites
echo "[1/4] Checking prerequisites..."

if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "ERROR: pip not found"
    exit 1
fi

echo "  - Python: $(python --version)"
echo "  - pip: $(pip --version)"
echo

# Install dependencies
echo "[2/4] Installing dependencies..."
pip install -q arize-phoenix groq openai psycopg2-binary python-dotenv 2>&1 | grep -v "Requirement already satisfied" || true
echo "  - Dependencies installed"
echo

# Check for dataset
echo "[3/4] Checking for golden dataset..."
if [ ! -f "datasets/golden_from_neon.jsonl" ]; then
    echo "  WARNING: Golden dataset not found at datasets/golden_from_neon.jsonl"
    echo "  Creating stub dataset for testing..."
    mkdir -p datasets
    cat > datasets/golden_from_neon.jsonl << 'EOF'
{"test_case_id":"test_1","equipment":{"manufacturer":"Siemens","model":"S7-1200"},"input":{"fault_code":"F47","fault_description":"Overcurrent fault"},"expected_output":{"root_cause":"Motor overload","safety_warnings":["Lockout/Tagout required"],"repair_steps":["Check motor current","Inspect wiring"],"manual_citations":["S7-1200 Manual Section 8.3"]},"metadata":{"atom_id":"test_atom_1","exported_at":"2025-12-28","needs_review":false}}
{"test_case_id":"test_2","equipment":{"manufacturer":"Rockwell","model":"CompactLogix"},"input":{"fault_code":"E001","fault_description":"Communication fault"},"expected_output":{"root_cause":"Network cable disconnect","safety_warnings":[],"repair_steps":["Check Ethernet cable","Verify IP configuration"],"manual_citations":["CompactLogix Manual Chapter 3"]},"metadata":{"atom_id":"test_atom_2","exported_at":"2025-12-28","needs_review":false}}
{"test_case_id":"test_3","equipment":{"manufacturer":"ABB","model":"ACS880"},"input":{"fault_code":"AL01","fault_description":"Drive overheating"},"expected_output":{"root_cause":"Insufficient ventilation","safety_warnings":["High temperature"],"repair_steps":["Check cooling fans","Clean air filters"],"manual_citations":["ACS880 Manual Section 12.1"]},"metadata":{"atom_id":"test_atom_3","exported_at":"2025-12-28","needs_review":false}}
EOF
    echo "  - Stub dataset created (3 test cases)"
else
    echo "  - Dataset found: $(wc -l < datasets/golden_from_neon.jsonl) cases"
fi
echo

# Run evals (limit 10 for speed)
echo "[4/4] Running evaluations (limit 10)..."
echo

# Check if run_eval.py exists
if [ ! -f "phoenix_integration/evals/run_eval.py" ]; then
    echo "ERROR: phoenix_integration/evals/run_eval.py not found"
    echo "This script should be created by Tab 2"
    exit 1
fi

# Run the eval
python phoenix_integration/evals/run_eval.py \
    --dataset datasets/golden_from_neon.jsonl \
    --limit 10 \
    --output evals/local_ci_results.json

echo
echo "=== CHECKING THRESHOLDS ==="
echo

# Check thresholds using check_results.py
if [ -f "evals/check_results.py" ]; then
    python evals/check_results.py evals/local_ci_results.json
else
    # Fallback: inline check
    python -c "
import json
with open('evals/local_ci_results.json') as f:
    results = json.load(f)

summary = results.get('summary', {})
gate_passed = summary.get('gate_passed', False)

print('=' * 60)
if gate_passed:
    print('[PASS] All blocking evals passed')
    exit(0)
else:
    print('[FAIL] One or more blocking evals failed')
    exit(1)
"
fi

echo
echo "=== LOCAL CI TEST COMPLETE ==="
