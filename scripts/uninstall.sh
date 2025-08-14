#!/bin/bash

# TunaCode Robust Uninstall Script
# This script safely removes TunaCode from your system with comprehensive detection

set -euo pipefail

echo "🗑️  TunaCode Robust Uninstall Script"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
VENV_DIR="${HOME}/.tunacode-venv"
BIN_DIR="${HOME}/.local/bin"

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
        echo -e "${YELLOW}Removing: $1${NC}"
        rm -rf "$1"
        print_success "Removed: $1"
        return 0
    else
        print_status "Not found: $1 (skipping)"
        return 1
    fi
}

# Enhanced installation detection (similar to install script)
detect_installations() {
    local found_venv=false
    local found_global_system=false
    local found_global_user=false
    local found_pipx=false
    local venv_working=false
    local global_system_working=false
    local global_user_working=false
    local pipx_working=false

    echo -e "${BLUE}Scanning for TunaCode installations...${NC}"

    # Check venv installation
    if [ -d "$VENV_DIR" ]; then
        found_venv=true
        if [ -f "$VENV_DIR/bin/tunacode" ]; then
            if "$VENV_DIR/bin/tunacode" --version &>/dev/null; then
                venv_working=true
                echo -e "${GREEN}✓${NC} Found working venv installation at $VENV_DIR"
            else
                echo -e "${YELLOW}⚠${NC} Found venv installation but not working"
            fi
        else
            echo -e "${YELLOW}⚠${NC} Found venv directory but no tunacode binary"
        fi
    fi

    # Check global system installation
    if command -v tunacode &>/dev/null; then
        local tunacode_path=$(command -v tunacode)
        if [[ "$tunacode_path" =~ ^/usr/local/bin/ ]] || [[ "$tunacode_path" =~ ^/usr/bin/ ]]; then
            found_global_system=true
            if tunacode --version &>/dev/null; then
                global_system_working=true
                echo -e "${GREEN}✓${NC} Found working global system installation at $tunacode_path"
            else
                echo -e "${YELLOW}⚠${NC} Found global system installation but not working"
            fi
        fi
    fi

    # Check global user installation (direct pip --user installs)
    if [ -f "$HOME/.local/bin/tunacode" ] && [ "$HOME/.local/bin/tunacode" != "$BIN_DIR/tunacode" ]; then
        found_global_user=true
        if "$HOME/.local/bin/tunacode" --version &>/dev/null; then
            global_user_working=true
            echo -e "${GREEN}✓${NC} Found working global user installation"
        else
            echo -e "${YELLOW}⚠${NC} Found global user installation but not working"
        fi
    fi

    # Check pipx installation
    if command_exists pipx; then
        if pipx list 2>/dev/null | grep -q "tunacode"; then
            found_pipx=true
            if pipx run tunacode --version &>/dev/null; then
                pipx_working=true
                echo -e "${GREEN}✓${NC} Found working pipx installation"
            else
                echo -e "${YELLOW}⚠${NC} Found pipx installation but not working"
            fi
        fi
    fi

    # Check wrapper script
    if [ -f "$BIN_DIR/tunacode" ]; then
        echo -e "${BLUE}Found wrapper script at $BIN_DIR/tunacode${NC}"
        if [ -x "$BIN_DIR/tunacode" ]; then
            if "$BIN_DIR/tunacode" --version &>/dev/null; then
                echo -e "${GREEN}✓${NC} Wrapper script is working"
            else
                echo -e "${YELLOW}⚠${NC} Wrapper script exists but not working"
            fi
        else
            echo -e "${YELLOW}⚠${NC} Wrapper script not executable"
        fi
    fi

    # Export detection results
    export FOUND_VENV=$found_venv
    export FOUND_GLOBAL_SYSTEM=$found_global_system
    export FOUND_GLOBAL_USER=$found_global_user
    export FOUND_PIPX=$found_pipx
    export VENV_WORKING=$venv_working
    export GLOBAL_SYSTEM_WORKING=$global_system_working
    export GLOBAL_USER_WORKING=$global_user_working
    export PIPX_WORKING=$pipx_working
}

# Variables to track what was removed
removed_count=0
found_installation=false

print_status "Starting comprehensive TunaCode detection..."
detect_installations

# Count detected installations
installation_count=0
[ "$FOUND_VENV" = true ] && installation_count=$((installation_count + 1))
[ "$FOUND_GLOBAL_SYSTEM" = true ] && installation_count=$((installation_count + 1))
[ "$FOUND_GLOBAL_USER" = true ] && installation_count=$((installation_count + 1))
[ "$FOUND_PIPX" = true ] && installation_count=$((installation_count + 1))

