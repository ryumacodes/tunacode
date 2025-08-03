"""Module: tunacode.core.agents.main

Main agent functionality and coordination for the TunaCode CLI.
Handles agent creation, configuration, and request processing.
"""

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from pydantic_ai import Agent

from tunacode.core.logging.logger import get_logger

# Import streaming types with fallback for older versions
try:
    from pydantic_ai.messages import PartDeltaEvent, TextPartDelta

    STREAMING_AVAILABLE = True
except ImportError:
    # Fallback for older pydantic-ai versions
    PartDeltaEvent = None
    TextPartDelta = None
    STREAMING_AVAILABLE = False

from tunacode.constants import READ_ONLY_TOOLS
from tunacode.core.state import StateManager
from tunacode.core.token_usage.api_response_parser import ApiResponseParser
from tunacode.core.token_usage.cost_calculator import CostCalculator
from tunacode.exceptions import ToolBatchingJSONError, UserAbortError
from tunacode.services.mcp import get_mcp_servers
from tunacode.tools.bash import bash
from tunacode.tools.glob import glob
from tunacode.tools.grep import grep
from tunacode.tools.list_dir import list_dir
from tunacode.tools.read_file import read_file
from tunacode.tools.run_command import run_command
from tunacode.tools.todo import TodoTool
from tunacode.tools.update_file import update_file
from tunacode.tools.write_file import write_file
from tunacode.types import (
    AgentRun,
    ErrorMessage,
    FallbackResponse,
    ModelName,
    PydanticAgent,
    ResponseState,
    SimpleResult,
    ToolCallback,
    ToolCallId,
    ToolName,
    UsageTrackerProtocol,
)

# Configure logging
logger = get_logger(__name__)


def check_task_completion(content: str) -> Tuple[bool, str]:
    """
    Check if the content indicates task completion.

    Args:
        content: The text content to check

    Returns:
        Tuple of (is_complete, cleaned_content)
        - is_complete: True if task completion marker found
        - cleaned_content: Content with marker removed
    """
    if not content:
        return False, content

    lines = content.strip().split("\n")
    if lines and lines[0].strip() == "TUNACODE_TASK_COMPLETE":
        # Task is complete, return cleaned content
        cleaned_lines = lines[1:] if len(lines) > 1 else []
        cleaned_content = "\n".join(cleaned_lines).strip()
        return True, cleaned_content

    return False, content


class ToolBuffer:
    """Buffer for collecting read-only tool calls to execute in parallel."""

    def __init__(self):
        self.read_only_tasks: List[Tuple[Any, Any]] = []

    def add(self, part: Any, node: Any) -> None:
        """Add a read-only tool call to the buffer."""
        self.read_only_tasks.append((part, node))

    def flush(self) -> List[Tuple[Any, Any]]:
        """Return buffered tasks and clear the buffer."""
        tasks = self.read_only_tasks
        self.read_only_tasks = []
        return tasks

    def has_tasks(self) -> bool:
        """Check if there are buffered tasks."""
        return len(self.read_only_tasks) > 0


# Lazy import for Agent and Tool
def get_agent_tool():
    import importlib

    pydantic_ai = importlib.import_module("pydantic_ai")
    return pydantic_ai.Agent, pydantic_ai.Tool


def get_model_messages():
    """
    Safely retrieve message-related classes from pydantic_ai.

    The test-suite provides a stub `pydantic_ai.messages` module which, at the
    moment, is missing `SystemPromptPart`. Rather than letting an
    `AttributeError` propagate we create a very small stand-in so that the rest
    of the runtime code keeps working.
    """
    import importlib

    messages = importlib.import_module("pydantic_ai.messages")

    # Provide minimal fallbacks for missing classes when running under the stubbed test module
    # SystemPromptPart
    if not hasattr(messages, "SystemPromptPart"):

        class SystemPromptPart:  # type: ignore
            def __init__(self, content: str = "", role: str = "system", part_kind: str = ""):
                self.content = content
                self.role = role
                self.part_kind = part_kind

            def __repr__(self) -> str:  # pragma: no cover
                return f"SystemPromptPart(content={self.content!r})"

        SystemPromptPart.__module__ = messages.__name__
        setattr(messages, "SystemPromptPart", SystemPromptPart)

    # UserPromptPart
    if not hasattr(messages, "UserPromptPart"):

        class UserPromptPart:  # type: ignore
            def __init__(self, content: str = "", role: str = "user", part_kind: str = ""):
                self.content = content
                self.role = role
                self.part_kind = part_kind

            def __repr__(self) -> str:  # pragma: no cover
                return f"UserPromptPart(content={self.content!r})"

        UserPromptPart.__module__ = messages.__name__
        setattr(messages, "UserPromptPart", UserPromptPart)

    return messages.ModelRequest, messages.ToolReturnPart, messages.SystemPromptPart


async def execute_tools_parallel(
    tool_calls: List[Tuple[Any, Any]], callback: ToolCallback, return_exceptions: bool = True
) -> List[Any]:
    """
    Execute multiple tool calls in parallel using asyncio.

    Args:
        tool_calls: List of (part, node) tuples
        callback: The tool callback function to execute
        return_exceptions: Whether to return exceptions or raise them

    Returns:
        List of results in the same order as input, with exceptions for failed calls
    """
    # Get max parallel from environment or default to CPU count
    max_parallel = int(os.environ.get("TUNACODE_MAX_PARALLEL", os.cpu_count() or 4))

    async def execute_with_error_handling(part, node):
        try:
            return await callback(part, node)
        except Exception as e:
            logger.error(f"Error executing parallel tool: {e}", exc_info=True)
            return e

    # If we have more tools than max_parallel, execute in batches
    if len(tool_calls) > max_parallel:
        results = []
        for i in range(0, len(tool_calls), max_parallel):
            batch = tool_calls[i : i + max_parallel]
            batch_tasks = [execute_with_error_handling(part, node) for part, node in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=return_exceptions)
            results.extend(batch_results)
        return results
    else:
        tasks = [execute_with_error_handling(part, node) for part, node in tool_calls]
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)


