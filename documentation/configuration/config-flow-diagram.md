graph TD
    %% Configuration Sources
    A[User Config File<br/>~/.config/tunacode.json] --> B[load_config()]
    C[CLI Arguments<br/>--model, --key] --> D[CLI Override Logic]
    E[Environment Variables<br/>OPENAI_API_KEY, etc.] --> F[Environment Setup]
    G[Default Config<br/>src/tunacode/configuration/defaults.py] --> H[Config Merging]

    %% Loading and Validation
    B --> I[SHA-1 Fingerprint Check]
    I --> J{Config Changed?}
    J -->|No| K[Use Cached Config]
    J -->|Yes| L[JSON Validation]
    L --> M[Merge with Defaults]
    D --> M
    M --> N[Configuration Validation]

    %% Configuration Distribution
    N --> O[StateManager.session.user_config]
    O --> P[Export Environment Variables]
    P --> Q[Agent Configuration]
    O --> R[Tool Configuration]
    O --> S[Model Selection Logic]
    O --> T[MCP Server Setup]

    %% Runtime Updates
    U[/model command] --> V{Has 'default' keyword?}
    V -->|Yes| W[set_default_model()]
    V -->|No| X[session.current_model only]
    W --> Y[save_config()]
    Y --> A
    X --> Z[Session Only - NOT PERSISTED]

    %% Tool-Specific Config Paths
    R --> AA[tool_ignore list]
    R --> BB[ripgrep settings]
    R --> CC[tool_strict_validation]
    AA --> DD[Tool Filtering]
    BB --> EE[Search Tool Config]
    CC --> FF[Parameter Validation]

    %% Agent Setup Flow
    Q --> GG[System Prompt Loading]
    Q --> HH[Tool Initialization]
    Q --> II[Model Client Setup]
    S --> II

    %% Configuration Persistence Issues
    JJ[Setup Wizard] --> KK[Interactive Config Changes]
    KK --> LL[save_config() called]
    LL --> A

    MM[Runtime Model Switch] --> X
    NN[Runtime Setting Change] --> OO{Explicit save?}
    OO -->|No| PP[Lost on Exit]
    OO -->|Yes| Y

    %% Potential Issue Points
    style Z fill:#ffcccc
    style PP fill:#ffcccc
    style X fill:#ffcccc

    %% Legend
    QQ[Legend:]
    RR[Red boxes = Config not persisted]
    SS[Normal boxes = Config persisted]
