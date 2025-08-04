<!-- This guide covers the template system for creating reusable prompts with pre-approved tools and shortcuts -->

# TunaCode Template System Guide

Templates in TunaCode provide reusable prompts with pre-approved tools, enabling efficient workflows for common tasks. This guide explains how to create, manage, and use templates effectively.

## Template Overview

Templates are JSON files that define:
- A reusable prompt with optional parameter substitution
- Pre-approved tools that skip confirmation
- Shortcuts for quick access
- Custom parameters for specialized behavior

## Template Structure

### Basic Template Format

```json
{
    "name": "code_review",
    "description": "Perform comprehensive code review",
    "prompt": "Please review the following code files and provide feedback on:\n1. Code quality and readability\n2. Potential bugs or issues\n3. Performance considerations\n4. Security concerns\n5. Suggested improvements\n\nFiles to review: $ARGUMENTS",
    "allowed_tools": ["read_file", "grep", "list_dir"],
    "parameters": {
        "focus_areas": ["security", "performance", "maintainability"],
        "severity_levels": ["critical", "warning", "suggestion"]
    },
    "shortcuts": ["review", "cr"]
}
```

### Template Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique template identifier |
| `description` | string | Yes | Brief description of template purpose |
| `prompt` | string | Yes | The prompt text sent to the agent |
| `allowed_tools` | array | Yes | Tools that skip confirmation |
| `parameters` | object | No | Custom parameters for the template |
| `shortcuts` | array | No | Command shortcuts for quick access |

## Creating Templates

### Step 1: Design Your Template

Identify the common task and required tools:

```json
{
    "name": "add_tests",
    "description": "Add comprehensive tests for existing code",
    "prompt": "Please analyze the code in $ARGUMENTS and create comprehensive tests including:\n1. Unit tests for all public methods\n2. Edge case testing\n3. Error handling tests\n4. Integration tests if applicable\n\nUse pytest framework and follow existing test patterns.",
    "allowed_tools": ["read_file", "write_file", "grep", "list_dir"],
    "parameters": {
        "test_framework": "pytest",
        "coverage_target": 80
    },
    "shortcuts": ["test", "addtest"]
}
```

### Step 2: Save the Template

Templates are stored in `~/.config/tunacode/templates/`:

```bash
# Create template directory if needed
mkdir -p ~/.config/tunacode/templates

# Save your template
echo '{
    "name": "add_tests",
    "description": "Add comprehensive tests for existing code",
    "prompt": "...",
    "allowed_tools": ["read_file", "write_file", "grep", "list_dir"],
    "shortcuts": ["test", "addtest"]
}' > ~/.config/tunacode/templates/add_tests.json
```

### Step 3: Use the Template

Load and use templates via commands:

```bash
# List available templates
/template list

# Load a template
/template load add_tests

# Use shortcut (if defined)
/test src/mymodule.py

# Direct usage with arguments
/template load add_tests src/mymodule.py
```

## Template Examples

### 1. Refactoring Template

```json
{
    "name": "refactor_clean",
    "description": "Refactor code following clean code principles",
    "prompt": "Please refactor the code in $ARGUMENTS following clean code principles:\n\n1. **Single Responsibility**: Each function/class should do one thing\n2. **DRY**: Remove duplication\n3. **Meaningful Names**: Use clear, descriptive names\n4. **Small Functions**: Break down large functions\n5. **Error Handling**: Proper exception handling\n6. **Type Hints**: Add Python type hints\n\nPreserve all functionality and ensure tests pass.",
    "allowed_tools": ["read_file", "update_file", "grep"],
    "parameters": {
        "max_function_lines": 20,
        "max_class_lines": 200,
        "style_guide": "PEP8"
    },
    "shortcuts": ["refactor", "clean"]
}
```

### 2. Documentation Template

