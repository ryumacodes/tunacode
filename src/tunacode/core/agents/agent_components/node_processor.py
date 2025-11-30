"""Node processing functionality for agent responses."""

import json
from typing import Any, Awaitable, Callable, Optional, Tuple

from tunacode.constants import UI_COLORS
from tunacode.core.logging.logger import get_logger
from tunacode.core.state import StateManager
from tunacode.exceptions import UserAbortError
from tunacode.types import AgentState, UsageTrackerProtocol
from tunacode.utils.file_utils import DotDict
from tunacode.utils.tool_descriptions import get_batch_description, get_tool_description

from .response_state import ResponseState
from .task_completion import check_task_completion
from .tool_buffer import ToolBuffer
from .truncation_checker import check_for_truncation

logger = get_logger(__name__)
colors = DotDict(UI_COLORS)


def _update_tool_status(
    message: str,
    tool_status_callback: Optional[Callable[[str], None]],
) -> None:
    """Update tool status via callback if available.

    This is a synchronous helper that posts to the Textual app's message queue.
    The callback is designed to be called from async context but uses post_message
    which is thread-safe and non-blocking.
    """
    if tool_status_callback is not None:
        # Strip Rich markup for cleaner status bar display
        import re
        clean_message = re.sub(r"\[.*?\]", "", message)
        tool_status_callback(clean_message)


def _clear_tool_status(
    tool_status_callback: Optional[Callable[[str], None]],
) -> None:
    """Clear tool status via callback if available."""
    if tool_status_callback is not None:
        tool_status_callback("")


