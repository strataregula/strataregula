# Changelog

All notable changes to strataregula will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-08-24

### Added
- **Comprehensive Test Suite** (SR-2)
  - CLI integration tests for all `sr compile` functionality  
  - ConfigCompiler unit tests with 95% coverage
  - End-to-end integration tests for complete workflows
  - Performance tests for large-scale processing (1000+ patterns)
  - Memory efficiency tests with constraints
  - Error handling and edge case coverage
  
- **Enhanced Test Infrastructure**
  - Pytest configuration with coverage reporting
  - Performance test markers (`@pytest.mark.performance`)
  - Integration test suite with realistic configurations
  - Concurrent compilation testing
  - Memory usage monitoring and validation
  
- **Bug Fixes and Improvements**
  - Fixed YAML output template formatting issues
  - Improved error message handling in CLI tests
  - Enhanced template engine with proper indentation
  - Deprecation warning fixes for datetime handling

### Technical
- **Test Coverage**: 90%+ across core modules
- **Test Count**: 65+ comprehensive test cases
- **Performance Validation**: 1000+ pattern compilation <30s
- **Memory Efficiency**: Processing within 200MB constraints
- **Error Resilience**: Graceful handling of malformed inputs

### Quality Assurance
- All CLI commands tested with various input combinations
- Template generation accuracy verification
- Provenance tracking validation
- Concurrent execution safety
- Large dataset processing capabilities

## [0.1.0] - 2025-08-24

### Added
- Development rules framework with versioning standards
- CHANGELOG.md following Keep a Changelog format
- Project roadmap and architecture documentation

### Changed
- Version bump to 0.1.0 reflecting MVP completion status

## [0.1.0] - 2025-08-24

### Added
- **Enhanced Pattern Expansion Engine** (SR-MVP)
  - Wildcard pattern expansion (`edge.*.gateway` → 47 prefectures)
  - Hierarchical Japanese geography support (47 prefectures → 8 regions)
  - Multiple wildcard handling (`service.*.*` patterns)
  - LRU caching with configurable limits
  
- **CLI Integration** (SR-MVP)
  - `sr compile` command with full backward compatibility
  - Multiple output formats (Python, JSON, YAML)
  - Planning mode (`--plan`) for expansion analysis
  - Statistics mode (`--stats`) for performance metrics
  - Streaming processing with memory limits
  
- **Static Module Generation** (SR-MVP)
  - O(1) lookup performance with compiled Python modules
  - Template-based code generation system
  - Provenance tracking (input files, fingerprints, performance stats)
  - Hierarchical lookup functions (by region, prefecture, pattern)
  
- **Core Infrastructure**
  - ConfigCompiler with CompilationConfig dataclass
  - EnhancedPatternExpander with RegionHierarchy support
  - StreamingPatternProcessor for memory-efficient processing
  - TemplateEngine with multiple output format support

### Performance
- **Expansion Results**: 13 input patterns → 179 expanded services
- **Processing Time**: <10ms compilation time
- **Memory Usage**: ~44MB peak memory usage
- **Hierarchy Support**: 47 prefectures mapped to 8 regions + services + roles

### Technical
- Comprehensive test suite (21/21 tests passing)
- Type-safe dataclass-based configuration
- Stream-based processing for large datasets
- Memory cleanup and optimization mechanisms
- Regex-based pattern matching for service lookup

### Examples
- Sample traffic configuration (`examples/sample_traffic.yaml`)
- Sample prefecture hierarchy (`examples/sample_prefectures.yaml`)
- Generated Python module with full functionality

## [0.0.1] - 2025-01-XX (Historical)

### Added
- Initial project structure and scaffold
- PiPE (Pattern Input Processing Engine) command chaining system
- STDIN processing support
- Rich plugin system with hooks and callbacks
- Dependency injection container
- CLI interface foundation

### Project Structure
- Core package: `strataregula/`
- Entry point: `sr` command skeleton
- Hook system: `strataregula/hooks/`
- Pipeline system: `strataregula/pipe/`
- Dependency injection: `strataregula/di/`

[Unreleased]: https://github.com/[org]/strataregula/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/[org]/strataregula/releases/tag/v0.1.0
[0.0.1]: https://github.com/[org]/strataregula/releases/tag/v0.0.1