```json
{
    "name": "document_code",
    "description": "Add comprehensive documentation to code",
    "prompt": "Please add comprehensive documentation to $ARGUMENTS:\n\n1. **Module Docstrings**: Explain module purpose and usage\n2. **Class Docstrings**: Document class responsibility and usage\n3. **Method Docstrings**: Document parameters, returns, raises\n4. **Inline Comments**: Explain complex logic\n5. **Type Hints**: Ensure all functions have type hints\n6. **Examples**: Add usage examples in docstrings\n\nFollow Google Python Style Guide for docstrings.",
    "allowed_tools": ["read_file", "update_file"],
    "parameters": {
        "docstring_style": "google",
        "include_examples": true,
        "update_readme": false
    },
    "shortcuts": ["doc", "document"]
}
```

### 3. Security Audit Template

```json
{
    "name": "security_audit",
    "description": "Perform security audit on code",
    "prompt": "Please perform a security audit on $ARGUMENTS checking for:\n\n1. **Input Validation**: Ensure all inputs are validated\n2. **SQL Injection**: Check for SQL injection vulnerabilities\n3. **XSS**: Look for cross-site scripting issues\n4. **Authentication**: Review authentication mechanisms\n5. **Authorization**: Check authorization controls\n6. **Secrets**: Ensure no hardcoded secrets\n7. **Dependencies**: Check for vulnerable dependencies\n8. **Error Handling**: Ensure errors don't leak sensitive info\n\nProvide severity levels (Critical/High/Medium/Low) for findings.",
    "allowed_tools": ["read_file", "grep", "list_dir"],
    "parameters": {
        "check_dependencies": true,
        "owasp_top_10": true,
        "severity_threshold": "medium"
    },
    "shortcuts": ["security", "audit"]
}
```

### 4. Performance Analysis Template

```json
{
    "name": "performance_analysis",
    "description": "Analyze code for performance issues",
    "prompt": "Analyze the performance of $ARGUMENTS focusing on:\n\n1. **Algorithm Complexity**: Identify O(n²) or worse algorithms\n2. **Database Queries**: Look for N+1 queries or missing indexes\n3. **Memory Usage**: Find memory leaks or excessive allocation\n4. **I/O Operations**: Identify blocking I/O that could be async\n5. **Caching Opportunities**: Suggest where caching would help\n6. **Hot Paths**: Identify frequently executed code\n\nProvide specific optimization suggestions with expected impact.",
    "allowed_tools": ["read_file", "grep", "list_dir"],
    "parameters": {
        "profile_data": false,
        "benchmark": false,
        "target_improvement": "50%"
    },
    "shortcuts": ["perf", "performance"]
}
```

### 5. API Endpoint Template

```json
{
    "name": "create_api_endpoint",
    "description": "Create a new REST API endpoint",
    "prompt": "Create a new REST API endpoint based on these requirements:\n$ARGUMENTS\n\nInclude:\n1. Route definition with proper HTTP method\n2. Request validation (body, query params, headers)\n3. Business logic implementation\n4. Error handling with appropriate status codes\n5. Response serialization\n6. OpenAPI/Swagger documentation\n7. Unit and integration tests\n8. Rate limiting consideration\n\nFollow RESTful conventions and existing patterns in the codebase.",
    "allowed_tools": ["read_file", "write_file", "update_file", "grep", "list_dir"],
    "parameters": {
        "framework": "fastapi",
        "auth_required": true,
        "rate_limit": "100/hour",
        "response_format": "json"
    },
    "shortcuts": ["api", "endpoint"]
}
```

### 6. Database Migration Template

```json
{
    "name": "database_migration",
    "description": "Create database migration scripts",
    "prompt": "Create a database migration for: $ARGUMENTS\n\nEnsure:\n1. **Forward Migration**: CREATE/ALTER statements\n2. **Rollback Migration**: Reverse operations\n3. **Data Migration**: Handle existing data if needed\n4. **Indexes**: Add appropriate indexes\n5. **Constraints**: Add foreign keys and checks\n6. **Transaction Safety**: Use transactions appropriately\n7. **Zero-Downtime**: Consider online migration strategies\n\nUse the project's migration framework.",
    "allowed_tools": ["read_file", "write_file", "list_dir", "grep"],
    "parameters": {
        "migration_tool": "alembic",
        "database": "postgresql",
        "zero_downtime": true
    },
    "shortcuts": ["migrate", "dbmigrate"]
}
```

## Advanced Template Features

### 1. Parameter Substitution