async def _process_node(
    node,
    tool_callback: Optional[ToolCallback],
    state_manager: StateManager,
    tool_buffer: Optional[ToolBuffer] = None,
    streaming_callback: Optional[Callable[[str], None]] = None,
    usage_tracker: Optional[UsageTrackerProtocol] = None,
    response_state: Optional[ResponseState] = None,
):
    """Process a single node from the agent response.

    Returns:
        tuple: (is_empty: bool, reason: Optional[str]) - True if empty/problematic response detected,
               with reason being one of: "empty", "truncated", "intention_without_action"
    """
    from tunacode.ui import console as ui
    from tunacode.utils.token_counter import estimate_tokens

    # Use the original callback directly - parallel execution will be handled differently
    buffering_callback = tool_callback
    empty_response_detected = False
    has_non_empty_content = False
    appears_truncated = False
    has_intention = False
    has_tool_calls = False

    if hasattr(node, "request"):
        state_manager.session.messages.append(node.request)

    if hasattr(node, "thought") and node.thought:
        state_manager.session.messages.append({"thought": node.thought})
        # Display thought immediately if show_thoughts is enabled
        if state_manager.session.show_thoughts:
            await ui.muted(f"THOUGHT: {node.thought}")

    if hasattr(node, "model_response"):
        state_manager.session.messages.append(node.model_response)

        if usage_tracker:
            await usage_tracker.track_and_display(node.model_response)

        # Check for task completion marker in response content
        if response_state:
            has_non_empty_content = False
            appears_truncated = False
            all_content_parts = []
            
            # First, check if there are any tool calls in this response
            has_queued_tools = any(
                hasattr(part, "part_kind") and part.part_kind == "tool-call"
                for part in node.model_response.parts
            )
            
            for part in node.model_response.parts:
                if hasattr(part, "content") and isinstance(part.content, str):
                    # Check if we have any non-empty content
                    if part.content.strip():
                        has_non_empty_content = True
                        all_content_parts.append(part.content)

                    is_complete, cleaned_content = check_task_completion(part.content)
                    if is_complete:
                        # Validate completion - check for premature completion
                        if has_queued_tools:
                            # Agent is trying to complete with pending tools!
                            if state_manager.session.show_thoughts:
                                await ui.warning("⚠️ PREMATURE COMPLETION DETECTED - Agent queued tools but marked complete")
                                await ui.muted("   Overriding completion to allow tool execution")
                            # Don't mark as complete - let the tools run first
                            # Update the content to remove the marker but don't set task_completed
                            part.content = cleaned_content
                            # Log this as an issue
                            logger.warning(
                                f"Agent attempted premature completion with {sum(1 for p in node.model_response.parts if getattr(p, 'part_kind', '') == 'tool-call')} pending tools"
                            )
                        else:
                            # Check if content suggests pending actions
                            combined_text = " ".join(all_content_parts).lower()
                            pending_phrases = [
                                "let me", "i'll check", "i will", "going to", "about to", 
                                "need to check", "let's check", "i should", "need to find",
                                "let me see", "i'll look", "let me search", "let me find"
                            ]
                            has_pending_intention = any(phrase in combined_text for phrase in pending_phrases)
                            
                            # Also check for action verbs at end of content suggesting incomplete action
                            action_endings = ["checking", "searching", "looking", "finding", "reading", "analyzing"]
                            ends_with_action = any(combined_text.rstrip().endswith(ending) for ending in action_endings)
                            
                            if (has_pending_intention or ends_with_action) and state_manager.session.iteration_count <= 1:
                                # Too early to complete with pending intentions
                                if state_manager.session.show_thoughts:
                                    await ui.warning("⚠️ SUSPICIOUS COMPLETION - Stated intentions but completing early")
                                    found_phrases = [p for p in pending_phrases if p in combined_text]
                                    await ui.muted(f"   Iteration {state_manager.session.iteration_count} with pending: {found_phrases}")
                                    if ends_with_action:
                                        await ui.muted(f"   Content ends with action verb: '{combined_text.split()[-1] if combined_text.split() else ''}'")
                                # Still allow it but log warning
                                logger.warning(f"Task completion with pending intentions detected: {found_phrases}")
                            
                            # Normal completion
                            response_state.task_completed = True
                            response_state.has_user_response = True
                            # Update the part content to remove the marker
                            part.content = cleaned_content
                            if state_manager.session.show_thoughts:
                                await ui.muted("✅ TASK COMPLETION DETECTED")
                        break

            # Check for truncation patterns
            if all_content_parts:
                combined_content = " ".join(all_content_parts).strip()
                
                # Truncation indicators:
                # 1. Ends with "..." or "…" (but not part of a complete sentence)
                # 2. Ends mid-word (no punctuation, space, or complete word)
                # 3. Contains incomplete markdown/code blocks
                # 4. Ends with incomplete parentheses/brackets
                
                # Check for ellipsis at end suggesting truncation
                if combined_content.endswith(("...", "…")) and not combined_content.endswith(("....", "….")):
                    appears_truncated = True
                    
                # Check for mid-word truncation (ends with letters but no punctuation)
                elif combined_content and combined_content[-1].isalpha():
                    # Look for incomplete words by checking if last "word" seems cut off
                    words = combined_content.split()
                    if words:
                        last_word = words[-1]
                        # Common complete word endings vs likely truncations
                        complete_endings = ("ing", "ed", "ly", "er", "est", "tion", "ment", "ness", "ity", "ous", "ive", "able", "ible")
                        incomplete_patterns = ("referen", "inte", "proces", "analy", "deve", "imple", "execu")
                        
                        if any(last_word.lower().endswith(pattern) for pattern in incomplete_patterns):
                            appears_truncated = True
                        elif len(last_word) > 2 and not any(last_word.lower().endswith(end) for end in complete_endings):
                            # Likely truncated if doesn't end with common suffix
                            appears_truncated = True
                
                # Check for unclosed markdown code blocks
                code_block_count = combined_content.count("```")
                if code_block_count % 2 != 0:
                    appears_truncated = True
                    
                # Check for unclosed brackets/parentheses (more opens than closes)
                open_brackets = combined_content.count("[") + combined_content.count("(") + combined_content.count("{")
                close_brackets = combined_content.count("]") + combined_content.count(")") + combined_content.count("}")
                if open_brackets > close_brackets:
                    appears_truncated = True

            # If we only got empty content and no tool calls, we should NOT consider this a valid response
            # This prevents the agent from stopping when it gets empty responses
            if not has_non_empty_content and not any(
                hasattr(part, "part_kind") and part.part_kind == "tool-call"
                for part in node.model_response.parts
            ):
                # Empty response with no tools - keep going
                empty_response_detected = True
                if state_manager.session.show_thoughts:
                    await ui.muted("⚠️ EMPTY RESPONSE - CONTINUING")
            
            # Check if response appears truncated
            elif appears_truncated and not any(
                hasattr(part, "part_kind") and part.part_kind == "tool-call"
                for part in node.model_response.parts
            ):
                # Truncated response detected
                empty_response_detected = True
                if state_manager.session.show_thoughts:
                    await ui.muted("⚠️ TRUNCATED RESPONSE DETECTED - CONTINUING")
                    await ui.muted(f"   Last content: ...{combined_content[-100:]}")

        # Stream content to callback if provided
        # Use this as fallback when true token streaming is not available
        if streaming_callback and not STREAMING_AVAILABLE:
            for part in node.model_response.parts:
                if hasattr(part, "content") and isinstance(part.content, str):
                    content = part.content.strip()
                    if content and not content.startswith('{"thought"'):
                        # Stream non-JSON content (actual response content)
                        await streaming_callback(content)

        # Enhanced display when thoughts are enabled
        if state_manager.session.show_thoughts:
            # Show raw API response data
            import json
            import re

            # Display the raw model response parts
            await ui.muted("\n" + "=" * 60)
            await ui.muted(" RAW API RESPONSE DATA:")
            await ui.muted("=" * 60)

            for idx, part in enumerate(node.model_response.parts):
                part_data = {"part_index": idx, "part_kind": getattr(part, "part_kind", "unknown")}

                # Add part-specific data
                if hasattr(part, "content"):
                    part_data["content"] = (
                        part.content[:200] + "..." if len(str(part.content)) > 200 else part.content
                    )
                if hasattr(part, "tool_name"):
                    part_data["tool_name"] = part.tool_name
                if hasattr(part, "args"):
                    part_data["args"] = part.args
                if hasattr(part, "tool_call_id"):
                    part_data["tool_call_id"] = part.tool_call_id

                await ui.muted(json.dumps(part_data, indent=2))

            await ui.muted("=" * 60)

            # Count how many tool calls are in this response
            tool_count = sum(
                1
                for part in node.model_response.parts
                if hasattr(part, "part_kind") and part.part_kind == "tool-call"
            )
            if tool_count > 0:
                await ui.muted(f"\n MODEL RESPONSE: Contains {tool_count} tool call(s)")

            # Display LLM response content
            for part in node.model_response.parts:
                if hasattr(part, "content") and isinstance(part.content, str):
                    content = part.content.strip()

                    # Skip empty content
                    if not content:
                        continue

                    # Estimate tokens in this response
                    token_count = estimate_tokens(content)

                    # Display non-JSON content as LLM response
                    if not content.startswith('{"thought"'):
                        # Truncate very long responses for display
                        display_content = content[:500] + "..." if len(content) > 500 else content
                        await ui.muted(f"\nRESPONSE: {display_content}")
                        await ui.muted(f"TOKENS: ~{token_count}")

                    # Pattern 1: Inline JSON thoughts {"thought": "..."}
                    thought_pattern = r'\{"thought":\s*"([^"]+)"\}'
                    matches = re.findall(thought_pattern, content)
                    for thought in matches:
                        await ui.muted(f"REASONING: {thought}")

                    # Pattern 2: Standalone thought JSON objects
                    try:
                        if content.startswith('{"thought"'):
                            thought_obj = json.loads(content)
                            if "thought" in thought_obj:
                                await ui.muted(f"REASONING: {thought_obj['thought']}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Failed to parse thought JSON: {e}")

                    # Pattern 3: Multi-line thoughts with context
                    multiline_pattern = r'\{"thought":\s*"([^"]+(?:\\.[^"]*)*?)"\}'
                    multiline_matches = re.findall(multiline_pattern, content, re.DOTALL)
                    for thought in multiline_matches:
                        if thought not in [m for m in matches]:  # Avoid duplicates
                            # Clean up escaped characters
                            cleaned_thought = thought.replace('\\"', '"').replace("\\n", " ")
                            await ui.muted(f"REASONING: {cleaned_thought}")

        # Check for tool calls and collect them for potential parallel execution
        has_tool_calls = False
        tool_parts = []  # Collect all tool calls from this node

        for part in node.model_response.parts:
            if part.part_kind == "tool-call" and tool_callback:
                has_tool_calls = True
                tool_parts.append(part)

                # Display tool call details when thoughts are enabled
                if state_manager.session.show_thoughts:
                    # Show each tool as it's collected
                    tool_desc = f" COLLECTED: {part.tool_name}"
                    if hasattr(part, "args") and isinstance(part.args, dict):
                        if part.tool_name == "read_file" and "file_path" in part.args:
                            tool_desc += f" → {part.args['file_path']}"
                        elif part.tool_name == "grep" and "pattern" in part.args:
                            tool_desc += f" → pattern: '{part.args['pattern']}'"
                        elif part.tool_name == "list_dir" and "directory" in part.args:
                            tool_desc += f" → {part.args['directory']}"
                        elif part.tool_name == "run_command" and "command" in part.args:
                            tool_desc += f" → {part.args['command']}"
                    await ui.muted(tool_desc)

                # Track this tool call (moved outside thoughts block)
                state_manager.session.tool_calls.append(
                    {
                        "tool": part.tool_name,
                        "args": part.args if hasattr(part, "args") else {},
                        "iteration": state_manager.session.current_iteration,
                    }
                )

                # Track files if this is read_file (moved outside thoughts block)
                if (
                    part.tool_name == "read_file"
                    and hasattr(part, "args")
                    and isinstance(part.args, dict)
                    and "file_path" in part.args
                ):
                    state_manager.session.files_in_context.add(part.args["file_path"])
                    # Show files in context when thoughts are enabled
                    if state_manager.session.show_thoughts:
                        await ui.muted(
                            f"\nFILES IN CONTEXT: {list(state_manager.session.files_in_context)}"
                        )

        # Execute tool calls - with ACTUAL parallel execution for read-only batches
        if tool_parts:
            if state_manager.session.show_thoughts:
                await ui.muted(
                    f"\n NODE SUMMARY: {len(tool_parts)} tool(s) collected in this response"
                )

            # Check if ALL tools in this node are read-only
            all_read_only = all(part.tool_name in READ_ONLY_TOOLS for part in tool_parts)

            # TODO: Currently only batches if ALL tools are read-only. Should be updated to use
            # batch_read_only_tools() function from utils to group consecutive read-only tools and execute
            # them in parallel even when mixed with write/execute tools. For example:
            # [read, read, write, read] should execute as: [read||read], [write], [read]
            # instead of all sequential.
            if all_read_only and len(tool_parts) > 1 and buffering_callback:
                # Execute read-only tools in parallel!
                import time

                start_time = time.time()

                if state_manager.session.show_thoughts:
                    await ui.muted("\n" + "=" * 60)
                    await ui.muted(
                        f" PARALLEL BATCH: Executing {len(tool_parts)} read-only tools concurrently"
                    )
                    await ui.muted("=" * 60)

                    for idx, part in enumerate(tool_parts, 1):
                        tool_desc = f"  [{idx}] {part.tool_name}"
                        if hasattr(part, "args") and isinstance(part.args, dict):
                            if part.tool_name == "read_file" and "file_path" in part.args:
                                tool_desc += f" → {part.args['file_path']}"
                            elif part.tool_name == "grep" and "pattern" in part.args:
                                tool_desc += f" → pattern: '{part.args['pattern']}'"
                            elif part.tool_name == "list_dir" and "directory" in part.args:
                                tool_desc += f" → {part.args['directory']}"
                            elif part.tool_name == "glob" and "pattern" in part.args:
                                tool_desc += f" → pattern: '{part.args['pattern']}'"
                        await ui.muted(tool_desc)
                    await ui.muted("=" * 60)

                # Execute in parallel
                tool_tuples = [(part, node) for part in tool_parts]
                await execute_tools_parallel(tool_tuples, buffering_callback)

                if state_manager.session.show_thoughts:
                    elapsed_time = (time.time() - start_time) * 1000
                    sequential_estimate = len(tool_parts) * 100
                    speedup = sequential_estimate / elapsed_time if elapsed_time > 0 else 1.0
                    await ui.muted(
                        f" Parallel batch completed in {elapsed_time:.0f}ms ({speedup:.1f}x faster than sequential)"
                    )

            else:
                # Sequential execution for mixed or write/execute tools
                for part in tool_parts:
                    if (
                        state_manager.session.show_thoughts
                        and part.tool_name not in READ_ONLY_TOOLS
                    ):
                        await ui.muted(f"\n SEQUENTIAL: {part.tool_name} (write/execute tool)")

                    # Execute the tool
                    if buffering_callback:
                        await buffering_callback(part, node)

        # Handle tool returns
        for part in node.model_response.parts:
            if part.part_kind == "tool-return":
                state_manager.session.messages.append(
                    f"OBSERVATION[{part.tool_name}]: {part.content}"
                )

                # Display tool return when thoughts are enabled
                if state_manager.session.show_thoughts:
                    # Truncate for display
                    display_content = (
                        part.content[:200] + "..." if len(part.content) > 200 else part.content
                    )
                    await ui.muted(f"TOOL RESULT: {display_content}")

        # If no structured tool calls found, try parsing JSON from text content
        if not has_tool_calls and buffering_callback:
            for part in node.model_response.parts:
                if hasattr(part, "content") and isinstance(part.content, str):
                    try:
                        await extract_and_execute_tool_calls(
                            part.content, buffering_callback, state_manager
                        )
                    except ToolBatchingJSONError as e:
                        # Handle JSON parsing failure after retries
                        logger.error(f"Tool batching JSON error: {e}")
                        if state_manager.session.show_thoughts:
                            await ui.error(str(e))
                        # Continue processing other parts instead of failing completely
                        continue

    # Check for intention without action pattern
    # This catches when the agent says it will do something but doesn't execute tools
    if not empty_response_detected and has_non_empty_content and not has_tool_calls:
        # Common intention phrases that suggest the agent should be taking action
        intention_phrases = [
            "let me", "i'll", "i will", "i'm going to", "i need to", "i should",
            "i want to", "going to", "need to", "let's", "i can", "i would",
            "allow me to", "i shall", "about to", "plan to", "intend to"
        ]
        
        # Check if any content contains intention phrases
        has_intention = False
        for part in node.model_response.parts:
            if hasattr(part, "content") and isinstance(part.content, str):
                content_lower = part.content.lower()
                if any(phrase in content_lower for phrase in intention_phrases):
                    # Also check for action verbs that suggest tool usage
                    action_verbs = ["read", "check", "search", "find", "look", "create", "write", 
                                   "update", "modify", "run", "execute", "analyze", "examine", "scan"]
                    if any(verb in content_lower for verb in action_verbs):
                        has_intention = True
                        break
        
        if has_intention:
            # Agent stated intention but didn't execute tools
            empty_response_detected = True
            if state_manager.session.show_thoughts:
                await ui.muted("⚠️ INTENTION WITHOUT ACTION DETECTED - FORCING TOOL EXECUTION")

    # Return a tuple with (is_empty, reason) for better retry handling
    if empty_response_detected:
        # Determine the specific reason for empty response
        if appears_truncated:
            return True, "truncated"
        elif has_intention:
            return True, "intention_without_action"
        else:
            return True, "empty"
    return False, None


