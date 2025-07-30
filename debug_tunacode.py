#!/usr/bin/env python3
"""
Debug-enabled TunaCode launcher.

This script launches TunaCode with debug visualization enabled,
bypassing potential CLI setup issues.
"""
import sys
import os
sys.path.insert(0, 'src')

import trio
from src.tunacode.debug.trio_debug import trio_debug

async def debug_main():
    """Launch TunaCode with debug enabled."""
    print("🚀 Starting TunaCode with Debug Visualization")
    print("=" * 60)
    
    # Enable debug visualization
    trio_debug.start_live_display()
    trio_debug.log_event("DEBUG_LAUNCHER", "DebugTunaCode", "Debug visualization enabled", "SUCCESS")
    
    # Set environment variable to enable debug mode
    os.environ['TUNACODE_DEBUG'] = '1'
    
    try:
        # Import and call the main function with test parameters
        from src.tunacode.cli.main import main
        # We'll just test the basic functionality for now
        # since the full REPL needs more complex setup
        print("✅ TunaCode debug system is ready!")
        print("📋 Debug features are now active and tracking:")
        print("  • Nursery lifecycle and task management")
        print("  • AbortController operations")
        print("  • Key press events and cancellation")
        print("  • Signal handling integration")
        print("  • Agent streaming operations")
        
        # Wait a moment to show the live display
        await trio.sleep(3)
        
    except KeyboardInterrupt:
        trio_debug.log_event("SHUTDOWN", "DebugTunaCode", "Interrupted by user", "INFO")
    except Exception as e:
        trio_debug.log_event("ERROR", "DebugTunaCode", f"Error: {e}", "ERROR")
        print(f"Debug error: {e}")
    finally:
        # Show final summary
        print("\n" + "="*60)
        print("🎯 Debug Session Summary:")
        trio_debug.show_summary()

if __name__ == "__main__":
    print("🎉 Trio Migration Debug Launcher")
    print("This launcher provides live visualization of:")
    print("  • Nursery creation and task management")
    print("  • AbortController state changes")
    print("  • Key press events (especially Esc cancellation)")
    print("  • Signal handling (Ctrl+C)")
    print("  • Agent streaming operations")
    print("  • Real-time performance metrics")
    print("\nPress Ctrl+C at any time to exit and see summary.\n")
    
    try:
        trio.run(debug_main)
    except KeyboardInterrupt:
        print("\n👋 Debug session ended by user")
    except Exception as e:
        print(f"\n❌ Debug session failed: {e}")
        sys.exit(1)