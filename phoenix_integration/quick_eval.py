#!/usr/bin/env python3
"""
Quick Eval Test - Verify Pipeline Works

Runs a mini-eval on 3 cases to validate the entire pipeline:
1. Load golden dataset ✓
2. Call agent for diagnosis ✓
3. Run LLM judge ✓
4. Output results ✓

Run this BEFORE full evals to catch setup issues fast.

Usage:
    python quick_eval.py
    python quick_eval.py --dataset ../datasets/golden_from_neon.jsonl
"""

import os
import sys
import json
import time
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()


def load_cases(dataset_path: str, limit: int = 3) -> list:
    """Load test cases from JSONL."""
    cases = []
    with open(dataset_path) as f:
        for line in f:
            cases.append(json.loads(line.strip()))
            if len(cases) >= limit:
                break
    return cases


def get_agent_diagnosis(case: dict) -> dict:
    """
    Get diagnosis from your agent.
    
    This uses Groq directly for testing - swap with your real orchestrator.
    """
    try:
        from groq import Groq
        client = Groq()
        
        prompt = f"""You are an expert industrial maintenance technician.
        
Equipment: {case["equipment"]["model"]} ({case["equipment"]["manufacturer"]})
Fault Code: {case["input"]["fault_code"]}
Description: {case["input"].get("fault_description", "N/A")}
Context: {case["input"].get("context", "N/A")[:500]}

Analyze this fault and provide:
1. Root cause (what's actually wrong)
2. Safety warnings (LOTO, PPE, hazards)
3. Repair steps (numbered list)
4. Manual citations (if known)

Respond in JSON format with keys: root_cause, safety_warnings, repair_steps, manual_citations"""

        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure all fields exist
        return {
            "root_cause": result.get("root_cause", ""),
            "safety_warnings": result.get("safety_warnings", []),
            "repair_steps": result.get("repair_steps", []),
            "manual_citations": result.get("manual_citations", [])
        }
        
    except ImportError:
        print("⚠️  Groq not installed. Using mock response.")
        return {
            "root_cause": f"Mock diagnosis for {case['input']['fault_code']}",
            "safety_warnings": ["Verify lockout before inspection"],
            "repair_steps": ["1. Lockout", "2. Inspect", "3. Repair"],
            "manual_citations": ["Equipment Manual Section 8.2"]
        }
    except Exception as e:
        print(f"⚠️  Agent call failed: {e}")
        return {
            "root_cause": f"Error getting diagnosis: {e}",
            "safety_warnings": [],
            "repair_steps": [],
            "manual_citations": []
        }


def run_quick_judge(case: dict, agent_output: dict) -> dict:
    """Run judge eval using TECHNICAL_ACCURACY template."""
    try:
        from openai import OpenAI
        # Import the judge template and formatter
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "evals"))
        from judges import format_judge_prompt

        client = OpenAI()

        # Use the official TECHNICAL_ACCURACY template
        prompt = format_judge_prompt("technical_accuracy", case, agent_output)

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Low temperature for consistent judging
            max_tokens=200,   # Allow more tokens for full reason
        )

        result = response.choices[0].message.content.strip()

        # Parse LABEL: and REASON: from response
        label = "UNKNOWN"
        reason = result

        lines = result.split("\n")
        for line in lines:
            if line.startswith("LABEL:"):
                label = line.replace("LABEL:", "").strip().split()[0]
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()

        # Validate label
        if label not in ["CORRECT", "PARTIAL", "INCORRECT"]:
            # Fallback parsing
            if "CORRECT" in result.upper():
                label = "CORRECT"
            elif "PARTIAL" in result.upper():
                label = "PARTIAL"
            elif "INCORRECT" in result.upper():
                label = "INCORRECT"

        return {"label": label, "reason": reason, "raw": result}

    except Exception as e:
        print(f"⚠️  Judge call failed: {e}")
        return {"label": "UNKNOWN", "error": str(e), "reason": str(e)}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="../datasets/golden_from_neon.jsonl")
    parser.add_argument("--cases", type=int, default=3)
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧪 QUICK EVAL TEST")
    print("=" * 60)
    print(f"Dataset: {args.dataset}")
    print(f"Cases: {args.cases}")
    print("=" * 60)
    
    # Check dataset exists
    if not os.path.exists(args.dataset):
        print(f"\n❌ Dataset not found: {args.dataset}")
        print("   Run export_golden_dataset.py first")
        sys.exit(1)
    
    # Load cases
    print("\n📂 Loading cases...")
    cases = load_cases(args.dataset, args.cases)
    print(f"   Loaded {len(cases)} cases")
    
    # Run evals
    results = []
    for i, case in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {case.get('test_case_id', 'unknown')}")
        print(f"   Fault: {case['input']['fault_code']}")
        print(f"   Equipment: {case['equipment']['model']}")
        
        # Get agent diagnosis
        print("   🤖 Calling agent...")
        start = time.time()
        agent_output = get_agent_diagnosis(case)
        agent_time = time.time() - start
        print(f"   Agent response ({agent_time:.1f}s): {agent_output['root_cause'][:80]}...")
        
        # Run judge
        print("   ⚖️  Running judge...")
        start = time.time()
        judge_result = run_quick_judge(case, agent_output)
        judge_time = time.time() - start
        print(f"   Judge result ({judge_time:.1f}s): {judge_result['label']}")
        
        results.append({
            "case_id": case.get("test_case_id"),
            "fault_code": case["input"]["fault_code"],
            "agent_time_s": agent_time,
            "judge_time_s": judge_time,
            "judge_label": judge_result["label"]
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 QUICK EVAL SUMMARY")
    print("=" * 60)
    
    labels = [r["judge_label"] for r in results]
    correct = labels.count("CORRECT")
    partial = labels.count("PARTIAL")
    incorrect = labels.count("INCORRECT")
    unknown = labels.count("UNKNOWN")
    
    print(f"   CORRECT:   {correct}/{len(results)}")
    print(f"   PARTIAL:   {partial}/{len(results)}")
    print(f"   INCORRECT: {incorrect}/{len(results)}")
    if unknown:
        print(f"   UNKNOWN:   {unknown}/{len(results)}")
    
    total_time = sum(r["agent_time_s"] + r["judge_time_s"] for r in results)
    print(f"\n   Total time: {total_time:.1f}s")
    print(f"   Avg per case: {total_time/len(results):.1f}s")
    
    # Status
    print("\n" + "=" * 60)
    if correct + partial >= len(results) * 0.5:
        print("✅ Quick test PASSED - pipeline is working")
        print("   Ready for full eval: python evals/run_eval.py")
    else:
        print("⚠️  Quick test shows issues - review agent responses")
        print("   May need to improve golden dataset or agent prompts")
    print("=" * 60)
    
    # Save results
    output_path = "quick_eval_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "cases_tested": len(results),
            "results": results
        }, f, indent=2)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
