"""
Common test utilities for file operation tests.
Provides helper functions and fixtures for testing.
"""
import os
import tempfile
import contextlib
from pathlib import Path
from typing import Dict, List, Optional, Generator
import string
import random


def create_test_tree(root_path: Path, structure: Dict[str, str]) -> None:
    """
    Create a directory tree with files from a dictionary specification.
    
    Args:
        root_path: Root directory to create the tree in
        structure: Dict mapping file paths to their content
        
    Example:
        create_test_tree(Path("/tmp/test"), {
            "src/main.py": "print('hello')",
            "src/utils.py": "def helper(): pass",
            "README.md": "# Project"
        })
    """
    for file_path, content in structure.items():
        full_path = root_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)


def assert_file_contents(file_path: str, expected: str, normalize_newlines: bool = True) -> None:
    """
    Assert that a file contains the expected content.
    
    Args:
        file_path: Path to the file to check
        expected: Expected content
        normalize_newlines: Whether to normalize line endings before comparison
    """
    actual = Path(file_path).read_text()
    
    if normalize_newlines:
        actual = actual.replace('\r\n', '\n').replace('\r', '\n')
        expected = expected.replace('\r\n', '\n').replace('\r', '\n')
    
    assert actual == expected, f"File {file_path} content mismatch.\nExpected:\n{expected}\nActual:\n{actual}"


@contextlib.contextmanager
def with_temp_cwd() -> Generator[Path, None, None]:
    """
    Context manager that creates a temporary directory and changes to it.
    Restores the original directory on exit.
    
    Example:
        with with_temp_cwd() as temp_dir:
            # Working directory is now temp_dir
            Path("test.txt").write_text("content")
    """
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    try:
        os.chdir(temp_dir)
        yield Path(temp_dir)
    finally:
        os.chdir(original_cwd)
        import shutil
        shutil.rmtree(temp_dir)


class MockUserInput:
    """
    Mock user input for testing interactive commands.
    
    Example:
        mock = MockUserInput(['y', 'n', 'test input'])
        with mock:
            response1 = input()  # Returns 'y'
            response2 = input()  # Returns 'n'
            response3 = input()  # Returns 'test input'
    """
    def __init__(self, responses: List[str]):
        self.responses = responses
        self.index = 0
        self.original_input = None
    
    def __enter__(self):
        self.original_input = __builtins__['input']
        __builtins__['input'] = self._mock_input
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        __builtins__['input'] = self.original_input
    
    def _mock_input(self, prompt: str = "") -> str:
        if self.index >= len(self.responses):
            raise ValueError(f"No more mock responses available (prompt: {prompt})")
        response = self.responses[self.index]
        self.index += 1
        return response


def generate_large_content(size_mb: float) -> str:
    """
    Generate content of approximately the specified size in megabytes.
    
    Args:
        size_mb: Target size in megabytes
        
    Returns:
        String content of approximately the requested size
    """
    chars = string.ascii_letters + string.digits + ' \n'
    target_size = int(size_mb * 1024 * 1024)
    
    # Generate random content
    content = []
    current_size = 0
    
    while current_size < target_size:
        line_length = random.randint(50, 200)
        line = ''.join(random.choice(chars) for _ in range(line_length)) + '\n'
        content.append(line)
        current_size += len(line)
    
    return ''.join(content)[:target_size]


def generate_binary_data(size_bytes: int, pattern: Optional[str] = None) -> bytes:
    """
    Generate binary data for testing.
    
    Args:
        size_bytes: Size of data to generate
        pattern: Optional pattern ('random', 'zeros', 'ones', 'sequential')
        
    Returns:
        Binary data of the specified size
    """
    if pattern == 'zeros':
        return b'\x00' * size_bytes
    elif pattern == 'ones':
        return b'\xff' * size_bytes
    elif pattern == 'sequential':
        return bytes(i % 256 for i in range(size_bytes))
    else:  # random
        return bytes(random.randint(0, 255) for _ in range(size_bytes))


