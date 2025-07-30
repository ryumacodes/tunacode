#!/usr/bin/env python3
"""Real-world test to see how ESC behaves in the actual TunaCode app."""

import sys
import os
sys.path.insert(0, 'src')

# Simple test to demonstrate the ESC behavior issue
def test_instructions():
    print("=" * 60)
    print("ESC CANCELLATION TEST INSTRUCTIONS")
    print("=" * 60)
    print()
    print("1. Run TunaCode in this directory:")
    print("   python -m tunacode")
    print()
    print("2. When TunaCode is ready, run a long command:")
    print("   !sleep 10")
    print()
    print("3. While 'sleep 10' is running, press ESC key")
    print("   - Look for debug messages indicating ESC detection")
    print("   - Check if the command actually gets cancelled")
    print()
    print("4. Compare with Ctrl+C behavior")
    print("   - Run the same command again: !sleep 10")
    print("   - This time press Ctrl+C")
    print("   - Note the difference in behavior")
    print()
    print("EXPECTED:")
    print("- ESC should show debug messages and cancel the command")
    print("- Ctrl+C should also cancel the command")
    print("- Both should have similar cancellation behavior")
    print()
    print("=" * 60)

if __name__ == "__main__":
    test_instructions()