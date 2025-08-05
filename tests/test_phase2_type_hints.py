"""Tests for Phase 2: Type Hints Enhancement

These tests validate that type hints are properly added and working
across the codebase. They will fail initially and guide the implementation.
"""

import inspect

import pytest

from tunacode.configuration import defaults
from tunacode.core.agents import main as agents_main
from tunacode.tools.bash import bash
from tunacode.tools.grep import grep
from tunacode.tools.read_file import read_file
from tunacode.ui.tool_ui import ToolUI


class TestCoreAgentsTypeHints:
    """Test type hints in core/agents/main.py"""

    def test_get_agent_tool_has_return_type(self):
        """Test that get_agent_tool has proper return type annotation"""
        # This function should return a tuple of (Agent, Tool) types
        sig = inspect.signature(agents_main.get_agent_tool)
        assert sig.return_annotation != inspect.Signature.empty, (
            "get_agent_tool should have return type annotation"
        )

    def test_check_query_satisfaction_fully_typed(self):
        """Test that check_query_satisfaction has all parameters and return typed"""
        sig = inspect.signature(agents_main.check_query_satisfaction)

        # Check all parameters have type annotations
        for param_name, param in sig.parameters.items():
            assert param.annotation != inspect.Parameter.empty, (
                f"Parameter '{param_name}' in check_query_satisfaction should have type annotation"
            )

        # Check return type
        assert sig.return_annotation != inspect.Signature.empty, (
            "check_query_satisfaction should have return type annotation"
        )

    def test_process_request_fully_typed(self):
        """Test that process_request has all parameters and return typed"""
        sig = inspect.signature(agents_main.process_request)

        # Check all parameters have type annotations
        for param_name, param in sig.parameters.items():
            assert param.annotation != inspect.Parameter.empty, (
                f"Parameter '{param_name}' in process_request should have type annotation"
            )

        # Check return type
        assert sig.return_annotation != inspect.Signature.empty, (
            "process_request should have return type annotation"
        )


class TestToolsTypeHints:
    """Test type hints in tools/ modules"""

    def test_bash_tool_fully_typed(self):
        """Test that bash tool function has proper type annotations"""
        sig = inspect.signature(bash)

        for param_name, param in sig.parameters.items():
            assert param.annotation != inspect.Parameter.empty, (
                f"Parameter '{param_name}' in bash tool should have type annotation"
            )

        assert sig.return_annotation != inspect.Signature.empty, (
            "bash tool should have return type annotation"
        )

    def test_grep_tool_fully_typed(self):
        """Test that grep tool function has proper type annotations"""
        sig = inspect.signature(grep)

        for param_name, param in sig.parameters.items():
            assert param.annotation != inspect.Parameter.empty, (
                f"Parameter '{param_name}' in grep tool should have type annotation"
            )

        assert sig.return_annotation != inspect.Signature.empty, (
            "grep tool should have return type annotation"
        )

    def test_read_file_tool_fully_typed(self):
        """Test that read_file tool function has proper type annotations"""
        sig = inspect.signature(read_file)

        for param_name, param in sig.parameters.items():
            assert param.annotation != inspect.Parameter.empty, (
                f"Parameter '{param_name}' in read_file tool should have type annotation"
            )

        assert sig.return_annotation != inspect.Signature.empty, (
            "read_file tool should have return type annotation"
        )


class TestUITypeHints:
    """Test type hints in ui/ components"""

    def test_tool_ui_show_confirmation_fully_typed(self):
        """Test that ToolUI.show_confirmation has proper type annotations"""
        sig = inspect.signature(ToolUI.show_confirmation)

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            assert param.annotation != inspect.Parameter.empty, (
                f"Parameter '{param_name}' in ToolUI.show_confirmation should have type annotation"
            )

        assert sig.return_annotation != inspect.Signature.empty, (
            "ToolUI.show_confirmation should have return type annotation"
        )

    def test_tool_ui_log_mcp_fully_typed(self):
        """Test that ToolUI.log_mcp has proper type annotations"""
        sig = inspect.signature(ToolUI.log_mcp)

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            assert param.annotation != inspect.Parameter.empty, (
                f"Parameter '{param_name}' in ToolUI.log_mcp should have type annotation"
            )


class TestConfigurationTypeHints:
    """Test type hints in configuration/ modules"""

    def test_path_config_attributes_typed(self):
        """Test that PathConfig attributes have type annotations"""
        # Check class attributes
        from tunacode.configuration.settings import PathConfig

        # The attributes should have type annotations in __init__
        assert hasattr(PathConfig, "__init__"), "PathConfig should have __init__ method"

        # Check that the class uses type annotations (through inspection of source)
        import inspect

        source = inspect.getsource(PathConfig.__init__)
        assert "ConfigPath" in source, "PathConfig should use ConfigPath type annotation"
        assert "ConfigFile" in source, "PathConfig should use ConfigFile type annotation"

    def test_application_settings_attributes_typed(self):
        """Test that ApplicationSettings has proper type annotations"""
        from tunacode.configuration.settings import ApplicationSettings

        # Check that internal_tools has type annotation
        source = inspect.getsource(ApplicationSettings)
        assert "list[ToolName]" in source, (
            "internal_tools should have list[ToolName] type annotation"
        )

    def test_defaults_constants_have_type_annotations(self):
        """Test that module-level constants in defaults have type annotations"""
        # This will check that when we add type annotations to module constants,
        # they are properly defined
        # We'll use AST to check for annotated assignments
        import ast
        import inspect

        source = inspect.getsource(defaults)
        tree = ast.parse(source)

        # Count annotated assignments (this will increase as we add type hints)
        annotated_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.AnnAssign))

        # The defaults module has DEFAULT_USER_CONFIG which is already annotated
        assert annotated_count >= 1, (
            f"Expected at least 1 annotated constant in defaults module, found {annotated_count}"
        )


class TestMypyCompliance:
    """Test that modules pass mypy type checking"""

    @pytest.mark.skip(reason="Will enable after adding type hints")
    def test_core_agents_mypy_compliant(self):
        """Test that core/agents passes mypy checks"""
        import subprocess

        result = subprocess.run(
            ["mypy", "src/tunacode/core/agents/main.py", "--strict"], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Mypy errors:\n{result.stdout}\n{result.stderr}"

    @pytest.mark.skip(reason="Will enable after adding type hints")
    def test_tools_mypy_compliant(self):
        """Test that tools modules pass mypy checks"""
        import subprocess

        result = subprocess.run(
            ["mypy", "src/tunacode/tools/", "--strict"], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Mypy errors:\n{result.stdout}\n{result.stderr}"