def create_unicode_test_files(root_path: Path) -> Dict[str, str]:
    """
    Create a set of files with various Unicode content for testing.
    
    Returns:
        Dict mapping file paths to their content
    """
    unicode_files = {
        "chinese.txt": "你好世界 - Hello World in Chinese",
        "japanese.txt": "こんにちは世界 - Hello World in Japanese",
        "korean.txt": "안녕하세요 세계 - Hello World in Korean",
        "arabic.txt": "مرحبا بالعالم - Hello World in Arabic",
        "russian.txt": "Привет мир - Hello World in Russian",
        "emoji.txt": "Hello 👋 World 🌍 Testing 🧪 Code 💻",
        "mixed.txt": "Mixed: 你好 • こんにちは • 안녕하세요 • مرحبا • Привет 🌏",
        "symbols.txt": "Symbols: ™ © ® € £ ¥ § ¶ † ‡ • ° ± × ÷",
    }
    
    for filename, content in unicode_files.items():
        (root_path / filename).write_text(content, encoding='utf-8')
    
    return unicode_files


def create_special_filename_files(root_path: Path) -> List[str]:
    """
    Create files with special characters in filenames for testing.
    Some may fail on certain filesystems.
    
    Returns:
        List of successfully created filenames
    """
    special_names = [
        "file with spaces.txt",
        "file-with-dashes.txt",
        "file.with.dots.txt",
        "file_with_underscores.txt",
        "UPPERCASE.TXT",
        "CamelCase.txt",
        ".hidden_file",
        "file(with)parens.txt",
        "file[with]brackets.txt",
        "file{with}braces.txt",
        "file@with#special$chars.txt",
        "file+plus-minus.txt",
        "file=equals.txt",
        "très_français.txt",
        "файл_по_русски.txt",
        "文件名.txt",
    ]
    
    if os.name != 'nt':  # Unix-like systems allow more characters
        special_names.extend([
            "file:with:colons.txt",
            "file|with|pipes.txt",
            "file<with>angles.txt",
            "file?with?questions.txt",
            "file*with*asterisks.txt",
            "file\"with\"quotes.txt",
        ])
    
    created = []
    for name in special_names:
        try:
            (root_path / name).write_text(f"Content for: {name}")
            created.append(name)
        except (OSError, ValueError):
            # Some names might not be supported
            pass
    
    return created


def compare_file_lists(actual: List[str], expected: List[str], ignore_order: bool = True) -> None:
    """
    Compare two lists of file paths, with helpful error messages.
    
    Args:
        actual: Actual list of files
        expected: Expected list of files
        ignore_order: Whether to ignore the order of files
    """
    if ignore_order:
        actual_set = set(actual)
        expected_set = set(expected)
        
        missing = expected_set - actual_set
        extra = actual_set - expected_set
        
        if missing or extra:
            msg = "File lists don't match.\n"
            if missing:
                msg += f"Missing files: {sorted(missing)}\n"
            if extra:
                msg += f"Extra files: {sorted(extra)}\n"
            raise AssertionError(msg)
    else:
        assert actual == expected, f"File lists don't match.\nActual: {actual}\nExpected: {expected}"


def normalize_path_separators(path: str) -> str:
    """
    Normalize path separators for cross-platform comparison.
    
    Args:
        path: Path string to normalize
        
    Returns:
        Path with forward slashes
    """
    return path.replace('\\', '/')


def create_git_repo(root_path: Path, initial_files: Optional[Dict[str, str]] = None) -> None:
    """
    Initialize a git repository with optional initial files.
    
    Args:
        root_path: Directory to initialize as git repo
        initial_files: Optional dict of files to create and commit
    """
    import subprocess
    
    # Initialize repo
    subprocess.run(['git', 'init'], cwd=root_path, check=True, capture_output=True)
    
    # Configure git (required for commits)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                   cwd=root_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                   cwd=root_path, check=True, capture_output=True)
    
    # Create and commit initial files
    if initial_files:
        for file_path, content in initial_files.items():
            full_path = root_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        subprocess.run(['git', 'add', '.'], cwd=root_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], 
                       cwd=root_path, check=True, capture_output=True)


def assert_file_permissions(file_path: str, expected_mode: int) -> None:
    """
    Assert that a file has the expected permissions.
    
    Args:
        file_path: Path to check
        expected_mode: Expected permission bits (e.g., 0o644)
    """
    if os.name == 'nt':
        # Windows doesn't have Unix-style permissions
        return
    
    actual_mode = Path(file_path).stat().st_mode & 0o777
    assert actual_mode == expected_mode, \
        f"File {file_path} has permissions {oct(actual_mode)}, expected {oct(expected_mode)}"