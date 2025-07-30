#!/usr/bin/env python3
"""
Instructions and test for ESC debugging in TunaCode.

This script will show you exactly how to test ESC debugging.
"""

import os
import sys
from pathlib import Path

def main():
    print("🐛 ESC DEBUGGING TEST INSTRUCTIONS")
    print("=" * 50)
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    src_dir = current_dir / "src"
    
    if not src_dir.exists():
        print("❌ ERROR: Run this from the tunacode root directory")
        print(f"   Current directory: {current_dir}")
        print("   Expected to find: src/tunacode/")
        return
    
    print(f"✅ Running from correct directory: {current_dir}")
    print(f"✅ Found src directory: {src_dir}")
    
    # Test 1: Environment variable method
    print("\n🧪 TEST 1: Environment Variable Method")
    print("-" * 40)
    print("Run these commands in your terminal:")
    print()
    print("export TUNACODE_ESC_DEBUG=1")
    print("cd 'tunacode'")
    print("python3 -c \"")
    print("import sys")
    print("sys.path.insert(0, 'src')")
    print("from tunacode.utils.esc_debug import log_esc_event")
    print("log_esc_event('TEST', 'Testing from terminal')")
    print("\"")
    print()
    print("Expected output:")
    print("🐛 ESC debugging auto-enabled via TUNACODE_ESC_DEBUG environment variable")
    print("📝 Debug log: /path/to/tunacode/esc.log")
    
    # Test 2: Direct testing
    print("\n🧪 TEST 2: Direct Testing")  
    print("-" * 40)
    print("Run this command:")
    print()
    print("cd 'tunacode' && python3 test_real_flow.py")
    print()
    print("This will test the complete debug flow and show you a summary.")
    
    # Test 3: Check current status
    print("\n🔍 CURRENT STATUS CHECK")
    print("-" * 40)
    
    # Check if environment variable is set
    esc_debug = os.getenv('TUNACODE_ESC_DEBUG', '')
    if esc_debug.lower() in ('1', 'true', 'yes', 'on'):
        print(f"✅ TUNACODE_ESC_DEBUG is set to: '{esc_debug}'")
    else:
        print(f"❌ TUNACODE_ESC_DEBUG is not set (current value: '{esc_debug}')")
        print("   Set it with: export TUNACODE_ESC_DEBUG=1")
    
    # Check if we can import the debug module
    try:
        sys.path.insert(0, str(src_dir))
        from tunacode.utils.esc_debug import _ESC_DEBUG_ENABLED, log_esc_event
        print(f"✅ Debug module imports successfully")
        print(f"✅ Auto-debug enabled: {_ESC_DEBUG_ENABLED}")
        
        # Test logging
        print("\n🧪 Testing debug logging now...")
        log_esc_event('INSTRUCTION_TEST', 'Testing from debug instructions script')
        print("✅ Debug logging test completed")
        
    except Exception as e:
        print(f"❌ Error importing debug module: {e}")
        return
    
    # Check log file
    log_file = current_dir / "esc.log"
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()
        print(f"\n📝 Log file status:")
        print(f"   Path: {log_file}")
        print(f"   Lines: {len(lines)}")
        if lines:
            print(f"   Last line: {lines[-1].strip()}")
        print(f"✅ Debug log is working!")
    else:
        print(f"\n❌ Log file not found at: {log_file}")
    
    print("\n" + "=" * 50)
    print("🎯 TO TEST ESC INTERRUPTION:")
    print("1. Set environment variable: export TUNACODE_ESC_DEBUG=1")
    print("2. Run TunaCode (however you usually run it)")
    print("3. Enter a query that triggers agent thinking")
    print("4. Press ESC while it's thinking")
    print("5. Check esc.log file for the complete trace")
    print("=" * 50)

if __name__ == "__main__":
    main()