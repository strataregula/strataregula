"""
Strataregula - YAML Configuration Pattern Compiler with PiPE Command Chaining.

A powerful pattern expansion engine for configuration generation,
infrastructure automation, and dynamic configuration management.

Features:
- PiPE (Pattern Input Processing Engine) command chaining
- STDIN and file processing support
- Rich plugin system with hooks and callbacks
- Dependency injection container
- CLI interface with rich output
"""

__version__ = "0.0.1"
__author__ = "Strataregula Team"
__email__ = "support@strataregula.dev"

# Import core PiPE system
from .pipe import (
    CommandChain,
    ChainExecutor,
    STDINProcessor,
    StreamProcessor,
    BaseCommand,
    CommandRegistry,
    Pipeline,
    PipelineBuilder,
    PipelineManager
)

# Import hook system
from .hooks import (
    HookManager,
    HookCallback,
    HookRegistry
)

# Import dependency injection system
from .di import (
    Container,
    ServiceLifetime
)

# Import CLI system (temporarily disabled due to missing dependencies)
# from .cli import main

# Backward compatibility aliases
YAMLConfigCompiler = Pipeline
PatternCompiler = CommandChain
YAMLCompiler = Pipeline
WildcardExpander = CommandChain

__all__ = [
    # Core PiPE system
    'CommandChain',
    'ChainExecutor',
    'STDINProcessor',
    'StreamProcessor',
    'BaseCommand',
    'CommandRegistry',
    'Pipeline',
    'PipelineBuilder',
    'PipelineManager',
    
    # Hook system
    'HookManager',
    'HookCallback',
    'HookRegistry',
    
    # Dependency injection
    'Container',
    'ServiceLifetime',
    
    # CLI (temporarily disabled)
    # 'main',
    
    # Backward compatibility
    'YAMLConfigCompiler',
    'PatternCompiler',
    'YAMLCompiler',
    'WildcardExpander',
    
    # Version info
    '__version__',
]