if [ $installation_count -eq 0 ]; then
    print_warning "No TunaCode installations found!"
    echo ""
    print_status "Checking for leftover files anyway..."
else
    print_status "Found $installation_count TunaCode installation(s)"

    # If multiple installations, ask user what to remove
    if [ $installation_count -gt 1 ]; then
        echo ""
        print_warning "Multiple TunaCode installations detected:"
        [ "$FOUND_VENV" = true ] && echo -e "  - Venv installation ($VENV_DIR)"
        [ "$FOUND_GLOBAL_SYSTEM" = true ] && echo -e "  - Global system installation"
        [ "$FOUND_GLOBAL_USER" = true ] && echo -e "  - Global user installation"
        [ "$FOUND_PIPX" = true ] && echo -e "  - Pipx installation"
        echo ""
        print_warning "What would you like to remove?"
        echo -e "1) Remove all installations (recommended)"
        echo -e "2) Select specific installations"
        echo -e "3) Cancel uninstall"
        echo ""
        echo -n "Choice (1-3): "
        read -r choice

        case "$choice" in
            1)
                REMOVE_ALL=true
                print_status "Will remove all installations"
                ;;
            2)
                REMOVE_ALL=false
                print_status "Interactive removal mode"
                ;;
            3)
                print_status "Uninstall cancelled by user"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Cancelling uninstall."
                exit 1
                ;;
        esac
    else
        REMOVE_ALL=true
        print_status "Single installation detected, will remove it"
    fi

    echo ""
    print_status "Proceeding with TunaCode removal..."

    # Remove venv installation
    if [ "$FOUND_VENV" = true ]; then
        should_remove=true
        if [ "$REMOVE_ALL" = false ]; then
            echo -n "Remove venv installation at $VENV_DIR? (y/N): "
            read -r response
            [ "$response" != "y" ] && [ "$response" != "Y" ] && should_remove=false
        fi

        if [ "$should_remove" = true ]; then
            print_status "Removing venv installation..."
            if safe_remove "$VENV_DIR"; then
                found_installation=true
                ((removed_count++))
            fi
        fi
    fi

    # Remove pipx installation
    if [ "$FOUND_PIPX" = true ]; then
        should_remove=true
        if [ "$REMOVE_ALL" = false ]; then
            echo -n "Remove pipx installation? (y/N): "
            read -r response
            [ "$response" != "y" ] && [ "$response" != "Y" ] && should_remove=false
        fi

        if [ "$should_remove" = true ]; then
            print_status "Removing pipx installation..."
            if pipx uninstall tunacode; then
                found_installation=true
                ((removed_count++))
                print_success "Uninstalled TunaCode from pipx"
            else
                print_error "Failed to remove from pipx"
            fi
        fi
    fi

    # Remove global user installation
    if [ "$FOUND_GLOBAL_USER" = true ]; then
        should_remove=true
        if [ "$REMOVE_ALL" = false ]; then
            echo -n "Remove global user installation? (y/N): "
            read -r response
            [ "$response" != "y" ] && [ "$response" != "Y" ] && should_remove=false
        fi

        if [ "$should_remove" = true ]; then
            print_status "Removing global user installation..."
            # Try different methods for user installations
            local removed_via_pip=false

            # Try UV first if available
            if command_exists uv; then
                if uv pip uninstall tunacode-cli --user 2>/dev/null; then
                    removed_via_pip=true
                    print_success "Removed via UV"
                fi
            fi

            # Fallback to pip
            if [ "$removed_via_pip" = false ]; then
                if pip uninstall tunacode-cli -y --user 2>/dev/null; then
                    removed_via_pip=true
                    print_success "Removed via pip --user"
                elif pip list --user 2>/dev/null | grep -q "tunacode"; then
                    if pip uninstall tunacode -y --user 2>/dev/null; then
                        removed_via_pip=true
                        print_success "Removed via pip --user (package name: tunacode)"
                    fi
                fi
            fi

            if [ "$removed_via_pip" = true ]; then
                found_installation=true
                ((removed_count++))
            else
                print_warning "Could not remove via package manager"
            fi
        fi
    fi

    # Remove global system installation
    if [ "$FOUND_GLOBAL_SYSTEM" = true ]; then
        should_remove=true
        if [ "$REMOVE_ALL" = false ]; then
            echo -n "Remove global system installation? (y/N): "
            read -r response
            [ "$response" != "y" ] && [ "$response" != "Y" ] && should_remove=false
        fi

        if [ "$should_remove" = true ]; then
            print_status "Removing global system installation..."
            local removed_via_pip=false

            # Try UV first if available
            if command_exists uv; then
                if uv pip uninstall tunacode-cli --system 2>/dev/null; then
                    removed_via_pip=true
                    print_success "Removed via UV --system"
                fi
            fi

            # Fallback to pip
            if [ "$removed_via_pip" = false ]; then
                if pip uninstall tunacode-cli -y 2>/dev/null; then
                    removed_via_pip=true
                    print_success "Removed via pip"
                elif pip uninstall tunacode-cli -y --break-system-packages 2>/dev/null; then
                    removed_via_pip=true
                    print_success "Removed via pip (with --break-system-packages)"
                elif pip list 2>/dev/null | grep -q "tunacode"; then
                    if pip uninstall tunacode -y 2>/dev/null; then
                        removed_via_pip=true
                        print_success "Removed via pip (package name: tunacode)"
                    elif pip uninstall tunacode -y --break-system-packages 2>/dev/null; then
                        removed_via_pip=true
                        print_success "Removed via pip --break-system-packages (package name: tunacode)"
                    fi
                fi
            fi

            if [ "$removed_via_pip" = true ]; then
                found_installation=true
                ((removed_count++))
            else
                print_warning "Could not remove system installation via package manager"
            fi
        fi
    fi
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