def get_or_create_agent(model: ModelName, state_manager: StateManager) -> PydanticAgent:
    if model not in state_manager.session.agents:
        max_retries = state_manager.session.user_config.get("settings", {}).get("max_retries", 3)

        # Lazy import Agent and Tool
        Agent, Tool = get_agent_tool()

        # Load system prompt
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "system.md"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
        except FileNotFoundError:
            # Fallback to system.txt if system.md not found
            prompt_path = Path(__file__).parent.parent.parent / "prompts" / "system.txt"
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    system_prompt = f.read().strip()
            except FileNotFoundError:
                # Use a default system prompt if neither file exists
                system_prompt = "You are a helpful AI assistant for software development tasks."

        # Load TUNACODE.md context
        # Use sync version of get_code_style to avoid nested event loop issues
        try:
            from pathlib import Path as PathlibPath

            tunacode_path = PathlibPath.cwd() / "TUNACODE.md"
            if tunacode_path.exists():
                tunacode_content = tunacode_path.read_text(encoding="utf-8")
                if tunacode_content.strip():
                    # Log that we found TUNACODE.md
                    logger.info("📄 TUNACODE.md located: Loading context...")

                    system_prompt += "\n\n# Project Context from TUNACODE.md\n" + tunacode_content
            else:
                # Log that TUNACODE.md was not found
                logger.info("📄 TUNACODE.md not found: Using default context")
        except Exception as e:
            # Log errors loading TUNACODE.md at debug level
            logger.debug(f"Error loading TUNACODE.md: {e}")

        todo_tool = TodoTool(state_manager=state_manager)

        try:
            # Only add todo section if there are actual todos
            current_todos = todo_tool.get_current_todos_sync()
            if current_todos != "No todos found":
                system_prompt += f'\n\n# Current Todo List\n\nYou have existing todos that need attention:\n\n{current_todos}\n\nRemember to check progress on these todos and update them as you work. Use todo("list") to see current status anytime.'
        except Exception as e:
            # Log error but don't fail agent creation

            logger.warning(f"Warning: Failed to load todos: {e}")

        state_manager.session.agents[model] = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=[
                Tool(bash, max_retries=max_retries),
                Tool(glob, max_retries=max_retries),
                Tool(grep, max_retries=max_retries),
                Tool(list_dir, max_retries=max_retries),
                Tool(read_file, max_retries=max_retries),
                Tool(run_command, max_retries=max_retries),
                Tool(todo_tool._execute, max_retries=max_retries),
                Tool(update_file, max_retries=max_retries),
                Tool(write_file, max_retries=max_retries),
            ],
            mcp_servers=get_mcp_servers(state_manager),
        )
    return state_manager.session.agents[model]