Templates support `$ARGUMENTS` substitution:

```json
{
    "prompt": "Review the file $ARGUMENTS for code quality"
}
```

Usage:
```bash
/template load code_review src/main.py
# Prompt becomes: "Review the file src/main.py for code quality"
```

### 2. Multiple Placeholders

Use custom placeholders:

```json
{
    "name": "compare_files",
    "prompt": "Compare $FILE1 with $FILE2 and highlight differences",
    "parameters": {
        "placeholders": ["$FILE1", "$FILE2"]
    }
}
```

### 3. Conditional Tools

While not directly supported, you can create template variants:

```json
{
    "name": "review_readonly",
    "description": "Code review (read-only)",
    "allowed_tools": ["read_file", "grep", "list_dir"]
}
```

```json
{
    "name": "review_withfix",
    "description": "Code review with fixes",
    "allowed_tools": ["read_file", "grep", "list_dir", "update_file"]
}
```

### 4. Template Composition

Create templates that reference others:

```json
{
    "name": "full_feature",
    "description": "Implement complete feature",
    "prompt": "Implement the feature described in $ARGUMENTS. First analyze the codebase, then:\n1. Create the implementation\n2. Add comprehensive tests\n3. Update documentation\n4. Add API endpoints if needed\n\nUse the code_review template after implementation.",
    "allowed_tools": ["read_file", "write_file", "update_file", "grep", "list_dir"],
    "parameters": {
        "subtemplates": ["add_tests", "document_code", "code_review"]
    }
}
```

## Template Best Practices

### 1. Clear, Specific Prompts

```json
{
    "prompt": "Please analyze the Python file $ARGUMENTS and:\n1. Identify functions longer than 20 lines\n2. Find duplicate code blocks\n3. Detect missing type hints\n4. Check for proper error handling\n\nProvide specific line numbers for each issue."
}
```

### 2. Minimal Tool Permissions

Only include tools actually needed:

```json
{
    "name": "analyze_only",
    "allowed_tools": ["read_file", "grep"],  // No write tools
    "description": "Analysis template - read only"
}
```

### 3. Descriptive Names and Shortcuts

```json
{
    "name": "add_pytest_fixtures",
    "shortcuts": ["fixture", "pf"],
    "description": "Add pytest fixtures for test files"
}
```

### 4. Reusable Parameters

```json
{
    "parameters": {
        "code_style": "PEP8",
        "max_line_length": 88,
        "quote_style": "double",
        "import_style": "absolute"
    }
}
```

## Managing Templates

### List Templates

```bash
/template list

# Output:
Available templates:
  - code_review: Perform comprehensive code review
    Shortcuts: review, cr
  - add_tests: Add comprehensive tests for existing code
    Shortcuts: test, addtest
  - security_audit: Perform security audit on code
    Shortcuts: security, audit
```

### Load Template

```bash
/template load security_audit

# Output:
Loaded template: security_audit
Pre-approved tools: read_file, grep, list_dir
```

### Clear Template

```bash
/template clear

# Output:
Template cleared. Tool confirmations reset.
```

### Template Shortcuts

Use shortcuts for quick access:

```bash
# Instead of: /template load code_review src/main.py
/review src/main.py

# Instead of: /template load add_tests src/module.py
/test src/module.py
```

## Template Organization

Organize templates in subdirectories:

```
~/.config/tunacode/templates/
├── development/
│   ├── add_tests.json
│   ├── refactor_clean.json
│   └── document_code.json
├── security/
│   ├── security_audit.json
│   └── dependency_check.json
├── operations/
│   ├── performance_analysis.json
│   └── debug_issue.json
└── project-specific/
    ├── create_api_endpoint.json
    └── database_migration.json
```

## Creating Custom Workflows

### 1. Chain Templates

Create a workflow template:

