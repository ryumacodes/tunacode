<!-- This document provides API documentation for core components: StateManager, Agent system, ToolHandler, and Setup -->

# Core API Reference

This document provides detailed API documentation for TunaCode's core components.

## StateManager

`tunacode.core.state.StateManager`

Central state management for TunaCode sessions.

### Class Definition

```python
class StateManager:
    """Manages all application state in a centralized location."""

    def __init__(self) -> None:
        """Initialize state manager with default values."""
```

### Properties

```python
@property
def state(self) -> SessionState:
    """Get the current session state."""
    return self._state
```

### Methods

#### get_model()
```python
def get_model(self) -> Optional[str]:
    """
    Get the current model identifier.

    Returns:
        Optional[str]: Model in 'provider:model' format, or None

    Example:
        >>> state.get_model()
        'anthropic:claude-3-5-sonnet-20241022'
    """
```

#### set_model()
```python
def set_model(self, model: str) -> None:
    """
    Set the model override.

    Args:
        model: Model identifier in 'provider:model' format

    Example:
        >>> state.set_model('openai:gpt-4o')
    """
```

#### update_config()
```python
def update_config(self, updates: Dict[str, Any]) -> None:
    """
    Update configuration and persist to disk.

    Args:
        updates: Dictionary of configuration updates

    Example:
        >>> state.update_config({'streaming': False})
    """
```

#### add_message()
```python
def add_message(self, message: Message) -> None:
    """
    Add a message to conversation history.

    Args:
        message: Message object to add

    Note:
        Automatically tracks token usage and assistant responses.
    """
```

#### estimate_tokens_in_messages()
```python
def estimate_tokens_in_messages(self) -> int:
    """
    Estimate total tokens in conversation history.

    Returns:
        int: Estimated token count

    Example:
        >>> tokens = state.estimate_tokens_in_messages()
        >>> print(f"Using {tokens} tokens")
    """
```

#### get_agent()
```python
async def get_agent(self, model: Optional[str] = None) -> Any:
    """
    Get or create agent instance for model.

    Args:
        model: Optional model override

    Returns:
        Pydantic AI agent instance

    Note:
        Agents are cached per model for performance.
    """
```

### SessionState

`tunacode.core.state.SessionState`

```python
@dataclass
class SessionState:
    """Comprehensive session state container."""

    # Configuration
    user_config: Dict[str, Any]
    default_model: Optional[str]
    model_override: Optional[str]
    api_keys: Dict[str, Optional[str]]

    # Agent state
    agent_instances: Dict[str, Any]
    registry: Optional[CommandRegistry]
    mcp_manager: Optional[MCPManager]
    tools: List[Any]
    allowed_tools: Set[str]

    # Conversation
    messages: List[Message]
    last_assistant_message: Optional[str]

    # UI state
    streaming_panel: Optional[Any]
    is_streaming: bool
    yolo_mode: bool
    show_thoughts: bool

    # Usage tracking
    total_tokens_used: int
    total_cost: float
    context_window: int
    max_response_tokens: int
    max_iterations: Optional[int]

    # Execution context
    in_sub_agent: bool
    top_level_iterations_used: int
    top_level_max_iterations: int

    # Task management
    current_task: Optional[asyncio.Task]
    task_cancelled: bool
    code_base_path: Optional[Path]
```

## Agent System

### process_request()

`tunacode.core.agents.main.process_request`

```python
async def process_request(
    request: str,
    state: StateManager,
    process_request_callback: Optional[Callable] = None,
    is_template: bool = False
) -> str:
    """
    Process a user request through the agent.

    Args:
        request: User's request text
        state: Current state manager
        process_request_callback: Optional callback for recursive requests
        is_template: Whether this is a template request

    Returns:
        str: Agent's response

    Raises:
        Exception: Various exceptions based on processing errors

    Example:
        >>> response = await process_request(
        ...     "Write a hello world function",
        ...     state_manager
        ... )
    """
```

### create_agent()

`tunacode.core.agents.main.create_agent`

```python
async def create_agent(
    state: StateManager,
    model: Optional[str] = None
) -> Agent:
    """
    Create a pydantic-ai agent with tools.

    Args:
        state: State manager instance
        model: Optional model override

    Returns:
        Agent: Configured agent instance

    Example:
        >>> agent = await create_agent(state, "openai:gpt-4")
    """
```

## Tool Handler

`tunacode.core.tool_handler.ToolHandler`

```python
class ToolHandler:
    """Manages tool execution and permissions."""

    def __init__(
        self,
        ui: UIProtocol,
        state: StateManager,
        process_request_callback: Optional[Callable] = None
    ):
        """
        Initialize tool handler.

        Args:
            ui: UI protocol implementation
            state: State manager
            process_request_callback: Optional callback
        """
```

### Methods

#### get_tools()
```python
def get_tools(self) -> List[Any]:
    """
    Get all available tools.

    Returns:
        List[Any]: List of tool instances
    """
```

#### check_tool_permission()
```python
async def check_tool_permission(
    self,
    tool_name: str,
    args: Dict[str, Any]
) -> bool:
    """
    Check if tool execution is permitted.

    Args:
        tool_name: Name of the tool
        args: Tool arguments

    Returns:
        bool: Whether tool can execute

    Note:
        Checks YOLO mode, allowed tools, and user confirmation.
    """
```

