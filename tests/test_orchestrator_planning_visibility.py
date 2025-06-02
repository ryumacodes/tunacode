#!/usr/bin/env python3
"""Test the orchestrator planning visibility features."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

async def test_planning_visibility():
    """Test that planning steps are visible in orchestrator output."""
    from tunacode.core.agents.orchestrator import OrchestratorAgent
    from tunacode.core.state import StateManager
    from tunacode.types import ModelName
    
    # Create state manager
    state = StateManager()
    
    # Set a default model
    state.session.current_model = ModelName("anthropic:claude-3-haiku-20240307")
    
    # Set required config
    state.session.user_config = {
        "settings": {
            "max_retries": 3,
            "max_iterations": 20
        }
    }
    
    # Create orchestrator
    orchestrator = OrchestratorAgent(state)
    
    # Test request that should generate multiple tasks
    test_request = """
    I need to analyze the project structure and then add a new feature.
    First, read the README.md file to understand the project.
    Then create a new file called feature.py with a simple function.
    """
    
    print("=== Testing Orchestrator Planning Visibility ===\n")
    print(f"Request: {test_request.strip()}\n")
    
    try:
        # Run the orchestrator
        results = await orchestrator.run(test_request)
        
        print(f"\n=== Orchestrator completed with {len(results)} results ===")
        
    except Exception as e:
        print(f"\nError during orchestration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_planning_visibility())