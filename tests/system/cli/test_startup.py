"""Tests for TUI startup.

These tests verify that the TUI initializes correctly:
1. TUI components initialize without import errors
"""

from pathlib import Path


class TestTUIInitialization:
    """Tests for TUI component initialization without running the full app."""

    def test_state_manager_initializes(self) -> None:
        """Verify StateManager creates correctly."""
        from tunacode.core.session import StateManager

        state_manager = StateManager()
        assert state_manager is not None
        assert state_manager.session is not None

    def test_ui_main_imports_without_tools_layer(self) -> None:
        """Verify ui/main.py has no direct imports from tunacode.tools."""
        import tunacode.ui.main as main_module

        source = Path(main_module.__file__).read_text()
        assert "from tunacode.tools" not in source, "ui/main.py should not import from tools layer"

    def test_ui_repl_support_imports_without_tools_layer(self) -> None:
        """Verify ui/repl_support.py has no direct imports from tunacode.tools."""
        import tunacode.ui.repl_support as repl_module

        source = Path(repl_module.__file__).read_text()
        assert "from tunacode.tools" not in source, (
            "ui/repl_support.py should not import from tools layer"
        )

    def test_tui_module_imports_cleanly(self) -> None:
        """Verify TUI modules import without errors."""
        # These imports would fail if there were circular dependencies
        import tunacode.ui.main as main_module

        assert main_module.state_manager is None

        from tunacode.ui.repl_support import build_textual_tool_callback

        assert callable(build_textual_tool_callback)
