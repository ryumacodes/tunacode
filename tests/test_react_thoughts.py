#!/usr/bin/env python3
"""
Simple test for ReAct thoughts functionality
"""
import asyncio
import sys
import os

# Add src to path so we can import tunacode modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_thoughts_command_import():
    """Test that ThoughtsCommand can be imported without errors"""
    try:
        from tunacode.cli.commands import ThoughtsCommand
        print("✓ ThoughtsCommand import successful")
        return True
    except ImportError as e:
        print(f"✗ ThoughtsCommand import failed: {e}")
        return False

def test_session_state_thoughts():
    """Test that SessionState has show_thoughts attribute"""
    try:
        from tunacode.core.state import SessionState
        
        # Create a session state
        session = SessionState()
        
        # Check default value
        assert hasattr(session, 'show_thoughts'), "SessionState missing show_thoughts attribute"
        assert session.show_thoughts == False, "Default show_thoughts should be False"
        
        # Test setting the value
        session.show_thoughts = True
        assert session.show_thoughts == True, "show_thoughts should be settable to True"
        
        session.show_thoughts = False
        assert session.show_thoughts == False, "show_thoughts should be settable to False"
        
        print("✓ SessionState.show_thoughts works correctly")
        return True
        
    except Exception as e:
        print(f"✗ SessionState thoughts test failed: {e}")
        return False

def test_agent_thought_processing():
    """Test that agent can process thought messages"""
    try:
        from tunacode.core.agents.main import _process_node
        from tunacode.core.state import StateManager
        
        # Create a mock state manager
        state_manager = StateManager()
        
        # Create a mock node with thought
        class MockNode:
            def __init__(self, thought_text):
                self.thought = thought_text
        
        # Test processing a node with a thought
        node_with_thought = MockNode("This is a test thought")
        
        # This should not raise an error
        asyncio.run(_process_node(node_with_thought, None, state_manager))
        
        # Check that thought was added to messages
        messages = state_manager.session.messages
        thought_messages = [msg for msg in messages if isinstance(msg, dict) and "thought" in msg]
        
        assert len(thought_messages) > 0, "Thought message should be added to session messages"
        assert thought_messages[0]["thought"] == "This is a test thought", "Thought content should match"
        
        print("✓ Agent thought processing works")
        return True
        
    except Exception as e:
        print(f"✗ Agent thought processing test failed: {e}")
        return False

def test_thoughts_command_functionality():
    """Test ThoughtsCommand execute method"""
    try:
        from tunacode.cli.commands import ThoughtsCommand, CommandContext
        from tunacode.core.state import StateManager
        
        # Create command and context
        command = ThoughtsCommand()
        state_manager = StateManager()
        context = CommandContext(state_manager=state_manager)
        
        # Test initial state
        assert state_manager.session.show_thoughts == False, "Initial state should be False"
        
        # Test toggle with no args (should toggle)
        asyncio.run(command.execute([], context))
        assert state_manager.session.show_thoughts == True, "Should toggle to True"
        
        asyncio.run(command.execute([], context))
        assert state_manager.session.show_thoughts == False, "Should toggle back to False"
        
        # Test explicit on
        asyncio.run(command.execute(["on"], context))
        assert state_manager.session.show_thoughts == True, "Should set to True with 'on'"
        
        # Test explicit off
        asyncio.run(command.execute(["off"], context))
        assert state_manager.session.show_thoughts == False, "Should set to False with 'off'"
        
        print("✓ ThoughtsCommand functionality works")
        return True
        
    except Exception as e:
        print(f"✗ ThoughtsCommand functionality test failed: {e}")
        return False

def main():
    """Run all ReAct thoughts tests"""
    print("Testing ReAct thoughts functionality...")
    print("=" * 50)
    
    tests = [
        test_thoughts_command_import,
        test_session_state_thoughts,
        test_agent_thought_processing,
        test_thoughts_command_functionality,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All ReAct thoughts tests PASSED!")
        return 0
    else:
        print("❌ Some tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())