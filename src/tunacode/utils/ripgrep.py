import subprocess
from typing import List


def ripgrep(pattern: str, directory: str = ".") -> List[str]:
    """Return a list of file paths matching a pattern using ripgrep."""
    try:
        result = subprocess.run(
            ["rg", "--files", "-g", pattern, directory],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return []