#### execute_tool()
```python
async def execute_tool(
    self,
    tool_name: str,
    args: Dict[str, Any]
) -> str:
    """
    Execute a tool with permission checking.

    Args:
        tool_name: Name of the tool
        args: Tool arguments

    Returns:
        str: Tool execution result

    Raises:
        ModelRetry: If tool execution should be retried
    """
```

## Background Task Manager

`tunacode.core.background.manager.BackgroundTaskManager`

```python
class BackgroundTaskManager:
    """Manages background asyncio tasks."""

    def __init__(self):
        """Initialize task manager."""
        self.tasks: List[asyncio.Task] = []
        self.shutdown_handlers: List[Callable] = []
```

### Methods

#### create_task()
```python
async def create_task(self, coro: Coroutine) -> asyncio.Task:
    """
    Create and track a background task.

    Args:
        coro: Coroutine to run

    Returns:
        asyncio.Task: Created task

    Example:
        >>> task = await manager.create_task(
        ...     long_running_operation()
        ... )
    """
```

#### add_shutdown_handler()
```python
def add_shutdown_handler(self, handler: Callable) -> None:
    """
    Add a shutdown handler.

    Args:
        handler: Async function to call on shutdown
    """
```

#### shutdown()
```python
async def shutdown(self) -> None:
    """
    Gracefully shutdown all tasks.

    Note:
        Calls all shutdown handlers and cancels tasks.
    """
```

## Setup System

### SetupCoordinator

`tunacode.core.setup.coordinator.SetupCoordinator`

```python
class SetupCoordinator:
    """Coordinates application setup steps."""

    def __init__(self, ui: UIProtocol):
        """
        Initialize coordinator.

        Args:
            ui: UI protocol implementation
        """
```

#### run()
```python
async def run(self) -> StateManager:
    """
    Run all setup steps.

    Returns:
        StateManager: Configured state manager

    Raises:
        SetupError: If setup fails

    Example:
        >>> coordinator = SetupCoordinator(ui)
        >>> state = await coordinator.run()
    """
```

### BaseSetup

`tunacode.core.setup.base.BaseSetup`

```python
class BaseSetup(ABC):
    """Base class for setup steps."""

    @abstractmethod
    async def should_run(self, context: SetupContext) -> bool:
        """Check if this step should run."""

    @abstractmethod
    async def run(self, context: SetupContext) -> SetupResult:
        """Execute the setup step."""

    @abstractmethod
    def description(self) -> str:
        """Get step description."""
```

## Token Usage Tracking

### UsageTracker

`tunacode.core.token_usage.usage_tracker.UsageTracker`

```python
class UsageTracker:
    """Track token usage and costs."""

    def __init__(self, model: str):
        """
        Initialize tracker.

        Args:
            model: Model identifier
        """
```

#### update_usage()
```python
def update_usage(
    self,
    response: Any,
    model: Optional[str] = None
) -> None:
    """
    Update usage from API response.

    Args:
        response: API response object
        model: Optional model override
    """
```

#### get_usage_string()
```python
def get_usage_string(self) -> str:
    """
    Get formatted usage string.

    Returns:
        str: Formatted usage information

    Example:
        >>> tracker.get_usage_string()
        'Tokens: 1,234 (≈$0.0037) | Total: 12,345 (≈$0.0370)'
    """
```

## Logging System

### get_logger()

`tunacode.core.logging.logger.get_logger`

```python
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Configured logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting operation")
    """
```

### setup_logging()

`tunacode.core.logging.config.setup_logging`

```python
def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None
) -> None:
    """
    Configure logging system.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path

    Example:
        >>> setup_logging("DEBUG", Path("app.log"))
    """
```

## Type Definitions

### Message

`tunacode.types.Message`

```python
@dataclass
class Message:
    """Conversation message."""
    role: Literal["user", "assistant", "system", "tool"]
    content: Union[str, List[Dict[str, Any]]]
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

### UIProtocol

`tunacode.types.UIProtocol`

```python
class UIProtocol(Protocol):
    """Protocol for UI implementations."""

    async def info(self, message: str) -> None: ...
    async def warning(self, message: str) -> None: ...
    async def error(self, message: str) -> None: ...
    async def success(self, message: str) -> None: ...
    async def debug(self, message: str) -> None: ...
    async def show_spinner(self, message: str) -> Any: ...
    async def hide_spinner(self) -> None: ...
```

## Error Types

### ModelRetry

`pydantic_ai.ModelRetry`

```python
class ModelRetry(Exception):
    """
    Indicates the agent should retry with different parameters.

    Example:
        >>> if not valid_input:
        ...     raise ModelRetry("Please provide valid input")
    """
```

### Custom Exceptions

`tunacode.exceptions`

```python
class TunaCodeError(Exception):
    """Base exception for TunaCode."""

class ConfigurationError(TunaCodeError):
    """Configuration-related errors."""

class ToolExecutionError(TunaCodeError):
    """Tool execution errors."""

class StateError(TunaCodeError):
    """State management errors."""
```
