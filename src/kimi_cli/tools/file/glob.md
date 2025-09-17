Find files and directories using glob patterns. This tool supports standard glob syntax like *, ?, and ** for recursive searches.

**When to use:**
- Find files matching specific patterns (e.g., all Python files: `*.py`)
- Search for files recursively in subdirectories (e.g., `src/**/*.js`)
- Locate configuration files (e.g., `*.config.*`, `*.json`)
- Find test files (e.g., `test_*.py`, `*_test.go`)

**Pattern examples:**
- `*.py` - All Python files in current directory
- `src/**/*.js` - All JavaScript files in src directory recursively
- `test_*.py` - Python test files starting with "test_"
- `*.config.{js,ts}` - Config files with .js or .ts extension
- `.env*` - Environment files (including .env.local, etc.)

**Options:**
- `recursive: true` enables ** patterns to search subdirectories
- `include_dirs: false` to return only files, not directories
- `directory` to search in a specific directory (defaults to working directory)
