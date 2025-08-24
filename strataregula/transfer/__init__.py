"""
Transfer/Copy Subsystem for Strataregula

Provides safe, reproducible object copying and transfer functionality with:
- Rule-based copying control (deep/shallow/link/cow modes)
- JSONPath/label-based matching
- Hook/trigger integration
- Memory-efficient streaming processing
- Circular reference detection and depth limiting
- Built-in transforms (mask/rename/exclude/map)
"""

from .copy_engine import CopyEngine, CopyPlan
from .rules import CopyRule, RuleSet, MatchExpr
from .deep_copy import DeepCopyVisitor, CopyMode
from .transforms import TransformRegistry, MaskStyle
from .diff import CopyDiff, ChangeType

__version__ = "0.1.0"
__all__ = [
    "CopyEngine",
    "CopyPlan", 
    "CopyRule",
    "RuleSet",
    "MatchExpr",
    "DeepCopyVisitor",
    "CopyMode",
    "TransformRegistry",
    "MaskStyle",
    "CopyDiff",
    "ChangeType"
]