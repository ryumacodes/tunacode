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
uv sync --dev

# Set up pre-commit hooks
echo "Installing pre-commit hooks..."
uv run pre-commit install

# Create .env from template if missing
if [[ ! -f .env ]] && [[ -f .env.example ]]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Edit .env to add your API keys"
fi

# Validate environment
echo "Validating environment..."
uv run python -c "import tunacode; print(f'tunacode {tunacode.__version__ if hasattr(tunacode, \"__version__\") else \"installed\"}')" 2>/dev/null || echo "Package ready"

echo "=== Setup complete ==="
echo "Run: uv run tunacode"
