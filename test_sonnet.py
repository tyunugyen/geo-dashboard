#!/usr/bin/env python3
"""Test if Claude Sonnet 4.6 is available on GoCaaS"""
import os, sys
from openai import OpenAI

PROXY_URL = "https://caas-gocode-prod.caas-prod.prod.onkatana.net"
MODELS_TO_TEST = [
    "claude-sonnet-4-6",
    "claude-sonnet-4.6",
    "claude-sonnet-4-5",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
]

api_key = os.environ.get("CAAS_API_KEY")
if not api_key:
    print("ERROR: Set CAAS_API_KEY environment variable")
    sys.exit(1)

client = OpenAI(api_key=api_key, base_url=PROXY_URL, timeout=15.0)

print(f"Testing models against: {PROXY_URL}\n")
print("="*60)

for model_id in MODELS_TO_TEST:
    print(f"\nTesting: {model_id}...", end=" ", flush=True)
    try:
        response = client.chat.completions.create(
            model=model_id,
            max_tokens=20,
            temperature=0,
            messages=[{"role": "user", "content": "Say OK"}]
        )
        result = response.choices[0].message.content if response.choices else ""
        print(f"✅ SUCCESS - Response: {repr(result[:50])}")
    except Exception as e:
        error_msg = str(e)[:100]
        print(f"❌ FAILED - {error_msg}")

print("\n" + "="*60)
print("Test complete!")
