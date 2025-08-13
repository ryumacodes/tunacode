# Phase 5: Tool Prompt Injection System

**Status: COMPLETED**

## Overview

Phase 5 implemented a comprehensive XML-based prompt injection system for all 12 TunaCode tools, enabling dynamic prompt loading without code changes.

## Implementation Details

### Files Modified
- All 12 tool files in `src/tunacode/tools/`
- Created 11 new XML files in `src/tunacode/tools/prompts/`
- Updated base tool architecture with `_get_base_prompt()` methods

### XML Prompt Structure

Each tool now has a corresponding XML file with this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tool_prompt>
    <description>
        Tool description and usage instructions
    </description>

    <parameters>
        <parameter name="param_name" required="true|false">
            <description>Parameter description</description>
            <type>string|array|object</type>
            <!-- For arrays -->
            <items>
                <type>string|object</type>
                <properties>
                    <property name="prop_name">
                        <type>string</type>
                    </property>
                </properties>
            </items>
        </parameter>
    </parameters>

    <examples>
        <example>
            <title>Example title</title>
            <command>{"param": "value"}</command>
        </example>
    </examples>
</tool_prompt>
```

### Security Measures
- Uses `defusedxml.ElementTree` for secure XML parsing
- Graceful fallback to hardcoded prompts if XML parsing fails
- No arbitrary code execution risks

### Tools Updated

All 12 tools now implement the system:

1. **bash.py** - Bash command execution
2. **exit_plan_mode.py** - Plan mode controls
3. **glob.py** - File pattern matching
4. **grep.py** - Text search
5. **list_dir.py** - Directory listing
6. **present_plan.py** - Plan presentation
7. **read_file.py** - File reading
8. **run_command.py** - Command execution
9. **todo.py** - Task management
10. **update_file.py** - File modification
11. **write_file.py** - File creation

*Note: glob.py implementation was previously completed in Phase 3*

### Code Pattern

Each tool implements these methods:

```python
def _get_base_prompt(self) -> str:
    """Load and return the base prompt from XML file."""
    try:
        prompt_file = Path(__file__).parent / "prompts" / "tool_prompt.xml"
        if prompt_file.exists():
            tree = ET.parse(prompt_file)
            root = tree.getroot()
            description = root.find("description")
            if description is not None:
                return description.text.strip()
    except Exception as e:
        logger.warning(f"Failed to load XML prompt for {tool_name}: {e}")

    # Fallback to default prompt
    return "Default prompt text"

def _get_parameters_schema(self) -> Dict[str, Any]:
    """Get the parameters schema from XML or fallback."""
    # XML parsing logic with hardcoded fallback
```

### Benefits Achieved

1. **Dynamic Updates**: Prompts can be modified without code changes
2. **Consistency**: All tools follow the same XML structure
3. **Maintainability**: Centralized prompt management
4. **Security**: Safe XML parsing with defusedxml
5. **Reliability**: Graceful fallbacks ensure system stability

## Testing Status

- All tests passing with proper XML prompt injection
- Tests use regular tools instead of tools_v2 approach
- Proper fallback behavior verified

## Future Considerations

- **glob.py Refactor**: File slightly exceeds 600-line limit (618 lines), could be refactored later
- **Prompt Versioning**: Consider adding version metadata to XML files
- **Hot Reloading**: Could implement prompt reloading during runtime
