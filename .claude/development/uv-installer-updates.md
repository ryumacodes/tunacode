# UV Installer & Uninstaller Updates

_Updated: 2025-08-14_

## Key Changes

### Install Script (`scripts/install_linux.sh`)

**UV Integration:**
- Auto-detects UV availability with version reporting
- Falls back gracefully to pip when UV unavailable
- 10-100x faster installations with UV

**Robust Update Logic:**
- Detects venv, global system, and global user installations
- Health checks verify installations actually work
- Handles mixed installation scenarios
- Interactive selection for multiple installations
- Backup/rollback system for safe updates
- Retry logic with proper error handling

### Uninstall Script (`scripts/uninstall.sh`)

**Comprehensive Detection:**
- Matches install script detection logic
- Identifies venv, global, user, and pipx installations
- Health verification for each found installation

**Safe Removal:**
- Interactive mode for multiple installations
- Multiple uninstall methods (UV, pip, pipx)
- Handles `--break-system-packages` scenarios
- Complete verification after removal
- Config file and binary cleanup

## Installation Types Supported

1. **Venv**: `~/.tunacode-venv/` (recommended)
2. **Global System**: `/usr/local/bin/`, `/usr/bin/`
3. **Global User**: `pip install --user`
4. **Pipx**: `pipx install tunacode-cli`

## Usage

```bash
# Install/Update with UV detection
curl -sSL https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash

# Uninstall with detection
bash scripts/uninstall.sh
```

## Implementation Notes

- Both scripts share similar detection functions for consistency
- Update logic prevents mixing installation types
- Wrapper script automatically points to correct installation
- Handles externally-managed Python environments
- Error handling prevents partial/broken installations

## Testing

Successfully tested scenarios:
- Mixed venv + system pip installations
- UV available vs unavailable environments
- Multiple installation cleanup
- Failed installation rollback