def patch_tool_messages(
    error_message: ErrorMessage = "Tool operation failed",
    state_manager: StateManager = None,
):
    """
    Find any tool calls without responses and add synthetic error responses for them.
    Takes an error message to use in the synthesized tool response.

    Ignores tools that have corresponding retry prompts as the model is already
    addressing them.
    """
    if state_manager is None:
        raise ValueError("state_manager is required for patch_tool_messages")

    messages = state_manager.session.messages

    if not messages:
        return

    # Map tool calls to their tool returns
    tool_calls: dict[ToolCallId, ToolName] = {}  # tool_call_id -> tool_name
    tool_returns: set[ToolCallId] = set()  # set of tool_call_ids with returns
    retry_prompts: set[ToolCallId] = set()  # set of tool_call_ids with retry prompts

    for message in messages:
        if hasattr(message, "parts"):
            for part in message.parts:
                if (
                    hasattr(part, "part_kind")
                    and hasattr(part, "tool_call_id")
                    and part.tool_call_id
                ):
                    if part.part_kind == "tool-call":
                        tool_calls[part.tool_call_id] = part.tool_name
                    elif part.part_kind == "tool-return":
                        tool_returns.add(part.tool_call_id)
                    elif part.part_kind == "retry-prompt":
                        retry_prompts.add(part.tool_call_id)

    # Identify orphaned tools (those without responses and not being retried)
    for tool_call_id, tool_name in list(tool_calls.items()):
        if tool_call_id not in tool_returns and tool_call_id not in retry_prompts:
            # Import ModelRequest and ToolReturnPart lazily
            ModelRequest, ToolReturnPart, _ = get_model_messages()
            messages.append(
                ModelRequest(
                    parts=[
                        ToolReturnPart(
                            tool_name=tool_name,
                            content=error_message,
                            tool_call_id=tool_call_id,
                            timestamp=datetime.now(timezone.utc),
                            part_kind="tool-return",
                        )
                    ],
                    kind="request",
                )
            )


