#!/usr/bin/env bash
# Single command setup for tunacode development environment
set -euo pipefail

echo "=== Tunacode Development Setup ==="

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create venv and install deps
echo "Installing dependencies..."
uv sync --extra dev

# Set up pre-commit hooks
echo "Installing pre-commit hooks..."
uv run pre-commit install

# Validate environment
echo "Validating environment..."
if uv run python -c "import tunacode; print(f'tunacode {tunacode.__version__ if hasattr(tunacode, \"__version__\") else \"installed\"}')" 2>&1; then
    echo "✓ Package validation successful"
else
    echo "✗ Package validation failed"
    exit 1
fi

echo "=== Setup complete ==="
echo "Run: uv run tunacode"
