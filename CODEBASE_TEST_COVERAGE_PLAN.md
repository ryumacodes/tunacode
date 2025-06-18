# TunaCode Test Coverage Plan - Path to 80% Coverage

## Current State
- Overall Coverage: 44%
- Target Coverage: 80%
- Gap to Close: 36%

## Testing Strategy

### 1. Priority Matrix (Impact vs Effort)

#### High Priority (Core Components - Low Coverage)
1. **StateManager** (`core/state.py`) - 22% → 85%
2. **Background Manager** (`core/background/manager.py`) - 0% → 80%
3. **REPL** (`cli/repl.py`) - 14% → 75%
4. **Code Index** (`core/code_index.py`) - 0% → 80%

#### Medium Priority (Important Features)
1. **UI Components** - 20-37% → 70%
   - `ui/console.py` - 37% → 70%
   - `ui/prompt.py` - 20% → 70%
   - `ui/tool_confirmation.py` - 37% → 70%
2. **Services** - Variable → 75%
   - `services/llm.py` - 73% → 85%
   - `services/mcp.py` - 49% → 75%
3. **Utils** - 0-33% → 70%
   - `utils/file.py` - 33% → 70%
   - `utils/git.py` - 0% → 70%
   - `utils/token_counter.py` - 0% → 70%

#### Lower Priority (Already Well-Tested or Less Critical)
1. **Tools** - Already 70-100%
2. **Setup** - Already 65-76%
3. **Models** - Already 79%

## Test Implementation Plan

### Phase 1: Core Components (Week 1-2)

#### 1.1 StateManager Characterization Tests
**File**: `tests/characterization/state/`
```
├── test_state_initialization.py
├── test_session_management.py
├── test_user_config.py
├── test_permissions.py
├── test_agent_tracking.py
└── test_message_history.py
```

**Key Test Cases**:
- State initialization with/without config
- Session creation and persistence
- User config loading and defaults
- Permission state transitions
- Agent instance management
- Message history operations
- Cost tracking
- Files in context management

**Quirks to Capture**:
- Singleton pattern enforcement
- Config file error handling
- Permission inheritance
- Message history mutations

#### 1.2 Background Manager Tests
**File**: `tests/characterization/background/`
```
├── test_task_creation.py
├── test_task_execution.py
├── test_task_cancellation.py
├── test_cleanup.py
└── test_edge_cases.py
```

**Key Test Cases**:
- Task submission and queuing
- Async execution patterns
- Task cancellation
- Cleanup on shutdown
- Exception handling
- Thread safety

#### 1.3 REPL Component Tests
**File**: `tests/characterization/repl/`
```
├── test_repl_initialization.py
├── test_input_handling.py
├── test_command_parsing.py
├── test_multiline_input.py
├── test_keyboard_interrupts.py
└── test_session_flow.py
```

**Key Test Cases**:
- REPL initialization
- Input validation
- Command vs message detection
- Multiline input handling
- Ctrl+C behavior
- Session state management
- Prompt generation

#### 1.4 Code Index Tests
**File**: `tests/characterization/code_index/`
```
├── test_index_building.py
├── test_file_scanning.py
├── test_symbol_extraction.py
├── test_search_operations.py
└── test_cache_management.py
```

**Key Test Cases**:
- Index building for various languages
- File filtering and ignoring
- Symbol extraction accuracy
- Search performance
- Cache invalidation
- Memory efficiency

### Phase 2: UI & Services (Week 3)

#### 2.1 UI Component Tests
**File**: `tests/characterization/ui/`
```
├── test_console_output.py
├── test_prompt_rendering.py
├── test_tool_confirmations.py
├── test_diff_display.py
└── test_async_ui.py
```

**Key Test Cases**:
- Console output formatting
- Rich markup handling
- Prompt customization
- Tool confirmation flows
- Diff generation and display
- Async UI updates

#### 2.2 Service Layer Tests
**File**: `tests/characterization/services/`
```
├── test_llm_routing.py
├── test_mcp_integration.py
├── test_error_recovery.py
└── test_service_lifecycle.py
```

**Key Test Cases**:
- LLM provider selection
- Model validation
- MCP server discovery
- MCP tool registration
- Service initialization
- Error handling and retries

### Phase 3: Utilities (Week 4)

