#!/usr/bin/env python3
"""
Test the actual debug flow that would happen when running TunaCode.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_real_debug_flow():
    """Test the actual debug flow as it would happen in TunaCode."""
    
    # Set the environment variable to enable debugging
    os.environ['TUNACODE_ESC_DEBUG'] = '1'
    
    print("🧪 Testing real TunaCode debug flow...")
    print(f"📍 Current directory: {Path.cwd()}")
    print(f"📝 Environment variable: {os.getenv('TUNACODE_ESC_DEBUG')}")
    
    # Import the modules (this will trigger environment variable detection)
    from tunacode.core.state import StateManager
    from tunacode.utils.esc_debug import log_esc_event, print_debug_summary
    from tunacode.cli.repl import process_request
    
    # Create state manager
    state_manager = StateManager()
    state_manager.session.current_model = "test:model"
    
    print("\n✅ Modules imported, testing debug flow...")
    
    # This should trigger auto-debugging
    log_esc_event("FLOW_TEST_START", "Testing real TunaCode debug flow")
    
    # Simulate what happens when process_request is called
    print("📤 Simulating process_request call...")
    
    # Import the debug functions used in process_request
    from tunacode.utils.esc_debug import log_thinking_start
    log_thinking_start("test:model", 25)
    
    # Test ESC monitoring setup
    print("🔧 Testing ESC monitoring setup...")
    from tunacode.ui.esc_monitor import escape_monitor_context
    
    async with escape_monitor_context(state_manager):
        log_esc_event("MONITOR_TEST", "ESC monitoring active in test")
        
        # Test interrupt checking
        interrupted = state_manager.is_interrupted()
        from tunacode.utils.esc_debug import log_interrupt_check
        log_interrupt_check("test_location", interrupted)
    
    log_esc_event("FLOW_TEST_END", "Real TunaCode debug flow test completed")
    
    print("\n🎉 Test completed! Checking debug summary...")
    print_debug_summary()

if __name__ == "__main__":
    asyncio.run(test_real_debug_flow())