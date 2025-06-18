# Project Brief

## What is this project?
TunaCode is a CLI tool that provides an AI-powered coding assistant using pydantic-ai. It offers intelligent code generation, file operations, and project management through a command-line interface.

## Why does it exist?
TunaCode solves the problem of integrating AI assistance directly into the development workflow. It provides:
- Seamless AI-powered coding assistance in the terminal
- Safe file operations with confirmation UI
- Multi-provider LLM support (Anthropic, OpenAI, Google, OpenRouter)
- Structured memory management for maintaining context across sessions

## Core requirements
- [x] AI agent system with retryable tools
- [x] File operation tools (read, write, update, bash, grep, list_dir)
- [x] Command system with REPL interface
- [x] State management for session persistence
- [x] Memory bank workflow for context preservation
- [ ] Achieve ~80% test coverage with characterization tests
- [ ] Complete refactoring safety net
