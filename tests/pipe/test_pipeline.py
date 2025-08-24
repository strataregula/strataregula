"""
Tests for pipe pipeline module
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from strataregula.pipe.pipeline import (
    PipelineConfig, Pipeline, PipelineBuilder, PipelineManager
)


class TestPipelineConfig:
    """Test PipelineConfig dataclass"""

    def test_pipeline_config_creation(self):
        """Test creating a PipelineConfig with defaults"""
        config = PipelineConfig(name="test_pipeline")
        
        assert config.name == "test_pipeline"
        assert config.description == ""
        assert config.version == "1.0.0"
        assert config.input_format == "auto"
        assert config.output_format == "yaml"
        assert config.commands == []
        assert config.hooks == {}
        assert config.environment == {}
        assert config.metadata == {}

    def test_pipeline_config_with_values(self):
        """Test creating a PipelineConfig with custom values"""
        commands = [{"command": "test", "args": ["arg1"]}]
        hooks = {"pre_process": ["hook1"]}
        environment = {"ENV_VAR": "value"}
        metadata = {"author": "test"}
        
        config = PipelineConfig(
            name="custom_pipeline",
            description="Custom test pipeline",
            version="2.0.0",
            input_format="json",
            output_format="json",
            commands=commands,
            hooks=hooks,
            environment=environment,
            metadata=metadata
        )
        
        assert config.name == "custom_pipeline"
        assert config.description == "Custom test pipeline"
        assert config.version == "2.0.0"
        assert config.input_format == "json"
        assert config.output_format == "json"
        assert config.commands == commands
        assert config.hooks == hooks
        assert config.environment == environment
        assert config.metadata == metadata

    def test_from_yaml(self):
        """Test creating PipelineConfig from YAML string"""
        yaml_content = """
        name: yaml_pipeline
        description: Pipeline from YAML
        version: 1.5.0
        input_format: json
        commands:
          - command: test_cmd
            args: [arg1, arg2]
        """
        
        config = PipelineConfig.from_yaml(yaml_content)
        assert config.name == "yaml_pipeline"
        assert config.description == "Pipeline from YAML"
        assert config.version == "1.5.0"
        assert config.input_format == "json"
        assert len(config.commands) == 1
        assert config.commands[0]["command"] == "test_cmd"

    def test_from_file(self):
        """Test creating PipelineConfig from YAML file"""
        yaml_content = """
        name: file_pipeline
        description: Pipeline from file
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            config = PipelineConfig.from_file(temp_file)
            assert config.name == "file_pipeline"
            assert config.description == "Pipeline from file"
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_from_file_not_found(self):
        """Test loading from non-existent file"""
        with pytest.raises(FileNotFoundError):
            PipelineConfig.from_file("nonexistent.yaml")

    def test_to_yaml(self):
        """Test converting PipelineConfig to YAML"""
        config = PipelineConfig(
            name="yaml_test",
            description="Test YAML conversion",
            commands=[{"command": "test"}]
        )
        
        yaml_str = config.to_yaml()
        assert "name: yaml_test" in yaml_str
        assert "description: Test YAML conversion" in yaml_str
        assert "test" in yaml_str

    def test_save_to_file(self):
        """Test saving PipelineConfig to file"""
        config = PipelineConfig(name="save_test")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            config.save_to_file(temp_file)
            
            # Verify file was created and contains expected content
            content = Path(temp_file).read_text()
            assert "name: save_test" in content
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestPipeline:
    """Test Pipeline class"""

    @pytest.fixture
    def sample_config(self):
        """Sample pipeline configuration"""
        return PipelineConfig(
            name="test_pipeline",
            description="Test pipeline",
            commands=[
                {"command": "cmd1", "args": ["arg1"]},
                {"command": "cmd2", "kwargs": {"param": "value"}}
            ]
        )

    def test_pipeline_init(self, sample_config):
        """Test Pipeline initialization"""
        with patch('strataregula.pipe.pipeline.CommandChain'), \
             patch('strataregula.pipe.pipeline.ChainExecutor'), \
             patch('strataregula.pipe.pipeline.HookManager'), \
             patch('strataregula.pipe.pipeline.Container'):
            
            pipeline = Pipeline(sample_config)
            assert pipeline.config == sample_config

    @patch('strataregula.pipe.pipeline.CommandChain')
    @patch('strataregula.pipe.pipeline.ChainExecutor')
    @patch('strataregula.pipe.pipeline.HookManager')
    @patch('strataregula.pipe.pipeline.Container')
    def test_build_chain(self, mock_container, mock_hook, mock_executor, mock_chain, sample_config):
        """Test building command chain from config"""
        mock_chain_instance = Mock()
        mock_chain.return_value = mock_chain_instance
        
        pipeline = Pipeline(sample_config)
        
        # Verify add_command was called for each command in config
        assert mock_chain_instance.add_command.call_count == 2

    @pytest.mark.asyncio
    @patch('strataregula.pipe.pipeline.STDINProcessor')
    @patch('strataregula.pipe.pipeline.StreamProcessor')
    @patch('strataregula.pipe.pipeline.CommandChain')
    @patch('strataregula.pipe.pipeline.ChainExecutor')
    @patch('strataregula.pipe.pipeline.HookManager')
    @patch('strataregula.pipe.pipeline.Container')
    @patch('strataregula.pipe.pipeline.ChainContext')
    async def test_process_with_stdin(self, mock_context, mock_container, mock_hook, 
                                     mock_executor, mock_chain, mock_stream, mock_stdin, sample_config):
        """Test processing with stdin input"""
        mock_stdin_instance = Mock()
        mock_stdin_instance.read_stdin = AsyncMock(return_value={"test": "data"})
        mock_stdin.return_value = mock_stdin_instance
        
        mock_executor_instance = Mock()
        mock_executor_instance.execute_chain = AsyncMock(return_value={"result": "processed"})
        mock_executor.return_value = mock_executor_instance
        
        pipeline = Pipeline(sample_config)
        result = await pipeline.process(input_stdin=True)
        
        mock_stdin_instance.read_stdin.assert_called_once()
        mock_executor_instance.execute_chain.assert_called_once()

    @pytest.mark.asyncio
    @patch('strataregula.pipe.pipeline.StreamProcessor')
    @patch('strataregula.pipe.pipeline.CommandChain')
    @patch('strataregula.pipe.pipeline.ChainExecutor')
    @patch('strataregula.pipe.pipeline.HookManager')
    @patch('strataregula.pipe.pipeline.Container')
    @patch('strataregula.pipe.pipeline.ChainContext')
    async def test_process_with_file(self, mock_context, mock_container, mock_hook,
                                    mock_executor, mock_chain, mock_stream, sample_config):
        """Test processing with file input"""
        mock_stream_instance = Mock()
        mock_stream_instance.process_file = AsyncMock(return_value={"file": "data"})
        mock_stream.return_value = mock_stream_instance
        
        mock_executor_instance = Mock()
        mock_executor_instance.execute_chain = AsyncMock(return_value={"result": "processed"})
        mock_executor.return_value = mock_executor_instance
        
        pipeline = Pipeline(sample_config)
        result = await pipeline.process(input_file="test.json")
        
        mock_stream_instance.process_file.assert_called_once()
        mock_executor_instance.execute_chain.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_no_input(self, sample_config):
        """Test processing with no input should raise error"""
        with patch('strataregula.pipe.pipeline.CommandChain'), \
             patch('strataregula.pipe.pipeline.ChainExecutor'), \
             patch('strataregula.pipe.pipeline.HookManager'), \
             patch('strataregula.pipe.pipeline.Container'):
            
            pipeline = Pipeline(sample_config)
            
            with pytest.raises(ValueError, match="Must provide input"):
                await pipeline.process()

    def test_process_sync(self, sample_config):
        """Test synchronous processing"""
        with patch('strataregula.pipe.pipeline.CommandChain'), \
             patch('strataregula.pipe.pipeline.ChainExecutor'), \
             patch('strataregula.pipe.pipeline.HookManager'), \
             patch('strataregula.pipe.pipeline.Container'):
            
            pipeline = Pipeline(sample_config)
            
            with patch.object(pipeline, 'process', return_value=asyncio.Future()) as mock_process:
                mock_process.return_value.set_result({"sync": "result"})
                
                result = pipeline.process_sync(input_data={"test": "data"})
                assert result == {"sync": "result"}

    def test_add_hook(self, sample_config):
        """Test adding hooks to pipeline"""
        with patch('strataregula.pipe.pipeline.CommandChain'), \
             patch('strataregula.pipe.pipeline.ChainExecutor'), \
             patch('strataregula.pipe.pipeline.HookManager') as mock_hook, \
             patch('strataregula.pipe.pipeline.Container'):
            
            mock_hook_instance = Mock()
            mock_hook.return_value = mock_hook_instance
            
            pipeline = Pipeline(sample_config)
            callback = Mock()
            
            pipeline.add_hook("test_hook", callback)
            mock_hook_instance.register.assert_called_once_with("test_hook", callback)

    def test_get_info(self, sample_config):
        """Test getting pipeline information"""
        with patch('strataregula.pipe.pipeline.CommandChain'), \
             patch('strataregula.pipe.pipeline.ChainExecutor'), \
             patch('strataregula.pipe.pipeline.HookManager') as mock_hook, \
             patch('strataregula.pipe.pipeline.Container'):
            
            mock_hook_instance = Mock()
            mock_hook_instance.get_registered_hooks.return_value = ["hook1", "hook2"]
            mock_hook.return_value = mock_hook_instance
            
            pipeline = Pipeline(sample_config)
            info = pipeline.get_info()
            
            assert info['name'] == sample_config.name
            assert info['description'] == sample_config.description
            assert info['version'] == sample_config.version
            assert info['command_count'] == len(sample_config.commands)
            assert info['hook_count'] == 2


