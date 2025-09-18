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

**Anti-examples**
- `**`, `**/*.py` - Any pattern starting with '**' is PROHIBITED. It would recursively search all directories and subdirectories, which is highly possible to yield large result that exceeds your context size.
- `node_modules/**/*.js` - Although this does not start with '**', it would still highly possible to yield large result because `node_modules` is well-known to contain too many directories and files. Avoid recursivelly searching in such directories, other examples include `venv`, `.venv`, `__pycache__`, `target`. If you really need to search in a dependency, use something like `node_modules/react/src/*` instead.

**Options:**
- `recursive: true` enables ** patterns to search subdirectories
- `include_dirs: false` to return only files, not directories
- `directory` to search in a specific directory (defaults to working directory)
