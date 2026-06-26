#!/usr/bin/env python3
import os
import sys

print("=== Environment Variable Test ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print("")

api_key = os.environ.get("CAAS_API_KEY")
if api_key:
    print(f"✓ CAAS_API_KEY is set (length: {len(api_key)})")
    sys.exit(0)
else:
    print("✗ CAAS_API_KEY is NOT set")
    print("")
    print("Available environment variables containing 'CAAS' or 'API':")
    for key in os.environ:
        if 'CAAS' in key.upper() or 'API' in key.upper():
            print(f"  {key} = {os.environ[key][:20]}...")
    sys.exit(1)
