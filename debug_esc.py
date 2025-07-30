#!/usr/bin/env python3
"""
ESC Debug Test Script for TunaCode

This script enables comprehensive ESC debugging and provides a test interface
to validate the ESC interruption flow.

Usage:
    python debug_esc.py

This will:
1. Enable ESC debugging logging to esc.log
2. Start TunaCode with debug tracing active
3. Provide instructions for testing ESC interruption
4. Show debug log summary after completion
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import tunacode modules
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from tunacode.utils.esc_debug import enable_esc_debugging, print_debug_summary, get_debug_log_path
from tunacode.core.state import StateManager
from tunacode.cli.repl import repl

async def main():
    """Main debug test function."""
    
    print("🐛 ESC DEBUGGING ENABLED")
    print(f"📝 Debug log will be written to: {get_debug_log_path()}")
    print("=" * 60)
    print("ESC DEBUG TEST INSTRUCTIONS:")
    print("1. Enter a query that will cause agent thinking (e.g., 'write a hello world program')")
    print("2. While the agent is processing (shows 'Thinking...' or streaming), press ESC")
    print("3. Observe the interruption behavior")
    print("4. Type 'exit' to quit and see debug summary")
    print("=" * 60)
    print()
    
    # Enable ESC debugging
    with enable_esc_debugging() as debug_ctx:
        # Create state manager
        state_manager = StateManager()
        
        try:
            # Start the REPL with debugging enabled
            await repl(state_manager)
        except KeyboardInterrupt:
            print("\n🛑 Interrupted with Ctrl+C")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("ESC DEBUG SESSION COMPLETE")
    print_debug_summary()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())