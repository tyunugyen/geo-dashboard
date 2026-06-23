#!/usr/bin/env python3
"""
test_multi_model.py
Quick test runner for GEO benchmark with a subset of prompts and models.
Use this to validate setup before running full benchmark.
"""

import os, sys
from geo_benchmark_multi_model import (
    run_model_benchmark, calculate_summary, PROMPTS, MODEL_GROUPS
)

# Test with just first 5 prompts (mix of unaided and aided)
TEST_PROMPTS = PROMPTS[:5]

def quick_test():
    api_key = os.getenv("CAAS_API_KEY")
    if not api_key:
        print("[FAIL] CAAS_API_KEY environment variable not set")
        sys.exit(1)

    # Test models - one from each major provider
    test_models = [
        {"id": "claude-sonnet-4-6", "name": "Claude Sonnet 4.6"},
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
    ]

    print(f"\n{'='*60}")
    print("Quick GEO Benchmark Test")
    print(f"{'='*60}")
    print(f"Testing {len(test_models)} models with {len(TEST_PROMPTS)} prompts")
    print()

    results = {}
    for model_info in test_models:
        print(f"\nTesting {model_info['name']}...")

        # Temporarily replace PROMPTS for testing
        import geo_benchmark_multi_model as gbm
        original_prompts = gbm.PROMPTS
        gbm.PROMPTS = TEST_PROMPTS

        rows, error = run_model_benchmark(model_info, api_key, verbose=True)

        # Restore original prompts
        gbm.PROMPTS = original_prompts

        if rows:
            summary = calculate_summary(rows)
            results[model_info["id"]] = {
                "name": model_info["name"],
                "summary": summary
            }
        else:
            print(f"  [FAIL] {error}")

    # Print results
    print(f"\n{'='*60}")
    print("TEST RESULTS")
    print(f"{'='*60}")
    for model_id, data in results.items():
        s = data["summary"]
        print(f"\n{data['name']}:")
        print(f"  Unaided SOV: {s['unaided_sov']:.1f}% ({s['unaided_hits']}/{s['unaided_prompts']})")
        print(f"  Aided SOV: {s['aided_sov']:.1f}% ({s['aided_hits']}/{s['aided_prompts']})")

    print(f"\n{'='*60}")
    print("Test complete! Run geo_benchmark_multi_model.py for full benchmark.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    quick_test()
