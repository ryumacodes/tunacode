"""Module: tunacode.core.agents.main

Main agent functionality and coordination for the TunaCode CLI.
Handles agent creation, configuration, and request processing.

CLAUDE_ANCHOR[main-agent-module]: Primary agent orchestration and lifecycle management
"""

from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from pydantic_ai import Agent

if TYPE_CHECKING:
    from pydantic_ai import Tool  # noqa: F401

from tunacode.core.logging.logger import get_logger
from tunacode.core.state import StateManager
from tunacode.exceptions import ToolBatchingJSONError, UserAbortError
from tunacode.services.mcp import get_mcp_servers
from tunacode.types import (
    AgentRun,
    ModelName,
    ToolCallback,
    UsageTrackerProtocol,
)
from tunacode.ui.tool_descriptions import get_batch_description

# Import agent components
from .agent_components import (
    AgentRunWithState,
    AgentRunWrapper,
    ResponseState,
    SimpleResult,
    ToolBuffer,
    _process_node,
    check_task_completion,
    create_empty_response_message,
    create_fallback_response,
    create_progress_summary,
    create_user_message,
    execute_tools_parallel,
    extract_and_execute_tool_calls,
    format_fallback_output,
    get_model_messages,
    get_or_create_agent,
    get_recent_tools_context,
    get_tool_summary,
    parse_json_tool_calls,
    patch_tool_messages,
)

# Import streaming types with fallback for older versions
try:
    from pydantic_ai.messages import PartDeltaEvent, TextPartDelta

    STREAMING_AVAILABLE = True
except ImportError:
    PartDeltaEvent = None
    TextPartDelta = None
    STREAMING_AVAILABLE = False

# Configure logging
logger = get_logger(__name__)

__all__ = [
    "ToolBuffer",
    "check_task_completion",
    "extract_and_execute_tool_calls",
    "get_model_messages",
    "parse_json_tool_calls",
    "patch_tool_messages",
    "get_mcp_servers",
    "check_query_satisfaction",
    "process_request",
    "get_or_create_agent",
    "_process_node",
    "ResponseState",
    "SimpleResult",
    "AgentRunWrapper",
    "AgentRunWithState",
    "execute_tools_parallel",
    "get_agent_tool",
]


def get_agent_tool() -> tuple[type[Agent], type["Tool"]]:
    """Lazy import for Agent and Tool to avoid circular imports."""
    from pydantic_ai import Agent, Tool

    return Agent, Tool


async def check_query_satisfaction(
    agent: Agent,
    original_query: str,
    response: str,
    state_manager: StateManager,
) -> bool:
    """Check if the response satisfies the original query."""
    return True  # Agent uses TUNACODE_TASK_COMPLETE marker


