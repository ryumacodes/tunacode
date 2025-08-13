# TunaCode Search Architecture Enhancement Plan

## Overview
This document outlines the phased implementation plan for enhancing TunaCode's search capabilities to achieve Claude Code-level performance through ripgrep integration, parallel processing, and intelligent caching.

## Implementation Status
- ✅ **Phase 1**: Foundation - Ripgrep Binary Management (COMPLETED)
- ✅ **Phase 2**: Search Tool Core Enhancements (COMPLETED)
- ✅ **Phase 3**: Glob Tool Optimization (COMPLETED)
- ⏳ **Phase 4**: Caching Layer Enhancement (PENDING)
- ✅ **Phase 5**: Tool Prompt Micro-Injection System (COMPLETED)
- ⏳ **Phase 6**: Integration and Optimization (PENDING)
- ⏳ **Phase 7**: Testing and Documentation (PENDING)

## Phase 1: Foundation - Ripgrep Binary Management ✅

### 1.1 Binary Distribution Setup ✅
- ✅ Created `vendor/ripgrep/` directory structure
- ✅ Created download script (`scripts/download_ripgrep.py`) with:
  - Platform-specific binary downloads from GitHub releases
  - SHA256 checksum verification
  - Support for all major platforms (Linux, macOS, Windows)
  - CI/CD integration ready

### 1.2 Binary Path Resolution (`src/tunacode/utils/ripgrep.py`) ✅
- ✅ Implemented platform detection logic with `get_platform_identifier()`
- ✅ Created binary path resolver with fallback chain:
  1. Environment variable override (`TUNACODE_RIPGREP_PATH`)
  2. System ripgrep (if version >= 14.0.0)
  3. Bundled ripgrep binary
  4. Python-based fallback search
- ✅ Added `@functools.lru_cache` memoization for path resolution
- ✅ Implemented `RipgrepExecutor` class with comprehensive error handling

### 1.3 Configuration Management ✅
- ✅ Added ripgrep settings to `configuration/defaults.py`:
  - `use_bundled`: Control bundled vs system binary
  - `timeout`: Configurable search timeout
  - `max_buffer_size`: 1MB output buffer limit
  - `max_results`: Result count limit
  - `enable_metrics`: Performance metrics toggle
  - `debug`: Debug logging toggle
- ✅ Implemented `RipgrepMetrics` class for performance tracking
- ✅ Added binary version checking with `_check_ripgrep_version()`

## Phase 2: Search Tool Core Enhancements ✅

### 2.1 Grep Tool Resource Management (`src/tunacode/tools/grep.py`) ✅
- ✅ Integrated `RipgrepExecutor` with grep tool
- ✅ Implemented timeout management:
  - Configurable timeout (default 10 seconds)
  - 3-second first match deadline maintained
  - `TooBroadPatternError` for slow patterns
- ✅ Added buffer limits:
  - 1MB max buffer from configuration
  - 100-result limit with proper handling
- ✅ Resource cleanup with graceful fallback to Python search
- ✅ Efficient result processing with early termination

### 2.2 Parallel Processing Architecture ✅
- ✅ ThreadPoolExecutor with 8 workers maintained
- ✅ Work distribution strategies preserved:
  - Pre-filtering with fast_glob
  - Smart strategy selection (python/ripgrep/hybrid)
- ✅ Result aggregation and deduplication in place
- ✅ First match monitoring for performance tracking

### 2.3 Context and Filtering Features ✅
- ✅ Context lines support:
  - `context_before` and `context_after` parameters
  - Context preserved in search results
- ✅ Enhanced `ResultFormatter` with multiple output modes:
  - `content`: Full results with context (default)
  - `files_with_matches`: File paths only
  - `count`: Match counts per file
  - `json`: Structured JSON output
- ✅ Regex and pattern support maintained
- ✅ Include/exclude patterns functional

## Phase 3: Glob Tool Optimization

### 3.1 Performance Enhancements (`src/tunacode/tools/glob.py`)
- Integrate with CodeIndex for pre-filtered candidates
- Add results sorting options:
  - Modification time (default)
  - File size
  - Alphabetical
  - Path depth
- Implement smart pagination for large result sets

### 3.2 Pattern Matching Improvements
- Add case-insensitive matching by default
- Support extended glob patterns:
  - Brace expansion (`{a,b,c}`)
  - Extended wildcards (`**`, `?(pattern)`)
- Implement negative patterns (exclusions)

### 3.3 Git Integration
- Parse and respect `.gitignore` patterns
- Support `.ignore` and `.rgignore` files
- Add `--no-ignore` override option
- Cache gitignore patterns per repository

## Phase 4: Caching Layer Enhancement

### 4.1 Multi-Level Cache Architecture
- Extend existing CodeIndex with search-specific caches:
  - File encoding detection cache (UTF-8, ASCII, etc.)
  - Line ending detection cache (LF, CRLF, CR)
  - Repository configuration cache
- Configure cache parameters:
  - 1000 entries maximum per cache
  - 5-minute TTL for freshness
  - LRU eviction policy
- Implement cache warming strategies

### 4.2 Cache Performance Monitoring
- Add cache hit rate tracking
- Implement memory usage monitoring
- Create cache effectiveness metrics
- Add debug logging for cache operations

### 4.3 Thread Safety and Concurrency
- Ensure all cache operations are async-safe
- Implement read-write locks for cache updates
- Add atomic cache operations
- Create cache consistency checks

## Phase 5: Tool Prompt Micro-Injection System ✅

