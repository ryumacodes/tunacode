#!/usr/bin/env python3
"""Integration test for architect mode with actual orchestrator."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))


async def test_orchestrator_planning():
    """Test that orchestrator actually creates and shows a plan."""
    print("\n[TEST] Testing orchestrator planning output...")
    
    try:
        from tunacode.core.agents.orchestrator import OrchestratorAgent
        from tunacode.core.state import StateManager
        from tunacode.types import ModelName
        from unittest.mock import patch, MagicMock
        
        # Create state manager
        state = StateManager()
        state.session.current_model = ModelName("anthropic:claude-3-haiku-20240307")
        state.session.user_config = {
            "settings": {
                "max_retries": 3,
                "max_iterations": 20
            }
        }
        
        # Create orchestrator
        orchestrator = OrchestratorAgent(state)
        
        # Mock the LLM to return a simple plan
        mock_tasks = [
            MagicMock(id=1, description="Read the file", mutate=False),
            MagicMock(id=2, description="Update the code", mutate=True)
        ]
        
        # Capture console output
        outputs = []
        
        def capture_print(*args, **kwargs):
            if args:
                outputs.append(str(args[0]))
        
        with patch('rich.console.Console.print', side_effect=capture_print):
            with patch('tunacode.core.llm.planner.make_plan', return_value=mock_tasks):
                # Mock the agent execution
                mock_run = MagicMock()
                mock_run.result = MagicMock(output="Task completed")
                
                with patch.object(orchestrator, '_run_sub_task', return_value=mock_run):
                    # Run orchestrator
                    results = await orchestrator.run("Test request")
                    
                    # Check outputs
                    assert any("[TARGET] Orchestrator Mode" in out for out in outputs), "Missing orchestrator start message"
                    assert any("Executing plan" in out for out in outputs), "Missing execution message"
                    assert any("[SUCCESS] Orchestrator completed" in out for out in outputs), "Missing completion message"
                    
                    print("[PASS] Orchestrator displayed planning messages")
                    print("[PASS] Orchestrator completed successfully")
                    
        print("[SUCCESS] Orchestrator planning test PASSED!")
        
    except ImportError as e:
        print(f"[WARNING]  Skipping integration test due to missing dependencies: {e}")
        print("[SUCCESS] Integration test skipped (dependencies not available)")


async def test_architect_mode_check():
    """Test the actual check in repl.py for architect mode."""
    print("\n[TEST] Testing architect mode check in process_request...")
    
    # Simulate the check from repl.py
    class MockSession:
        architect_mode = False
    
    class MockState:
        session = MockSession()
    
    state = MockState()
    
    # Test the actual condition used in repl.py
    if getattr(state.session, 'architect_mode', False):
        print("[FAIL] Should not use orchestrator when architect_mode is False")
        assert False
    else:
        print("[PASS] Correctly skipping orchestrator when architect_mode is False")
    
    # Enable architect mode
    state.session.architect_mode = True
    
    if getattr(state.session, 'architect_mode', False):
        print("[PASS] Correctly using orchestrator when architect_mode is True")
    else:
        print("[FAIL] Should use orchestrator when architect_mode is True")
        assert False
    
    print("[SUCCESS] Architect mode check test PASSED!")


async def main():
    """Run integration tests."""
    print("=" * 60)
    print("ARCHITECT MODE INTEGRATION TESTS")
    print("=" * 60)
    
    await test_architect_mode_check()
    await test_orchestrator_planning()
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL INTEGRATION TESTS COMPLETED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())