#!/usr/bin/env python3
"""
Simple test for CLI functionality without trio interference.
"""
import sys
sys.path.insert(0, 'src')

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing module imports...")
    
    try:
        from src.tunacode.debug.trio_debug import trio_debug, debug_trio_function
        print("✅ Debug system imported")
    except Exception as e:
        print(f"❌ Debug system import failed: {e}")
        return False
    
    try:
        from src.tunacode.core.abort_controller import AbortController, AppContext
        print("✅ AbortController imported")
    except Exception as e:
        print(f"❌ AbortController import failed: {e}")
        return False
    
    try:
        from src.tunacode.cli.commands.debug_command import TrioDebugCommand
        cmd = TrioDebugCommand()
        print(f"✅ Debug command imported: {cmd.name}")
    except Exception as e:
        print(f"❌ Debug command import failed: {e}")
        return False
    
    try:
        from src.tunacode.cli.main import app
        print("✅ Main CLI app imported")
    except Exception as e:
        print(f"❌ Main CLI app import failed: {e}")
        return False
    
    return True

def test_debug_functionality():
    """Test debug functionality."""
    print("\n🔧 Testing debug functionality...")
    
    try:
        from src.tunacode.debug.trio_debug import trio_debug
        
        # Test event logging
        trio_debug.log_event("TEST_EVENT", "TestRunner", "Testing debug system", "INFO")
        print("✅ Event logging works")
        
        # Test abort controller tracking
        trio_debug.abort_controller_created("test-controller")
        trio_debug.abort_controller_aborted("test-controller", "test-trigger")
        trio_debug.abort_controller_reset("test-controller")
        print("✅ AbortController tracking works")
        
        # Test key press tracking
        trio_debug.key_pressed("Esc", "test_action")
        print("✅ Key press tracking works")
        
        # Test streaming tracking
        trio_debug.streaming_started("test-stream")
        trio_debug.streaming_stopped("test-stream", "test-reason")
        print("✅ Streaming tracking works")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug functionality failed: {e}")
        return False

def test_command_creation():
    """Test that commands can be created."""
    print("\n⚙️ Testing command creation...")
    
    try:
        from src.tunacode.cli.commands.debug_command import TrioDebugCommand
        from src.tunacode.types import CommandContext
        from src.tunacode.core.state import StateManager
        
        # Create command
        cmd = TrioDebugCommand()
        print(f"✅ Command created: {cmd.name}")
        print(f"   Aliases: {cmd.aliases}")
        print(f"   Category: {cmd.category}")
        
        # Test command properties
        assert cmd.name == "triodebug"
        assert "debug" in cmd.aliases
        print("✅ Command properties correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Command creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Trio Debug CLI Integration\n")
    
    success = True
    success &= test_imports()
    success &= test_debug_functionality() 
    success &= test_command_creation()
    
    print(f"\n{'🎉 All tests passed!' if success else '❌ Some tests failed!'}")
    
    if success:
        print("\n📋 Debug features available:")
        print("  • Live debug visualization")
        print("  • Event tracking and logging")
        print("  • AbortController monitoring")
        print("  • Key press detection")
        print("  • Streaming operation tracking")
        print("  • /debug command for runtime control")
        
        print("\n🔧 To use debug features:")
        print("  1. Start TunaCode normally")
        print("  2. Use '/debug on' to enable live display")
        print("  3. Press Esc or Ctrl+C to test cancellation")
        print("  4. Use '/debug summary' to see session stats")

if __name__ == "__main__":
    main()