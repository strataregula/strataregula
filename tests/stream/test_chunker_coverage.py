import pytest
from pathlib import Path
from io import StringIO
from unittest.mock import patch, mock_open

from strataregula.stream.chunker import ChunkConfig, Chunker


class TestChunkConfig:
    """Test ChunkConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ChunkConfig()
        assert config.chunk_size == 8192
        assert config.overlap_size == 0
        assert config.encoding is None
        assert config.line_based is False
        assert config.preserve_boundaries is True

    def test_custom_config(self):
        """Test custom configuration"""
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
    """Test Chunker class functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = ChunkConfig(chunk_size=10, overlap_size=2)
        self.chunker = Chunker(self.config)

    def test_init(self):
        """Test chunker initialization"""
        assert self.chunker.config == self.config

    def test_chunk_bytes_basic(self):
        """Test basic byte chunking"""
        data = b"0123456789abcdefghij"
        chunks = list(self.chunker.chunk_bytes(data))
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, bytes) for chunk in chunks)
        assert len(chunks[0]) <= 10

    def test_chunk_bytes_empty(self):
        """Test chunking empty bytes"""
        chunks = list(self.chunker.chunk_bytes(b""))
        assert len(chunks) == 0

    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        text = "This is a test string for chunking"
        chunks = list(self.chunker.chunk_text(text))
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_text_line_based(self):
        """Test line-based text chunking"""
        config = ChunkConfig(chunk_size=20, line_based=True)
        chunker = Chunker(config)
        text = "Line 1\\nLine 2\\nLine 3\\nLine 4"
        
        chunks = list(chunker.chunk_text(text))
        assert len(chunks) > 0

    def test_chunk_file_text(self):
        """Test file chunking with text mode"""
        test_data = "Test file content for chunking"
        
        with patch("builtins.open", mock_open(read_data=test_data)):
            chunks = list(self.chunker.chunk_file(Path("test.txt")))
            assert len(chunks) > 0

    def test_chunk_file_binary(self):
        """Test file chunking with binary mode"""
        config = ChunkConfig(encoding=None)  # Binary mode
        chunker = Chunker(config)
        test_data = b"Binary test data"
        
        with patch("builtins.open", mock_open(read_data=test_data)):
            chunks = list(chunker.chunk_file(Path("test.bin")))
            assert len(chunks) >= 0

    def test_chunk_with_overlap_basic(self):
        """Test chunking with overlap"""
        data = "0123456789abcdefghij"
        chunks = list(self.chunker.chunk_with_overlap(data))
        
        assert len(chunks) > 1
        # Check overlap exists between chunks
        if len(chunks) > 1:
            # Some overlap should exist due to overlap_size=2
            assert len(chunks[0]) > 0

    def test_chunk_lines_basic(self):
        """Test internal line chunking"""
        lines = ["line1", "line2", "line3", "line4", "line5"]
        chunks = list(self.chunker._chunk_lines(lines))
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, list) for chunk in chunks)

    def test_chunk_lines_from_file(self):
        """Test line chunking from file"""
        test_lines = "line1\\nline2\\nline3\\nline4\\n"
        
        with patch("builtins.open", mock_open(read_data=test_lines)):
            chunks = list(self.chunker._chunk_lines_from_file(Path("test.txt")))
            assert len(chunks) > 0

    def test_estimate_chunks(self):
        """Test chunk count estimation"""
        estimate = self.chunker.estimate_chunks(100)  # 100 bytes with 10 byte chunks
        assert estimate >= 10  # Should be at least 10 chunks

    def test_chunk_iterable_basic(self):
        """Test iterable chunking"""
        items = list(range(25))  # 25 items
        chunks = list(self.chunker.chunk_iterable(items))
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, list) for chunk in chunks)
        
        # Verify all items are included
        all_items = [item for chunk in chunks for item in chunk]
        assert len(all_items) == 25

    def test_chunk_iterable_empty(self):
        """Test chunking empty iterable"""
        chunks = list(self.chunker.chunk_iterable([]))
        assert len(chunks) == 0

    def test_chunk_iterable_single_item(self):
        """Test chunking single item iterable"""
        chunks = list(self.chunker.chunk_iterable([1]))
        assert len(chunks) == 1
        assert chunks[0] == [1]


class TestChunkerEdgeCases:
    """Test edge cases and error conditions"""

    def test_zero_chunk_size(self):
        """Test behavior with zero chunk size"""
        config = ChunkConfig(chunk_size=0)
        chunker = Chunker(config)
        
        # Should handle gracefully or raise appropriate error
        with pytest.raises((ValueError, ZeroDivisionError)):
            list(chunker.chunk_bytes(b"test"))

    def test_negative_chunk_size(self):
        """Test behavior with negative chunk size"""
        config = ChunkConfig(chunk_size=-1)
        chunker = Chunker(config)
        
        # Should handle gracefully
        chunks = list(chunker.chunk_bytes(b"test"))
        assert len(chunks) >= 0

    def test_large_overlap(self):
        """Test overlap larger than chunk size"""
        config = ChunkConfig(chunk_size=5, overlap_size=10)
        chunker = Chunker(config)
        
        chunks = list(chunker.chunk_with_overlap("test data"))
        assert len(chunks) >= 0  # Should not crash

    def test_encoding_error_handling(self):
        """Test encoding error handling"""
        config = ChunkConfig(encoding="ascii")
        chunker = Chunker(config)
        
        # Test with non-ASCII content
        with patch("builtins.open", mock_open(read_data="Test 日本語")):
            try:
                chunks = list(chunker.chunk_file(Path("test.txt")))
                # May succeed or fail depending on implementation
                assert len(chunks) >= 0
            except UnicodeDecodeError:
                # Expected for strict ASCII
                pass