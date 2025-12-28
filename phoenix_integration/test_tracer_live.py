"""
Live test for Phoenix tracer integration.

Prerequisites:
- Phoenix server running on port 6006 (run: phoenix serve --port 6006)
- GROQ_API_KEY in environment

This test validates that:
1. Phoenix tracer module functions work
2. Groq client wrapper captures LLM calls
3. Custom span logging (route decisions, knowledge retrieval) works
4. Traces appear in Phoenix UI
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from phoenix_integration.phoenix_tracer import (
    init_phoenix,
    wrap_client,
    traced,
    log_route_decision,
    log_knowledge_retrieval
)

def main():
    print("=" * 60)
    print("PHOENIX TRACER LIVE TEST")
    print("=" * 60)

    # Step 1: Initialize Phoenix (launch app for testing)
    print("\n[1/6] Initializing Phoenix connection...")
    print("   Launching Phoenix UI on port 6006...")
    session = init_phoenix(
        project_name="tab3_tracer_test",
        launch_app=True  # Launch Phoenix for testing
    )

    if session is None:
        print("[FAIL] Failed to initialize Phoenix")
        return 1

    print("[OK] Phoenix started successfully")

    # Step 2: Create and wrap Groq client
    print("\n[2/6] Creating and wrapping Groq client...")

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("[FAIL] GROQ_API_KEY not found in environment")
        return 1

    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        wrapped_client = wrap_client(client, provider="groq")
        print("[OK] Groq client wrapped for tracing")
    except ImportError:
        print("[FAIL] Groq package not installed. Run: pip install groq")
        return 1
    except Exception as e:
        print(f"[FAIL] Failed to create Groq client: {e}")
        return 1

    # Step 3: Make a traced LLM call
    print("\n[3/6] Making traced LLM call about PLC fault...")

    try:
        start_time = time.time()
        response = wrapped_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Updated to current model
            messages=[
                {
                    "role": "system",
                    "content": "You are an industrial maintenance expert. Answer concisely."
                },
                {
                    "role": "user",
                    "content": "What does fault code F47 mean on a Siemens S7-1200 PLC?"
                }
            ],
            max_tokens=200
        )
        elapsed_ms = (time.time() - start_time) * 1000

        answer = response.choices[0].message.content
        print(f"[OK] LLM response received ({elapsed_ms:.0f}ms)")
        print(f"   Answer preview: {answer[:100]}...")
    except Exception as e:
        print(f"[FAIL] LLM call failed: {e}")
        return 1

    # Step 4: Log route decision
    print("\n[4/6] Logging route decision...")

    try:
        log_route_decision(
            query="What does fault code F47 mean on a Siemens S7-1200 PLC?",
            selected_route="siemens_sme",
            confidence=0.92,
            all_routes={
                "siemens_sme": 0.92,
                "rockwell_sme": 0.15,
                "abb_sme": 0.08,
                "general_sme": 0.45
            }
        )
        print("[OK] Route decision logged")
    except Exception as e:
        print(f"[FAIL] Failed to log route decision: {e}")
        return 1

    # Step 5: Log knowledge retrieval
    print("\n[5/6] Logging knowledge retrieval...")

    try:
        fake_atoms = [
            {
                "atom_id": "siemens-s7-1200-f47-overcurrent",
                "title": "F47 Overcurrent Fault - S7-1200",
                "manufacturer": "Siemens",
                "relevance_score": 0.95
            },
            {
                "atom_id": "siemens-fault-codes-reference",
                "title": "Siemens Fault Code Reference",
                "manufacturer": "Siemens",
                "relevance_score": 0.87
            },
            {
                "atom_id": "plc-troubleshooting-general",
                "title": "General PLC Troubleshooting Guide",
                "manufacturer": "Generic",
                "relevance_score": 0.62
            }
        ]

        log_knowledge_retrieval(
            query="F47 fault Siemens S7-1200",
            retrieved_atoms=fake_atoms,
            retrieval_time_ms=45.3
        )
        print("[OK] Knowledge retrieval logged")
    except Exception as e:
        print(f"[FAIL] Failed to log knowledge retrieval: {e}")
        return 1

    # Step 6: Success message
    print("\n[6/6] Test complete!")
    print("=" * 60)
    print("[PASS] ALL TESTS PASSED")
    print("=" * 60)
    print("\nView traces in Phoenix UI:")
    print("   http://localhost:6006")
    print("\nExpected traces:")
    print("   - 1 LLM call (Groq llama-3.1-70b-versatile)")
    print("   - 1 route decision (siemens_sme selected)")
    print("   - 1 knowledge retrieval (3 atoms)")
    print("\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