#### 3.1 File Utilities Tests
**File**: `tests/characterization/utils/`
```
├── test_file_operations.py
├── test_git_commands.py
├── test_token_counting.py
├── test_path_handling.py
└── test_edge_cases.py
```

**Key Test Cases**:
- Safe file operations
- Path resolution
- Git command execution
- Token estimation accuracy
- Binary file detection
- Permission checks

### Phase 4: Integration Tests (Week 5)

#### 4.1 End-to-End Scenarios
**File**: `tests/integration/`
```
├── test_full_session_flow.py
├── test_multi_tool_operations.py
├── test_error_recovery_flow.py
├── test_mcp_tool_flow.py
└── test_performance_scenarios.py
```

**Key Test Cases**:
- Complete user sessions
- Multi-step operations
- Error recovery scenarios
- MCP tool integration
- Performance benchmarks

## Implementation Guidelines

### 1. Characterization Test Principles
- Capture CURRENT behavior, including bugs
- Use mocks to isolate units
- Test edge cases and error paths
- Document quirks and workarounds
- Preserve async behavior

### 2. Mock Strategy
```python
# Standard mock setup for each component
@pytest.fixture
def mock_state_manager():
    """Standard state manager mock"""
    pass

@pytest.fixture
def mock_console():
    """Mock console for UI testing"""
    pass

@pytest.fixture
def mock_llm_response():
    """Mock LLM responses"""
    pass
```

### 3. Test Data Management
- Create fixture files in `tests/fixtures/`
- Use parameterized tests for variations
- Maintain test data consistency

### 4. Coverage Monitoring
```bash
# Run coverage for specific modules
pytest tests/characterization/state/ --cov=tunacode.core.state --cov-report=html

# Monitor overall progress
pytest --cov=tunacode --cov-report=term-missing

# Generate detailed reports
pytest --cov=tunacode --cov-report=html --cov-report=term
```

## Success Metrics

### Coverage Targets by Component
| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| StateManager | 22% | 85% | High |
| Background Manager | 0% | 80% | High |
| REPL | 14% | 75% | High |
| Code Index | 0% | 80% | High |
| UI Components | 20-37% | 70% | Medium |
| Services | 49-73% | 75% | Medium |
| Utils | 0-33% | 70% | Medium |
| **Overall** | **44%** | **80%** | - |

### Test Quality Metrics
- All async functions properly tested
- Edge cases documented
- Mocks properly isolated
- No test interdependencies
- Clear test naming

## Execution Timeline

### Week 1-2: Core Components
- StateManager (3 days)
- Background Manager (2 days)
- REPL (2 days)
- Code Index (3 days)

### Week 3: UI & Services
- UI Components (3 days)
- Service Layer (2 days)

### Week 4: Utilities
- File/Git/Token utils (3 days)
- Edge cases (2 days)

### Week 5: Integration & Polish
- Integration tests (3 days)
- Coverage gaps (2 days)

## Next Steps

1. **Start with StateManager** - It's central to everything
2. **Create test structure** - Set up directories and fixtures
3. **Implement incrementally** - One component at a time
4. **Monitor progress** - Daily coverage checks
5. **Document findings** - Update this plan with discoveries

## Common Testing Patterns

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation():
    # Always use pytest-asyncio for async tests
    pass
```

### Mock Injection
```python
with patch('module.function') as mock:
    # Test with controlled behavior
    pass
```

### State Verification
```python
# Always verify state changes
assert state_manager.session.messages == expected
assert state_manager.session.iteration_count == 5
```

### Error Path Testing
```python
# Test both success and failure paths
with pytest.raises(ExpectedException):
    # Test error conditions
    pass
```

## Risk Mitigation

1. **Time Overruns**: Focus on high-impact areas first
2. **Complex Mocking**: Use integration tests where mocking is too complex
3. **Async Complexity**: Use pytest-asyncio fixtures consistently
4. **Coverage Plateau**: Accept 75% for complex UI components

## Maintenance Strategy

1. **Run tests on every PR** - GitHub Actions
2. **Monitor coverage trends** - Don't let it drop
3. **Update tests with bugs** - Add regression tests
4. **Refactor tests** - Keep them maintainable
5. **Document patterns** - Share knowledge

This plan provides a clear path from 44% to 80% coverage, focusing on the most impactful components first while maintaining test quality and documentation standards.