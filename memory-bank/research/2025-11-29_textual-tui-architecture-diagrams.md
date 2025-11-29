---
date: "2025-11-29T17:45:00-06:00"
researcher: claude-opus
git_commit: 1fcb170bdbe851bb455a596f702d6fe9695bc4c6
branch: textual_repl
repository: alchemiststudiosDOTai/tunacode
topic: "Textual TUI Architecture Diagrams"
tags: [research, textual, tui, architecture, mermaid, diagrams]
status: complete
---

# Textual TUI Architecture Diagrams

## 1. Widget Hierarchy

```mermaid
graph TD
    subgraph TextualReplApp
        Header[Header<br/><i>built-in</i>]
        ResourceBar[ResourceBar<br/><i>Static</i>]

        subgraph Body["Vertical #body"]
            RichLog[RichLog<br/><i>conversation history</i>]
            StreamingOutput["Static #streaming-output<br/><i>live response</i>"]
            Editor[Editor<br/><i>TextArea + completions</i>]
        end

        Footer[Footer<br/><i>built-in</i>]
    end

    Header --> ResourceBar
    ResourceBar --> Body
    Body --> Footer

    RichLog --> StreamingOutput
    StreamingOutput --> Editor

    style Header fill:#2d4461,stroke:#00d7ff
    style Footer fill:#2d4461,stroke:#00d7ff
    style ResourceBar fill:#162332,stroke:#00d7ff,color:#00d7ff
    style RichLog fill:#162332,stroke:#2d4461
    style StreamingOutput fill:#162332,stroke:#2d4461
    style Editor fill:#0d1720,stroke:#0ea5e9
```

## 2. Message Flow Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant E as Editor
    participant App as TextualReplApp
    participant Q as request_queue
    participant W as _request_worker
    participant O as Orchestrator
    participant M as Modal

    U->>E: Types input + Enter
    E->>App: EditorSubmitRequested
    App->>Q: put(text)
    App->>App: RichLog.write("> input")

    Q->>W: get()
    W->>O: process_request()

    alt Tool needs confirmation
        O->>App: tool_callback()
        App->>App: ShowToolConfirmationModal
        App->>M: push_screen()
        U->>M: Click Yes/No
        M->>App: ToolConfirmationResult
        App->>O: Future.set_result()
    end

    loop Streaming
        O->>App: streaming_callback(chunk)
        App->>App: streaming_output.update()
    end

    O->>App: Complete
    App->>App: RichLog.write(response)
    App->>App: ResourceBar.update_stats()
```

## 3. Theme & Styling Architecture

```mermaid
flowchart TB
    subgraph Source["Source of Truth"]
        UI[constants.py<br/>UI_COLORS]
    end

    subgraph ThemeLayer["Theme Layer"]
        Builder[_build_tunacode_theme<br/>textual_repl.py:221-245]
        Theme[Theme Object<br/>name='tunacode']
    end

    subgraph TextualEngine["Textual Engine"]
        ColorSystem[ColorSystem<br/>design.py]
        CSSVars["120+ CSS Variables<br/>$primary, $surface, etc."]
    end

    subgraph StyleLayer["Style Layer"]
        TCSS[textual_repl.tcss<br/>80 lines]
    end

    subgraph Widgets["Widget Rendering"]
        W1[ResourceBar]
        W2[RichLog]
        W3[Editor]
        W4[Modal]
    end

    UI -->|palette| Builder
    Builder -->|creates| Theme
    Theme -->|to_color_system| ColorSystem
    ColorSystem -->|generates| CSSVars
    CSSVars -->|consumed by| TCSS
    TCSS -->|styles| W1
    TCSS -->|styles| W2
    TCSS -->|styles| W3
    TCSS -->|styles| W4

    style UI fill:#00d7ff,stroke:#0095b3,color:#0d1720
    style Theme fill:#0ea5e9,stroke:#0095b3,color:#fff
    style CSSVars fill:#4de4ff,stroke:#00d7ff,color:#0d1720
```

## 4. UI_COLORS Mapping

```mermaid
flowchart LR
    subgraph UI_COLORS["UI_COLORS (constants.py)"]
        primary["primary<br/>#00d7ff"]
        primary_light["primary_light<br/>#4de4ff"]
        primary_dark["primary_dark<br/>#0095b3"]
        accent["accent<br/>#0ea5e9"]
        background["background<br/>#0d1720"]
        surface["surface<br/>#162332"]
        border["border<br/>#2d4461"]
        border_light["border_light<br/>#1e2d3f"]
        muted["muted<br/>#6b8aa3"]
        success["success<br/>#059669"]
        warning["warning<br/>#d97706"]
        error["error<br/>#dc2626"]
    end

    subgraph ThemeProps["Theme Properties"]
        T_primary[primary]
        T_accent[accent]
        T_boost[boost]
        T_secondary[secondary]
        T_background[background]
        T_surface[surface]
        T_panel[panel]
        T_foreground[foreground]
        T_success[success]
        T_warning[warning]
        T_error[error]
    end

    subgraph CustomVars["Custom Variables"]
        V_textmuted[text-muted]
        V_border[border]
        V_borderlight[border-light]
    end

    primary --> T_primary
    primary_light --> T_accent
    primary_dark --> T_boost
    accent --> T_secondary
    background --> T_background
    surface --> T_surface
    border_light --> T_panel
    primary_light --> T_foreground
    success --> T_success
    warning --> T_warning
    error --> T_error

    muted --> V_textmuted
    border --> V_border
    border_light --> V_borderlight

    style primary fill:#00d7ff,color:#0d1720
    style surface fill:#162332,color:#fff
    style background fill:#0d1720,color:#fff
