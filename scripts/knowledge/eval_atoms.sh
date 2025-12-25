#!/usr/bin/env bash
set -euo pipefail

INPUT="$1"
OUTPUT="$2"

python scripts/knowledge/eval_atoms.py --input "$INPUT" --output "$OUTPUT"
