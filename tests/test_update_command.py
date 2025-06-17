#!/usr/bin/env python3
"""
Test script for the UpdateCommand functionality.
Tests command registration and basic execution without actually running updates.
"""

import asyncio
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tunacode.cli.commands import UpdateCommand, CommandRegistry


@pytest.mark.asyncio
async def test_update_command():
    """Test the update command registration and basic functionality."""
    print("Testing UpdateCommand...")

    # Test command creation
    update_cmd = UpdateCommand()
    assert update_cmd.name == "update"
    assert "/update" in update_cmd.aliases
    assert update_cmd.description == "Update TunaCode to the latest version"
    print("✓ UpdateCommand created successfully")

    # Test command registry
    registry = CommandRegistry()
    registry.discover_commands()
    
    # Check if update command is registered
    assert "update" in registry._commands
    assert "/update" in registry._commands
    print("✓ UpdateCommand registered in command registry")

    # Test command detection
    assert registry.is_command("/update")
    assert registry.is_command("update")
    print("✓ UpdateCommand properly detected")

    print("✓ All UpdateCommand tests passed!")


if __name__ == "__main__":
    asyncio.run(test_update_command())