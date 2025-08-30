"""Tests for stream processor functionality."""

import pytest
from strataregula.stream.processor import ProcessingStats, ChunkProcessor, StreamProcessor
from strataregula.stream.chunker import ChunkConfig


class TestProcessingStats:
    """Test ProcessingStats functionality."""
    
    def test_processing_stats_init(self):
        """Test ProcessingStats initialization."""
        stats = ProcessingStats()
        assert stats.chunks_processed == 0
        assert stats.bytes_processed == 0
        assert stats.processing_time == 0.0
        assert stats.errors == 0

    def test_throughput_calculation(self):
        """Test throughput calculation."""
        stats = ProcessingStats(bytes_processed=1000, processing_time=2.0)
        assert stats.throughput == 500.0

    def test_throughput_zero_time(self):
        """Test throughput with zero processing time."""
        stats = ProcessingStats(bytes_processed=1000, processing_time=0.0)
        assert stats.throughput == 0.0


class TestChunkProcessor:
    """Test ChunkProcessor functionality."""
    
    def test_chunk_processor_init(self):
        """Test ChunkProcessor initialization."""
        processor = ChunkProcessor()
        assert processor is not None
        assert processor._processors == {}

    def test_register_processor(self):
        """Test processor registration."""
        processor = ChunkProcessor()
        
        def test_func(chunk):
            return chunk.upper()
            
        processor.register_processor("test", test_func)
        assert "test" in processor._processors

    def test_process_chunks_string(self):
        """Test processing string chunks."""
        processor = ChunkProcessor(ChunkConfig(chunk_size=5))
        
        def test_func(chunk):
            return chunk.upper()
            
        processor.register_processor("upper", test_func)
        
        results = list(processor.process_chunks("hello world", "upper"))
        assert len(results) > 0
        assert all(isinstance(r, str) for r in results)

    def test_process_chunks_unregistered(self):
        """Test processing with unregistered processor."""
        processor = ChunkProcessor()
        
        with pytest.raises(ValueError):
            list(processor.process_chunks("test", "nonexistent"))

    def test_process_chunks_error_handling(self):
        """Test error handling in processing."""
        processor = ChunkProcessor(ChunkConfig(chunk_size=5))
        
        def error_func(chunk):
            if "bad" in chunk:
                raise ValueError("Test error")
            return chunk
            
        processor.register_processor("error", error_func)
        
        results = list(processor.process_chunks("good bad test", "error"))
        assert len(results) > 0
        assert processor.stats.errors > 0

    def test_process_file_chunks_unregistered(self):
        """Test file processing with unregistered processor."""
        processor = ChunkProcessor()
        
        with pytest.raises(ValueError):
            list(processor.process_file_chunks("test.txt", "nonexistent"))


class TestStreamProcessor:
    """Test StreamProcessor functionality."""
    
    def test_stream_processor_init(self):
        """Test StreamProcessor initialization."""
        processor = StreamProcessor()
        assert processor is not None
        assert processor.max_workers == 4
        assert processor._active_streams == {}

    def test_register_processor(self):
        """Test processor registration."""
        processor = StreamProcessor()
        
        def test_func(chunk):
            return chunk
            
        processor.register_processor("test", test_func)
        assert "test" in processor.chunk_processor._processors

    def test_process_stream_sync(self):
        """Test synchronous stream processing."""
        processor = StreamProcessor()
        
        def count_func(chunk):
            return len(chunk)
            
        processor.register_processor("count", count_func)
        
        data_stream = ["hello", "world", "test"]
        results = list(processor.process_stream_sync(data_stream, "count"))
        assert len(results) > 0

    def test_stop_stream(self):
        """Test stream stopping."""
        processor = StreamProcessor()
        
        def test_func(chunk):
            return chunk
            
        processor.register_processor("test", test_func)
        
        data_stream = ["data1", "data2"]
        stream_id = "test_stream"
        
        results = list(processor.process_stream_sync(data_stream, "test", stream_id=stream_id))
        assert len(results) > 0
        
        # Test stopping
        result = processor.stop_stream(stream_id)
        assert result is True
        
        # Test stopping nonexistent
        result = processor.stop_stream("nonexistent")
        assert result is False

    def test_get_stream_stats(self):
        """Test stream statistics."""
        processor = StreamProcessor()
        
        def test_func(chunk):
            return chunk
            
        processor.register_processor("test", test_func)
        
        data_stream = ["test"]
        list(processor.process_stream_sync(data_stream, "test", stream_id="stats_test"))
        
        stats = processor.get_stream_stats("stats_test")
        assert stats is not None
        
        # Test nonexistent
        stats = processor.get_stream_stats("nonexistent")
        assert stats is None

    def test_get_all_stats(self):
        """Test getting all statistics."""
        processor = StreamProcessor()
        
        def test_func(chunk):
            return chunk
            
        processor.register_processor("test", test_func)
        
        list(processor.process_stream_sync(["data1"], "test", stream_id="stream1"))
        list(processor.process_stream_sync(["data2"], "test", stream_id="stream2"))
        
        all_stats = processor.get_all_stats()
        assert "stream1" in all_stats
        assert "stream2" in all_stats

    def test_process_parallel(self):
        """Test parallel processing."""
        processor = StreamProcessor()
        
        def test_func(chunk):
            return len(chunk)
            
        processor.register_processor("test", test_func)
        
        data_list = ["short", "longer text", "very long text data"]
        results = processor.process_parallel(data_list, "test")
        assert len(results) > 0

    def test_process_parallel_unregistered(self):
        """Test parallel processing with unregistered processor."""
        processor = StreamProcessor()
        
        with pytest.raises(ValueError):
            processor.process_parallel(["test"], "nonexistent")

    def test_cleanup(self):
        """Test resource cleanup."""
        processor = StreamProcessor()
        processor.cleanup()
        
        # Should not raise any errors
        assert True
