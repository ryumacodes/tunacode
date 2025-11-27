---
title: "Recovery Status Notification Plan"
phase: Plan
date: "2025-11-20T11:46:00Z"
owner: "Context Engineer Agent"
parent_research: "memory-bank/research/2025-11-20_error_signaling_gaps_analysis.md"
git_commit_at_plan: "36f9c6f"
tags: [plan, recovery-notifications, error-awareness, rich-ui]
---

## Goal
Implement user notifications for automatic error recovery events so users know when the system has recovered from errors, ensuring transparency about silent recovery operations.

## Scope & Assumptions
- **In Scope**: Recovery success/failure notifications with rich formatting
- **In Scope**: Error aggregation for multiple related recovery events
- **In Scope**: Debug mode for detailed recovery visibility
- **Out of Scope**: Rate limit specific handling (covered in separate plan)
- **Out of Scope**: Main exception handler changes
- **Assumptions**: Recovery system already works technically
- **Constraints**: Must maintain existing recovery success behavior

## Deliverables (DoD)
- **Recovery Notifications**: Users informed when automatic recovery occurs
- **Error Aggregation**: Multiple recovery events grouped intelligently
- **Debug Mode**: Optional detailed recovery information display
- **Rich Formatting**: Use existing Rich library and panel system
- **One Integration Test**: Validates recovery notification flow

## Readiness (DoD)
- ✅ Research confirms recovery happens silently (success masks problems)
- ✅ Error recovery system exists in `repl_components/error_recovery.py`
- ✅ UI system has rich formatting capabilities available
- ✅ Recovery system already has success/failure states
- ✅ All required UI infrastructure (panels, colors) exists

## Milestones

### M1: Recovery Notification Framework
- Add user-facing recovery status messages
- Create recovery message templates with rich formatting
- Design error aggregation logic for related events

### M2: Rich Display Implementation
- Implement rich panels for recovery notifications
- Add error aggregation display with counts and context
- Integrate with existing spinner and status systems

### M3: Debug Mode & Testing
- Add optional debug mode for detailed recovery visibility
- Create integration test for recovery notification scenarios
- Add configuration for notification verbosity levels

## Work Breakdown (Tasks)

### T001: Add Recovery Status Messages
**Owner**: Context Engineer
**Estimate**: 1 hour
**Dependencies**: None
**Target Milestone**: M1

**Acceptance Tests**:
- Recovery attempts trigger user notification via ui.warning()
- Recovery success shows original error context
- Recovery failure includes troubleshooting suggestions
- Messages use consistent formatting and tone

**Files/Interfaces**:
- `src/tunacode/cli/repl_components/error_recovery.py:131-153` (modify)

### T002: Create Recovery Message Templates
**Owner**: Context Engineer
**Estimate**: 1 hour
**Dependencies**: T001
**Target Milestone**: M1

**Acceptance Tests**:
- Recovery success template with original error type
- Recovery failure template with retry suggestions
- Multiple recovery template with count and frequency
- All templates use existing UI_COLORS warning theme

**Files/Interfaces**:
- `src/tunacode/ui/recovery_templates.py` (new)

### T003: Implement Error Aggregation
**Owner**: Context Engineer
**Estimate**: 2 hours
**Dependencies**: T001
**Target Milestone**: M1

**Acceptance Tests**:
- Related recovery events grouped by error type
- Aggregation tracks frequency within time windows
- Grouped notification shows count and recent examples
- Prevents notification spam for repeated recoveries

**Files/Interfaces**:
- `src/tunacode/core/error_handling/recovery_aggregator.py` (new)

### T004: Create Rich Recovery Display
**Owner**: Context Engineer
**Estimate**: 2 hours
**Dependencies**: T002, T003
**Target Milestone**: M2

**Acceptance Tests**:
- Rich panels displayed for recovery notifications
- Color scheme uses warning colors (#d97706) appropriately
- Panel includes recovery status and context information
- Formatted display integrates with existing UI flow

**Files/Interfaces**:
- `src/tunacode/ui/recovery_display.py` (new)

### T005: Integrate with Spinner System
**Owner**: Context Engineer
**Estimate**: 1 hour
**Dependencies**: T004
**Target Milestone**: M2

**Acceptance Tests**:
- Recovery notifications update spinner messages appropriately
- Spinner status reflects recovery state changes
- Recovery status integrates with existing StateManager
- No spinner conflicts during recovery operations

**Files/Interfaces**:
- Leverage existing spinner management in `ui/output.py`

### T006: Add Debug Mode
**Owner**: Context Engineer
**Estimate**: 1 hour
**Dependencies**: T004
**Target Milestone**: M3

**Acceptance Tests**:
- Debug mode shows all recovery events with details
- Debug information includes stack traces and recovery timing
- Production mode shows only user-friendly recovery summaries
- Debug toggle works dynamically without restart

**Files/Interfaces**:
- `src/tunacore/configuration/defaults.py` (add debug_recovery_mode)

### T007: Create Integration Test
**Owner**: Context Engineer
**Estimate**: 2 hours
**Dependencies**: T004, T005
**Target Milestone**: M3

**Acceptance Tests**:
- Test simulates multiple recovery scenarios
- Validates rich recovery message content and formatting
- Tests error aggregation for repeated events
- Verifies debug mode shows detailed information

**Files/Interfaces**:
- `tests/test_recovery_notifications.py` (new)

### T008: Add Configuration Options
**Owner**: Context Engineer
**Estimate**: 1 hour
**Dependencies**: T007
**Target Milestone**: M3

**Acceptance Tests**:
- Configuration option for recovery notification level
- Silent mode maintains existing behavior (no notifications)
- Verbose mode includes detailed recovery information
- Default mode shows user-friendly recovery summaries

**Files/Interfaces**:
- `src/tunacode/configuration/key_descriptions.py` (add recovery_verbosity)

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Recovery notifications create notification spam | Medium | Medium | Error aggregation prevents repeated notifications | User complaints during testing |
| Debug mode exposes sensitive information | High | Low | Sanitize debug output, make debug opt-in | Security review findings |
| Recovery display interferes with ongoing operations | Medium | Low | Non-blocking display, integrates with existing UI | UI conflicts during testing |
| Performance overhead from aggregation tracking | Low | Low | Efficient time-window tracking, cleanup old data | Performance tests show degradation |

## Test Strategy
**Single Integration Test**: `tests/test_recovery_notifications.py` will simulate multiple error recovery scenarios, validate rich recovery message formatting, test error aggregation for repeated events, and verify debug mode shows appropriate detail level. This focused approach ensures recovery notifications work correctly without over-testing.

## References
- Research: `memory-bank/research/2025-11-20_error_signaling_gaps_analysis.md`
- Recovery System: `src/tunacode/cli/repl_components/error_recovery.py:93-169`
- UI System: `src/tunacode/ui/panels.py`, `src/tunacode/ui/output.py`
- Color Theme: `src/tunacode/constants.py:109-130`
- Spinner System: Existing spinner management in `ui/output.py:135-174`

## Final Gate
**Summary**: Focused plan for implementing recovery status notifications with rich formatting and error aggregation to provide transparency about automatic recovery operations.

**Plan Path**: `memory-bank/plan/2025-11-20_recovery-notification-plan.md`
**Milestones**: 3 (Framework → Display → Testing)
**Gates**: 1 integration test validates complete recovery notification flow
**Next Command**: `/context-engineer:execute "memory-bank/plan/2025-11-20_recovery-notification-plan.md"`