async def process_request(
    message: str,
    model: ModelName,
    state_manager: StateManager,
    tool_callback: Optional[ToolCallback] = None,
    streaming_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    usage_tracker: Optional[UsageTrackerProtocol] = None,
    fallback_enabled: bool = True,
) -> AgentRun:
    """
    Process a single request to the agent.

    CLAUDE_ANCHOR[process-request-entry]: Main entry point for all agent requests

    Args:
        message: The user's request
        model: The model to use
        state_manager: State manager instance
        tool_callback: Optional callback for tool execution
        streaming_callback: Optional callback for streaming responses
        usage_tracker: Optional usage tracker
        fallback_enabled: Whether to enable fallback responses

    Returns:
        AgentRun or wrapper with result
    """
    # Get or create agent for the model
    agent = get_or_create_agent(model, state_manager)

    # Create a unique request ID for debugging
    import uuid

    request_id = str(uuid.uuid4())[:8]

    # Reset state for new request
    state_manager.session.current_iteration = 0
    state_manager.session.iteration_count = 0
    state_manager.session.tool_calls = []

    # Initialize batch counter if not exists
    if not hasattr(state_manager.session, "batch_counter"):
        state_manager.session.batch_counter = 0

    # Create tool buffer for parallel execution
    tool_buffer = ToolBuffer()

    # Track iterations and productivity
    max_iterations = state_manager.session.user_config.get("settings", {}).get("max_iterations", 15)
    unproductive_iterations = 0
    last_productive_iteration = 0

    # Track response state
    response_state = ResponseState()

    try:
        # Get message history from session messages
        # Create a copy of the message history to avoid modifying the original
        message_history = list(state_manager.session.messages)

        async with agent.iter(message, message_history=message_history) as agent_run:
            # Process nodes iteratively
            i = 1
            async for node in agent_run:
                state_manager.session.current_iteration = i
                state_manager.session.iteration_count = i

                # Handle token-level streaming for model request nodes
                Agent, _ = get_agent_tool()
                if streaming_callback and STREAMING_AVAILABLE and Agent.is_model_request_node(node):
                    async with node.stream(agent_run.ctx) as request_stream:
                        async for event in request_stream:
                            if isinstance(event, PartDeltaEvent) and isinstance(
                                event.delta, TextPartDelta
                            ):
                                # Stream individual token deltas
                                if event.delta.content_delta and streaming_callback:
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

                # Handle empty response
                if empty_response:
                    if not hasattr(state_manager.session, "consecutive_empty_responses"):
                        state_manager.session.consecutive_empty_responses = 0
                    state_manager.session.consecutive_empty_responses += 1

                    if state_manager.session.consecutive_empty_responses >= 1:
                        force_action_content = create_empty_response_message(
                            message,
                            empty_reason,
                            state_manager.session.tool_calls,
                            i,
                            state_manager,
                        )
                        create_user_message(force_action_content, state_manager)

                        if state_manager.session.show_thoughts:
                            from tunacode.ui import console as ui

                            await ui.warning(
                                "\n⚠️ EMPTY RESPONSE FAILURE - AGGRESSIVE RETRY TRIGGERED"
                            )
                            await ui.muted(f"   Reason: {empty_reason}")
                            await ui.muted(
                                f"   Recent tools: {get_recent_tools_context(state_manager.session.tool_calls)}"
                            )
                            await ui.muted("   Injecting retry guidance prompt")

                        state_manager.session.consecutive_empty_responses = 0
                else:
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

                    create_user_message(no_progress_content, state_manager)

                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui

                        await ui.warning(
                            f"⚠️ NO PROGRESS: {unproductive_iterations} iterations without tool usage"
                        )

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
                        tool_summary = get_tool_summary(state_manager.session.tool_calls)
                        summary_str = ", ".join(
                            [f"{name}: {count}" for name, count in tool_summary.items()]
                        )
                        await ui.muted(f"TOOLS USED: {summary_str}")

                # User clarification: Ask user for guidance when explicitly awaiting
                if response_state.awaiting_user_guidance:
                    _, tools_used_str = create_progress_summary(state_manager.session.tool_calls)

                    clarification_content = f"""I need clarification to continue.

Original request: {getattr(state_manager.session, "original_query", "your request")}

Progress so far:
- Iterations: {i}
- Tools used: {tools_used_str}

If the task is complete, I should respond with TUNACODE_TASK_COMPLETE.
Otherwise, please provide specific guidance on what to do next."""

                    create_user_message(clarification_content, state_manager)

                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui

                        await ui.muted(
                            "\n🤔 SEEKING CLARIFICATION: Asking user for guidance on task progress"
                        )

                    response_state.awaiting_user_guidance = True

                # Check if task is explicitly completed
                if response_state.task_completed:
                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui

                        await ui.success("Task completed successfully")
                    break

                if i >= max_iterations and not response_state.task_completed:
                    _, tools_str = create_progress_summary(state_manager.session.tool_calls)
                    tools_str = tools_str if tools_str != "No tools used yet" else "No tools used"

                    extend_content = f"""I've reached the iteration limit ({max_iterations}).

Progress summary:
- Tools used: {tools_str}
- Iterations completed: {i}

The task appears incomplete. Would you like me to:
1. Continue working (I can extend the limit)
2. Summarize what I've done and stop
3. Try a different approach

Please let me know how to proceed."""

                    create_user_message(extend_content, state_manager)

                    if state_manager.session.show_thoughts:
                        from tunacode.ui import console as ui

                        await ui.muted(
                            f"\n📊 ITERATION LIMIT: Asking user for guidance at {max_iterations} iterations"
                        )

                    max_iterations += 5
                    response_state.awaiting_user_guidance = True

                # Increment iteration counter
                i += 1

            # Final flush: execute any remaining buffered read-only tools
            if tool_callback and tool_buffer.has_tasks():
                import time

                from tunacode.ui import console as ui

                buffered_tasks = tool_buffer.flush()
                start_time = time.time()

                # Update spinner message for final batch execution
                tool_names = [part.tool_name for part, _ in buffered_tasks]
                batch_msg = get_batch_description(len(buffered_tasks), tool_names)
                await ui.update_spinner_message(
                    f"[bold #00d7ff]{batch_msg}...[/bold #00d7ff]", state_manager
                )

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

                # Reset spinner back to thinking
                from tunacode.constants import UI_THINKING_MESSAGE

                await ui.update_spinner_message(UI_THINKING_MESSAGE, state_manager)

            # If we need to add a fallback response, create a wrapper
            if (
                not response_state.has_user_response
                and not response_state.task_completed
                and i >= max_iterations
                and fallback_enabled
            ):
                patch_tool_messages("Task incomplete", state_manager=state_manager)
                response_state.has_final_synthesis = True

                verbosity = state_manager.session.user_config.get("settings", {}).get(
                    "fallback_verbosity", "normal"
                )
                fallback = create_fallback_response(
                    i,
                    max_iterations,
                    state_manager.session.tool_calls,
                    state_manager.session.messages,
                    verbosity,
                )
                comprehensive_output = format_fallback_output(fallback)

                wrapper = AgentRunWrapper(
                    agent_run, SimpleResult(comprehensive_output), response_state
                )
                return wrapper

            # For non-fallback cases, we still need to handle the response_state
            # Create a minimal wrapper just to add response_state
            state_wrapper = AgentRunWithState(agent_run, response_state)
            return state_wrapper

    except UserAbortError:
        raise
    except ToolBatchingJSONError as e:
        logger.error(f"Tool batching JSON error: {e}", exc_info=True)
        # Patch orphaned tool messages with error
        patch_tool_messages(f"Tool batching failed: {str(e)[:100]}...", state_manager=state_manager)
        # Re-raise to be handled by caller
        raise
    except Exception as e:
        logger.error(f"Error in process_request: {e}", exc_info=True)
        # Patch orphaned tool messages with generic error
        patch_tool_messages(
            f"Request processing failed: {str(e)[:100]}...", state_manager=state_manager
        )
        # Re-raise to be handled by caller
        raise