### 5.1 Base Tool Enhancement (`src/tunacode/tools/base.py`) ✅
- ✅ Added `prompt()` method to BaseTool for dynamic prompt generation
- ✅ Implemented prompt caching with context-based cache keys
- ✅ Created `get_tool_schema()` method for API integration
- ✅ Added abstract `_get_parameters_schema()` for tool parameters

### 5.2 Dynamic Prompt Generation ✅
- ✅ Created XML-based prompt system in `tools/prompts/` directory
- ✅ Updated existing tools (grep.py, glob.py) with XML loading:
  - Added `_get_base_prompt()` method to load from XML files
  - Enhanced `_get_parameters_schema()` to parse XML parameters
  - Fallback to hardcoded prompts if XML loading fails
- ✅ Dynamic loading of prompts from XML files
- ✅ Support for prompt updates without code changes

### 5.3 Security and Type Safety ✅
- ✅ Used defusedxml instead of xml.etree for secure XML parsing
- ✅ Fixed type hints for proper mypy compliance
- ✅ Added proper error handling with fallbacks

### 5.4 Testing and Validation ✅
- ✅ Updated tests to use regular tools (not tools_v2 approach)
- ✅ All Phase 5 tests passing
- ✅ Created `ToolSchemaAssembler` for managing tool schemas
- ✅ JSON-serializable schema format for API calls

### 5.5 Known Issues
- glob.py file is 618 lines (exceeds 600 line recommendation)
- Should be refactored in future to reduce file size

## Phase 6: Integration and Optimization

### 6.1 Cross-Tool Integration
- Create unified search interface
- Implement tool chaining capabilities
- Add result format standardization
- Create cross-tool result deduplication

### 6.2 Performance Optimization
- Profile and optimize hot paths
- Implement lazy loading for heavy operations
- Add result streaming for real-time feedback
- Create adaptive timeout strategies

### 6.3 Error Handling and Fallbacks
- Implement graceful degradation:
  - Ripgrep failure → Python fallback
  - Cache miss → Direct filesystem access
  - Timeout → Partial results with warning
- Add comprehensive error logging
- Create recovery strategies for common failures

## Phase 7: Testing and Documentation

### 7.1 Test Coverage
- Unit tests for each component
- Integration tests for tool interactions
- Performance benchmarks
- Stress tests for large repositories
- Thread safety validation
- Cache effectiveness tests

### 7.2 Documentation
- Update tool documentation
- Create performance tuning guide
- Add troubleshooting section
- Write migration guide for existing users

### 7.3 Monitoring and Metrics
- Implement performance dashboards
- Add usage analytics
- Create debugging tools
- Set up continuous performance monitoring

## Success Metrics

### Performance Targets
- **Search Speed**: 10-100x improvement over current implementation
- **Cache Hit Rate**: >80% for active projects
- **First Result Time**: <100ms for most searches
- **Memory Overhead**: <10MB for typical projects

### Functionality Goals
- Full ripgrep feature parity
- Zero-configuration setup
- Platform-independent behavior
- Backward compatibility maintained

## Dependencies and Prerequisites

### External Dependencies
- ripgrep binaries (v14.0+)
- Python 3.8+ (for async features)
- cachetools or similar LRU cache library
- Platform-specific libraries for OS detection

### Internal Dependencies
- Existing CodeIndex infrastructure
- Current tool base classes
- Configuration management system
- Logging framework

## Risk Mitigation

### Technical Risks
- **Binary distribution size**: Use compression, optional downloads
- **Platform compatibility**: Extensive testing, fallback mechanisms
- **Performance regression**: Benchmark suite, gradual rollout
- **Cache invalidation**: TTL strategy, filesystem watching option

### Operational Risks
- **Increased complexity**: Modular design, clear interfaces
- **Debugging difficulty**: Comprehensive logging, debug modes
- **Resource consumption**: Configurable limits, monitoring

## Implementation Notes

### Completed Work (Phases 1-2)
- **Ripgrep Binary Management**: Full infrastructure for binary distribution and fallback
- **Enhanced Search Tool**: Integrated ripgrep with graceful Python fallback
- **Configuration System**: Added comprehensive ripgrep settings
- **Performance Metrics**: Built-in metrics collection for monitoring
- **Multiple Output Formats**: Extended ResultFormatter for flexible output

### Known Limitations
- Ripgrep binary needs to be downloaded separately (not bundled)
- File candidate filtering not fully integrated with ripgrep executor
- Test failure with timeout handling needs investigation

### Next Steps (Phase 3+)
1. Glob tool optimization with ripgrep integration
2. Enhanced caching layer for search results
3. Tool prompt micro-injection system
4. Full integration and optimization
5. Comprehensive testing and documentation

### Priority Order
1. ✅ Ripgrep integration (foundation for speed)
2. ✅ Resource management (reliability)
3. ✅ Glob tool optimization (file searching)
4. ✅ Micro-injection system (extensibility)
5. ⏳ Caching enhancements (performance)
6. ⏳ Advanced features (functionality)

### Backward Compatibility
- All enhancements maintain existing API
- New features are opt-in through configuration
- Python fallback ensures functionality without ripgrep
- Existing grep tool interface unchanged

### Performance Considerations
- Startup overhead minimized with lazy loading
- Memoization used for expensive operations
- Async operations maintained throughout
- Graceful degradation on binary unavailability

This implementation has successfully laid the foundation for Claude Code-level search performance while maintaining TunaCode's architecture and principles.