class TestPipelineBuilder:
    """Test PipelineBuilder class"""

    def test_builder_init(self):
        """Test PipelineBuilder initialization"""
        builder = PipelineBuilder("test_builder")
        assert builder.config.name == "test_builder"

    def test_builder_methods(self):
        """Test all builder methods"""
        builder = PipelineBuilder("test")
        
        result = (builder
                  .set_description("Test description")
                  .set_version("2.0.0")
                  .set_input_format("json")
                  .set_output_format("json")
                  .add_command("test_cmd", args=["arg1"])
                  .add_hook("pre_process", "hook1")
                  .set_environment({"ENV": "value"})
                  .add_metadata("key", "value"))
        
        # Check builder returns self for chaining
        assert result is builder
        
        # Check config was updated
        assert builder.config.description == "Test description"
        assert builder.config.version == "2.0.0"
        assert builder.config.input_format == "json"
        assert builder.config.output_format == "json"
        assert len(builder.config.commands) == 1
        assert "pre_process" in builder.config.hooks
        assert builder.config.environment["ENV"] == "value"
        assert builder.config.metadata["key"] == "value"

    def test_builder_build(self):
        """Test building pipeline from builder"""
        builder = PipelineBuilder("build_test")
        
        with patch('strataregula.pipe.pipeline.Pipeline') as mock_pipeline:
            pipeline = builder.build()
            mock_pipeline.assert_called_once_with(builder.config)

    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        builder = PipelineBuilder("config_test")
        builder.set_description("Test config")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save config
            builder.save_config(temp_file)
            
            # Load config into new builder
            new_builder = PipelineBuilder("new")
            new_builder.load_config(temp_file)
            
            assert new_builder.config.name == "config_test"
            assert new_builder.config.description == "Test config"
        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestPipelineManager:
    """Test PipelineManager class"""

    def test_manager_init(self):
        """Test PipelineManager initialization"""
        manager = PipelineManager()
        assert manager.pipelines == {}
        assert hasattr(manager, 'hooks')

    def test_create_pipeline(self):
        """Test creating pipeline builder"""
        manager = PipelineManager()
        builder = manager.create_pipeline("test")
        
        assert isinstance(builder, PipelineBuilder)
        assert builder.config.name == "test"

    def test_add_and_get_pipeline(self):
        """Test adding and getting pipeline"""
        manager = PipelineManager()
        
        # Create mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.config.name = "test_pipeline"
        
        # Add pipeline
        manager.add_pipeline(mock_pipeline)
        assert "test_pipeline" in manager.pipelines
        
        # Get pipeline
        retrieved = manager.get_pipeline("test_pipeline")
        assert retrieved is mock_pipeline
        
        # Get non-existent pipeline
        assert manager.get_pipeline("nonexistent") is None

    def test_list_pipelines(self):
        """Test listing pipelines"""
        manager = PipelineManager()
        
        # Add mock pipelines
        for i in range(3):
            mock_pipeline = Mock()
            mock_pipeline.config.name = f"pipeline_{i}"
            manager.add_pipeline(mock_pipeline)
        
        pipeline_list = manager.list_pipelines()
        assert len(pipeline_list) == 3
        assert "pipeline_0" in pipeline_list
        assert "pipeline_1" in pipeline_list
        assert "pipeline_2" in pipeline_list

    def test_remove_pipeline(self):
        """Test removing pipeline"""
        manager = PipelineManager()
        
        mock_pipeline = Mock()
        mock_pipeline.config.name = "to_remove"
        manager.add_pipeline(mock_pipeline)
        
        assert "to_remove" in manager.pipelines
        
        manager.remove_pipeline("to_remove")
        assert "to_remove" not in manager.pipelines
        
        # Removing non-existent pipeline should not error
        manager.remove_pipeline("nonexistent")

    def test_execute_pipeline(self):
        """Test executing pipeline by name"""
        manager = PipelineManager()
        
        mock_pipeline = Mock()
        mock_pipeline.config.name = "executable"
        mock_pipeline.process_sync.return_value = {"result": "success"}
        
        manager.add_pipeline(mock_pipeline)
        
        result = manager.execute_pipeline("executable", input_data={"test": "data"})
        assert result == {"result": "success"}
        mock_pipeline.process_sync.assert_called_once_with(input_data={"test": "data"})

    def test_execute_nonexistent_pipeline(self):
        """Test executing non-existent pipeline"""
        manager = PipelineManager()
        
        with pytest.raises(ValueError, match="Pipeline not found"):
            manager.execute_pipeline("nonexistent")

    def test_load_pipeline_from_file(self):
        """Test loading pipeline from configuration file"""
        manager = PipelineManager()
        
        yaml_content = """
        name: loaded_pipeline
        description: Loaded from file
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            with patch('strataregula.pipe.pipeline.Pipeline') as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline.config.name = "loaded_pipeline"
                mock_pipeline_class.return_value = mock_pipeline
                
                pipeline = manager.load_pipeline_from_file(temp_file)
                
                assert "loaded_pipeline" in manager.pipelines
                assert pipeline is mock_pipeline
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_save_all_pipelines(self):
        """Test saving all pipeline configurations"""
        manager = PipelineManager()
        
        # Add mock pipelines
        for i in range(2):
            mock_pipeline = Mock()
            mock_pipeline.config.name = f"pipeline_{i}"
            mock_pipeline.config.save_to_file = Mock()
            manager.add_pipeline(mock_pipeline)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            manager.save_all_pipelines(temp_dir)
            
            # Verify save_to_file was called for each pipeline
            for pipeline in manager.pipelines.values():
                pipeline.config.save_to_file.assert_called_once()