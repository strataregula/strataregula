"""
Tests for pipe processor module
"""

import pytest
import asyncio
import json
import yaml
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import Mock, patch, AsyncMock

from strataregula.pipe.processor import STDINProcessor, StreamProcessor


class TestSTDINProcessor:
    """Test STDINProcessor class"""

    def test_init(self):
        """Test STDINProcessor initialization"""
        processor = STDINProcessor()
        assert processor.supported_formats == ['yaml', 'yml', 'json', 'text', 'auto']
        assert hasattr(processor, 'hooks')

    @pytest.mark.asyncio
    async def test_read_stdin_invalid_format(self):
        """Test reading stdin with invalid format"""
        processor = STDINProcessor()
        
        with pytest.raises(ValueError, match="Unsupported format"):
            await processor.read_stdin(format='invalid')

    def test_read_stdin_sync(self):
        """Test synchronous stdin reading"""
        processor = STDINProcessor()
        
        with patch.object(processor, 'read_stdin', return_value=asyncio.Future()) as mock_read:
            mock_read.return_value.set_result("test_data")
            
            result = processor.read_stdin_sync()
            assert result == "test_data"

    @pytest.mark.asyncio
    @patch('sys.stdin')
    async def test_read_raw_stdin_interactive(self, mock_stdin):
        """Test reading raw stdin in interactive mode"""
        mock_stdin.isatty.return_value = True
        processor = STDINProcessor()
        
        with patch('builtins.input', return_value="test input"):
            result = await processor._read_raw_stdin('utf-8')
            assert result == "test input"

    @pytest.mark.asyncio
    @patch('sys.stdin')
    async def test_read_raw_stdin_pipe(self, mock_stdin):
        """Test reading raw stdin in pipe mode"""
        mock_stdin.isatty.return_value = False
        processor = STDINProcessor()
        
        async def mock_async_readlines(file):
            yield "line1\n"
            yield "line2\n"
            yield "line3\n"
        
        with patch.object(processor, '_async_readlines', return_value=mock_async_readlines(mock_stdin)):
            result = await processor._read_raw_stdin('utf-8')
            assert result == "line1\nline2\nline3"

    def test_detect_format_json(self):
        """Test format detection for JSON"""
        processor = STDINProcessor()
        json_content = '{"key": "value"}'
        
        result = processor._detect_format(json_content)
        assert result == 'json'

    def test_detect_format_yaml(self):
        """Test format detection for YAML"""
        processor = STDINProcessor()
        yaml_content = 'key: value'
        
        result = processor._detect_format(yaml_content)
        assert result == 'yaml'

    def test_detect_format_text(self):
        """Test format detection for plain text"""
        processor = STDINProcessor()
        text_content = 'This is plain text'
        
        result = processor._detect_format(text_content)
        assert result == 'text'

    @pytest.mark.asyncio
    async def test_parse_input_yaml(self):
        """Test parsing YAML input"""
        processor = STDINProcessor()
        yaml_content = 'key: value\nlist:\n  - item1\n  - item2'
        
        result = await processor._parse_input(yaml_content, 'yaml')
        assert result == {'key': 'value', 'list': ['item1', 'item2']}

    @pytest.mark.asyncio
    async def test_parse_input_json(self):
        """Test parsing JSON input"""
        processor = STDINProcessor()
        json_content = '{"key": "value", "number": 42}'
        
        result = await processor._parse_input(json_content, 'json')
        assert result == {'key': 'value', 'number': 42}

    @pytest.mark.asyncio
    async def test_parse_input_text(self):
        """Test parsing text input"""
        processor = STDINProcessor()
        text_content = 'Plain text content'
        
        result = await processor._parse_input(text_content, 'text')
        assert result == 'Plain text content'

    @pytest.mark.asyncio
    async def test_parse_input_unknown_format(self):
        """Test parsing with unknown format"""
        processor = STDINProcessor()
        
        with pytest.raises(ValueError, match="Unknown format"):
            await processor._parse_input("content", "unknown")

    @pytest.mark.asyncio
    async def test_async_readlines(self):
        """Test async readlines method"""
        processor = STDINProcessor()
        mock_file = Mock()
        mock_file.readline.side_effect = ["line1\n", "line2\n", ""]
        
        lines = []
        async for line in processor._async_readlines(mock_file):
            lines.append(line)
        
        assert lines == ["line1\n", "line2\n"]


