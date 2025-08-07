# ESC Key Transport Investigation
_Started: 2025-08-06 21:54:43_
_Agent: esc-investigation

[1] Pydantic-ai version: 0.2.6
[2] StreamedResponse is an abstract base class in pydantic_ai/models/__init__.py
[3] It does NOT expose any transport control methods like abort(), aclose(), or cancel()
[4] The StreamedResponse class only has: _parts_manager for managing response parts, _event_iterator for streaming events, _usage for tracking token usage, Abstract methods for model_name and timestamp
[5] No access to underlying HTTP client or transport layer
[6] The streaming happens through _get_event_iterator() which subclasses implement
[7] Vendor-specific implementations (OpenAI, Anthropic, etc.) do not expose transport either
[8] Conclusion: Pydantic-ai does NOT expose transport control, confirming the limitation mentioned in the implementation.
