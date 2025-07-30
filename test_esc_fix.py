#!/usr/bin/env python3
"""
Test the Esc key cancellation fix.
This directly tests the key binding with state_manager.
"""
import sys
sys.path.insert(0, 'src')

import trio
from rich.console import Console
from src.tunacode.core.abort_controller import AbortController, AppContext
from src.tunacode.core.state import StateManager
from src.tunacode.ui.keybindings import create_key_bindings

console = Console()

def test_key_binding_creation():
    """Test that key bindings are created properly with state_manager."""
    
    print("🔧 Testing key binding creation...")
    
    # Test 1: Create key bindings without state_manager (old way)
    kb1 = create_key_bindings()
    print(f"✓ Key bindings created without state_manager: {len(kb1.bindings)} bindings")
    
    # Test 2: Create key bindings with state_manager (new way)
    state_manager = StateManager()
    kb2 = create_key_bindings(state_manager)
    print(f"✓ Key bindings created with state_manager: {len(kb2.bindings)} bindings")
    
    # Test 3: Verify Esc key binding exists
    try:
        esc_bindings = []
        for binding in kb2.bindings:
            # Check if this binding is for the escape key
            key_str = str(binding.keys)
            if 'escape' in key_str.lower():
                esc_bindings.append(binding)
        
        print(f"✓ Found {len(esc_bindings)} Esc key binding(s)")
        
        if esc_bindings:
            print("✓ Esc key binding is properly configured")
            return True
        else:
            print("❌ No Esc key binding found")
            return False
    except Exception as e:
        print(f"❌ Error checking key bindings: {e}")
        return False

async def test_abort_controller_integration():
    """Test that abort controller works with key bindings."""
    
    print("\n🚀 Testing AbortController integration...")
    
    # Create state manager and abort controller
    state_manager = StateManager()
    abort_controller = AbortController()
    
    async with trio.open_nursery() as nursery:
        app_context = AppContext(nursery, abort_controller)
        state_manager.app_context = app_context
        
        # Test that abort controller is accessible
        if state_manager.app_context:
            if state_manager.app_context.abort_controller:
                print("✓ AbortController is accessible from state_manager")
                
                # Test abort mechanism
                abort_controller.abort(trigger="test")
                if abort_controller.is_aborted():
                    print("✓ AbortController.abort() works")
                    return True
                else:
                    print("❌ AbortController.abort() failed")
            else:
                print("❌ AbortController not found in app_context")
        else:
            print("❌ app_context not found in state_manager")
    
    return False

def test_multiline_input_integration():
    """Test that multiline_input correctly passes state_manager to key bindings."""
    
    print("\n🔌 Testing multiline_input integration...")
    
    # Look at the multiline_input function
    from src.tunacode.ui.input import multiline_input
    import inspect
    
    # Get the source code of multiline_input
    source = inspect.getsource(multiline_input)
    
    # Check if it passes state_manager to create_key_bindings
    if "create_key_bindings(state_manager)" in source:
        print("✓ multiline_input correctly passes state_manager to create_key_bindings")
        return True
    else:
        print("❌ multiline_input does not pass state_manager to create_key_bindings")
        print("Found in source:")
        for line in source.split('\n'):
            if 'create_key_bindings' in line:
                print(f"  {line.strip()}")
        return False

async def main():
    """Run all tests."""
    
    print("🧪 Testing Esc Key Cancellation Fix")
    print("=" * 50)
    
    test1_passed = test_key_binding_creation()
    test2_passed = await test_abort_controller_integration()
    test3_passed = test_multiline_input_integration()
    
    print("\n📊 Test Results:")
    print(f"  Key binding creation: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  AbortController integration: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"  multiline_input integration: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 All tests passed! The Esc key cancellation fix should work.")
        print("\nThe key components are properly connected:")
        print("  1. Key bindings can be created with state_manager")
        print("  2. AbortController is accessible from state_manager")
        print("  3. multiline_input passes state_manager to key bindings")
    else:
        print("\n⚠️  Some tests failed. The Esc key cancellation may not work properly.")

if __name__ == "__main__":
    try:
        trio.run(main)
    except KeyboardInterrupt:
        print("\n👋 Test ended by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()