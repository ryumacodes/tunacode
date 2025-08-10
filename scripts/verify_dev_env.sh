#!/usr/bin/env bash
# Verify TunaCode development environment

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Verifying TunaCode Development Environment${NC}"
echo "==========================================="

# Check venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "  Run: hatch run install"
    exit 1
fi

# Check if we're in venv
if [ "${VIRTUAL_ENV:-}" != "" ]; then
    echo -e "${GREEN}✓ Virtual environment is activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not activated${NC}"
    echo "  Run: source venv/bin/activate"
fi

# Check Python version
PYTHON_VERSION=$(venv/bin/python --version 2>&1 | cut -d' ' -f2)
echo -e "${BLUE}Python version:${NC} $PYTHON_VERSION"

# Check required tools
echo -e "\n${BLUE}Development tools:${NC}"
for tool in black isort flake8 pytest; do
    if venv/bin/$tool --version &>/dev/null; then
        echo -e "${GREEN}✓${NC} $tool installed"
    else
        echo -e "${RED}✗${NC} $tool not found"
    fi
done

# Check if pytest-asyncio is installed
if venv/bin/python -c "import pytest_asyncio" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} pytest-asyncio installed"
else
    echo -e "${RED}✗${NC} pytest-asyncio not found"
fi

# Check if tunacode is installed
if venv/bin/pip show tunacode-cli &>/dev/null; then
    # Check if it's editable by looking for the .egg-link file
    if [ -f "venv/lib/python3.10/site-packages/tunacode-cli.egg-link" ] || [ -f "venv/lib/python3.11/site-packages/tunacode-cli.egg-link" ] || [ -f "venv/lib/python3.12/site-packages/tunacode-cli.egg-link" ]; then
        echo -e "${GREEN}✓${NC} tunacode-cli installed in editable mode"
    else
        echo -e "${GREEN}✓${NC} tunacode-cli installed"
    fi
else
    echo -e "${RED}✗${NC} tunacode-cli not installed"
fi

# Run a simple test
echo -e "\n${BLUE}Running sample test...${NC}"
if venv/bin/pytest tests/test_agent_initialization.py::test_agent_creation_with_missing_system_prompt_files -q; then
    echo -e "${GREEN}✓ Tests are working${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
fi

echo -e "\n${GREEN}Environment verification complete!${NC}"
