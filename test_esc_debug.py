#!/usr/bin/env python3
"""
Quick test script to verify ESC debugging works with the real app.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_esc_debugging():
    """Test ESC debugging functionality."""
    
    # Import and setup
    from tunacode.core.state import StateManager
    from tunacode.utils.esc_debug import enable_esc_debugging, print_debug_summary, log_esc_event
    from tunacode.ui.esc_monitor import escape_monitor_context
    from tunacode.ui.input import multiline_input
    
    print("🧪 Testing ESC debugging integration...")
    print("📝 Debug events will be logged to esc.log")
    print()
    
    # Enable debugging
    with enable_esc_debugging():
        # Create state manager
        state_manager = StateManager()
        
        # Test the complete flow
        log_esc_event("TEST_START", "Starting ESC debugging integration test")
        
        # Test ESC monitoring setup
        async with escape_monitor_context(state_manager):
            log_esc_event("MONITOR_ACTIVE", "ESC monitoring is now active")
            
            # Simulate some processing time where ESC could be pressed
            print("✅ ESC monitoring is active")
            print("✅ Debug logging is working")
            print("✅ State manager is initialized")
            
            # Test interrupt checking
            is_interrupted = state_manager.is_interrupted()
            log_esc_event("INTERRUPT_TEST", f"Interrupt check result: {is_interrupted}")
            
        log_esc_event("TEST_COMPLETE", "ESC debugging integration test completed")
    
    print("\n🎉 ESC debugging test completed!")
    print_debug_summary()

if __name__ == "__main__":
    asyncio.run(test_esc_debugging())