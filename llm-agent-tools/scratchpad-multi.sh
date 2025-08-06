#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# scratchpad-multi.sh – Multi-agent enhanced scratchpad workflow
#                      with documentation categorization
#
# Commands (with optional --agent <name>):
#   start   <task‑title>          → create/overwrite scratchpad.md
#   step    <text>|‑              → add next sequential thinking step
#   revise  <N>    <text>|‑       → attach a revision to step N
#   branch  <N>    <text>|‑       → start sub‑step N.x (branch)
#   append  <text>|‑              → raw append (fallback / free‑form)
#   status                       → show counters & last entries
#   finish  [task‑title]          → archive with categorization prompt
#   categorize                   → show documentation guidelines
#   handoff <to-agent> <message>  → handoff task to another agent
#   agents                       → list active agents
#
# Documentation structure:
# - @documentation/  → General user-facing documentation
# - @.claude/       → Developer/tunacode-specific documentation
#
# Multi-agent features:
# - Agent-specific scratchpads: .claude/scratchpad/agents/<agent>/
# - Shared memory space: .claude/scratchpad/shared/
# - File locking for concurrent access
# - Agent handoff capabilities
#
# Requires: Bash ≥ 4, coreutils, flock.
# ──────────────────────────────────────────────────────────────
set -euo pipefail

# Default configuration
BANK_DIR="${BANK_DIR:-.claude/scratchpad}"
DOC_DIR="${DOC_DIR:-documentation}"
AGENT_NAME="${AGENT_NAME:-default}"
LOCK_TIMEOUT="${LOCK_TIMEOUT:-5}"

