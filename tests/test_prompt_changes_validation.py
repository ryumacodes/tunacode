"""Test to validate the system prompt changes."""

from pathlib import Path


def test_system_prompt_no_json_in_responses():
    """Verify system prompt doesn't instruct agent to output JSON to users."""
    prompt_path = Path(__file__).parent.parent / "src" / "tunacode" / "prompts" / "system.md"

    with open(prompt_path, "r") as f:
        content = f.read()

    # Check that we have the new formatting rules
    assert "Output Formatting Rules" in content
    assert "NO JSON in responses" in content
    assert 'Never output {"thought":' in content

    # Check that thoughts are marked as internal
    assert "Thoughts are for internal reasoning only" in content
    assert "NEVER include JSON-formatted thoughts in your responses to users" in content

    # Check examples use clean formatting
    assert "RESPONSE TO USER:" in content
    assert "[Internal thinking - not shown to user]" in content

    # Check we have good/bad examples
    assert "Example of GOOD response formatting:" in content
    assert "Example of BAD response formatting (DO NOT DO THIS):" in content

    print("\n=== SYSTEM PROMPT VALIDATION ===")
    print("✓ Output formatting rules added")
    print("✓ JSON responses explicitly forbidden")
    print("✓ Thoughts marked as internal only")
    print("✓ Examples updated to show clean output")
    print("\nThe system prompt should now produce clean, formatted text responses.")