```

## 5. Current vs Unified Style Architecture

```mermaid
flowchart TB
    subgraph Current["Current State (Mixed)"]
        direction TB
        C_RB["ResourceBar<br/>background: #162332<br/>color: #00d7ff"]
        C_RL["RichLog<br/>background: $surface"]
        C_ED["Editor<br/>border: solid $accent"]
    end

    subgraph Unified["Unified Target"]
        direction TB
        U_RB["ResourceBar<br/>background: $surface<br/>color: $primary"]
        U_RL["RichLog<br/>background: $surface"]
        U_ED["Editor<br/>border: solid $accent"]
    end

    Current -->|"Replace hardcoded<br/>with theme vars"| Unified

    style C_RB fill:#dc2626,stroke:#fff,color:#fff
    style C_RL fill:#059669,stroke:#fff,color:#fff
    style C_ED fill:#059669,stroke:#fff,color:#fff
    style U_RB fill:#059669,stroke:#fff,color:#fff
    style U_RL fill:#059669,stroke:#fff,color:#fff
    style U_ED fill:#059669,stroke:#fff,color:#fff
```

## 6. Complete System Overview

```mermaid
graph TB
    subgraph Entry["Entry Point"]
        CLI[run_textual_repl]
    end

    subgraph App["TextualReplApp"]
        subgraph State["App State"]
            SM[state_manager]
            RQ[request_queue]
            PC[pending_confirmation]
            SS[streaming state]
        end

        subgraph UI["Widget Tree"]
            H[Header]
            RB[ResourceBar]
            B["#body"]
            F[Footer]
        end

        subgraph Messages["Message Types"]
            M1[EditorSubmitRequested]
            M2[EditorCompletionsAvailable]
            M3[ShowToolConfirmationModal]
            M4[ToolConfirmationResult]
        end

        subgraph Handlers["Message Handlers"]
            H1[on_editor_submit_requested]
            H2[on_editor_completions_available]
            H3[on_show_tool_confirmation_modal]
            H4[on_tool_confirmation_result]
        end

        subgraph Workers["Background Workers"]
            RW[_request_worker]
        end
    end

    subgraph Core["Core Layer"]
        PR[process_request]
        TH[ToolHandler]
    end

    subgraph Theme["Theming"]
        UC[UI_COLORS]
        TT[tunacode Theme]
        TC[textual_repl.tcss]
    end

    CLI --> App
    SM --> RW
    RQ --> RW
    RW --> PR
    PR --> TH

    M1 --> H1
    M2 --> H2
    M3 --> H3
    M4 --> H4

    UC --> TT
    TT --> TC
    TC --> UI

    style Entry fill:#00d7ff,stroke:#0095b3,color:#0d1720
    style App fill:#162332,stroke:#2d4461
    style Core fill:#0d1720,stroke:#2d4461
    style Theme fill:#0ea5e9,stroke:#00d7ff
```

## 7. Current vs Target File Architecture

```mermaid
flowchart LR
    subgraph Current["Current: Junk Drawer"]
        TR[textual_repl.py<br/>478 lines]
        TR --> C1[Theme builder]
        TR --> C2[Path completion]
        TR --> C3[Command names]
        TR --> C4[ResourceBar]
        TR --> C5[Editor]
        TR --> C6[Modal]
        TR --> C7[Messages]
        TR --> C8[App]
        TR --> C9[Callback factory]
    end

    subgraph Target["Target: Separated Concerns"]
        direction TB
        subgraph Constants["constants.py"]
            T1[UI_COLORS]
            T2[build_tunacode_theme]
        end
        subgraph CLI["cli/"]
            T3[widgets.py<br/>ResourceBar, Editor]
            T4[screens.py<br/>ToolConfirmationModal]
            T5[textual_repl.py<br/>App + Messages only]
        end
        subgraph Core["core/"]
            T6[tool_handler.py<br/>+ callback factory]
        end
        subgraph UI["ui/"]
            T7[completers.py<br/>consolidated]
        end
    end

    Current -->|refactor| Target

    style TR fill:#dc2626,stroke:#fff,color:#fff
    style T5 fill:#059669,stroke:#fff,color:#fff
```

## 8. Binding Architecture

```mermaid
flowchart TB
    subgraph AppBindings["App-Level Bindings"]
        B1["ctrl+p → action_toggle_pause<br/>'Pause/Resume Stream'"]
    end

    subgraph EditorBindings["Editor Bindings"]
        B2["tab → action_complete<br/>'Complete' (hidden)"]
        B3["enter → action_submit<br/>'Submit' (hidden)"]
    end

    subgraph CustomKeyHandling["Custom Key Handler (on_key)"]
        K1["escape → set _awaiting_escape_enter"]
        K2["escape+enter → insert newline"]
        K3["enter alone → trigger submit"]
    end

    AppBindings --> TextualReplApp
    EditorBindings --> Editor
    CustomKeyHandling --> Editor

    style AppBindings fill:#00d7ff,stroke:#0095b3,color:#0d1720
    style EditorBindings fill:#0ea5e9,stroke:#00d7ff,color:#fff
    style CustomKeyHandling fill:#162332,stroke:#2d4461,color:#fff
```