async def parse_json_tool_calls(
    text: str, tool_callback: Optional[ToolCallback], state_manager: StateManager
) -> int:
    """
    Parse JSON tool calls from text when structured tool calling fails.
    Fallback for when API providers don't support proper tool calling.

    Returns:
        int: Number of tools successfully executed
    """
    if not tool_callback:
        return 0

    # Pattern for JSON tool calls: {"tool": "tool_name", "args": {...}}
    # Find potential JSON objects and parse them
    potential_jsons = []
    brace_count = 0
    start_pos = -1

    for i, char in enumerate(text):
        if char == "{":
            if brace_count == 0:
                start_pos = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0 and start_pos != -1:
                potential_json = text[start_pos : i + 1]
                try:
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                        potential_jsons.append((parsed["tool"], parsed["args"]))
                except json.JSONDecodeError:
                    logger.debug(
                        f"Failed to parse potential JSON tool call: {potential_json[:50]}..."
                    )
                start_pos = -1

    matches = potential_jsons
    tools_executed = 0

    for tool_name, args in matches:
        try:
            # Create a mock tool call object
            class MockToolCall:
                def __init__(self, tool_name: str, args: dict):
                    self.tool_name = tool_name
                    self.args = args
                    self.tool_call_id = f"fallback_{datetime.now().timestamp()}"

            class MockNode:
                pass

            # Execute the tool through the callback
            mock_call = MockToolCall(tool_name, args)
            mock_node = MockNode()

            await tool_callback(mock_call, mock_node)
            tools_executed += 1

            if state_manager.session.show_thoughts:
                from tunacode.ui import console as ui

                await ui.muted(f"FALLBACK: Executed {tool_name} via JSON parsing")

        except Exception as e:
            if state_manager.session.show_thoughts:
                from tunacode.ui import console as ui

                await ui.error(f"Error executing fallback tool {tool_name}: {str(e)}")

    return tools_executed


async def extract_and_execute_tool_calls(
    text: str, tool_callback: Optional[ToolCallback], state_manager: StateManager
) -> int:
    """
    Extract tool calls from text content and execute them.
    Supports multiple formats for maximum compatibility.

    Returns:
        int: The number of tool calls found and executed.
    """
    if not tool_callback:
        return 0

    tools_executed = 0

    # Format 1: {"tool": "name", "args": {...}}
    tools_executed += await parse_json_tool_calls(text, tool_callback, state_manager)

    # Format 2: Tool calls in code blocks
    code_block_pattern = r'```json\s*(\{(?:[^{}]|"[^"]*"|(?:\{[^}]*\}))*"tool"(?:[^{}]|"[^"]*"|(?:\{[^}]*\}))*\})\s*```'
    code_matches = re.findall(code_block_pattern, text, re.MULTILINE | re.DOTALL)

    for match in code_matches:
        try:
            tool_data = json.loads(match)
            if "tool" in tool_data and "args" in tool_data:

                class MockToolCall:
                    def __init__(self, tool_name: str, args: dict):
                        self.tool_name = tool_name
                        self.args = args
                        self.tool_call_id = f"codeblock_{datetime.now().timestamp()}"

                class MockNode:
                    pass

                mock_call = MockToolCall(tool_data["tool"], tool_data["args"])
                mock_node = MockNode()

                await tool_callback(mock_call, mock_node)
                tools_executed += 1

                if state_manager.session.show_thoughts:
                    from tunacode.ui import console as ui

                    await ui.muted(f"FALLBACK: Executed {tool_data['tool']} from code block")

        except (json.JSONDecodeError, KeyError, Exception) as e:
            if state_manager.session.show_thoughts:
                from tunacode.ui import console as ui

                await ui.error(f"Error parsing code block tool call: {str(e)}")

    return tools_executed


async def check_query_satisfaction(
    original_query: str,
    actions_taken: List[dict],
    current_response: str,
    iteration: int,
    agent: PydanticAgent,
    state_manager: StateManager,
) -> Tuple[bool, str]:
    """
    DEPRECATED: This function previously made recursive agent calls which caused empty responses.
    Now we rely on the agent's own TUNACODE_TASK_COMPLETE signal instead.
    
    This function always returns (False, "Agent should decide completion") to maintain compatibility
    while we transition to the new completion mechanism.
    """
    # No longer perform recursive agent calls
    # The agent should use TUNACODE_TASK_COMPLETE to signal completion
    return False, "Agent should decide when to use TUNACODE_TASK_COMPLETE"


