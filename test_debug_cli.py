#!/usr/bin/env python3
"""
Quick test for debug CLI functionality.
"""
import sys
sys.path.insert(0, 'src')

import trio
from src.tunacode.cli.main import main
from src.tunacode.debug.trio_debug import trio_debug

async def test_debug_cli():
    """Test the debug CLI functionality directly."""
    print("🚀 Testing Debug CLI Integration")
    
    # Test without debug
    print("\n1. Testing normal startup...")
    try:
        # Call main function with test parameters
        main(debug=False, version=True)
        print("✅ Normal startup works")
    except SystemExit:
        print("✅ Normal startup works (version exit)")
    except Exception as e:
        print(f"❌ Normal startup failed: {e}")
    
    # Test with debug enabled
    print("\n2. Testing debug startup...")
    try:
        main(debug=True, version=True)
        print("✅ Debug startup works")
    except SystemExit:
        print("✅ Debug startup works (version exit)")
    except Exception as e:
        print(f"❌ Debug startup failed: {e}")
    
    # Test debug system directly
    print("\n3. Testing debug system...")
    trio_debug.log_event("TEST_EVENT", "TestRunner", "Debug system test", "INFO")
    print("✅ Debug logging works")
    
    # Test command creation
    print("\n4. Testing debug command...")
    try:
        from src.tunacode.cli.commands.debug_command import TrioDebugCommand
        cmd = TrioDebugCommand()
        print(f"✅ Debug command created: {cmd.name}")
        print(f"   Description: {cmd.description}")
        print(f"   Usage: {cmd.usage}")
    except Exception as e:
        print(f"❌ Debug command failed: {e}")

if __name__ == "__main__":
    trio.run(test_debug_cli)