# TunaCode Search Architecture Enhancement Plan

## Overview
This document outlines the phased implementation plan for enhancing TunaCode's search capabilities to achieve Claude Code-level performance through ripgrep integration, parallel processing, and intelligent caching.

## Phase 1: Foundation - Ripgrep Binary Management

### 1.1 Binary Distribution Setup
- Create `vendor/ripgrep/` directory structure
- Download platform-specific ripgrep binaries:
  - `x64-linux/rg`
  - `arm64-linux/rg`
  - `x64-darwin/rg`
  - `arm64-darwin/rg`
  - `x64-win32/rg.exe`
- Add binary verification (checksums/signatures)
- Create download script for CI/CD integration

### 1.2 Binary Path Resolution (`src/tunacode/utils/ripgrep.py`)
- Implement platform detection logic
- Create binary path resolver with fallback chain:
  1. Environment variable override (`USE_BUILTIN_RIPGREP`)
  2. System ripgrep (if newer version)
  3. Bundled ripgrep binary
  4. Fallback to Python-based search
- Add memoization decorator for path resolution
- Implement binary execution wrapper with error handling

### 1.3 Configuration Management
- Add ripgrep settings to configuration system
- Support debug logging (`debug('tunacode:ripgrep')`)
- Create performance metrics collection
- Add binary version checking and reporting

## Phase 2: Search Tool Core Enhancements

### 2.1 Grep Tool Resource Management (`src/tunacode/tools/grep.py`)
- Implement timeout management:
  - 10-second hard timeout for search operations
  - 3-second deadline for first match (broad pattern detection)
- Add buffer limits:
  - 1MB maximum output buffer
  - 100-result hard limit with truncation messages
- Create resource cleanup handlers
- Add memory-efficient streaming for large results

### 2.2 Parallel Processing Architecture
- Enhance ThreadPoolExecutor configuration (8 workers)
- Implement work distribution strategies:
  - File-based partitioning for large directories
  - Smart chunking based on file sizes
- Add result aggregation with deduplication
- Create progress tracking for long operations

### 2.3 Context and Filtering Features
- Implement context lines support:
  - `-A` (after), `-B` (before), `-C` (context) flags
  - Efficient context buffer management
- Add file type filtering:
  - `--type` support (js, py, rust, go, etc.)
  - Custom type definitions
- Enhance regex support:
  - Full PCRE2 regex syntax
  - Multiline matching with `--multiline` flag
- Add exclude/include patterns:
  - Glob-based file filtering
  - Directory exclusion lists

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

## Phase 5: Tool Prompt Micro-Injection System

### 5.1 Base Tool Enhancement (`src/tunacode/tools/base.py`)
- Add abstract `prompt()` method to BaseTool
- Implement default prompt generation
- Create prompt template system
- Add context parameter support

### 5.2 Dynamic Prompt Generation
- Implement per-tool prompt methods:
  - Model-specific instructions
  - Permission-aware guidance
  - Environment-specific hints
- Create prompt evaluation pipeline
- Add prompt caching for performance

### 5.3 API Integration Point
- Identify injection point in API call preparation
- Create tool schema assembly:
  - Convert prompts to function descriptions
  - Generate OpenAI-compatible schemas
  - Support for multiple API formats
- Implement prompt refresh on context changes

### 5.4 Context-Aware Features
- Add model detection and adaptation
- Implement permission level handling
- Create environment variable support
- Add dynamic prompt updates based on:
  - Current model capabilities
  - User permissions
  - System resources
  - Previous interactions

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

### Priority Order
1. Ripgrep integration (foundation for speed)
2. Resource management (reliability)
3. Caching enhancements (performance)
4. Advanced features (functionality)
5. Micro-injection system (extensibility)

### Backward Compatibility
- All enhancements must maintain existing API
- New features should be opt-in initially
- Deprecation warnings for changed behaviors
- Migration tools for configuration changes

### Performance Considerations
- Minimize startup overhead
- Lazy load heavy components
- Use async operations where beneficial
- Profile before and after each phase

This plan provides a clear roadmap for achieving Claude Code-level search performance while maintaining TunaCode's architecture and principles.
