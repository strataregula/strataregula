"""
STDIN and Stream Processing - Core input handling for PiPE system.
"""

import sys
import asyncio
from typing import Any, Dict, List, Optional, Union, TextIO, BinaryIO
from pathlib import Path
import yaml
import json
from io import StringIO, BytesIO

from ..hooks.base import HookManager


class STDINProcessor:
    """Processes STDIN input with support for multiple formats."""
    
    def __init__(self):
        self.supported_formats = ['yaml', 'yml', 'json', 'text', 'auto']
        self.hooks = HookManager()
        
    async def read_stdin(self, format: str = 'auto', 
                        encoding: str = 'utf-8') -> Any:
        """Read and parse STDIN input."""
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}")
            
        # Read raw input
        raw_input = await self._read_raw_stdin(encoding)
        
        # Detect format if auto
        if format == 'auto':
            format = self._detect_format(raw_input)
            
        # Parse input
        parsed_data = await self._parse_input(raw_input, format)
        
        # Execute post-processing hooks
        await self.hooks.trigger('post_stdin_parse', parsed_data, format)
        
        return parsed_data
    
    def read_stdin_sync(self, format: str = 'auto', 
                       encoding: str = 'utf-8') -> Any:
        """Read and parse STDIN input synchronously."""
        return asyncio.run(self.read_stdin(format, encoding))
    
    async def _read_raw_stdin(self, encoding: str) -> str:
        """Read raw STDIN input."""
        if sys.stdin.isatty():
            # Interactive mode - read from input()
            return input()
        else:
            # Pipe mode - read all lines
            lines = []
            async for line in self._async_readlines(sys.stdin):
                lines.append(line.rstrip('\n'))
            return '\n'.join(lines)
    
    async def _async_readlines(self, file: TextIO):
        """Async generator for reading lines from a file-like object."""
        loop = asyncio.get_event_loop()
        while True:
            line = await loop.run_in_executor(None, file.readline)
            if not line:
                break
            yield line
    
    def _detect_format(self, content: str) -> str:
        """Auto-detect input format."""
        content = content.strip()
        
        # Try JSON first
        try:
            json.loads(content)
            return 'json'
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try YAML
        try:
            yaml.safe_load(content)
            return 'yaml'
        except yaml.YAMLError:
            pass
        
        # Default to text
        return 'text'
    
    async def _parse_input(self, content: str, format: str) -> Any:
        """Parse input content based on format."""
        if format in ['yaml', 'yml']:
            return yaml.safe_load(content)
        elif format == 'json':
            return json.loads(content)
        elif format == 'text':
            return content
        else:
            raise ValueError(f"Unknown format: {format}")


class StreamProcessor:
    """Processes various input streams and files."""
    
    def __init__(self):
        self.hooks = HookManager()
        
    async def process_file(self, file_path: Union[str, Path], 
                          format: str = 'auto') -> Any:
        """Process a file input."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Execute pre-file hooks
        await self.hooks.trigger('pre_file_process', file_path, format)
        
        # Read and parse file
        content = file_path.read_text(encoding='utf-8')
        
        if format == 'auto':
            format = self._detect_format_from_extension(file_path)
            
        parsed_data = await self._parse_input(content, format)
        
        # Execute post-file hooks
        await self.hooks.trigger('post_file_process', file_path, parsed_data, format)
        
        return parsed_data
    
    async def process_string(self, content: str, format: str = 'auto') -> Any:
        """Process a string input."""
        if format == 'auto':
            format = self._detect_format(content)
            
        return await self._parse_input(content, format)
    
    async def process_multiple(self, inputs: List[Union[str, Path, TextIO]], 
                             format: str = 'auto') -> List[Any]:
        """Process multiple inputs and return a list of results."""
        results = []
        
        for input_item in inputs:
            if isinstance(input_item, (str, Path)):
                if Path(input_item).exists():
                    result = await self.process_file(input_item, format)
                else:
                    result = await self.process_string(str(input_item), format)
            elif hasattr(input_item, 'read'):
                # File-like object
                content = input_item.read()
                result = await self.process_string(content, format)
            else:
                raise ValueError(f"Unsupported input type: {type(input_item)}")
                
            results.append(result)
            
        return results
    
    def _detect_format_from_extension(self, file_path: Path) -> str:
        """Detect format from file extension."""
        suffix = file_path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            return 'yaml'
        elif suffix == '.json':
            return 'json'
        elif suffix in ['.txt', '.md']:
            return 'text'
        else:
            return 'auto'
    
    def _detect_format(self, content: str) -> str:
        """Auto-detect content format."""
        content = content.strip()
        
        # Try JSON first
        try:
            json.loads(content)
            return 'json'
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try YAML
        try:
            yaml.safe_load(content)
            return 'yaml'
        except yaml.YAMLError:
            pass
        
        # Default to text
        return 'text'
    
    async def _parse_input(self, content: str, format: str) -> Any:
        """Parse input content based on format."""
        if format in ['yaml', 'yml']:
            return yaml.safe_load(content)
        elif format == 'json':
            return json.loads(content)
        elif format == 'text':
            return content
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def process_file_sync(self, file_path: Union[str, Path], 
                         format: str = 'auto') -> Any:
        """Process a file input synchronously."""
        return asyncio.run(self.process_file(file_path, format))
    
    def process_string_sync(self, content: str, format: str = 'auto') -> Any:
        """Process a string input synchronously."""
        return asyncio.run(self.process_string(content, format))
