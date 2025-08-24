"""
Tests for stream processor module
"""

import pytest
import asyncio
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from strataregula.stream.processor import (
    ProcessingStats, ChunkProcessor, StreamProcessor
)
from strataregula.stream.chunker import ChunkConfig


class TestProcessingStats:
    """Test ProcessingStats dataclass"""

    def test_processing_stats_defaults(self):
        """Test ProcessingStats creation with default values"""
        stats = ProcessingStats()
        
        assert stats.chunks_processed == 0
        assert stats.bytes_processed == 0
        assert stats.processing_time == 0.0
        assert stats.errors == 0
        assert stats.start_time is None
        assert stats.end_time is None

    def test_processing_stats_custom_values(self):
        """Test ProcessingStats creation with custom values"""
        start_time = time.time()
        end_time = start_time + 10.0
        
        stats = ProcessingStats(
            chunks_processed=100,
            bytes_processed=50000,
            processing_time=10.0,
            errors=2,
            start_time=start_time,
            end_time=end_time
        )
        
        assert stats.chunks_processed == 100
        assert stats.bytes_processed == 50000
        assert stats.processing_time == 10.0
        assert stats.errors == 2
        assert stats.start_time == start_time
        assert stats.end_time == end_time

    def test_throughput_calculation(self):
        """Test throughput property calculation"""
        # Normal case
        stats = ProcessingStats(
            bytes_processed=1000,
            processing_time=10.0
        )
        assert stats.throughput == 100.0  # 1000 bytes / 10 seconds
        
        # Zero processing time
        stats_zero_time = ProcessingStats(
            bytes_processed=1000,
            processing_time=0.0
        )
        assert stats_zero_time.throughput == 0.0

    def test_throughput_with_zero_bytes(self):
        """Test throughput calculation with zero bytes processed"""
        stats = ProcessingStats(
            bytes_processed=0,
            processing_time=10.0
        )
        assert stats.throughput == 0.0


