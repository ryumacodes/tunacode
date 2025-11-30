"""Tool description mappings for user-friendly spinner messages."""

from typing import Dict, Optional


def get_tool_description(tool_name: str, args: Optional[Dict] = None) -> str:
    """
    Get a human-readable description for a tool execution.

    Args:
        tool_name: Name of the tool being executed
        args: Optional tool arguments for more specific descriptions

    Returns:
        User-friendly description of the tool operation
    """
    # Base descriptions for each tool
    base_descriptions = {
        # File operations
        "read_file": "Reading file",
        "write_file": "Writing file",
        "update_file": "Updating file",
        "create_file": "Creating file",
        "delete_file": "Deleting file",
        # Directory operations
        "list_dir": "Listing directory",
        "create_dir": "Creating directory",
        "delete_dir": "Deleting directory",
        # Search operations
        "grep": "Searching files",
        "glob": "Finding files",
        "find_files": "Searching for files",
        # Code operations
        "run_command": "Executing command",
        "bash": "Running shell command",
        "python": "Executing Python code",
        # Analysis operations
        "analyze_code": "Analyzing code",
        "lint": "Running linter",
        "format_code": "Formatting code",
        # Version control
        "git_status": "Checking git status",
        "git_diff": "Getting git diff",
        "git_commit": "Creating git commit",
        # Testing
        "run_tests": "Running tests",
        "test": "Executing tests",
        # Documentation
        "generate_docs": "Generating documentation",
        "update_docs": "Updating documentation",
        # Default
        "unknown": "Processing",
    }

    # Get base description
    base_desc = base_descriptions.get(tool_name, f"Executing {tool_name}")

    # Add specific details from args if available
    if args:
        if tool_name == "read_file" and "file_path" in args:
            return f"{base_desc}: {args['file_path']}"
        elif tool_name == "write_file" and "file_path" in args:
            return f"{base_desc}: {args['file_path']}"
        elif tool_name == "update_file" and "file_path" in args:
            return f"{base_desc}: {args['file_path']}"
        elif tool_name == "list_dir" and "directory" in args:
            return f"{base_desc}: {args['directory']}"
        elif tool_name == "grep" and "pattern" in args:
            pattern = args["pattern"]
            # Truncate long patterns
            if len(pattern) > 30:
                pattern = pattern[:27] + "..."
            return f"{base_desc} for: {pattern}"
        elif tool_name == "glob" and "pattern" in args:
            return f"{base_desc}: {args['pattern']}"
        elif tool_name == "run_command" and "command" in args:
            cmd = args["command"]
            # Truncate long commands
            if len(cmd) > 40:
                cmd = cmd[:37] + "..."
            return f"{base_desc}: {cmd}"
        elif tool_name == "bash" and "command" in args:
            cmd = args["command"]
            if len(cmd) > 40:
                cmd = cmd[:37] + "..."
            return f"{base_desc}: {cmd}"

    return base_desc


def get_batch_description(tool_count: int, tool_names: Optional[list] = None) -> str:
    """
    Get a description for batch tool execution.

    Args:
        tool_count: Number of tools being executed
        tool_names: Optional list of tool names for more detail

    Returns:
        Description of the batch operation
    """
    if tool_count == 1:
        return "Executing 1 tool"

    if tool_names and len(set(tool_names)) == 1:
        # All tools are the same type
        tool_type = tool_names[0]
        if tool_type == "read_file":
            return f"Reading {tool_count} files in parallel"
        elif tool_type == "grep":
            return f"Searching {tool_count} patterns in parallel"
        elif tool_type == "list_dir":
            return f"Listing {tool_count} directories in parallel"

    return f"Executing {tool_count} tools in parallel"
