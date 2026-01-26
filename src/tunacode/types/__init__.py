"""Centralized type definitions for TunaCode CLI.

This package contains all type aliases, protocols, and type definitions
used throughout the TunaCode codebase.

All types are re-exported from this module for backward compatibility.
"""

# Base types
from tunacode.types.base import (
    AgentConfig,
    AgentName,
    CommandArgs,
    CommandResult,
    ConfigFile,
    ConfigPath,
    CostAmount,
    DiffHunk,
    DiffLine,
    EnvConfig,
    ErrorContext,
    ErrorMessage,
    FileContent,
    FileDiff,
    FileEncoding,
    FilePath,
    FileSize,
    InputSessions,
    LineNumber,
    ModelName,
    OriginalError,
    SessionId,
    TokenCount,
    ToolArgs,
    ToolCallId,
    ToolName,
    ToolResult,
    UpdateOperation,
    UserConfig,
    ValidationResult,
    Validator,
)

# Callback types
from tunacode.types.callbacks import (
    AsyncFunc,
    AsyncToolFunc,
    AsyncVoidFunc,
    NoticeCallback,
    PlanApprovalCallback,
    ProcessRequestCallback,
    StreamingCallback,
    ToolCallback,
    ToolProgress,
    ToolProgressCallback,
    ToolResultCallback,
    ToolStartCallback,
    UICallback,
    UIInputCallback,
)

# Canonical types (new - see docs/refactoring/architecture-refactor-plan.md)
from tunacode.types.canonical import (
    CanonicalMessage,
    CanonicalPart,
    CanonicalToolCall,
    MessageRole,
    PartKind,
    RecursiveContext,
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ThoughtPart,
    ToolCallStatus,
    UsageMetrics,
)
from tunacode.types.canonical import (
    ToolCallPart as CanonicalToolCallPart,
)
from tunacode.types.canonical import (
    ToolReturnPart as CanonicalToolReturnPart,
)

# Dataclasses
from tunacode.types.dataclasses import (
    AgentState,
    CommandContext,
    CostBreakdown,
    ModelConfig,
    ModelPricing,
    ModelRegistry,
    ResponseState,
    TokenUsage,
    ToolConfirmationRequest,
    ToolConfirmationResponse,
)

# Pydantic-AI wrappers
from tunacode.types.pydantic_ai import (
    AgentResponse,
    AgentRun,
    MessageHistory,
    MessagePart,
    ModelRequest,
    ModelResponse,
    NormalizedUsage,
    PydanticAgent,
    normalize_request_usage,
)

# State protocol
from tunacode.types.state import (
    AuthorizationProtocol,
    AuthorizationSessionProtocol,
    AuthorizationToolHandlerProtocol,
    PlanApprovalProtocol,
    PlanSessionProtocol,
    SessionStateProtocol,
    StateManagerProtocol,
    TemplateProtocol,
)
from tunacode.types.state_structures import (
    ConversationState,
    RuntimeState,
    TaskState,
    UsageState,
)
from tunacode.types.tool_registry import ToolCallRegistry

__all__ = [
    # Base types
    "AgentConfig",
    "AgentName",
    "CommandArgs",
    "CommandResult",
    "ConfigFile",
    "ConfigPath",
    "CostAmount",
    "DiffHunk",
    "DiffLine",
    "EnvConfig",
    "ErrorContext",
    "ErrorMessage",
    "FileContent",
    "FileDiff",
    "FileEncoding",
    "FilePath",
    "FileSize",
    "InputSessions",
    "LineNumber",
    "ModelName",
    "OriginalError",
    "SessionId",
    "TokenCount",
    "ToolArgs",
    "ToolCallId",
    "ToolName",
    "ToolResult",
    "UpdateOperation",
    "UserConfig",
    "ValidationResult",
    "Validator",
    # Pydantic-AI
    "AgentResponse",
    "AgentRun",
    "MessageHistory",
    "MessagePart",
    "ModelRequest",
    "ModelResponse",
    "NormalizedUsage",
    "PydanticAgent",
    "normalize_request_usage",
    # Callbacks
    "AsyncFunc",
    "AsyncToolFunc",
    "AsyncVoidFunc",
    "ProcessRequestCallback",
    "StreamingCallback",
    "ToolCallback",
    "ToolProgress",
    "ToolProgressCallback",
    "ToolResultCallback",
    "ToolStartCallback",
    "NoticeCallback",
    "PlanApprovalCallback",
    "UICallback",
    "UIInputCallback",
    # State
    "SessionStateProtocol",
    "StateManagerProtocol",
    "AuthorizationProtocol",
    "AuthorizationSessionProtocol",
    "AuthorizationToolHandlerProtocol",
    "PlanApprovalProtocol",
    "PlanSessionProtocol",
    "TemplateProtocol",
    "ConversationState",
    "RuntimeState",
    "TaskState",
    "UsageState",
    "ToolCallRegistry",
    # Dataclasses
    "AgentState",
    "CommandContext",
    "CostBreakdown",
    "ModelConfig",
    "ModelPricing",
    "ModelRegistry",
    "ResponseState",
    "TokenUsage",
    "ToolConfirmationRequest",
    "ToolConfirmationResponse",
    # Canonical types (new)
    "CanonicalMessage",
    "CanonicalPart",
    "CanonicalToolCall",
    "CanonicalToolCallPart",
    "CanonicalToolReturnPart",
    "MessageRole",
    "PartKind",
    "RecursiveContext",
    "RetryPromptPart",
    "SystemPromptPart",
    "TextPart",
    "ThoughtPart",
    "ToolCallStatus",
    "UsageMetrics",
]
