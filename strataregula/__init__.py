"""
Strataregula - Layered Configuration Management with Strata Rules Architecture.

A hierarchical configuration management tool with pattern expansion
for large-scale configuration generation.

Features:
- Wildcard pattern expansion (* and **)
- Hierarchical mapping (47 prefectures → 8 regions)  
- Multiple output formats (Python, JSON, YAML)
- Memory-efficient streaming processing
- Simple CLI interface
- Pass/View kernel architecture (v0.3.0)
- Config interning and hash-consing (v0.3.0)
- Content-addressed caching (v0.3.0)
"""

__version__ = "0.3.0"
__author__ = "Strataregula Team"
__email__ = "team@strataregula.com"

# Only import what actually works and is tested
try:
    from .core.pattern_expander import (
        PatternExpander,
        EnhancedPatternExpander
    )
except ImportError:
    pass

try:
    from .core.config_compiler import (
        ConfigCompiler,
        CompilationConfig
    )
except ImportError:
    pass

# v0.3.0 New Architecture
try:
    from .kernel import Kernel, CacheStats, LRUCacheBackend
except ImportError:
    pass

try:
    from .passes import InternPass
except ImportError:
    pass

__all__ = [
    # Version info
    '__version__',
    # v0.3.0 New Architecture
    'Kernel',
    'InternPass',
]