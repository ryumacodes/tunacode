# TunaCode Source Directory Map

```
src/
├── __init__.py
└── tunacode/                    # Main package
    ├── __init__.py
    ├── constants.py             # Version, paths
    ├── context.py               # Context utils
    ├── exceptions.py            # Custom errors
    ├── setup.py                 # Package setup
    ├── types.py                 # Type aliases
    ├── py.typed                 # Type marker
    │
    ├── cli/                     # Command-line interface
    │   ├── __init__.py
    │   ├── commands.py          # /help, /model, etc
    │   ├── main.py              # Entry point
    │   ├── repl.py              # REPL loop
    │   ├── textual_app.py       # TUI app
    │   └── textual_bridge.py    # TUI bridge
    │
    ├── configuration/           # Config management
    │   ├── __init__.py
    │   ├── defaults.py          # Default values
    │   ├── models.py            # Config models
    │   └── settings.py          # Settings logic
    │
    ├── core/                    # Core logic
    │   ├── __init__.py
    │   ├── code_index.py        # Codebase indexing
    │   ├── state.py             # StateManager
    │   ├── tool_handler.py      # Tool execution
    │   │
    │   ├── agents/              # AI agents
    │   │   ├── __init__.py
    │   │   └── main.py          # Main agent
    │   │
    │   ├── analysis/            # Code analysis
    │   │
    │   ├── background/          # Background tasks
    │   │   ├── __init__.py
    │   │   └── manager.py       # Task manager
    │   │
    │   ├── llm/                 # LLM providers
    │   │   └── __init__.py
    │   │
    │   └── setup/               # Setup flow
    │       ├── __init__.py
    │       ├── agent_setup.py   # Agent init
    │       ├── base.py          # Base interface
    │       ├── config_setup.py  # Config setup
    │       ├── coordinator.py   # Orchestrator
    │       ├── environment_setup.py  # Env check
    │       └── git_safety_setup.py   # Git checks
    │
    ├── prompts/                 # AI prompts
    │   └── system.md            # System prompt
    │
    ├── services/                # External services
    │   ├── __init__.py
    │   └── mcp.py               # MCP protocol
    │
    ├── tools/                   # Agent tools
    │   ├── __init__.py
    │   ├── base.py              # Base classes
    │   ├── bash.py              # Bash execution
    │   ├── grep.py              # Fast search
    │   ├── list_dir.py          # Dir listing
    │   ├── read_file.py         # File reader
    │   ├── run_command.py       # Shell commands
    │   ├── update_file.py       # File updater
    │   └── write_file.py        # File writer
    │
    ├── ui/                      # User interface
    │   ├── __init__.py
    │   ├── completers.py        # Tab completion
    │   ├── console.py           # Console output
    │   ├── constants.py         # UI constants
    │   ├── decorators.py        # UI decorators
    │   ├── input.py             # Input handling
    │   ├── keybindings.py       # Keyboard shortcuts
    │   ├── lexers.py            # Syntax highlight
    │   ├── output.py            # Output format
    │   ├── panels.py            # UI panels
    │   ├── prompt_manager.py    # Prompt mgmt
    │   ├── tool_ui.py           # Tool confirms
    │   └── validators.py        # Input validate
    │
    └── utils/                   # Utilities
        ├── __init__.py
        ├── bm25.py              # BM25 search
        ├── diff_utils.py        # Diff generation
        ├── file_utils.py        # File helpers
        ├── import_cache.py      # Import cache
        ├── ripgrep.py           # Ripgrep wrap
        ├── system.py            # System info
        ├── text_utils.py        # Text process
        ├── token_counter.py     # Token count
        └── user_configuration.py # User config
```

## Key Directories

- **cli/** - User interaction layer (commands, REPL)
- **core/** - Business logic (agents, state, setup)
- **tools/** - Agent capabilities (file ops, shell)
- **ui/** - Display layer (formatting, prompts)
- **utils/** - Shared helpers (search, diff, files)