# Enhanced final verification
print_status "Performing comprehensive verification..."

# Check if tunacode command still exists anywhere
remaining_binaries=""
if command_exists tunacode; then
    tunacode_path=$(command -v tunacode)
    remaining_binaries="$tunacode_path"
    print_warning "tunacode command still found in PATH: $tunacode_path"
fi

# Check specific binary locations
binary_check_locations=(
    "$HOME/.local/bin/tunacode"
    "/usr/local/bin/tunacode"
    "/usr/bin/tunacode"
    "$VENV_DIR/bin/tunacode"
)

for location in "${binary_check_locations[@]}"; do
    if [ -f "$location" ]; then
        remaining_binaries="$remaining_binaries $location"
        print_warning "Remaining binary found: $location"
    fi
done

# Check if venv directory still exists
if [ -d "$VENV_DIR" ]; then
    print_warning "Venv directory still exists: $VENV_DIR"
    print_warning "You may want to manually remove it: rm -rf $VENV_DIR"
fi

# Check for remaining Python packages
if command_exists pip; then
    if pip list 2>/dev/null | grep -q "tunacode"; then
        print_warning "TunaCode still found in system pip packages"
        pip list 2>/dev/null | grep "tunacode"
    fi
    if pip list --user 2>/dev/null | grep -q "tunacode"; then
        print_warning "TunaCode still found in user pip packages"
        pip list --user 2>/dev/null | grep "tunacode"
    fi
fi

# Check for remaining pipx installations
if command_exists pipx; then
    if pipx list 2>/dev/null | grep -q "tunacode"; then
        print_warning "TunaCode still found in pipx installations"
        pipx list 2>/dev/null | grep -A2 -B2 "tunacode"
    fi
fi

# Check for UV installations
if command_exists uv; then
    if uv pip list --system 2>/dev/null | grep -q "tunacode"; then
        print_warning "TunaCode still found in UV system packages"
    fi
    if uv pip list --user 2>/dev/null | grep -q "tunacode"; then
        print_warning "TunaCode still found in UV user packages"
    fi
fi

# Check for remaining config files with more specific search
remaining_configs=""
config_search_locations=(
    "$HOME/.config"
    "$HOME"
)

for location in "${config_search_locations[@]}"; do
    if [ -d "$location" ]; then
        found_configs=$(find "$location" -maxdepth 2 -name "*tunacode*" -type f 2>/dev/null)
        if [ -n "$found_configs" ]; then
            remaining_configs="$remaining_configs$found_configs\n"
        fi
    fi
done

if [ -n "$remaining_configs" ]; then
    print_warning "Some TunaCode-related config files may still exist:"
    echo -e "$remaining_configs" | head -5
fi

# Summary verification
if [ -z "$remaining_binaries" ] && [ ! -d "$VENV_DIR" ] && [ -z "$remaining_configs" ]; then
    print_success "✓ Complete verification passed - no TunaCode traces found"
else
    print_warning "⚠ Some TunaCode traces remain on the system"
    print_status "You may need to manually clean up remaining files"
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