class TestChunkProcessor:
    """Test ChunkProcessor class"""

    def test_chunk_processor_init_default(self):
        """Test ChunkProcessor initialization with default config"""
        processor = ChunkProcessor()
        
        assert hasattr(processor, 'chunker')
        assert isinstance(processor.stats, ProcessingStats)
        assert processor._processors == {}

    def test_chunk_processor_init_custom_config(self):
        """Test ChunkProcessor initialization with custom config"""
        custom_config = ChunkConfig(chunk_size=1024)
        processor = ChunkProcessor(custom_config)
        
        assert processor.chunker.config.chunk_size == 1024

    def test_register_processor(self):
        """Test registering a processing function"""
        processor = ChunkProcessor()
        
        def test_processor(chunk):
            return chunk.upper()
        
        processor.register_processor("uppercase", test_processor)
        
        assert "uppercase" in processor._processors
        assert processor._processors["uppercase"] is test_processor

    def test_process_chunks_string_data(self):
        """Test processing string data in chunks"""
        processor = ChunkProcessor()
        
        def test_processor(chunk):
            return f"processed: {chunk}"
        
        processor.register_processor("test", test_processor)
        
        data = "hello world test data"
        results = list(processor.process_chunks(data, "test"))
        
        assert len(results) > 0
        assert all("processed:" in str(result) for result in results)
        assert processor.stats.chunks_processed > 0
        assert processor.stats.bytes_processed > 0

    def test_process_chunks_bytes_data(self):
        """Test processing bytes data in chunks"""
        processor = ChunkProcessor()
        
        def test_processor(chunk):
            return len(chunk)
        
        processor.register_processor("count_bytes", test_processor)
        
        data = b"hello world test data"
        results = list(processor.process_chunks(data, "count_bytes"))
        
        assert len(results) > 0
        assert all(isinstance(result, int) for result in results)
        assert processor.stats.chunks_processed > 0

    def test_process_chunks_unregistered_processor(self):
        """Test processing with unregistered processor"""
        processor = ChunkProcessor()
        
        with pytest.raises(ValueError, match="Processor 'nonexistent' not registered"):
            list(processor.process_chunks("test data", "nonexistent"))

    def test_process_chunks_with_error(self):
        """Test processing chunks with error handling"""
        processor = ChunkProcessor()
        
        def error_processor(chunk):
            if "error" in chunk:
                raise ValueError("Test error")
            return f"ok: {chunk}"
        
        processor.register_processor("error_test", error_processor)
        
        data = "normal error trigger normal"
        results = list(processor.process_chunks(data, "error_test"))
        
        # Should have both success and error results
        assert len(results) > 0
        error_results = [r for r in results if isinstance(r, dict) and 'error' in r]
        assert len(error_results) > 0
        assert processor.stats.errors > 0

    def test_process_chunks_stats_timing(self):
        """Test that processing stats include timing information"""
        processor = ChunkProcessor()
        
        def slow_processor(chunk):
            time.sleep(0.01)  # Small delay
            return chunk
        
        processor.register_processor("slow", slow_processor)
        
        data = "test data"
        list(processor.process_chunks(data, "slow"))
        
        assert processor.stats.start_time is not None
        assert processor.stats.end_time is not None
        assert processor.stats.processing_time > 0

    def test_process_file_chunks(self):
        """Test processing file in chunks"""
        processor = ChunkProcessor()
        
        def test_processor(chunk):
            return len(chunk)
        
        processor.register_processor("file_processor", test_processor)
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            test_content = "Hello World! " * 100
            f.write(test_content)
            temp_file = f.name
        
        try:
            results = list(processor.process_file_chunks(temp_file, "file_processor"))
            
            assert len(results) > 0
            assert all(isinstance(result, int) for result in results)
            assert processor.stats.chunks_processed > 0
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_process_file_chunks_unregistered_processor(self):
        """Test processing file with unregistered processor"""
        processor = ChunkProcessor()
        
        with pytest.raises(ValueError, match="Processor 'nonexistent' not registered"):
            list(processor.process_file_chunks("test.txt", "nonexistent"))

    def test_process_file_chunks_with_error(self):
        """Test file processing with error in processor"""
        processor = ChunkProcessor()
        
        def error_processor(chunk):
            raise ValueError("Processing error")
        
        processor.register_processor("error_file", error_processor)
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            results = list(processor.process_file_chunks(temp_file, "error_file"))
            
            # Should have error results
            error_results = [r for r in results if isinstance(r, dict) and 'error' in r]
            assert len(error_results) > 0
            assert processor.stats.errors > 0
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestStreamProcessor:
    """Test StreamProcessor class"""

    def test_stream_processor_init(self):
        """Test StreamProcessor initialization"""
        processor = StreamProcessor()
        
        assert hasattr(processor, 'chunk_processor')
        assert processor.max_workers == 4
        assert hasattr(processor, '_executor')
        assert processor._active_streams == {}
        assert processor._stream_stats == {}

    def test_stream_processor_init_custom_workers(self):
        """Test StreamProcessor initialization with custom worker count"""
        processor = StreamProcessor(max_workers=8)
        
        assert processor.max_workers == 8

    def test_register_processor(self):
        """Test registering processor through StreamProcessor"""
        processor = StreamProcessor()
        
        def test_func(chunk):
            return chunk.upper()
        
        processor.register_processor("test", test_func)
        
        assert "test" in processor.chunk_processor._processors

    def test_process_stream_sync(self):
        """Test synchronous stream processing"""
        processor = StreamProcessor()
        
        def test_processor(chunk):
            return f"processed: {chunk}"
        
        processor.register_processor("sync_test", test_processor)
        
        # Create a simple data stream
        data_stream = ["chunk1", "chunk2", "chunk3"]
        
        results = list(processor.process_stream_sync(
            iter(data_stream), "sync_test", stream_id="test_stream"
        ))
        
        assert len(results) > 0
        assert "test_stream" in processor._stream_stats
        assert processor._stream_stats["test_stream"].chunks_processed > 0

    def test_process_stream_sync_with_stop(self):
        """Test stopping a synchronous stream"""
        processor = StreamProcessor()
        
        def test_processor(chunk):
            return chunk
        
        processor.register_processor("stop_test", test_processor)
        
        # Create a generator that would produce many items
        def long_stream():
            for i in range(1000):
                yield f"chunk_{i}"
        
        # Start processing in a separate thread to test stopping
        import threading
        results = []
        
        def process_stream():
            for result in processor.process_stream_sync(
                long_stream(), "stop_test", stream_id="stop_stream"
            ):
                results.append(result)
        
        thread = threading.Thread(target=process_stream)
        thread.start()
        
        # Give it a moment to start, then stop
        time.sleep(0.01)
        processor.stop_stream("stop_stream")
        thread.join(timeout=1.0)
        
        # Should have stopped early
        assert len(results) < 1000

    @pytest.mark.asyncio
    async def test_process_stream_async(self):
        """Test asynchronous stream processing"""
        processor = StreamProcessor()
        
        def test_processor(chunk):
            return f"async: {chunk}"
        
        processor.register_processor("async_test", test_processor)
        
        # Create async data stream
        async def async_stream():
            for i in range(3):
                yield f"chunk_{i}"
                await asyncio.sleep(0.001)  # Small delay
        
        results = []
        async for result in processor.process_stream_async(
            async_stream(), "async_test", stream_id="async_stream"
        ):
            results.append(result)
        
        assert len(results) > 0
        assert "async_stream" in processor._stream_stats

    def test_process_parallel(self):
        """Test parallel processing of data list"""
        processor = StreamProcessor()
        
        def test_processor(chunk):
            return len(chunk)
        
        processor.register_processor("parallel_test", test_processor)
        
        data_list = ["short", "medium data", "very long data string"]
        
        results = processor.process_parallel(data_list, "parallel_test")
        
        assert len(results) > 0
        # Should have processed all data items
        assert len([r for r in results if isinstance(r, int)]) > 0

    def test_process_parallel_unregistered_processor(self):
        """Test parallel processing with unregistered processor"""
        processor = StreamProcessor()
        
        with pytest.raises(ValueError, match="Processor 'nonexistent' not registered"):
            processor.process_parallel(["data"], "nonexistent")

    def test_process_parallel_with_errors(self):
        """Test parallel processing with errors"""
        processor = StreamProcessor()
        
        def error_processor(chunk):
            if "error" in chunk:
                raise ValueError("Test error")
            return f"ok: {chunk}"
        
        processor.register_processor("parallel_error", error_processor)
        
        data_list = ["good data", "error trigger", "more good data"]
        results = processor.process_parallel(data_list, "parallel_error")
        
        # Should have both success and error results
        error_results = [r for r in results if isinstance(r, dict) and 'error' in r]
        assert len(error_results) > 0

    def test_stop_stream_existing(self):
        """Test stopping an existing stream"""
        processor = StreamProcessor()
        processor._active_streams["test_stream"] = True
        
        result = processor.stop_stream("test_stream")
        
        assert result is True
        assert processor._active_streams["test_stream"] is False

    def test_stop_stream_nonexistent(self):
        """Test stopping a non-existent stream"""
        processor = StreamProcessor()
        
        result = processor.stop_stream("nonexistent_stream")
        
        assert result is False

    def test_get_stream_stats(self):
        """Test getting stream statistics"""
        processor = StreamProcessor()
        test_stats = ProcessingStats(chunks_processed=10)
        processor._stream_stats["test_stream"] = test_stats
        
        retrieved_stats = processor.get_stream_stats("test_stream")
        
        assert retrieved_stats is test_stats

    def test_get_stream_stats_nonexistent(self):
        """Test getting statistics for non-existent stream"""
        processor = StreamProcessor()
        
        result = processor.get_stream_stats("nonexistent")
        
        assert result is None

    def test_get_all_stats(self):
        """Test getting all stream statistics"""
        processor = StreamProcessor()
        stats1 = ProcessingStats(chunks_processed=10)
        stats2 = ProcessingStats(chunks_processed=20)
        
        processor._stream_stats["stream1"] = stats1
        processor._stream_stats["stream2"] = stats2
        
        all_stats = processor.get_all_stats()
        
        assert len(all_stats) == 2
        assert all_stats["stream1"] is stats1
        assert all_stats["stream2"] is stats2
        
        # Should be a copy, not the original dict
        assert all_stats is not processor._stream_stats

    def test_cleanup(self):
        """Test cleanup of resources"""
        processor = StreamProcessor()
        
        # Set up some active streams
        processor._active_streams["stream1"] = True
        processor._active_streams["stream2"] = True
        
        processor.cleanup()
        
        # All streams should be marked as inactive
        assert all(not active for active in processor._active_streams.values())

    def test_stream_id_auto_generation(self):
        """Test automatic stream ID generation"""
        processor = StreamProcessor()
        
        def test_processor(chunk):
            return chunk
        
        processor.register_processor("auto_id", test_processor)
        
        # Process without specifying stream_id
        results = list(processor.process_stream_sync(
            iter(["test"]), "auto_id"
        ))
        
        # Should have generated a stream ID
        assert len(processor._stream_stats) == 1
        # Stream ID should start with "stream_"
        stream_id = list(processor._stream_stats.keys())[0]
        assert stream_id.startswith("stream_")

    def test_chunk_processor_with_custom_config(self):
        """Test StreamProcessor with custom chunk configuration"""
        custom_config = ChunkConfig(chunk_size=100, overlap_size=10)
        processor = StreamProcessor(chunk_config=custom_config)
        
        assert processor.chunk_processor.chunker.config.chunk_size == 100
        assert processor.chunk_processor.chunker.config.overlap_size == 10