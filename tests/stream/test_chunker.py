"""
Tests for stream chunker module
"""

import pytest
import tempfile
from pathlib import Path
from io import StringIO, BytesIO

from strataregula.stream.chunker import ChunkConfig, Chunker


class TestChunkConfig:
    """Test ChunkConfig dataclass"""

    def test_chunk_config_defaults(self):
        """Test ChunkConfig creation with default values"""
        config = ChunkConfig()
        
        assert config.chunk_size == 8192
        assert config.overlap_size == 0
        assert config.encoding is None
        assert config.line_based is False
        assert config.preserve_boundaries is True

    def test_chunk_config_custom_values(self):
        """Test ChunkConfig creation with custom values"""
        config = ChunkConfig(
            chunk_size=4096,
            overlap_size=512,
            encoding="utf-8",
            line_based=True,
            preserve_boundaries=False
        )
        
        assert config.chunk_size == 4096
        assert config.overlap_size == 512
        assert config.encoding == "utf-8"
        assert config.line_based is True
        assert config.preserve_boundaries is False


class TestChunker:
    """Test Chunker class"""

    def test_chunker_init_default_config(self):
        """Test Chunker initialization with default config"""
        chunker = Chunker()
        
        assert isinstance(chunker.config, ChunkConfig)
        assert chunker.config.chunk_size == 8192

    def test_chunker_init_custom_config(self):
        """Test Chunker initialization with custom config"""
        custom_config = ChunkConfig(chunk_size=1024, overlap_size=100)
        chunker = Chunker(custom_config)
        
        assert chunker.config is custom_config
        assert chunker.config.chunk_size == 1024
        assert chunker.config.overlap_size == 100

    def test_chunk_bytes_from_bytes_object(self):
        """Test chunking bytes object"""
        chunker = Chunker()
        data = b"0123456789" * 100  # 1000 bytes
        
        chunks = list(chunker.chunk_bytes(data, chunk_size=100))
        
        assert len(chunks) == 10
        assert all(len(chunk) == 100 for chunk in chunks)
        assert b"".join(chunks) == data

    def test_chunk_bytes_partial_last_chunk(self):
        """Test chunking bytes with partial last chunk"""
        chunker = Chunker()
        data = b"0123456789" * 10 + b"abc"  # 103 bytes
        
        chunks = list(chunker.chunk_bytes(data, chunk_size=50))
        
        assert len(chunks) == 3
        assert len(chunks[0]) == 50
        assert len(chunks[1]) == 50
        assert len(chunks[2]) == 3  # Partial last chunk
        assert b"".join(chunks) == data

    def test_chunk_bytes_from_file_like_object(self):
        """Test chunking from file-like BytesIO object"""
        chunker = Chunker()
        data = b"0123456789" * 50  # 500 bytes
        file_obj = BytesIO(data)
        
        chunks = list(chunker.chunk_bytes(file_obj, chunk_size=100))
        
        assert len(chunks) == 5
        assert all(len(chunk) == 100 for chunk in chunks)
        assert b"".join(chunks) == data

    def test_chunk_bytes_empty_data(self):
        """Test chunking empty bytes"""
        chunker = Chunker()
        data = b""
        
        chunks = list(chunker.chunk_bytes(data, chunk_size=100))
        
        assert chunks == []

    def test_chunk_text_from_string(self):
        """Test chunking string"""
        chunker = Chunker()
        data = "abcdef" * 100  # 600 characters
        
        chunks = list(chunker.chunk_text(data, chunk_size=100))
        
        assert len(chunks) == 6
        assert all(len(chunk) == 100 for chunk in chunks)
        assert "".join(chunks) == data

    def test_chunk_text_line_based(self):
        """Test chunking text with line-based splitting"""
        config = ChunkConfig(line_based=True)
        chunker = Chunker(config)
        data = "line1\nline2\nline3\nline4\nline5\nline6"
        
        chunks = list(chunker.chunk_text(data, chunk_size=20))  # Approximate size
        
        # Should preserve line boundaries
        assert all('\n' not in chunk or chunk.endswith('\n') for chunk in chunks)
        # Reconstruct should match original (minus potential trailing newlines)
        reconstructed = "".join(chunks).rstrip('\n')
        assert reconstructed == data

    def test_chunk_text_from_file_like_object(self):
        """Test chunking from StringIO object"""
        chunker = Chunker()
        data = "Hello World! " * 50  # 650 characters
        file_obj = StringIO(data)
        
        chunks = list(chunker.chunk_text(file_obj, chunk_size=100))
        
        assert len(chunks) == 7  # 6 full chunks + 1 partial
        assert "".join(chunks) == data

    def test_chunk_text_line_based_from_file(self):
        """Test line-based chunking from file object"""
        config = ChunkConfig(line_based=True)
        chunker = Chunker(config)
        data = "line1\nline2\nline3\nline4\nline5"
        file_obj = StringIO(data)
        
        chunks = list(chunker.chunk_text(file_obj, chunk_size=15))
        
        # Should preserve line boundaries
        reconstructed = "".join(chunks)
        # Lines should be preserved
        assert "line1" in reconstructed
        assert "line2" in reconstructed

    def test_chunk_file_text_mode(self):
        """Test chunking file in text mode"""
        config = ChunkConfig(encoding="utf-8")
        chunker = Chunker(config)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            test_content = "Hello World! " * 100
            f.write(test_content)
            temp_file = f.name
        
        try:
            chunks = list(chunker.chunk_file(temp_file))
            
            assert all(isinstance(chunk, str) for chunk in chunks)
            assert "".join(chunks) == test_content
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_chunk_file_binary_mode(self):
        """Test chunking file in binary mode"""
        chunker = Chunker()  # No encoding = binary mode
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            test_content = b"Hello World! " * 100
            f.write(test_content)
            temp_file = f.name
        
        try:
            chunks = list(chunker.chunk_file(temp_file))
            
            assert all(isinstance(chunk, bytes) for chunk in chunks)
            assert b"".join(chunks) == test_content
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_chunk_with_overlap_string(self):
        """Test chunking string with overlap"""
        config = ChunkConfig(overlap_size=2)
        chunker = Chunker(config)
        data = "abcdefghijklmnop"  # 16 characters
        
        chunks = list(chunker.chunk_with_overlap(data, chunk_size=6))
        
        assert len(chunks) == 4
        assert chunks[0] == "abcdef"
        assert chunks[1] == "efghij"  # Overlaps with "ef"
        assert chunks[2] == "ijklmn"  # Overlaps with "ij"
        assert chunks[3] == "mnop"    # Final chunk

    def test_chunk_with_overlap_bytes(self):
        """Test chunking bytes with overlap"""
        config = ChunkConfig(overlap_size=2)
        chunker = Chunker(config)
        data = b"abcdefghijklmnop"  # 16 bytes
        
        chunks = list(chunker.chunk_with_overlap(data, chunk_size=6))
        
        assert len(chunks) == 4
        assert chunks[0] == b"abcdef"
        assert chunks[1] == b"efghij"  # Overlaps with b"ef"
        assert chunks[2] == b"ijklmn"  # Overlaps with b"ij"
        assert chunks[3] == b"mnop"    # Final chunk

    def test_chunk_with_overlap_invalid_config(self):
        """Test chunking with invalid overlap configuration"""
        config = ChunkConfig(overlap_size=10)
        chunker = Chunker(config)
        data = "test data"
        
        with pytest.raises(ValueError, match="Overlap size must be smaller than chunk size"):
            list(chunker.chunk_with_overlap(data, chunk_size=5))

    def test_chunk_with_overlap_empty_data(self):
        """Test chunking empty data with overlap"""
        config = ChunkConfig(overlap_size=2)
        chunker = Chunker(config)
        
        chunks = list(chunker.chunk_with_overlap("", chunk_size=6))
        assert chunks == []
        
        chunks = list(chunker.chunk_with_overlap(b"", chunk_size=6))
        assert chunks == []

    def test_chunk_lines_approximate_size(self):
        """Test internal _chunk_lines method"""
        chunker = Chunker()
        lines = ["line1", "line2", "line3", "line4", "line5"]
        
        chunks = list(chunker._chunk_lines(lines, approximate_chunk_size=15))
        
        # Should group lines to approximate the target size
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(chunk.endswith('\n') for chunk in chunks)

    def test_chunk_lines_from_file(self):
        """Test internal _chunk_lines_from_file method"""
        chunker = Chunker()
        data = "line1\nline2\nline3\nline4\nline5"
        file_obj = StringIO(data)
        
        chunks = list(chunker._chunk_lines_from_file(file_obj, approximate_chunk_size=15))
        
        assert all(isinstance(chunk, str) for chunk in chunks)
        # Reconstruct and compare
        reconstructed = "".join(chunks)
        assert reconstructed == data

    def test_estimate_chunks(self):
        """Test chunk estimation"""
        chunker = Chunker()
        
        # Exact division
        assert chunker.estimate_chunks(1000, chunk_size=100) == 10
        
        # With remainder (ceiling division)
        assert chunker.estimate_chunks(1001, chunk_size=100) == 11
        assert chunker.estimate_chunks(999, chunk_size=100) == 10
        
        # Using default chunk size
        config = ChunkConfig(chunk_size=256)
        chunker = Chunker(config)
        assert chunker.estimate_chunks(1024) == 4

    def test_chunk_iterable(self):
        """Test chunking generic iterable"""
        chunker = Chunker()
        data = range(25)  # 0 to 24
        
        chunks = list(chunker.chunk_iterable(data, chunk_size=5))
        
        assert len(chunks) == 5
        assert all(len(chunk) == 5 for chunk in chunks)
        assert chunks[0] == [0, 1, 2, 3, 4]
        assert chunks[1] == [5, 6, 7, 8, 9]
        assert chunks[4] == [20, 21, 22, 23, 24]

    def test_chunk_iterable_partial_last_chunk(self):
        """Test chunking iterable with partial last chunk"""
        chunker = Chunker()
        data = range(23)  # 0 to 22
        
        chunks = list(chunker.chunk_iterable(data, chunk_size=5))
        
        assert len(chunks) == 5
        assert len(chunks[0]) == 5
        assert len(chunks[1]) == 5
        assert len(chunks[2]) == 5
        assert len(chunks[3]) == 5
        assert len(chunks[4]) == 3  # Partial last chunk
        assert chunks[4] == [20, 21, 22]

    def test_chunk_iterable_empty(self):
        """Test chunking empty iterable"""
        chunker = Chunker()
        data = []
        
        chunks = list(chunker.chunk_iterable(data, chunk_size=5))
        
        assert chunks == []

    def test_chunk_config_with_different_settings(self):
        """Test chunker with different configuration combinations"""
        # Large chunks
        config1 = ChunkConfig(chunk_size=16384)
        chunker1 = Chunker(config1)
        assert chunker1.config.chunk_size == 16384
        
        # Line-based with encoding
        config2 = ChunkConfig(line_based=True, encoding="utf-8")
        chunker2 = Chunker(config2)
        assert chunker2.config.line_based is True
        assert chunker2.config.encoding == "utf-8"
        
        # With overlap and boundary preservation
        config3 = ChunkConfig(overlap_size=128, preserve_boundaries=True)
        chunker3 = Chunker(config3)
        assert chunker3.config.overlap_size == 128
        assert chunker3.config.preserve_boundaries is True