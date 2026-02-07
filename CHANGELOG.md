# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.61] - 2026-02-06

### Added
- End-to-end tests for mtime-driven caches
- Typed cache accessors for agents, context, and ignore manager
- Strict cache infrastructure with strategies

### Changed
- Migrated remaining lru_cache caches into CacheManager layer
- Refactored agent_config to use typed cache accessors
- Cache accessor now used for ignore manager; removed global ignore cache
- Reduced McCabe complexity to ≤10 for 14 functions
- Reduced cognitive complexity of 13 functions to under 10
- Re-enabled Ruff mccabe complexity check (max 10)

### Fixed
- Satisfied pre-commit dead code checks
