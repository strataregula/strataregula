"""
PiPE (Pattern Input Processing Engine) - Command chaining and STDIN processing.

A powerful system for processing YAML configurations through command chains,
supporting STDIN input, hooks, and plugin-based transformations.
"""

from .chain import CommandChain, ChainExecutor
from .processor import STDINProcessor, StreamProcessor
from .commands import BaseCommand, CommandRegistry
from .pipeline import Pipeline, PipelineBuilder, PipelineManager

__all__ = [
    'CommandChain',
    'ChainExecutor', 
    'STDINProcessor',
    'StreamProcessor',
    'BaseCommand',
    'CommandRegistry',
    'Pipeline',
    'PipelineBuilder',
    'PipelineManager',
]
