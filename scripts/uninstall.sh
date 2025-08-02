#!/bin/bash

# TunaCode Uninstall Script
# This script completely removes TunaCode from your system

set -e

echo "🗑️  TunaCode Uninstall Script"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to safely remove file/directory if it exists
safe_remove() {
    if [ -e "$1" ]; then
        rm -rf "$1"
        print_success "Removed: $1"
        return 0
    else
        print_status "Not found: $1 (skipping)"
        return 1
    fi
}

# Variables to track what was removed
removed_count=0
found_installation=false

print_status "Checking for TunaCode installations..."

# Check for pipx installation
if command_exists pipx; then
    print_status "Checking pipx installations..."
    if pipx list 2>/dev/null | grep -q "tunacode"; then
        print_status "Found TunaCode installed via pipx, removing..."
        pipx uninstall tunacode
        found_installation=true
        ((removed_count++))
        print_success "Uninstalled TunaCode from pipx"
    else
        print_status "TunaCode not found in pipx"
    fi
else
    print_warning "pipx not found, skipping pipx check"
fi

# Check for pip user installation
print_status "Checking pip user installations..."
if pip list --user 2>/dev/null | grep -q "tunacode"; then
    print_status "Found TunaCode in user pip packages, removing..."
    pip uninstall tunacode -y --user 2>/dev/null || true
    found_installation=true
    ((removed_count++))
    print_success "Uninstalled TunaCode from user pip"
else
    print_status "TunaCode not found in user pip packages"
fi

# Check for system pip installation
print_status "Checking system pip installations..."
if pip list 2>/dev/null | grep -q "tunacode"; then
    print_status "Found TunaCode in system pip packages, removing..."
    if pip uninstall tunacode -y 2>/dev/null; then
        found_installation=true
        ((removed_count++))
        print_success "Uninstalled TunaCode from system pip"
    else
        print_warning "Could not uninstall from system pip (may require sudo or be externally managed)"
        # Try with --break-system-packages flag if available
        if pip uninstall tunacode -y --break-system-packages 2>/dev/null; then
            found_installation=true
            ((removed_count++))
            print_success "Uninstalled TunaCode from system pip (with --break-system-packages)"
        fi
    fi
else
    print_status "TunaCode not found in system pip packages"
fi

# Remove leftover binaries
print_status "Checking for leftover binaries..."
binary_locations=(
    "$HOME/.local/bin/tunacode"
    "/usr/local/bin/tunacode"
    "/usr/bin/tunacode"
)

for binary in "${binary_locations[@]}"; do
    if safe_remove "$binary"; then
        ((removed_count++))
    fi
done

# Remove configuration files
print_status "Checking for configuration files..."
config_locations=(
    "$HOME/.config/tunacode.json"
    "$HOME/.config/tunacode_config.yml"
    "$HOME/.config/tunacode"
    "$HOME/.tunacode"
)

for config in "${config_locations[@]}"; do
    if safe_remove "$config"; then
        ((removed_count++))
    fi
done

# Final verification
print_status "Verifying removal..."

# Check if tunacode command still exists
if command_exists tunacode; then
    print_warning "tunacode command still found in PATH: $(which tunacode)"
    print_warning "You may need to manually remove it or restart your shell"
else
    print_success "tunacode command no longer found in PATH"
fi

# Check for remaining config files
remaining_configs=$(find "$HOME" -name "*tunacode*" -type f 2>/dev/null | head -5)
if [ -n "$remaining_configs" ]; then
    print_warning "Some TunaCode-related files may still exist:"
    echo "$remaining_configs"
fi

echo ""
echo "=============================="
if [ $removed_count -gt 0 ]; then
    print_success "TunaCode uninstallation completed!"
    print_success "Removed $removed_count item(s)"
    if [ "$found_installation" = true ]; then
        print_status "Package successfully uninstalled"
    fi
else
    print_warning "No TunaCode installation found to remove"
fi

echo ""
print_status "If you installed TunaCode from source or in a virtual environment,"
print_status "you may need to manually remove those installations."
echo ""
print_status "Thank you for using TunaCode!"
