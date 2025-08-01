# TunaCode: Release, FAQ & Quick Start Guide

## What is TunaCode? (30 seconds)

**TunaCode** is an AI-powered CLI coding assistant that lives in your terminal. Think of it as having a senior developer pair programming with you, but through the command line.

### Key Advantages ✅
- **Terminal-native**: No context switching, stays in your workflow
- **Multi-model support**: Use GPT-4, Claude, Gemini, DeepSeek - whatever works best
- **Safe by default**: Shows diffs before making changes (unless you `/yolo`)
- **Context-aware**: Loads project conventions from TUNACODE.md automatically
- **Fast file operations**: 3x faster with parallel reads

### Current Limitations ⚠️
- **No streaming UI yet**: Responses appear all at once (working on it!)
- **CLI only**: No web interface or IDE plugins
- **Requires API keys**: Not self-hosted (yet)

---

## Quick Start (2 minutes)

### 1. Install (10 seconds)
```bash
pip install tunacode-cli
```

### 2. Configure (20 seconds)
Pick your favorite model:
```bash
# Option A: OpenAI
tunacode --model "openai:gpt-4.1" --key "sk-..."

# Option B: Anthropic
tunacode --model "anthropic:claude-4-sonnet-20250522" --key "sk-ant-..."

# Option C: Google
tunacode --model "google/gemini-2.5-pro" --key "..."
```

### 3. Start Coding (90 seconds)
```bash
tunacode

# Example prompts:
> "Fix the bug in auth.py where users can't log in"
> "Add comprehensive tests for the payment module"
> "Refactor this codebase to use async/await"
```

**Essential Commands:**
- `/help` - See all commands
- `/yolo` - Skip confirmations (dangerous!)
- `/model` - Switch models mid-session
- `!ls` - Run any shell command

---

## FAQ (2 minutes)

### Q: How is this different from Cursor/GitHub Copilot?
**A:** TunaCode is CLI-first. No GUI, no browser, just your terminal. Perfect for SSH sessions, server work, or if you live in tmux.

### Q: Which model should I use?
**A:** Based on extensive testing:
- **Best overall**: `google/gemini-2.5-pro`
- **Best for code**: `deepseek/deepseek-r1-0528`
- **Best value**: `openai/gpt-4.1-mini`
- **Best context**: `anthropic/claude-4-sonnet-20250522`

### Q: Is my code safe?
**A:**
- ✅ Everything stays local until you approve
- ✅ Shows diffs before file changes
- ✅ No automatic git commits
- ⚠️ Your code is sent to AI providers (OpenAI/Anthropic/etc)

### Q: Can it work with my project?
**A:** Yes! Create a `TUNACODE.md` file in your project root with:
- Coding conventions
- Architecture decisions
- Project-specific context

The AI will automatically load and follow these guidelines.

### Q: What about large codebases?
**A:** TunaCode handles large projects well:
- Parallel file reading (3x faster)
- Smart grep with 3-second timeout
- Efficient directory listing
- Context management via `/compact`

---

## Live Demo Script (30 seconds)

```bash
# 1. Start TunaCode
$ tunacode

# 2. Real-world example
> "Find all TODO comments in the codebase and create a GitHub issue for each one"

# 3. Watch it work
[TunaCode searches files, finds TODOs, creates formatted issues]

# 4. Review and confirm
[Shows diff of new issue files]
Confirm? [y/N]: y

# Done! 🎉
```

---

## One-Liner Pitch

> "TunaCode brings AI pair programming to where developers actually work - the terminal. No context switching, no browser tabs, just pure CLI productivity with any LLM you prefer."

---

## Links & Resources

- **Install**: `pip install tunacode-cli`
- **GitHub**: [github.com/larock22/tunacode](https://github.com/larock22/tunacode)
- **Issues**: [Report bugs here](https://github.com/larock22/tunacode/issues)
- **Config**: `~/.config/tunacode.json`

*Current version: 0.0.34 (December 2025)*