async def _process_node(
    node,
    tool_callback: Optional[Callable],
    state_manager: StateManager,
    tool_buffer: Optional[ToolBuffer] = None,
    streaming_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    usage_tracker: Optional[UsageTrackerProtocol] = None,
    response_state: Optional[ResponseState] = None,
    tool_status_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[bool, Optional[str]]:
    """Process a single node from the agent response.

    Returns:
        tuple: (is_empty: bool, reason: Optional[str]) - True if empty/problematic
               response detected, with reason being one of: "empty", "truncated",
               "intention_without_action"
    """
    # Use the original callback directly - parallel execution will be handled differently
    buffering_callback = tool_callback
    empty_response_detected = False
    has_non_empty_content = False
    appears_truncated = False
    has_intention = False
    has_tool_calls = False

    # Transition to ASSISTANT at the start of node processing
    if response_state and response_state.can_transition_to(AgentState.ASSISTANT):
        response_state.transition_to(AgentState.ASSISTANT)

    if hasattr(node, "request"):
        state_manager.session.messages.append(node.request)

    if hasattr(node, "thought") and node.thought:
        state_manager.session.messages.append({"thought": node.thought})

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
                            # Don't mark as complete - let the tools run first
                            # Update the content to remove the marker but don't set task_completed
                            part.content = cleaned_content
                            # Log this as an issue
                            pending_tools_count = sum(
                                1
                                for p in node.model_response.parts
                                if getattr(p, "part_kind", "") == "tool-call"
                            )
                            logger.warning(
                                f"Agent attempted premature completion with {pending_tools_count} "
                                f"pending tools"
                            )
                        else:
                            # Check if content suggests pending actions
                            combined_text = " ".join(all_content_parts).lower()
                            pending_phrases = [
                                "let me",
                                "i'll check",
                                "i will",
                                "going to",
                                "about to",
                                "need to check",
                                "let's check",
                                "i should",
                                "need to find",
                                "let me see",
                                "i'll look",
                                "let me search",
                                "let me find",
                            ]
                            has_pending_intention = any(
                                phrase in combined_text for phrase in pending_phrases
                            )

                            # Also check for action verbs at end of content
                            # suggesting incomplete action
                            action_endings = [
                                "checking",
                                "searching",
                                "looking",
                                "finding",
                                "reading",
                                "analyzing",
                            ]
                            ends_with_action = any(
                                combined_text.rstrip().endswith(ending) for ending in action_endings
                            )

                            if (
                                has_pending_intention or ends_with_action
                            ) and state_manager.session.iteration_count <= 1:
                                # Too early to complete with pending intentions
                                found_phrases = [
                                    p for p in pending_phrases if p in combined_text
                                ]
                                # Still allow it but log warning
                                logger.warning(
                                    f"Task completion with pending intentions detected: "
                                    f"{found_phrases}"
                                )

                            # Normal completion - transition to RESPONSE state and mark completion
                            response_state.transition_to(AgentState.RESPONSE)
                            response_state.set_completion_detected(True)
                            response_state.has_user_response = True
                            # Update the part content to remove the marker
                            part.content = cleaned_content
                        break

            # Check for truncation patterns
            if all_content_parts:
                combined_content = " ".join(all_content_parts).strip()
                appears_truncated = check_for_truncation(combined_content)

            # If we only got empty content and no tool calls, we should NOT consider this
            # a valid response
            # This prevents the agent from stopping when it gets empty responses
            if not has_non_empty_content and not any(
                hasattr(part, "part_kind") and part.part_kind == "tool-call"
                for part in node.model_response.parts
            ):
                # Empty response with no tools - keep going
                empty_response_detected = True

            # Check if response appears truncated
            elif appears_truncated and not any(
                hasattr(part, "part_kind") and part.part_kind == "tool-call"
                for part in node.model_response.parts
            ):
                # Truncated response detected
                empty_response_detected = True

        # Process tool calls
        await _process_tool_calls(
            node,
            buffering_callback,
            state_manager,
            tool_buffer,
            response_state,
            tool_status_callback,
        )

    # If there were no tools and we processed a model response, transition to RESPONSE
    if response_state and response_state.can_transition_to(AgentState.RESPONSE):
        # Only transition if not already completed (set by completion marker path)
        if not response_state.is_completed():
            response_state.transition_to(AgentState.RESPONSE)

    # Determine empty response reason
    if empty_response_detected:
        if appears_truncated:
            return True, "truncated"
        else:
            return True, "empty"

    # Check for intention without action
    if has_intention and not has_tool_calls and not has_non_empty_content:
        return True, "intention_without_action"

    return False, None


async def _process_tool_calls(
    node: Any,
    tool_callback: Optional[Callable],
    state_manager: StateManager,
    tool_buffer: Optional[ToolBuffer],
    response_state: Optional[ResponseState],
    tool_status_callback: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Process tool calls from the node using smart batching strategy.

    Smart batching optimization:
    - Collect all read-only tools into a single batch (regardless of write tools in between)
    - Execute all read-only tools in one parallel batch
    - Execute write/execute tools sequentially in their original order

    This maximizes parallel execution efficiency by avoiding premature buffer flushes.
    """
    from tunacode.constants import READ_ONLY_TOOLS

    # Track if we're processing tool calls
    is_processing_tools = False

    # Phase 1: Collect and categorize all tools
    read_only_tasks = []
    research_agent_tasks = []
    write_execute_tasks = []

    for part in node.model_response.parts:
        if hasattr(part, "part_kind") and part.part_kind == "tool-call":
            is_processing_tools = True
            # Transition to TOOL_EXECUTION on first tool call
            if response_state and response_state.can_transition_to(AgentState.TOOL_EXECUTION):
                response_state.transition_to(AgentState.TOOL_EXECUTION)

            if tool_callback:
                # Categorize: research agent vs read-only vs write/execute
                if part.tool_name == "research_codebase":
                    research_agent_tasks.append((part, node))
                elif part.tool_name in READ_ONLY_TOOLS:
                    read_only_tasks.append((part, node))
                else:
                    write_execute_tasks.append((part, node))

    # Phase 2: Execute research agent
    if research_agent_tasks and tool_callback:
        from .tool_executor import execute_tools_parallel

        # Update tool status for research
        for part, _ in research_agent_tasks:
            tool_args = getattr(part, "args", {}) if hasattr(part, "args") else {}
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except (json.JSONDecodeError, TypeError):
                    tool_args = {}
            query = tool_args.get("query", "Unknown query")
            query_preview = query[:60] + "..." if len(query) > 60 else query
            _update_tool_status(f"Researching: {query_preview}", tool_status_callback)

        # Execute the research agent tool
        await execute_tools_parallel(research_agent_tasks, tool_callback)

        # Clear tool status
        _clear_tool_status(tool_status_callback)

    # Phase 3: Execute read-only tools in ONE parallel batch
    if read_only_tasks and tool_callback:
        from .tool_executor import execute_tools_parallel

        batch_id = getattr(state_manager.session, "batch_counter", 0) + 1
        state_manager.session.batch_counter = batch_id

        # Update tool status for batch execution
        tool_names = [part.tool_name for part, _ in read_only_tasks]
        batch_msg = get_batch_description(len(read_only_tasks), tool_names)
        _update_tool_status(f"{batch_msg}...", tool_status_callback)

        await execute_tools_parallel(read_only_tasks, tool_callback)

        # Clear tool status after batch execution
        _clear_tool_status(tool_status_callback)

    # Phase 4: Execute write/execute tools sequentially
    for part, node in write_execute_tasks:
        # Update tool status for sequential tool
        tool_args = getattr(part, "args", {}) if hasattr(part, "args") else {}
        # Parse args if they're a JSON string
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except (json.JSONDecodeError, TypeError):
                tool_args = {}
        tool_desc = get_tool_description(part.tool_name, tool_args)
        _update_tool_status(f"{tool_desc}...", tool_status_callback)

        # Execute the tool with robust error handling
        try:
            await tool_callback(part, node)
        except UserAbortError:
            raise
        except Exception as tool_err:
            logger.error(
                "Tool callback failed: tool=%s iter=%s err=%s",
                getattr(part, "tool_name", "<unknown>"),
                getattr(state_manager.session, "current_iteration", "?"),
                tool_err,
                exc_info=True,
            )
        finally:
            # Tool execution completed - resource cleanup handled by BaseTool.execute()
            tool_name = getattr(part, "tool_name", "<unknown>")
            logger.debug(
                "Tool execution completed (success or failure): tool=%s",
                tool_name,
            )
            # Clear tool status after each sequential tool
            _clear_tool_status(tool_status_callback)

    # Track tool calls in session
    if is_processing_tools:
        # Extract tool information for tracking
        for part in node.model_response.parts:
            if hasattr(part, "part_kind") and part.part_kind == "tool-call":
                tool_info = {
                    "tool": part.tool_name,
                    "args": getattr(part, "args", {}),
                    "timestamp": getattr(part, "timestamp", None),
                }
                state_manager.session.tool_calls.append(tool_info)

    # After tools are processed, transition back to RESPONSE
    if (
        is_processing_tools
        and response_state
        and response_state.can_transition_to(AgentState.RESPONSE)
    ):
        response_state.transition_to(AgentState.RESPONSE)

    # Update has_user_response based on presence of actual response content
    if (
        response_state
        and hasattr(node, "result")
        and node.result
        and hasattr(node.result, "output")
    ):
        if node.result.output:
            response_state.has_user_response = True