# Parse --agent parameter
while [[ $# -gt 0 ]] && [[ "$1" =~ ^-- ]]; do
  case "$1" in
    --agent)
      AGENT_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Set up paths based on agent
AGENT_DIR="$BANK_DIR/agents/$AGENT_NAME"
SHARED_DIR="$BANK_DIR/shared"
SCRATCH="$AGENT_DIR/scratchpad.md"
LOCK_FILE="$BANK_DIR/locks/${AGENT_NAME}.lock"
# Documentation paths
GENERAL_DOC_DIR="$DOC_DIR"
DEV_DOC_DIR=".claude"

# ──────────────────────────────────────────────────────────────
usage() {
  cat >&2 <<EOF
Usage: $0 [--agent <name>] {start|step|revise|branch|append|status|finish|handoff|agents|categorize} [...]

Documentation Directories:
  @documentation/    General user-facing documentation
  @.claude/         Developer/tunacode-specific documentation

Multi-Agent Commands:
  --agent <name>                 Use agent-specific scratchpad (default: "default")

Standard Commands:
  start  <task-title>            Create/overwrite scratchpad with header
  step   <text>|-               Add next sequential step (or read STDIN)
  revise <step-no> <text>|-     Add a revision to an existing step
  branch <step-no> <text>|-     Add a branched sub‑step under <step-no>
  append <text>|-               Raw append (no numbering / validation)
  status                        Show last main/branch/revision indices
  finish [task-title]           Archive scratchpad with categorization prompt
  categorize                    Show documentation categorization guidelines

Multi-Agent Commands:
  handoff <to-agent> <message>  Hand off current task to another agent
  agents                        List all active agents with their current tasks

Examples:
  $0 --agent researcher start "Research latest AI papers"
  $0 --agent coder step "Implementing authentication module"
  $0 --agent researcher handoff coder "Research complete, please implement"
  $0 categorize                # Show where to archive documentation
  $0 finish                     # Prompts for categorization before archiving
  $0 agents
EOF
  exit 1
}

# ───────────────────── helpers ────────────────────────────
init_dirs() {
  # Check and create base directories
  if [[ ! -d "$GENERAL_DOC_DIR" ]]; then
    echo "WARNING: Documentation directory '$GENERAL_DOC_DIR' does not exist."
    echo "Please create it with: mkdir -p $GENERAL_DOC_DIR"
    echo "Creating basic structure..."
    mkdir -p "$GENERAL_DOC_DIR"/{agent,configuration,development}
  fi

  if [[ ! -d "$DEV_DOC_DIR" ]]; then
    echo "WARNING: Developer documentation directory '$DEV_DOC_DIR' does not exist."
    echo "Please create it with: mkdir -p $DEV_DOC_DIR"
    echo "Creating basic structure..."
    mkdir -p "$DEV_DOC_DIR"/{agents,scratchpad,patterns,qa}
  fi

  # Create scratchpad directories
  mkdir -p "$AGENT_DIR" "$SHARED_DIR/done_tasks" "$BANK_DIR/locks"
  mkdir -p "$DEV_DOC_DIR/scratchpad/active" "$DEV_DOC_DIR/scratchpad/archived"
}

_line() {
  if [[ $# -eq 0 || "$1" == "-" ]]; then
    cat
  else
    printf '%s\n' "$*"
  fi
}

ensure_file() {
  [[ -f "$SCRATCH" ]] || {
    echo "ERROR: No active scratchpad for agent '$AGENT_NAME'; run '$0 --agent $AGENT_NAME start' first." >&2
    exit 1
  }
}

# File locking wrapper
with_lock() {
  local lock_file="$1"
  shift

  mkdir -p "$(dirname "$lock_file")"

  # Try to acquire lock with timeout
  if command -v flock >/dev/null 2>&1; then
    flock -w "$LOCK_TIMEOUT" "$lock_file" "$@"
  else
    # Fallback for systems without flock
    "$@"
  fi
}

# Safe file operations with locking
safe_append() {
  local file="$1"
  local content="$2"
  with_lock "$LOCK_FILE" bash -c "echo '$content' >> '$file'"
}

last_main()   { grep -Po '^\[\d+\]'      "$SCRATCH" 2>/dev/null | tail -1 | tr -d '[]' || echo 0; }
last_branch() { grep -Po "^\[$1\.\d+\]" "$SCRATCH" 2>/dev/null | tail -1 | sed -E "s/^\[$1\.([0-9]+)\].*/\1/" || echo 0; }
last_rev()    { grep -Po "^\[$1~\d+\]"  "$SCRATCH" 2>/dev/null | tail -1 | sed -E "s/^\[$1~([0-9]+)\].*/\1/" || echo 0; }

# Get current task from scratchpad
get_current_task() {
  [[ -f "$SCRATCH" ]] && head -1 "$SCRATCH" | sed 's/^# //' || echo "No active task"
}

# ─────────────────────── dispatcher ───────────────────────────
cmd="${1:-}" ; shift || true
case "$cmd" in
  # ───── start ───────────────────────────────────────────────
  start)
    [[ $# -ge 1 ]] || usage
    task="$*"
    init_dirs

    with_lock "$LOCK_FILE" bash -c "cat > '$SCRATCH' <<EOF
# $task
_Started: $(date '+%Y-%m-%d %H:%M:%S')_
_Agent: $AGENT_NAME

EOF"

    echo "Agent '$AGENT_NAME' started task: $task"
    ;;

  # ───── step ────────────────────────────────────────────────
  step)
    ensure_file
    next=$(( $(last_main) + 1 ))
    content=$(_line "$@" | sed "s/^/[${next}] /")
    safe_append "$SCRATCH" "$content"
    echo "Added step $next"
    ;;

  # ───── revise ──────────────────────────────────────────────
  revise)
    ensure_file
    [[ $# -ge 2 ]] || usage
    target="$1" ; shift
    [[ "$target" =~ ^[0-9]+$ ]] || { echo "Invalid step number '$target'." >&2; exit 1; }
    grep -q "^\[$target\]" "$SCRATCH" || { echo "Step $target not found." >&2; exit 1; }
    r=$(( $(last_rev "$target") + 1 ))
    content=$(_line "$@" | sed "s/^/[${target}~${r}] /")
    safe_append "$SCRATCH" "$content"
    echo "Added revision ${target}~${r}"
    ;;

  # ───── branch ──────────────────────────────────────────────
  branch)
    ensure_file
    [[ $# -ge 2 ]] || usage
    parent="$1" ; shift
    [[ "$parent" =~ ^[0-9]+$ ]] || { echo "Invalid step number '$parent'." >&2; exit 1; }
    grep -q "^\[$parent\]" "$SCRATCH" || { echo "Step $parent not found." >&2; exit 1; }
    b=$(( $(last_branch "$parent") + 1 ))
    content=$(_line "$@" | sed "s/^/[${parent}.${b}] /")
    safe_append "$SCRATCH" "$content"
    echo "Added branch ${parent}.${b}"
    ;;

  # ───── append (raw) ────────────────────────────────────────
  append)
    ensure_file
    content=$(_line "$@")
    safe_append "$SCRATCH" "$content"
    ;;

  # ───── status ──────────────────────────────────────────────
  status)
    ensure_file
    echo "Agent: $AGENT_NAME"
    echo "Task: $(get_current_task)"
    echo "Latest main step : $(last_main)"
    if [[ $(last_main) -gt 0 ]]; then
      echo "Latest branches  :"
      while read -r step; do
        lastb=$(last_branch "$step")
        [[ $lastb -gt 0 ]] && printf "  • %s → %s\n" "$step" "$step.$lastb"
      done < <(grep -Po '^\[\d+\]' "$SCRATCH" 2>/dev/null | tr -d '[]' | sort -un)
      echo "Latest revisions :"
      while read -r step; do
        lastr=$(last_rev "$step")
        [[ $lastr -gt 0 ]] && printf "  • %s → %s~%s\n" "$step" "$step" "$lastr"
      done < <(grep -Po '^\[\d+\]' "$SCRATCH" 2>/dev/null | tr -d '[]' | sort -un)
    fi
    ;;

  # ───── finish ──────────────────────────────────────────────
  finish)
    ensure_file
    ts="$(date '+%Y-%m-%d_%H%M%S')"
    title="${1:-$(get_current_task)}"
    safe_title="${title// /_}"
    out="${AGENT_NAME}_${safe_title}_${ts}_scratchpad.md"

    # Ask for categorization
    echo ""
    echo "Where should this documentation be archived?"
    echo "1) General documentation (@documentation/) - for user-facing docs"
    echo "2) Developer documentation (@.claude/) - for tunacode development docs"
    echo "3) Both locations"
    echo ""
    read -p "Select (1/2/3): " choice

    case "$choice" in
      1)
        # Determine subdirectory for general documentation
        echo ""
        echo "Select category for general documentation:"
        echo "a) agent - Agent-related documentation"
        echo "c) configuration - Configuration documentation"
        echo "d) development - Development practices"
        echo "o) other - Create in root documentation directory"
        read -p "Select (a/c/d/o): " subchoice

        case "$subchoice" in
          a) target_dir="$GENERAL_DOC_DIR/agent" ;;
          c) target_dir="$GENERAL_DOC_DIR/configuration" ;;
          d) target_dir="$GENERAL_DOC_DIR/development" ;;
          *) target_dir="$GENERAL_DOC_DIR" ;;
        esac

        mkdir -p "$target_dir"
        with_lock "$LOCK_FILE" cp "$SCRATCH" "$target_dir/$out"
        echo "Documentation archived to: $target_dir/$out"
        ;;

      2)
        # Archive to developer documentation
        target_dir="$DEV_DOC_DIR/scratchpad/archived"
        mkdir -p "$target_dir"
        with_lock "$LOCK_FILE" cp "$SCRATCH" "$target_dir/$out"
        echo "Developer documentation archived to: $target_dir/$out"
        ;;

      3)
        # Archive to both locations
        echo "Archiving to both locations..."

        # First to general documentation
        echo ""
        echo "Select category for general documentation:"
        echo "a) agent - Agent-related documentation"
        echo "c) configuration - Configuration documentation"
        echo "d) development - Development practices"
        echo "o) other - Create in root documentation directory"
        read -p "Select (a/c/d/o): " subchoice

        case "$subchoice" in
          a) target_dir="$GENERAL_DOC_DIR/agent" ;;
          c) target_dir="$GENERAL_DOC_DIR/configuration" ;;
          d) target_dir="$GENERAL_DOC_DIR/development" ;;
          *) target_dir="$GENERAL_DOC_DIR" ;;
        esac

        mkdir -p "$target_dir"
        with_lock "$LOCK_FILE" cp "$SCRATCH" "$target_dir/$out"
        echo "Documentation archived to: $target_dir/$out"

        # Then to developer documentation
        target_dir="$DEV_DOC_DIR/scratchpad/archived"
        mkdir -p "$target_dir"
        with_lock "$LOCK_FILE" cp "$SCRATCH" "$target_dir/$out"
        echo "Developer documentation archived to: $target_dir/$out"
        ;;

      *)
        echo "Invalid choice. Archiving to default location..."
        target_dir="$DEV_DOC_DIR/scratchpad/archived"
        mkdir -p "$target_dir"
        with_lock "$LOCK_FILE" cp "$SCRATCH" "$target_dir/$out"
        echo "Documentation archived to: $target_dir/$out"
        ;;
    esac

    # Always keep a backup in shared done_tasks
    mkdir -p "$SHARED_DIR/done_tasks"
    with_lock "$LOCK_FILE" mv "$SCRATCH" "$SHARED_DIR/done_tasks/$out"
    echo "Backup kept in: $SHARED_DIR/done_tasks/$out"
    ;;

  # ───── handoff ─────────────────────────────────────────────
  handoff)
    ensure_file
    [[ $# -ge 2 ]] || usage
    to_agent="$1"
    shift
    message="$*"

    # Create handoff record
    handoff_file="$SHARED_DIR/handoffs/${AGENT_NAME}_to_${to_agent}_$(date +%s).md"
    mkdir -p "$SHARED_DIR/handoffs"

    with_lock "$LOCK_FILE" bash -c "
      echo '# Handoff from $AGENT_NAME to $to_agent' > '$handoff_file'
      echo '_Time: $(date '+%Y-%m-%d %H:%M:%S')_' >> '$handoff_file'
      echo '' >> '$handoff_file'
      echo '## Message' >> '$handoff_file'
      echo '$message' >> '$handoff_file'
      echo '' >> '$handoff_file'
      echo '## Current Scratchpad' >> '$handoff_file'
      cat '$SCRATCH' >> '$handoff_file'

      # Copy scratchpad to target agent
      mkdir -p '$BANK_DIR/agents/$to_agent'
      cp '$SCRATCH' '$BANK_DIR/agents/$to_agent/scratchpad.md'

      # Archive current agent's scratchpad
      mv '$SCRATCH' '${SCRATCH}.handed_off_$(date +%s)'
    "

    echo "Task handed off from '$AGENT_NAME' to '$to_agent'"
    echo "Handoff record: $handoff_file"
    ;;

  # ───── agents ──────────────────────────────────────────────
  agents)
    echo "Active Agents:"
    echo ""

    if [[ -d "$BANK_DIR/agents" ]]; then
      for agent_dir in "$BANK_DIR/agents"/*; do
        if [[ -d "$agent_dir" ]]; then
          agent=$(basename "$agent_dir")
          if [[ -f "$agent_dir/scratchpad.md" ]]; then
            task=$(head -1 "$agent_dir/scratchpad.md" 2>/dev/null | sed 's/^# //')
            echo "• $agent: $task"
          else
            echo "• $agent: (no active task)"
          fi
        fi
      done
    else
      echo "(No agents found)"
    fi

    # Show recent handoffs
    if [[ -d "$SHARED_DIR/handoffs" ]] && [[ -n "$(ls -A "$SHARED_DIR/handoffs" 2>/dev/null)" ]]; then
      echo ""
      echo "Recent Handoffs:"
      ls -t "$SHARED_DIR/handoffs" | head -5 | while read -r handoff; do
        echo "  - $handoff"
      done
    fi
    ;;

  # ───── categorize ──────────────────────────────────────────
  categorize)
    echo "Documentation Categorization Guidelines:"
    echo ""
    echo "=== General Documentation (@documentation/) ==="
    echo "For user-facing documentation that helps understand and use the codebase:"
    echo ""
    echo "• agent/ - Agent architecture, workflows, tool usage patterns"
    echo "  - How agents work and interact"
    echo "  - Agent design patterns and best practices"
    echo "  - Tool workflow documentation"
    echo ""
    echo "• configuration/ - Setup and configuration guides"
    echo "  - Installation instructions"
    echo "  - Configuration file documentation"
    echo "  - Environment setup guides"
    echo ""
    echo "• development/ - Development practices and guidelines"
    echo "  - Coding standards and conventions"
    echo "  - Testing strategies"
    echo "  - Contribution guidelines"
    echo ""
    echo "=== Developer Documentation (@.claude/) ==="
    echo "For tunacode-specific development and internal documentation:"
    echo ""
    echo "• agents/ - Agent implementation details"
    echo "• scratchpad/ - Work-in-progress documentation"
    echo "• patterns/ - Code patterns and templates"
    echo "• qa/ - Quality assurance and testing docs"
    echo "• delta/ - Change logs and migration guides"
    echo "• metadata/ - System metadata and configurations"
    echo ""
    echo "=== Quick Decision Guide ==="
    echo "Ask yourself:"
    echo "1. Is this for end users of the codebase? → @documentation/"
    echo "2. Is this for tunacode developers/agents? → @.claude/"
    echo "3. Does it explain HOW to use something? → @documentation/"
    echo "4. Does it explain HOW something works internally? → @.claude/"
    echo ""
    echo "When in doubt, choose @documentation/ for broader accessibility."
    ;;

  *) usage ;;
esac
