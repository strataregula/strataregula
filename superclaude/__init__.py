"""
SuperClaude - Intelligent Development Assistant for Strataregula Project
An AI-powered development assistant that helps with code generation, analysis,
documentation, and project management for the Strataregula ecosystem.
"""

__version__ = "0.1.0"
__author__ = "Strataregula Team"

from .core import SuperClaude
from .analyzer import ProjectAnalyzer
from .generator import CodeGenerator
from .assistant import DevelopmentAssistant

__all__ = [
    "SuperClaude",
    "ProjectAnalyzer", 
    "CodeGenerator",
    "DevelopmentAssistant"
]