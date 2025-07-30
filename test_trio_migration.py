#!/usr/bin/env python3
"""
Test script to verify basic Trio migration functionality.
"""

import trio
from src.tunacode.core.abort_controller import AbortController, AppContext

async def test_abort_controller():
    """Test the AbortController functionality."""
    print("Testing AbortController...")
    
    abort_controller = AbortController()
    
    # Test basic state
    assert not abort_controller.is_aborted()
    print("✓ Initial state correct")
    
    # Test abort functionality
    abort_controller.abort()
    assert abort_controller.is_aborted()
    print("✓ Abort functionality works")
    
    # Test reset
    abort_controller.reset()
    assert not abort_controller.is_aborted()
    print("✓ Reset functionality works")
    
    print("AbortController tests passed!\n")

async def test_app_context():
    """Test the AppContext with a nursery."""
    print("Testing AppContext...")
    
    async with trio.open_nursery() as nursery:
        abort_controller = AbortController()
        app_context = AppContext(nursery, abort_controller)
        
        assert app_context.nursery is nursery
        assert app_context.abort_controller is abort_controller
        assert not app_context.is_shutdown_requested()
        print("✓ AppContext creation works")
        
        # Test shutdown request
        app_context.request_shutdown()
        assert app_context.is_shutdown_requested()
        assert app_context.abort_controller.is_aborted()
        print("✓ Shutdown request works")
    
    print("AppContext tests passed!\n")

async def test_cancellation():
    """Test cancellation with CancelScope.""" 
    print("Testing Trio cancellation...")
    
    abort_controller = AbortController()
    
    # Test that cancel scope gets cancelled when abort is called
    with trio.CancelScope() as cancel_scope:
        abort_controller.set_cancel_scope(cancel_scope)
        abort_controller.abort()
        
        # The scope should now be cancelled
        assert cancel_scope.cancel_called
        print("✓ CancelScope cancellation works")
    
    print("Cancellation tests passed!\n")

async def main():
    """Run all tests."""
    print("🚀 Testing Trio Migration Components\n")
    
    await test_abort_controller()
    await test_app_context()  
    await test_cancellation()
    
    print("🎉 All tests passed! Trio migration basics are working.")

if __name__ == "__main__":
    trio.run(main)