```json
{
    "name": "complete_feature_workflow",
    "description": "Complete feature development workflow",
    "prompt": "For the feature described in $ARGUMENTS, please:\n\n1. First, analyze existing code structure\n2. Implement the feature following patterns\n3. Add comprehensive tests (use add_tests template approach)\n4. Update documentation (use document_code template approach)\n5. Perform security review (use security_audit template approach)\n6. Create PR description\n\nProceed step by step, confirming completion of each phase.",
    "allowed_tools": ["read_file", "write_file", "update_file", "grep", "list_dir", "bash"],
    "parameters": {
        "workflow_steps": [
            "analyze",
            "implement",
            "test",
            "document",
            "review",
            "prepare_pr"
        ]
    }
}
```

### 2. Project-Specific Templates

Create templates for your project:

```json
{
    "name": "add_tunacode_tool",
    "description": "Add a new tool to TunaCode",
    "prompt": "Create a new TunaCode tool named $ARGUMENTS with:\n\n1. Tool implementation in src/tunacode/tools/\n2. Inherit from BaseTool or FileBasedTool\n3. Implement run() and format_confirmation()\n4. Add to INTERNAL_TOOLS in settings.py\n5. Categorize in READ_ONLY_TOOLS, WRITE_TOOLS, or EXECUTE_TOOLS\n6. Create tests in tests/tools/\n7. Update tool imports in main.py\n\nFollow existing tool patterns.",
    "allowed_tools": ["read_file", "write_file", "grep", "list_dir"],
    "parameters": {
        "tool_category": "READ_ONLY_TOOLS",
        "base_class": "BaseTool"
    },
    "shortcuts": ["newtool"]
}
```

### 3. Interactive Templates

Templates can guide interactive development:

```json
{
    "name": "debug_issue",
    "description": "Interactive debugging session",
    "prompt": "Help me debug the issue: $ARGUMENTS\n\nPlease:\n1. First, understand the issue by asking clarifying questions\n2. Examine relevant code and logs\n3. Form hypotheses about the cause\n4. Suggest diagnostic steps\n5. Implement fixes once we identify the issue\n\nLet's work through this interactively.",
    "allowed_tools": ["read_file", "grep", "list_dir", "bash"],
    "parameters": {
        "interactive": true,
        "diagnostic_tools": ["logs", "debugger", "tests"]
    },
    "shortcuts": ["debug"]
}
```

## Template Development Tips

### 1. Start Simple

Begin with basic templates and expand:

```json
{
    "name": "simple_review",
    "description": "Basic code review",
    "prompt": "Review $ARGUMENTS for obvious issues",
    "allowed_tools": ["read_file"],
    "shortcuts": ["qr"]
}
```

### 2. Test Templates

Test your templates thoroughly:

```bash
# Test with different arguments
/template load mytemplate test1.py
/template load mytemplate "test1.py test2.py"
/template load mytemplate src/

# Test shortcuts
/myshortcut test.py
```

### 3. Document Templates

Add usage examples in the description:

```json
{
    "description": "Add tests for code. Usage: /test <file_or_directory>"
}
```

### 4. Version Templates

Keep template versions:

```bash
# Backup before modifying
cp add_tests.json add_tests.json.v1

# Or use git
cd ~/.config/tunacode/templates
git init
git add .
git commit -m "Initial templates"
```

## Troubleshooting

### Template Not Loading

1. Check file exists: `ls ~/.config/tunacode/templates/`
2. Validate JSON: `python -m json.tool < template.json`
3. Check template name matches filename

### Shortcuts Not Working

1. Ensure shortcuts are defined in template
2. Check for conflicts with existing commands
3. Restart TunaCode after adding shortcuts

### Tools Not Pre-Approved

1. Verify tool names match exactly
2. Check tools are in allowed_tools array
3. Ensure you're not in a different template

## Future Enhancements

Planned template system improvements:

1. **Template Inheritance**: Base templates with overrides
2. **Dynamic Parameters**: Runtime parameter substitution
3. **Template Marketplace**: Share templates with community
4. **Conditional Logic**: If/then tool permissions
5. **Template Chains**: Automatic workflow execution
6. **GUI Editor**: Visual template creation

## Summary

Templates are powerful tools for automating common workflows in TunaCode. By creating well-designed templates, you can:

- Speed up repetitive tasks
- Ensure consistency across operations
- Share best practices with team members
- Build complex workflows from simple components

Start with the provided examples and create your own templates tailored to your specific needs!
