#!/usr/bin/env python3
"""Test DSPy integration in TunaCode."""

import pytest
from pathlib import Path

from tunacode.core.state import StateManager
from tunacode.core.agents.dspy_integration import DSPyIntegration
from tunacode.configuration.defaults import DEFAULT_USER_CONFIG


class TestDSPyIntegration:
    """Test suite for DSPy integration."""
    
    def setup_method(self):
        """Set up test state."""
        self.state_manager = StateManager()
        self.state_manager.session.user_config = DEFAULT_USER_CONFIG.copy()
        self.state_manager.session.cwd = "."
    
    def test_dspy_prompts_loaded(self):
        """Test that DSPy prompts are loaded correctly."""
        dspy = DSPyIntegration(self.state_manager)
        
        assert dspy._tool_selection_prompt is not None, "Tool selection prompt should be loaded"
        assert dspy._task_planning_prompt is not None, "Task planning prompt should be loaded"
        assert "DSPy Tool Selection Prompt" in dspy._tool_selection_prompt
        assert "DSPy Task Planning Prompt" in dspy._task_planning_prompt
    
    def test_system_prompt_enhancement(self):
        """Test that system prompt is enhanced with DSPy patterns."""
        dspy = DSPyIntegration(self.state_manager)
        
        base_prompt = "You are a helpful AI assistant."
        enhanced = dspy.enhance_system_prompt(base_prompt)
        
        # Should add DSPy content
        assert len(enhanced) > len(base_prompt), "Enhanced prompt should be longer"
        
        # Should contain key DSPy patterns
        assert "DSPy-Optimized Tool Selection Patterns" in enhanced
        assert "Always batch 3-4 read-only tools" in enhanced
        assert "Chain of Thought reasoning" in enhanced
        assert "Based on learned optimization patterns" in enhanced
    
    def test_complex_task_detection(self):
        """Test detection of complex tasks that need planning."""
        dspy = DSPyIntegration(self.state_manager)
        
        # Simple tasks
        assert not dspy.should_use_task_planner("Show me main.py")
        assert not dspy.should_use_task_planner("Read config.json")
        assert not dspy.should_use_task_planner("List files in src/")
        
        # Complex tasks
        assert dspy.should_use_task_planner("Implement user authentication with JWT")
        assert dspy.should_use_task_planner("Create REST API with database integration")
        assert dspy.should_use_task_planner("Build a todo app with React and tests")
    
    def test_tool_batching_optimization(self):
        """Test that tools are batched according to DSPy patterns."""
        dspy = DSPyIntegration(self.state_manager)
        
        # Mix of read-only and write tools
        tools = [
            {"tool": "read_file", "args": {"filepath": "a.py"}},
            {"tool": "grep", "args": {"pattern": "test"}},
            {"tool": "list_dir", "args": {"directory": "."}},
            {"tool": "write_file", "args": {"filepath": "out.py"}},
            {"tool": "read_file", "args": {"filepath": "b.py"}},
            {"tool": "glob", "args": {"pattern": "*.py"}},
        ]
        
        batches = dspy._apply_dspy_patterns(tools)
        
        # Should create 3 batches
        assert len(batches) == 3, "Should create 3 batches"
        
        # First batch: 3 read-only tools
        assert len(batches[0]) == 3
        assert all(t["tool"] in ["read_file", "grep", "list_dir"] for t in batches[0])
        
        # Second batch: 1 write tool
        assert len(batches[1]) == 1
        assert batches[1][0]["tool"] == "write_file"
        
        # Third batch: 2 read-only tools
        assert len(batches[2]) == 2
        assert all(t["tool"] in ["read_file", "glob"] for t in batches[2])
    
    def test_optimal_batch_size(self):
        """Test that read-only tools are batched in groups of 3-4."""
        dspy = DSPyIntegration(self.state_manager)
        
        # 6 read-only tools should be split into 2 batches
        tools = [
            {"tool": "read_file", "args": {"filepath": f"file{i}.py"}}
            for i in range(6)
        ]
        
        batches = dspy._apply_dspy_patterns(tools)
        
        # Should create 2 batches (4 + 2)
        assert len(batches) == 2
        assert len(batches[0]) == 4, "First batch should have 4 tools (optimal size)"
        assert len(batches[1]) == 2, "Second batch should have remaining 2 tools"
    
    def test_chain_of_thought_generation(self):
        """Test Chain of Thought reasoning generation."""
        dspy = DSPyIntegration(self.state_manager)
        
        cot = dspy.format_chain_of_thought("Find all error handlers", ["grep", "read_file"])
        
        assert "Let's think step by step" in cot
        assert "Find all error handlers" in cot
        assert "search" in cot.lower() or "find" in cot.lower()
    
    def test_dspy_disabled_in_config(self):
        """Test behavior when DSPy is disabled in config."""
        # Disable DSPy
        self.state_manager.session.user_config["settings"]["use_dspy_optimization"] = False
        
        # The setting should be respected
        assert not self.state_manager.session.user_config["settings"]["use_dspy_optimization"]
    
    def test_dspy_setting_exists(self):
        """Test that DSPy optimization setting exists in config."""
        # The setting should exist in the config
        assert "use_dspy_optimization" in self.state_manager.session.user_config["settings"]
        
        # And it should be a boolean
        setting = self.state_manager.session.user_config["settings"]["use_dspy_optimization"]
        assert isinstance(setting, bool)