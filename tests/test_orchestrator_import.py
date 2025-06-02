#!/usr/bin/env python3
"""Basic import tests for the orchestrator components."""

import sys
import os

# Add src to path so we can import tunacode modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_orchestrator_import():
    try:
        from tunacode.core.agents import OrchestratorAgent
        from tunacode.core.state import StateManager

        state = StateManager()
        orch = OrchestratorAgent(state)
        assert orch
        print("✓ OrchestratorAgent import successful")
    except Exception as e:
        print(f"✗ OrchestratorAgent import failed: {e}")
        raise
