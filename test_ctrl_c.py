#!/usr/bin/env python3
"""
Manual test script for Ctrl+C handling
Run this to test the behavior manually
"""

import subprocess
import time
import os

print("Testing TunaCode Ctrl+C handling...")
print("="*50)
print()

# Test 1: Basic launch and exit
print("Test 1: Launch tunacode and test Ctrl+C")
print("Instructions:")
print("1. When tunacode starts, press Ctrl+C once")
print("2. You should see 'Hit Ctrl+C again to exit'")
print("3. Press Ctrl+C again to exit")
print("4. No traceback should appear")
print()
input("Press Enter to start test 1...")

subprocess.run(["python", "-m", "tunacode"])

print("\nTest 1 complete.")
print("="*50)