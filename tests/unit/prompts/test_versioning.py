"""Unit tests for prompt versioning."""

from __future__ import annotations

from pathlib import Path

from tunacode.constants import AGENTS_MD
from tunacode.prompts.versioning import (
    agent_versions_equal,
    compute_agent_prompt_versions,
    compute_prompt_version,
    versions_equal,
)
from tunacode.types.canonical import AgentPromptVersions, PromptVersion


class TestComputePromptVersion:
    """Tests for compute_prompt_version()."""

    def test_returns_version_for_existing_file(self, tmp_path: Path) -> None:
        """Should return PromptVersion with valid SHA256 for existing file."""
        test_file = tmp_path / "test_prompt.md"
        test_content = "Test prompt content"
        test_file.write_text(test_content, encoding="utf-8")

        version = compute_prompt_version(test_file)

        assert version is not None
        assert isinstance(version, PromptVersion)
        assert version.source_path == str(test_file)
        assert version.content_hash
        assert len(version.content_hash) == 64  # SHA-256 hex length
        assert version.mtime > 0
        assert version.computed_at > 0
        assert version.length == len(test_content)

    def test_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Should return None for file that doesn't exist."""
        version = compute_prompt_version(tmp_path / "nonexistent.md")
        assert version is None

    def test_same_content_produces_same_hash(self, tmp_path: Path) -> None:
        """Should produce identical hash for identical content."""
        content = "Identical prompt content"

        file1 = tmp_path / "prompt1.md"
        file2 = tmp_path / "prompt2.md"
        file1.write_text(content, encoding="utf-8")
        file2.write_text(content, encoding="utf-8")

        version1 = compute_prompt_version(file1)
        version2 = compute_prompt_version(file2)

        assert version1 is not None
        assert version2 is not None
        assert version1.content_hash == version2.content_hash

    def test_different_content_produces_different_hash(self, tmp_path: Path) -> None:
        """Should produce different hash for different content."""
        file1 = tmp_path / "prompt1.md"
        file2 = tmp_path / "prompt2.md"
        file1.write_text("Content A", encoding="utf-8")
        file2.write_text("Content B", encoding="utf-8")

        version1 = compute_prompt_version(file1)
        version2 = compute_prompt_version(file2)

        assert version1 is not None
        assert version2 is not None
        assert version1.content_hash != version2.content_hash


class TestComputeAgentPromptVersions:
    """Tests for compute_agent_prompt_versions()."""

    def test_returns_agent_versions_with_fingerprint(self, tmp_path: Path) -> None:
        """Should return AgentPromptVersions with valid fingerprint."""
        system_file = tmp_path / "system.md"
        context_file = tmp_path / "context.md"
        tool_file = tmp_path / "tool.xml"

        system_file.write_text("System prompt", encoding="utf-8")
        context_file.write_text("Context content", encoding="utf-8")
        tool_file.write_text("<tool>Tool prompt</tool>", encoding="utf-8")

        versions = compute_agent_prompt_versions(
            system_prompt_path=system_file,
            tunacode_context_path=context_file,
            tool_prompt_paths={"bash": str(tool_file)},
        )

        assert isinstance(versions, AgentPromptVersions)
        assert versions.system_prompt is not None
        assert versions.tunacode_context is not None
        assert "bash" in versions.tool_prompts
        assert versions.fingerprint
        assert len(versions.fingerprint) == 64
        assert versions.computed_at > 0

    def test_handles_none_paths_gracefully(self, tmp_path: Path) -> None:
        """Should handle None paths without error."""
        versions = compute_agent_prompt_versions(
            system_prompt_path=None,
            tunacode_context_path=None,
            tool_prompt_paths=None,
        )

        assert isinstance(versions, AgentPromptVersions)
        assert versions.system_prompt is None
        assert versions.tunacode_context is None
        assert versions.tool_prompts == {}
        # Fingerprint should still be computed from empty input
        assert versions.fingerprint

    def test_fingerprint_changes_with_content_change(self, tmp_path: Path) -> None:
        """Fingerprint should change when any prompt content changes."""
        system_file = tmp_path / "system.md"

        system_file.write_text("Original content", encoding="utf-8")
        versions1 = compute_agent_prompt_versions(system_prompt_path=system_file)

        system_file.write_text("Modified content", encoding="utf-8")
        versions2 = compute_agent_prompt_versions(system_prompt_path=system_file)

        assert versions1.fingerprint != versions2.fingerprint


class TestVersionsEqual:
    """Tests for versions_equal()."""

    def test_none_both_none_returns_true(self) -> None:
        """Both None should return True."""
        assert versions_equal(None, None) is True

    def test_one_none_returns_false(self, tmp_path: Path) -> None:
        """One None, one value should return False."""
        test_file = tmp_path / "test.md"
        test_file.write_text("content", encoding="utf-8")
        version = compute_prompt_version(test_file)

        assert versions_equal(version, None) is False
        assert versions_equal(None, version) is False

    def test_same_hash_returns_true(self, tmp_path: Path) -> None:
        """Same content hash should return True."""
        content = "Same content"
        file1 = tmp_path / "file1.md"
        file2 = tmp_path / "file2.md"
        file1.write_text(content, encoding="utf-8")
        file2.write_text(content, encoding="utf-8")

        version1 = compute_prompt_version(file1)
        version2 = compute_prompt_version(file2)

        assert versions_equal(version1, version2) is True

    def test_different_hash_returns_false(self, tmp_path: Path) -> None:
        """Different content hash should return False."""
        file1 = tmp_path / "file1.md"
        file2 = tmp_path / "file2.md"
        file1.write_text("A", encoding="utf-8")
        file2.write_text("B", encoding="utf-8")

        version1 = compute_prompt_version(file1)
        version2 = compute_prompt_version(file2)

        assert versions_equal(version1, version2) is False


class TestAgentVersionsEqual:
    """Tests for agent_versions_equal()."""

    def test_none_both_none_returns_true(self) -> None:
        """Both None should return True."""
        assert agent_versions_equal(None, None) is True

    def test_one_none_returns_false(self, tmp_path: Path) -> None:
        """One None, one value should return False."""
        system_file = tmp_path / "system.md"
        system_file.write_text("content", encoding="utf-8")

        versions = compute_agent_prompt_versions(system_prompt_path=system_file)
        assert agent_versions_equal(versions, None) is False
        assert agent_versions_equal(None, versions) is False

    def test_same_fingerprint_returns_true(self, tmp_path: Path) -> None:
        """Same fingerprint should return True."""
        system_file = tmp_path / "system.md"
        system_file.write_text("content", encoding="utf-8")

        versions1 = compute_agent_prompt_versions(system_prompt_path=system_file)
        versions2 = compute_agent_prompt_versions(system_prompt_path=system_file)

        assert agent_versions_equal(versions1, versions2) is True

    def test_different_fingerprint_returns_false(self, tmp_path: Path) -> None:
        """Different fingerprint should return False."""
        system_file = tmp_path / "system.md"

        system_file.write_text("content A", encoding="utf-8")
        versions1 = compute_agent_prompt_versions(system_prompt_path=system_file)

        system_file.write_text("content B", encoding="utf-8")
        versions2 = compute_agent_prompt_versions(system_prompt_path=system_file)

        assert agent_versions_equal(versions1, versions2) is False


class TestAGENTSMDConstantUsage:
    """Regression tests for AGENTS.md hardcoded path consistency."""

    def test_agents_md_constant_value(self) -> None:
        """AGENTS_MD constant must be 'AGENTS.md'."""
        assert AGENTS_MD == "AGENTS.md"