class TestStreamProcessor:
    """Test StreamProcessor class"""

    def test_init(self):
        """Test StreamProcessor initialization"""
        processor = StreamProcessor()
        assert hasattr(processor, 'hooks')

    @pytest.mark.asyncio
    async def test_process_file_not_found(self):
        """Test processing non-existent file"""
        processor = StreamProcessor()
        
        with pytest.raises(FileNotFoundError):
            await processor.process_file("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_process_file_json(self):
        """Test processing JSON file"""
        processor = StreamProcessor()
        test_data = {"test": "data", "number": 123}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            with patch.object(processor.hooks, 'trigger', new_callable=AsyncMock):
                result = await processor.process_file(temp_file, 'auto')
                assert result == test_data
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_process_file_yaml(self):
        """Test processing YAML file"""
        processor = StreamProcessor()
        test_data = {"test": "data", "items": ["a", "b", "c"]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_data, f)
            temp_file = f.name
        
        try:
            with patch.object(processor.hooks, 'trigger', new_callable=AsyncMock):
                result = await processor.process_file(temp_file, 'auto')
                assert result == test_data
        finally:
            Path(temp_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_process_string_auto_detect(self):
        """Test processing string with auto format detection"""
        processor = StreamProcessor()
        
        # JSON string
        json_string = '{"key": "value"}'
        result = await processor.process_string(json_string, 'auto')
        assert result == {"key": "value"}
        
        # YAML string
        yaml_string = 'key: value'
        result = await processor.process_string(yaml_string, 'auto')
        assert result == {"key": "value"}
        
        # Text string
        text_string = 'plain text'
        result = await processor.process_string(text_string, 'auto')
        assert result == "plain text"

    @pytest.mark.asyncio
    async def test_process_multiple_inputs(self):
        """Test processing multiple inputs"""
        processor = StreamProcessor()
        
        # Create test files
        json_data = {"type": "json"}
        yaml_data = {"type": "yaml"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
            json.dump(json_data, f1)
            json_file = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f2:
            yaml.dump(yaml_data, f2)
            yaml_file = f2.name
        
        try:
            # Test with files and strings
            inputs = [json_file, yaml_file, '{"type": "string"}']
            
            with patch.object(processor.hooks, 'trigger', new_callable=AsyncMock):
                results = await processor.process_multiple(inputs, 'auto')
            
            assert len(results) == 3
            assert results[0] == json_data
            assert results[1] == yaml_data
            assert results[2] == {"type": "string"}
        finally:
            Path(json_file).unlink(missing_ok=True)
            Path(yaml_file).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_process_multiple_file_like_object(self):
        """Test processing file-like object in multiple inputs"""
        processor = StreamProcessor()
        
        # Create a StringIO object
        file_like = StringIO('{"from": "file_like"}')
        inputs = [file_like]
        
        results = await processor.process_multiple(inputs, 'auto')
        assert results == [{"from": "file_like"}]

    @pytest.mark.asyncio
    async def test_process_multiple_unsupported_type(self):
        """Test processing unsupported input type"""
        processor = StreamProcessor()
        
        inputs = [123]  # Unsupported type
        
        with pytest.raises(ValueError, match="Unsupported input type"):
            await processor.process_multiple(inputs)

    def test_detect_format_from_extension(self):
        """Test format detection from file extension"""
        processor = StreamProcessor()
        
        assert processor._detect_format_from_extension(Path("test.json")) == "json"
        assert processor._detect_format_from_extension(Path("test.yaml")) == "yaml"
        assert processor._detect_format_from_extension(Path("test.yml")) == "yaml"
        assert processor._detect_format_from_extension(Path("test.txt")) == "text"
        assert processor._detect_format_from_extension(Path("test.md")) == "text"
        assert processor._detect_format_from_extension(Path("test.unknown")) == "auto"

    def test_detect_format(self):
        """Test content format detection"""
        processor = StreamProcessor()
        
        # JSON
        json_content = '{"key": "value"}'
        assert processor._detect_format(json_content) == 'json'
        
        # YAML
        yaml_content = 'key: value'
        assert processor._detect_format(yaml_content) == 'yaml'
        
        # Text
        text_content = 'plain text'
        assert processor._detect_format(text_content) == 'text'

    @pytest.mark.asyncio
    async def test_parse_input_formats(self):
        """Test parsing input with different formats"""
        processor = StreamProcessor()
        
        # YAML
        yaml_result = await processor._parse_input('key: value', 'yaml')
        assert yaml_result == {'key': 'value'}
        
        # JSON
        json_result = await processor._parse_input('{"key": "value"}', 'json')
        assert json_result == {'key': 'value'}
        
        # Text
        text_result = await processor._parse_input('plain text', 'text')
        assert text_result == 'plain text'
        
        # Unknown format
        with pytest.raises(ValueError, match="Unknown format"):
            await processor._parse_input('content', 'unknown')

    def test_process_file_sync(self):
        """Test synchronous file processing"""
        processor = StreamProcessor()
        test_data = {"sync": "test"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            with patch.object(processor, 'process_file', return_value=asyncio.Future()) as mock_process:
                mock_process.return_value.set_result(test_data)
                
                result = processor.process_file_sync(temp_file)
                assert result == test_data
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_process_string_sync(self):
        """Test synchronous string processing"""
        processor = StreamProcessor()
        test_string = '{"sync": "string"}'
        
        with patch.object(processor, 'process_string', return_value=asyncio.Future()) as mock_process:
            mock_process.return_value.set_result({"sync": "string"})
            
            result = processor.process_string_sync(test_string)
            assert result == {"sync": "string"}