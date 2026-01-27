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
    StreamingCallback,
    ToolCallback,
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
    CostBreakdown,
    ModelConfig,
    ModelPricing,
    ModelRegistry,
    TokenUsage,
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
    "StreamingCallback",
    "ToolCallback",
    "ToolResultCallback",
    "ToolStartCallback",
    "NoticeCallback",
    "UICallback",
    "UIInputCallback",
    # Dataclasses
    "CostBreakdown",
    "ModelConfig",
    "ModelPricing",
    "ModelRegistry",
    "TokenUsage",
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
