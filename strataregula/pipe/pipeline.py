"""
Pipeline System - High-level pipeline management for PiPE.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import json
import logging

from .chain import CommandChain, ChainExecutor, ChainContext
from .processor import STDINProcessor, StreamProcessor
from .commands import CommandRegistry
from ..hooks.base import HookManager
from ..di.container import Container

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for a pipeline."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    input_format: str = "auto"
    output_format: str = "yaml"
    commands: List[Dict[str, Any]] = field(default_factory=list)
    hooks: Dict[str, List[str]] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'PipelineConfig':
        """Create pipeline config from YAML string."""
        data = yaml.safe_load(yaml_content)
        return cls(**data)
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'PipelineConfig':
        """Create pipeline config from YAML file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Pipeline config file not found: {file_path}")
            
        content = file_path.read_text(encoding='utf-8')
        return cls.from_yaml(content)
    
    def to_yaml(self) -> str:
        """Convert config to YAML string."""
        return yaml.dump(self.__dict__, default_flow_style=False, allow_unicode=True)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save config to YAML file."""
        file_path = Path(file_path)
        file_path.write_text(self.to_yaml(), encoding='utf-8')


class Pipeline:
    """High-level pipeline for processing data through command chains."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.chain = CommandChain(config.name)
        self.executor = ChainExecutor()
        self.hooks = HookManager()
        self.container = Container()
        
        # Build command chain from config
        self._build_chain()
        
    def _build_chain(self) -> None:
        """Build command chain from configuration."""
        for cmd_config in self.config.commands:
            command = cmd_config.get('command')
            if not command:
                continue
                
            args = cmd_config.get('args', [])
            kwargs = cmd_config.get('kwargs', {})
            condition = cmd_config.get('condition')
            error_handling = cmd_config.get('error_handling', 'continue')
            
            self.chain.add_command(
                command=command,
                args=args,
                kwargs=kwargs,
                condition=condition,
                error_handling=error_handling
            )
    
    async def process(self, input_data: Any = None, 
                     input_file: Optional[Union[str, Path]] = None,
                     input_stdin: bool = False) -> Any:
        """Process data through the pipeline."""
        # Determine input source
        if input_stdin:
            processor = STDINProcessor()
            input_data = await processor.read_stdin(self.config.input_format)
        elif input_file:
            processor = StreamProcessor()
            input_data = await processor.read_file(input_file, self.config.input_format)
        
        if input_data is None:
            raise ValueError("No input data provided")
        
        # Execute pipeline
        context = ChainContext(input_data=input_data)
        result = await self.executor.execute(self.chain, context)
        
        return result


class PipelineBuilder:
    """Builder for creating pipeline configurations."""
    
    def __init__(self, name: str):
        self.config = PipelineConfig(name=name)
    
    def set_description(self, description: str) -> 'PipelineBuilder':
        """Set pipeline description."""
        self.config.description = description
        return self
    
    def set_version(self, version: str) -> 'PipelineBuilder':
        """Set pipeline version."""
        self.config.version = version
        return self
    
    def set_input_format(self, format: str) -> 'PipelineBuilder':
        """Set input format."""
        self.config.input_format = format
        return self
    
    def set_output_format(self, format: str) -> 'PipelineBuilder':
        """Set output format."""
        self.config.output_format = format
        return self
    
    def add_command(self, command: str, args: List[Any] = None, 
                   kwargs: Dict[str, Any] = None, condition: str = None,
                   error_handling: str = 'continue') -> 'PipelineBuilder':
        """Add command to pipeline."""
        cmd_config = {
            'command': command,
            'args': args or [],
            'kwargs': kwargs or {},
            'condition': condition,
            'error_handling': error_handling
        }
        self.config.commands.append(cmd_config)
        return self
    
    def add_hook(self, hook_type: str, hook_name: str) -> 'PipelineBuilder':
        """Add hook to pipeline."""
        if hook_type not in self.config.hooks:
            self.config.hooks[hook_type] = []
        self.config.hooks[hook_type].append(hook_name)
        return self
    
    def set_environment(self, env: Dict[str, str]) -> 'PipelineBuilder':
        """Set environment variables."""
        self.config.environment = env
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'PipelineBuilder':
        """Add metadata to pipeline."""
        self.config.metadata[key] = value
        return self
    
    def build(self) -> PipelineConfig:
        """Build pipeline configuration."""
        return self.config
    
    def build_pipeline(self) -> Pipeline:
        """Build and return pipeline instance."""
        return Pipeline(self.config)


class PipelineManager:
    """Manager for multiple pipelines."""
    
    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.configs: Dict[str, PipelineConfig] = {}
        self.container = Container()
    
    def register_pipeline(self, config: PipelineConfig) -> bool:
        """Register a pipeline configuration."""
        try:
            self.configs[config.name] = config
            logger.debug(f"Registered pipeline: {config.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register pipeline {config.name}: {e}")
            return False
    
    def create_pipeline(self, name: str) -> Optional[Pipeline]:
        """Create a pipeline instance."""
        if name not in self.configs:
            logger.error(f"Pipeline not found: {name}")
            return None
        
        try:
            pipeline = Pipeline(self.configs[name])
            self.pipelines[name] = pipeline
            return pipeline
        except Exception as e:
            logger.error(f"Failed to create pipeline {name}: {e}")
            return None
    
    def get_pipeline(self, name: str) -> Optional[Pipeline]:
        """Get existing pipeline instance."""
        return self.pipelines.get(name)
    
    def list_pipelines(self) -> List[str]:
        """List all registered pipeline names."""
        return list(self.configs.keys())
    
    def remove_pipeline(self, name: str) -> bool:
        """Remove a pipeline."""
        try:
            if name in self.configs:
                del self.configs[name]
            if name in self.pipelines:
                del self.pipelines[name]
            logger.debug(f"Removed pipeline: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove pipeline {name}: {e}")
            return False
    
    def load_pipeline_from_file(self, file_path: Union[str, Path]) -> bool:
        """Load pipeline configuration from file."""
        try:
            config = PipelineConfig.from_file(file_path)
            return self.register_pipeline(config)
        except Exception as e:
            logger.error(f"Failed to load pipeline from {file_path}: {e}")
            return False
    
    def save_pipeline_to_file(self, name: str, file_path: Union[str, Path]) -> bool:
        """Save pipeline configuration to file."""
        if name not in self.configs:
            logger.error(f"Pipeline not found: {name}")
            return False
        
        try:
            self.configs[name].save_to_file(file_path)
            logger.debug(f"Saved pipeline {name} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save pipeline {name} to {file_path}: {e}")
            return False
    
    def get_pipeline_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get pipeline information."""
        if name not in self.configs:
            return None
        
        config = self.configs[name]
        return {
            'name': config.name,
            'description': config.description,
            'version': config.version,
            'input_format': config.input_format,
            'output_format': config.output_format,
            'command_count': len(config.commands),
            'hook_count': sum(len(hooks) for hooks in config.hooks.values()),
            'environment_vars': len(config.environment),
            'metadata_keys': list(config.metadata.keys())
        }
