"""Characterization tests for git command operations in git_safety_setup.py."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from tunacode.core.setup import git_safety_setup

@pytest.mark.asyncio
async def test_git_not_installed(monkeypatch):
    setup = git_safety_setup.GitSafetySetup(state_manager=MagicMock())
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: MagicMock(returncode=1))
    with patch("tunacode.core.setup.git_safety_setup.panel", new=AsyncMock()) as mock_panel:
        await setup.execute()
        mock_panel.assert_called()
        assert "Git is not installed" in mock_panel.call_args[0][1]

@pytest.mark.asyncio
async def test_not_a_git_repo(monkeypatch):
    setup = git_safety_setup.GitSafetySetup(state_manager=MagicMock())
    def run_side_effect(args, **kwargs):
        if args[:2] == ["git", "--version"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "rev-parse", "--git-dir"]:
            return MagicMock(returncode=1)
        return MagicMock(returncode=0)
    monkeypatch.setattr("subprocess.run", run_side_effect)
    with patch("tunacode.core.setup.git_safety_setup.panel", new=AsyncMock()) as mock_panel:
        await setup.execute()
        mock_panel.assert_called()
        assert "Not a Git Repository" in mock_panel.call_args[0][0]

@pytest.mark.asyncio
async def test_detached_head(monkeypatch):
    setup = git_safety_setup.GitSafetySetup(state_manager=MagicMock())
    def run_side_effect(args, **kwargs):
        if args[:2] == ["git", "--version"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "rev-parse", "--git-dir"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "branch", "--show-current"]:
            return MagicMock(returncode=0, stdout="")
        return MagicMock(returncode=0)
    monkeypatch.setattr("subprocess.run", run_side_effect)
    with patch("tunacode.core.setup.git_safety_setup.panel", new=AsyncMock()) as mock_panel:
        await setup.execute()
        mock_panel.assert_called()
        assert "Detached HEAD" in mock_panel.call_args[0][0]

@pytest.mark.asyncio
async def test_already_on_tunacode_branch(monkeypatch):
    setup = git_safety_setup.GitSafetySetup(state_manager=MagicMock())
    def run_side_effect(args, **kwargs):
        if args[:2] == ["git", "--version"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "rev-parse", "--git-dir"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "branch", "--show-current"]:
            return MagicMock(returncode=0, stdout="main-tunacode")
        return MagicMock(returncode=0)
    monkeypatch.setattr("subprocess.run", run_side_effect)
    with patch("tunacode.ui.console.info", new=AsyncMock()) as mock_info:
        await setup.execute()
        mock_info.assert_called()
        assert "Already on a TunaCode branch" in mock_info.call_args[0][0]

@pytest.mark.asyncio
async def test_create_branch_with_uncommitted_changes(monkeypatch):
    setup = git_safety_setup.GitSafetySetup(state_manager=MagicMock())
    def run_side_effect(args, **kwargs):
        if args[:2] == ["git", "--version"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "rev-parse", "--git-dir"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "branch", "--show-current"]:
            return MagicMock(returncode=0, stdout="main")
        if args[:3] == ["git", "status", "--porcelain"]:
            return MagicMock(returncode=0, stdout=" M file.txt")
        if args[:3] == ["git", "show-ref", "--verify"]:
            return MagicMock(returncode=1)
        if args[:3] == ["git", "checkout", "-b"]:
            return MagicMock(returncode=0)
        return MagicMock(returncode=0)
    monkeypatch.setattr("subprocess.run", run_side_effect)
    with patch("tunacode.core.setup.git_safety_setup.yes_no_prompt", new=AsyncMock(return_value=True)):
        with patch("tunacode.ui.console.success", new=AsyncMock()) as mock_success:
            await setup.execute()
            mock_success.assert_called()
            assert "Created and switched to new branch" in mock_success.call_args[0][0]

@pytest.mark.asyncio
async def test_branch_already_exists_and_switch(monkeypatch):
    setup = git_safety_setup.GitSafetySetup(state_manager=MagicMock())
    def run_side_effect(args, **kwargs):
        if args[:2] == ["git", "--version"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "rev-parse", "--git-dir"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "branch", "--show-current"]:
            return MagicMock(returncode=0, stdout="main")
        if args[:3] == ["git", "status", "--porcelain"]:
            return MagicMock(returncode=0, stdout="")
        if args[:3] == ["git", "show-ref", "--verify"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "checkout"]:
            return MagicMock(returncode=0)
        return MagicMock(returncode=0)
    monkeypatch.setattr("subprocess.run", run_side_effect)
    with patch("tunacode.core.setup.git_safety_setup.yes_no_prompt", new=AsyncMock(return_value=True)):
        with patch("tunacode.ui.console.success", new=AsyncMock()) as mock_success:
            await setup.execute()
            mock_success.assert_called()
            assert "Switched to existing branch" in mock_success.call_args[0][0]

@pytest.mark.asyncio
async def test_branch_creation_failure(monkeypatch):
    setup = git_safety_setup.GitSafetySetup(state_manager=MagicMock())
    def run_side_effect(args, **kwargs):
        if args[:2] == ["git", "--version"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "rev-parse", "--git-dir"]:
            return MagicMock(returncode=0)
        if args[:3] == ["git", "branch", "--show-current"]:
            return MagicMock(returncode=0, stdout="main")
        if args[:3] == ["git", "status", "--porcelain"]:
            return MagicMock(returncode=0, stdout="")
        if args[:3] == ["git", "show-ref", "--verify"]:
            return MagicMock(returncode=1)
        if args[:3] == ["git", "checkout", "-b"]:
            raise Exception("git error")
        return MagicMock(returncode=0)
    monkeypatch.setattr("subprocess.run", run_side_effect)
    with patch("tunacode.core.setup.git_safety_setup.yes_no_prompt", new=AsyncMock(return_value=True)):
        with patch("tunacode.core.setup.git_safety_setup.panel", new=AsyncMock()) as mock_panel:
            await setup.execute()
            mock_panel.assert_called()
            # Current behavior: shows "Git Safety Setup Failed" instead of specific error
            assert "Git Safety Setup Failed" in mock_panel.call_args[0][0]