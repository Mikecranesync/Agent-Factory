#!/usr/bin/env python3
"""
Test Phoenix Integration with Groq

Run this after starting Phoenix server:
    Terminal 1: phoenix serve
    Terminal 2: python test_phoenix_integration.py

Then check http://localhost:6006 to see your traces.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Import our tracer
from phoenix_tracer import (
    init_phoenix,
    wrap_client,
    traced,
    log_route_decision,
    log_knowledge_retrieval
)

# Initialize Phoenix (connects to running server)
print("🚀 Initializing Phoenix...")
session = init_phoenix(project_name="agent_factory_test", launch_app=False)

if session:
    print("✅ Phoenix connected")
else:
    print("⚠️  Phoenix not available - traces will be skipped")


# Test 1: Wrap Groq client and make a call
def test_groq_tracing():
    """Test that Groq calls are traced."""
    print("\n📡 Test 1: Groq client tracing...")
    
    try:
        from groq import Groq
        
        # Wrap the client
        client = wrap_client(Groq())
        
        # Make a simple call
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a PLC technician. Be brief."
                },
                {
                    "role": "user", 
                    "content": "What does fault code F47 mean on a Siemens VFD?"
                }
            ],
            max_tokens=100
        )
        
        print(f"✅ Groq response: {response.choices[0].message.content[:100]}...")
        print("   → Check Phoenix UI for trace")
        return True
        
    except Exception as e:
        print(f"❌ Groq test failed: {e}")
        return False


# Test 2: Use @traced decorator on a function
@traced(agent_name="siemens_sme", route="technical")
def diagnose_fault_sync(fault_code: str, equipment: str) -> dict:
    """Simulated sync agent function."""
    # In real code, this would call your LLM
    return {
        "root_cause": f"Simulated diagnosis for {fault_code}",
        "equipment": equipment,
        "confidence": 0.85
    }


@traced(agent_name="rockwell_sme", route="technical")
async def diagnose_fault_async(fault_code: str, equipment: str) -> dict:
    """Simulated async agent function (like your Telegram handlers)."""
    await asyncio.sleep(0.1)  # Simulate API call
    return {
        "root_cause": f"Async diagnosis for {fault_code}",
        "equipment": equipment,
        "confidence": 0.90
    }


def test_traced_decorator():
    """Test that @traced decorator works."""
    print("\n📡 Test 2: @traced decorator (sync)...")
    
    try:
        result = diagnose_fault_sync("F47", "Siemens S7-1200")
        print(f"✅ Sync result: {result}")
        print("   → Check Phoenix UI for 'siemens_sme.diagnose_fault_sync' span")
        return True
    except Exception as e:
        print(f"❌ Sync traced test failed: {e}")
        return False


async def test_async_traced():
    """Test async @traced decorator."""
    print("\n📡 Test 3: @traced decorator (async)...")
    
    try:
        result = await diagnose_fault_async("E0001", "Rockwell CompactLogix")
        print(f"✅ Async result: {result}")
        print("   → Check Phoenix UI for 'rockwell_sme.diagnose_fault_async' span")
        return True
    except Exception as e:
        print(f"❌ Async traced test failed: {e}")
        return False


def test_custom_logging():
    """Test custom logging functions."""
    print("\n📡 Test 4: Custom logging (route decisions, knowledge retrieval)...")
    
    try:
        # Log a route decision
        log_route_decision(
            query="My VFD is showing F47 error",
            selected_route="siemens_sme",
            confidence=0.92,
            all_routes={
                "siemens_sme": 0.92,
                "rockwell_sme": 0.15,
                "generic": 0.45,
                "safety": 0.30
            }
        )
        print("✅ Route decision logged")
        
        # Log a knowledge retrieval
        log_knowledge_retrieval(
            query="VFD F47 overcurrent",
            retrieved_atoms=[
                {"atom_id": "atom_001", "content": "F47 indicates overcurrent..."},
                {"atom_id": "atom_002", "content": "Check motor bearings..."},
                {"atom_id": "atom_003", "content": "LOTO procedure required..."},
            ],
            retrieval_time_ms=45.2
        )
        print("✅ Knowledge retrieval logged")
        print("   → Check Phoenix UI for custom spans")
        return True
        
    except Exception as e:
        print(f"❌ Custom logging test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("PHOENIX INTEGRATION TEST")
    print("=" * 60)
    print("\nMake sure Phoenix server is running:")
    print("  $ phoenix serve")
    print("\nThen open http://localhost:6006 to see traces")
    print("=" * 60)
    
    results = []
    
    # Run sync tests
    results.append(("Groq Tracing", test_groq_tracing()))
    results.append(("Sync @traced", test_traced_decorator()))
    results.append(("Custom Logging", test_custom_logging()))
    
    # Run async test
    results.append(("Async @traced", asyncio.run(test_async_traced())))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Check Phoenix UI at http://localhost:6006")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