async def process_request(
    model: ModelName,
    message: str,
    state_manager: StateManager,
    tool_callback: Optional[ToolCallback] = None,
    streaming_callback: Optional[Callable[[str], None]] = None,
) -> AgentRun:
    try:
        agent = get_or_create_agent(model, state_manager)
        mh = state_manager.session.messages.copy()
        request_id = getattr(state_manager.session, "request_id", "N/A")

        # Get max iterations from config (default: 40)
        max_iterations = state_manager.session.user_config.get("settings", {}).get(
            "max_iterations", 40
        )
        fallback_enabled = state_manager.session.user_config.get("settings", {}).get(
            "fallback_response", True
        )

        from tunacode.configuration.models import ModelRegistry
        from tunacode.core.token_usage.usage_tracker import UsageTracker

        parser = ApiResponseParser()
        registry = ModelRegistry()
        calculator = CostCalculator(registry)
        usage_tracker = UsageTracker(parser, calculator, state_manager)
        response_state = ResponseState()

        # Reset iteration tracking for this request
        state_manager.session.iteration_count = 0
        
        # Track unproductive iterations (no tool usage)
        unproductive_iterations = 0
        last_productive_iteration = 0

        # Create a request-level buffer for batching read-only tools across nodes
        tool_buffer = ToolBuffer()

        # Show TUNACODE.md preview if it was loaded and thoughts are enabled
        if state_manager.session.show_thoughts and hasattr(state_manager, "tunacode_preview"):
            from tunacode.ui import console as ui

            await ui.muted(state_manager.tunacode_preview)
            # Clear the preview after displaying it once
            delattr(state_manager, "tunacode_preview")

        # Show what we're sending to the API when thoughts are enabled
        if state_manager.session.show_thoughts:
            from tunacode.ui import console as ui

            await ui.muted("\n" + "=" * 60)
            await ui.muted("📤 SENDING TO API:")
            await ui.muted(f"Request ID: {request_id}")
            await ui.muted(f"Message: {message[:120]}")
            await ui.muted(f"Model: {model}")
            await ui.muted(f"Message History Length: {len(mh)}")
            await ui.muted("=" * 60)

        async with agent.iter(message, message_history=mh) as agent_run:
            i = 0
            async for node in agent_run:
                # Increment iteration counter at the very beginning so that it
                # is always updated, even if we break out of the loop early
                i += 1
                state_manager.session.current_iteration = i
                state_manager.session.iteration_count = i

                # Handle token-level streaming for model request nodes
                if streaming_callback and STREAMING_AVAILABLE and Agent.is_model_request_node(node):
                    async with node.stream(agent_run.ctx) as request_stream:
                        async for event in request_stream:
                            if isinstance(event, PartDeltaEvent) and isinstance(
                                event.delta, TextPartDelta
                            ):
                                # Stream individual token deltas
                                if event.delta.content_delta:
                                    await streaming_callback(event.delta.content_delta)

                empty_response, empty_reason = await _process_node(
                    node,
                    tool_callback,
                    state_manager,
                    tool_buffer,
                    streaming_callback,
                    usage_tracker,
                    response_state,
                )

                # Handle empty response by asking user for help instead of giving up
                if empty_response:
                    # Track consecutive empty responses
                    if not hasattr(state_manager.session, "consecutive_empty_responses"):
                        state_manager.session.consecutive_empty_responses = 0
                    state_manager.session.consecutive_empty_responses += 1

                    # IMMEDIATE AGGRESSIVE INTERVENTION on ANY empty response
                    if state_manager.session.consecutive_empty_responses >= 1:
                        # Get context about what was happening
                        last_tools_used = []
                        if state_manager.session.tool_calls:
                            for tc in state_manager.session.tool_calls[-3:]:
                                tool_name = tc.get("tool", "unknown")
                                tool_args = tc.get("args", {})
                                tool_desc = tool_name
                                if tool_name in ["grep", "glob"] and isinstance(tool_args, dict):
                                    pattern = tool_args.get("pattern", "")
                                    tool_desc = f"{tool_name}('{pattern}')"
                                elif tool_name == "read_file" and isinstance(tool_args, dict):
                                    path = tool_args.get("file_path", tool_args.get("filepath", ""))
                                    tool_desc = f"{tool_name}('{path}')"
                                last_tools_used.append(tool_desc)
                        
                        tools_context = f"Recent tools: {', '.join(last_tools_used)}" if last_tools_used else "No tools used yet"
                        
                        # AGGRESSIVE prompt - YOU FAILED, TRY HARDER
                        force_action_content = f"""FAILURE DETECTED: You returned {'an ' + empty_reason if empty_reason != 'empty' else 'an empty'} response.

This is UNACCEPTABLE. You FAILED to produce output.

Task: {message[:200]}...
{tools_context}
Current iteration: {i}

TRY AGAIN RIGHT NOW:

1. If your search returned no results → Try a DIFFERENT search pattern
2. If you found what you need → Use TUNACODE_TASK_COMPLETE
3. If you're stuck → EXPLAIN SPECIFICALLY what's blocking you
4. If you need to explore → Use list_dir or broader searches

YOU MUST PRODUCE REAL OUTPUT IN THIS RESPONSE. NO EXCUSES.
EXECUTE A TOOL OR PROVIDE SUBSTANTIAL CONTENT.
DO NOT RETURN ANOTHER EMPTY RESPONSE."""

                        from pydantic_ai.messages import UserPromptPart
                        model_request_cls = get_model_messages()[0]
                        
                        user_prompt_part = UserPromptPart(
                            content=force_action_content,
                            part_kind="user-prompt",
                        )
                        force_message = model_request_cls(
                            parts=[user_prompt_part],
                            kind="request",
                        )
                        state_manager.session.messages.append(force_message)
                        
                        if state_manager.session.show_thoughts:
                            from tunacode.ui import console as ui
                            await ui.warning(
                                f"\n⚠️ EMPTY RESPONSE FAILURE - AGGRESSIVE RETRY TRIGGERED"
                            )
                            await ui.muted(f"   Reason: {empty_reason}")
                            await ui.muted(f"   Recent tools: {tools_context}")
                            await ui.muted("   Injecting 'YOU FAILED TRY HARDER' prompt")
                        
                        # Reset counter after aggressive intervention
                        state_manager.session.consecutive_empty_responses = 0
                else:
                    # Reset counter on successful response
                    if hasattr(state_manager.session, "consecutive_empty_responses"):
                        state_manager.session.consecutive_empty_responses = 0

                if hasattr(node, "result") and node.result and hasattr(node.result, "output"):
                    if node.result.output:
                        response_state.has_user_response = True

                # Track productivity - check if any tools were used in this iteration
                iteration_had_tools = False
                if hasattr(node, "model_response"):
                    for part in node.model_response.parts:
                        if hasattr(part, "part_kind") and part.part_kind == "tool-call":
                            iteration_had_tools = True
                            break
                
                if iteration_had_tools:
                    # Reset unproductive counter
                    unproductive_iterations = 0
                    last_productive_iteration = i
                else:
                    # Increment unproductive counter
                    unproductive_iterations += 1
                    
                # After 3 unproductive iterations, force action
                if unproductive_iterations >= 3 and not response_state.task_completed:
                    no_progress_content = f"""ALERT: No tools executed for {unproductive_iterations} iterations.
                    
Last productive iteration: {last_productive_iteration}
Current iteration: {i}/{max_iterations}
Task: {message[:200]}...

You're describing actions but not executing them. You MUST:

1. If task is COMPLETE: Start response with TUNACODE_TASK_COMPLETE
2. If task needs work: Execute a tool RIGHT NOW (grep, read_file, bash, etc.)
3. If stuck: Explain the specific blocker

NO MORE DESCRIPTIONS. Take ACTION or mark COMPLETE."""

                    from pydantic_ai.messages import UserPromptPart
                    model_request_cls = get_model_messages()[0]
                    
                    user_prompt_part = UserPromptPart(
                        content=no_progress_content,
                        part_kind="user-prompt",
                    )
                    progress_message = model_request_cls(
                        parts=[user_prompt_part],
                        kind="request",
                    )
                    state_manager.session.messages.append(progress_message)
                    
                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui
                        await ui.warning(f"⚠️ NO PROGRESS: {unproductive_iterations} iterations without tool usage")
                    
                    # Reset counter after intervention
                    unproductive_iterations = 0

                # REMOVED: Recursive satisfaction check that caused empty responses
                # The agent now decides completion using TUNACODE_TASK_COMPLETE marker
                # This eliminates recursive agent calls and gives control back to the agent
                
                # Store original query for reference
                if not hasattr(state_manager.session, "original_query"):
                    state_manager.session.original_query = message

                # Display iteration progress if thoughts are enabled
                if state_manager.session.show_thoughts:
                    from tunacode.ui import console as ui

                    await ui.muted(f"\nITERATION: {i}/{max_iterations} (Request ID: {request_id})")

                    # Show summary of tools used so far
                    if state_manager.session.tool_calls:
                        tool_summary: dict[str, int] = {}
                        for tc in state_manager.session.tool_calls:
                            tool_name = tc.get("tool", "unknown")
                            tool_summary[tool_name] = tool_summary.get(tool_name, 0) + 1

                        summary_str = ", ".join(
                            [f"{name}: {count}" for name, count in tool_summary.items()]
                        )
                        await ui.muted(f"TOOLS USED: {summary_str}")

                # User clarification: Ask user for guidance when explicitly awaiting
                if response_state.awaiting_user_guidance:
                    # Build a progress summary
                    tool_summary = {}
                    if state_manager.session.tool_calls:
                        for tc in state_manager.session.tool_calls:
                            tool_name = tc.get("tool", "unknown")
                            tool_summary[tool_name] = tool_summary.get(tool_name, 0) + 1

                    tools_used_str = (
                        ", ".join([f"{name}: {count}" for name, count in tool_summary.items()])
                        if tool_summary
                        else "No tools used yet"
                    )

                    # Create user message asking for clarification
                    from pydantic_ai.messages import UserPromptPart

                    model_request_cls = get_model_messages()[0]

                    clarification_content = f"""I need clarification to continue.

Original request: {getattr(state_manager.session, "original_query", "your request")}

Progress so far:
- Iterations: {i}
- Tools used: {tools_used_str}

If the task is complete, I should respond with TUNACODE_TASK_COMPLETE.
Otherwise, please provide specific guidance on what to do next."""

                    user_prompt_part = UserPromptPart(
                        content=clarification_content,
                        part_kind="user-prompt",
                    )
                    clarification_message = model_request_cls(
                        parts=[user_prompt_part],
                        kind="request",
                    )
                    state_manager.session.messages.append(clarification_message)

                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui

                        await ui.muted(
                            "\n🤔 SEEKING CLARIFICATION: Asking user for guidance on task progress"
                        )

                    # Mark that we've asked for user guidance
                    response_state.awaiting_user_guidance = True

                # Check if task is explicitly completed
                if response_state.task_completed:
                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui

                        await ui.success("Task completed successfully")
                    break

                if i >= max_iterations and not response_state.task_completed:
                    # Instead of breaking, ask user if they want to continue
                    # Build progress summary
                    tool_summary = {}
                    if state_manager.session.tool_calls:
                        for tc in state_manager.session.tool_calls:
                            tool_name = tc.get("tool", "unknown")
                            tool_summary[tool_name] = tool_summary.get(tool_name, 0) + 1

                    tools_str = (
                        ", ".join([f"{name}: {count}" for name, count in tool_summary.items()])
                        if tool_summary
                        else "No tools used"
                    )

                    extend_content = f"""I've reached the iteration limit ({max_iterations}).

Progress summary:
- Tools used: {tools_str}
- Iterations completed: {i}

The task appears incomplete. Would you like me to:
1. Continue working (I can extend the limit)
2. Summarize what I've done and stop
3. Try a different approach

Please let me know how to proceed."""

                    # Create user message
                    from pydantic_ai.messages import UserPromptPart

                    model_request_cls = get_model_messages()[0]

                    user_prompt_part = UserPromptPart(
                        content=extend_content,
                        part_kind="user-prompt",
                    )
                    extend_message = model_request_cls(
                        parts=[user_prompt_part],
                        kind="request",
                    )
                    state_manager.session.messages.append(extend_message)

                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui

                        await ui.muted(
                            f"\n📊 ITERATION LIMIT: Asking user for guidance at {max_iterations} iterations"
                        )

                    # Extend the limit temporarily to allow processing the response
                    max_iterations += 5  # Give 5 more iterations to process user guidance
                    response_state.awaiting_user_guidance = True

            # Final flush: execute any remaining buffered read-only tools
            if tool_callback and tool_buffer.has_tasks():
                import time

                from tunacode.ui import console as ui

                buffered_tasks = tool_buffer.flush()
                start_time = time.time()

                await ui.muted("\n" + "=" * 60)
                await ui.muted(
                    f"🚀 FINAL BATCH: Executing {len(buffered_tasks)} buffered read-only tools"
                )
                await ui.muted("=" * 60)

                for idx, (part, node) in enumerate(buffered_tasks, 1):
                    tool_desc = f"  [{idx}] {part.tool_name}"
                    if hasattr(part, "args") and isinstance(part.args, dict):
                        if part.tool_name == "read_file" and "file_path" in part.args:
                            tool_desc += f" → {part.args['file_path']}"
                        elif part.tool_name == "grep" and "pattern" in part.args:
                            tool_desc += f" → pattern: '{part.args['pattern']}'"
                            if "include_files" in part.args:
                                tool_desc += f", files: '{part.args['include_files']}'"
                        elif part.tool_name == "list_dir" and "directory" in part.args:
                            tool_desc += f" → {part.args['directory']}"
                        elif part.tool_name == "glob" and "pattern" in part.args:
                            tool_desc += f" → pattern: '{part.args['pattern']}'"
                    await ui.muted(tool_desc)
                await ui.muted("=" * 60)

                await execute_tools_parallel(buffered_tasks, tool_callback)

                elapsed_time = (time.time() - start_time) * 1000
                sequential_estimate = len(buffered_tasks) * 100
                speedup = sequential_estimate / elapsed_time if elapsed_time > 0 else 1.0

                await ui.muted(
                    f"✅ Final batch completed in {elapsed_time:.0f}ms "
                    f"(~{speedup:.1f}x faster than sequential)\n"
                )

            # If we need to add a fallback response, create a wrapper
            # Don't add fallback if task was explicitly completed
            if (
                not response_state.has_user_response
                and not response_state.task_completed
                and i >= max_iterations
                and fallback_enabled
            ):
                patch_tool_messages("Task incomplete", state_manager=state_manager)
                response_state.has_final_synthesis = True

                # Extract context from the agent run
                tool_calls_summary = []
                files_modified = set()
                commands_run = []

                # Analyze message history for context
                for msg in state_manager.session.messages:
                    if hasattr(msg, "parts"):
                        for part in msg.parts:
                            if hasattr(part, "part_kind") and part.part_kind == "tool-call":
                                tool_name = getattr(part, "tool_name", "unknown")
                                tool_calls_summary.append(tool_name)

                                # Track specific operations
                                if tool_name in ["write_file", "update_file"] and hasattr(
                                    part, "args"
                                ):
                                    if isinstance(part.args, dict) and "file_path" in part.args:
                                        files_modified.add(part.args["file_path"])
                                elif tool_name in ["run_command", "bash"] and hasattr(part, "args"):
                                    if isinstance(part.args, dict) and "command" in part.args:
                                        commands_run.append(part.args["command"])

                # Build fallback response with context
                fallback = FallbackResponse(
                    summary="Reached maximum iterations without producing a final response.",
                    progress=f"Completed {i} iterations (limit: {max_iterations})",
                )

                # Get verbosity setting
                verbosity = state_manager.session.user_config.get("settings", {}).get(
                    "fallback_verbosity", "normal"
                )

                if verbosity in ["normal", "detailed"]:
                    # Add what was attempted
                    if tool_calls_summary:
                        tool_counts: dict[str, int] = {}
                        for tool in tool_calls_summary:
                            tool_counts[tool] = tool_counts.get(tool, 0) + 1

                        fallback.issues.append(f"Executed {len(tool_calls_summary)} tool calls:")
                        for tool, count in sorted(tool_counts.items()):
                            fallback.issues.append(f"  • {tool}: {count}x")

                    if verbosity == "detailed":
                        if files_modified:
                            fallback.issues.append(f"\nFiles modified ({len(files_modified)}):")
                            for f in sorted(files_modified)[:5]:  # Limit to 5 files
                                fallback.issues.append(f"  • {f}")
                            if len(files_modified) > 5:
                                fallback.issues.append(
                                    f"  • ... and {len(files_modified) - 5} more"
                                )

                        if commands_run:
                            fallback.issues.append(f"\nCommands executed ({len(commands_run)}):")
                            for cmd in commands_run[:3]:  # Limit to 3 commands
                                # Truncate long commands
                                display_cmd = cmd if len(cmd) <= 60 else cmd[:57] + "..."
                                fallback.issues.append(f"  • {display_cmd}")
                            if len(commands_run) > 3:
                                fallback.issues.append(f"  • ... and {len(commands_run) - 3} more")

                # Add helpful next steps
                fallback.next_steps.append(
                    "The task may be too complex - try breaking it into smaller steps"
                )
                fallback.next_steps.append(
                    "Check the output above for any errors or partial progress"
                )
                if files_modified:
                    fallback.next_steps.append(
                        "Review modified files to see what changes were made"
                    )

                # Create comprehensive output
                output_parts = [fallback.summary, ""]

                if fallback.progress:
                    output_parts.append(f"Progress: {fallback.progress}")

                if fallback.issues:
                    output_parts.append("\nWhat happened:")
                    output_parts.extend(fallback.issues)

                if fallback.next_steps:
                    output_parts.append("\nSuggested next steps:")
                    for step in fallback.next_steps:
                        output_parts.append(f"  • {step}")

                comprehensive_output = "\n".join(output_parts)

                # Create a wrapper object that mimics AgentRun with the required attributes
                class AgentRunWrapper:
                    def __init__(self, wrapped_run, fallback_result):
                        self._wrapped = wrapped_run
                        self._result = fallback_result
                        self.response_state = response_state

                    def __getattribute__(self, name):
                        # Handle special attributes first to avoid conflicts
                        if name in ["_wrapped", "_result", "response_state"]:
                            return object.__getattribute__(self, name)

                        # Explicitly handle 'result' to return our fallback result
                        if name == "result":
                            return object.__getattribute__(self, "_result")

                        # Delegate all other attributes to the wrapped object
                        try:
                            return getattr(object.__getattribute__(self, "_wrapped"), name)
                        except AttributeError:
                            raise AttributeError(
                                f"'{type(self).__name__}' object has no attribute '{name}'"
                            )

                return AgentRunWrapper(agent_run, SimpleResult(comprehensive_output))

            # For non-fallback cases, we still need to handle the response_state
            # Create a minimal wrapper just to add response_state
            class AgentRunWithState:
                def __init__(self, wrapped_run):
                    self._wrapped = wrapped_run
                    self.response_state = response_state

                def __getattribute__(self, name):
                    # Handle special attributes first
                    if name in ["_wrapped", "response_state"]:
                        return object.__getattribute__(self, name)

                    # Delegate all other attributes to the wrapped object
                    try:
                        return getattr(object.__getattribute__(self, "_wrapped"), name)
                    except AttributeError:
                        raise AttributeError(
                            f"'{type(self).__name__}' object has no attribute '{name}'"
                        )

        return AgentRunWithState(agent_run)
    except asyncio.CancelledError:
        # When task is cancelled, raise UserAbortError instead
        raise UserAbortError("Operation was cancelled by user")
