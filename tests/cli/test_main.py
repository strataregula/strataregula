"""
Unit tests for CLI main module

Tests for main CLI commands, argument parsing, and error handling.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, mock_open
import json
import yaml

from strataregula.cli.main import cli, main


class TestCLIMain:
    """Test main CLI functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_cli_version(self):
        """Test CLI version display"""
        result = self.runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "2.0.0" in result.output
    
    def test_cli_help(self):
        """Test CLI help display"""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Strataregula" in result.output
        assert "YAML Configuration Pattern Compiler" in result.output
    
    def test_cli_verbose_flag(self):
        """Test verbose flag"""
        result = self.runner.invoke(cli, ['--verbose', '--help'])
        
        assert result.exit_code == 0
        # Note: verbose output would show in stderr or with special handling
    
    def test_cli_quiet_flag(self):
        """Test quiet flag"""
        result = self.runner.invoke(cli, ['--quiet', '--help'])
        
        assert result.exit_code == 0
        # Quiet mode should suppress the banner


class TestProcessCommand:
    """Test process command"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    @patch('strataregula.cli.main.ProcessCommand')
    def test_process_with_file(self, mock_process_cmd):
        """Test process command with file input"""
        mock_instance = Mock()
        mock_process_cmd.return_value = mock_instance
        mock_instance.execute.return_value = {"result": "success"}
        
        with self.runner.isolated_filesystem():
            with open('test.yaml', 'w') as f:
                yaml.dump({"test": "data"}, f)
            
            result = self.runner.invoke(cli, ['process', 'test.yaml'])
        
        assert result.exit_code == 0
        mock_process_cmd.assert_called_once()
        mock_instance.execute.assert_called_once()
    
    @patch('strataregula.cli.main.ProcessCommand')
    def test_process_with_stdin(self, mock_process_cmd):
        """Test process command with stdin input"""
        mock_instance = Mock()
        mock_process_cmd.return_value = mock_instance
        mock_instance.execute.return_value = {"result": "success"}
        
        result = self.runner.invoke(cli, ['process', '--stdin'])
        
        assert result.exit_code == 0
        mock_process_cmd.assert_called_once()
        mock_instance.execute.assert_called_once()
        
        # Check that stdin=True was passed
        call_args = mock_instance.execute.call_args
        assert call_args[1]['stdin'] is True
    
    def test_process_missing_input(self):
        """Test process command without input"""
        result = self.runner.invoke(cli, ['process'])
        
        assert result.exit_code == 1
        assert "Must specify either --stdin or input file" in result.output
    
    def test_process_both_stdin_and_file(self):
        """Test process command with both stdin and file"""
        result = self.runner.invoke(cli, ['process', '--stdin', 'file.yaml'])
        
        assert result.exit_code == 1
        assert "Cannot specify both --stdin and input file" in result.output
    
    @patch('strataregula.cli.main.ProcessCommand')
    def test_process_with_options(self, mock_process_cmd):
        """Test process command with various options"""
        mock_instance = Mock()
        mock_process_cmd.return_value = mock_instance
        mock_instance.execute.return_value = {"result": "success"}
        
        with self.runner.isolated_filesystem():
            with open('test.yaml', 'w') as f:
                yaml.dump({"test": "data"}, f)
            
            result = self.runner.invoke(cli, [
                'process', 'test.yaml',
                '--format', 'yaml',
                '--output', 'output.yaml',
                '--output-format', 'json',
                '--command', 'filter:condition="test"',
                '--command', 'transform:expression="data"'
            ])
        
        assert result.exit_code == 0
        
        # Check arguments passed to execute
        call_args = mock_instance.execute.call_args[1]
        assert call_args['format'] == 'yaml'
        assert call_args['output'] == 'output.yaml'
        assert call_args['output_format'] == 'json'
        assert len(call_args['commands']) == 2
    
    @patch('strataregula.cli.main.ProcessCommand')
    def test_process_error_handling(self, mock_process_cmd):
        """Test process command error handling"""
        mock_instance = Mock()
        mock_process_cmd.return_value = mock_instance
        mock_instance.execute.side_effect = ValueError("Test error")
        
        result = self.runner.invoke(cli, ['process', '--stdin'])
        
        assert result.exit_code == 1
        assert "Error: Test error" in result.output
    
    @patch('strataregula.cli.main.ProcessCommand')
    def test_process_verbose_error(self, mock_process_cmd):
        """Test process command error with verbose output"""
        mock_instance = Mock()
        mock_process_cmd.return_value = mock_instance
        mock_instance.execute.side_effect = ValueError("Test error")
        
        result = self.runner.invoke(cli, ['--verbose', 'process', '--stdin'])
        
        assert result.exit_code == 1
        assert "Error: Test error" in result.output


class TestCreateCommand:
    """Test create command"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    @patch('strataregula.cli.main.PipelineCommand')
    def test_create_basic(self, mock_pipeline_cmd):
        """Test basic pipeline creation"""
        mock_instance = Mock()
        mock_pipeline_cmd.return_value = mock_instance
        mock_pipeline = Mock()
        mock_instance.create.return_value = mock_pipeline
        
        result = self.runner.invoke(cli, ['create', 'test-pipeline'])
        
        assert result.exit_code == 0
        mock_instance.create.assert_called_once()
        assert "created successfully" in result.output
    
    @patch('strataregula.cli.main.PipelineCommand')
    def test_create_with_options(self, mock_pipeline_cmd):
        """Test pipeline creation with options"""
        mock_instance = Mock()
        mock_pipeline_cmd.return_value = mock_instance
        mock_pipeline = Mock()
        mock_instance.create.return_value = mock_pipeline
        
        result = self.runner.invoke(cli, [
            'create', 'test-pipeline',
            '--description', 'Test pipeline',
            '--input-format', 'json',
            '--output-format', 'yaml',
            '--command', 'filter:test',
            '--command', 'transform:test'
        ])
        
        assert result.exit_code == 0
        
        # Check arguments
        call_args = mock_instance.create.call_args[1]
        assert call_args['name'] == 'test-pipeline'
        assert call_args['description'] == 'Test pipeline'
        assert call_args['input_format'] == 'json'
        assert call_args['output_format'] == 'yaml'
        assert len(call_args['commands']) == 2
    
    @patch('strataregula.cli.main.PipelineCommand')
    def test_create_with_save(self, mock_pipeline_cmd):
        """Test pipeline creation with save option"""
        mock_instance = Mock()
        mock_pipeline_cmd.return_value = mock_instance
        mock_pipeline = Mock()
        mock_pipeline.config = Mock()
        mock_instance.create.return_value = mock_pipeline
        
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, [
                'create', 'test-pipeline',
                '--save', 'pipeline.yaml'
            ])
        
        assert result.exit_code == 0
        mock_pipeline.config.save_to_file.assert_called_once_with('pipeline.yaml')
        assert "saved to pipeline.yaml" in result.output
    
    @patch('strataregula.cli.main.PipelineCommand')
    def test_create_error_handling(self, mock_pipeline_cmd):
        """Test create command error handling"""
        mock_instance = Mock()
        mock_pipeline_cmd.return_value = mock_instance
        mock_instance.create.side_effect = ValueError("Creation failed")
        
        result = self.runner.invoke(cli, ['create', 'test-pipeline'])
        
        assert result.exit_code == 1
        assert "Error: Creation failed" in result.output


class TestListCommand:
    """Test list command"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    @patch('strataregula.cli.main.ListCommand')
    def test_list_basic(self, mock_list_cmd):
        """Test basic list command"""
        mock_instance = Mock()
        mock_list_cmd.return_value = mock_instance
        
        result = self.runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0
        mock_instance.list_commands.assert_called_once_with(category=None, search=None)
        mock_instance.list_pipelines.assert_called_once()
    
    @patch('strataregula.cli.main.ListCommand')
    def test_list_with_filters(self, mock_list_cmd):
        """Test list command with filters"""
        mock_instance = Mock()
        mock_list_cmd.return_value = mock_instance
        
        result = self.runner.invoke(cli, [
            'list',
            '--category', 'transform',
            '--search', 'filter'
        ])
        
        assert result.exit_code == 0
        mock_instance.list_commands.assert_called_once_with(
            category='transform', 
            search='filter'
        )
    
    @patch('strataregula.cli.main.ListCommand')
    def test_list_error_handling(self, mock_list_cmd):
        """Test list command error handling"""
        mock_instance = Mock()
        mock_list_cmd.return_value = mock_instance
        mock_instance.list_commands.side_effect = ValueError("List failed")
        
        result = self.runner.invoke(cli, ['list'])
        
        assert result.exit_code == 1
        assert "Error: List failed" in result.output


class TestRunCommand:
    """Test run command"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    @patch('strataregula.cli.main.yaml')
    def test_run_with_file(self, mock_yaml):
        """Test run command with file input"""
        mock_yaml.dump.return_value = "result: data"
        
        with patch('strataregula.cli.main.PipelineManager') as mock_pm_class:
            mock_pm = Mock()
            mock_pm_class.return_value = mock_pm
            mock_pm.execute_pipeline.return_value = {"result": "data"}
            
            with self.runner.isolated_filesystem():
                with open('input.yaml', 'w') as f:
                    yaml.dump({"input": "data"}, f)
                
                result = self.runner.invoke(cli, ['run', 'test-pipeline', 'input.yaml'])
        
        assert result.exit_code == 0
        mock_pm.execute_pipeline.assert_called_once_with(
            'test-pipeline', 
            input_file='input.yaml'
        )
    
    def test_run_with_stdin(self):
        """Test run command with stdin input"""
        with patch('strataregula.cli.main.PipelineManager') as mock_pm_class:
            mock_pm = Mock()
            mock_pm_class.return_value = mock_pm
            mock_pm.execute_pipeline.return_value = {"result": "data"}
            
            result = self.runner.invoke(cli, ['run', 'test-pipeline', '--stdin'])
        
        assert result.exit_code == 0
        mock_pm.execute_pipeline.assert_called_once_with(
            'test-pipeline',
            input_stdin=True
        )
    
    def test_run_missing_input(self):
        """Test run command without input"""
        result = self.runner.invoke(cli, ['run', 'test-pipeline'])
        
        assert result.exit_code == 1
        assert "Must specify either --stdin or input file" in result.output
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('strataregula.cli.main.yaml')
    def test_run_with_output_file(self, mock_yaml, mock_file):
        """Test run command with output file"""
        with patch('strataregula.cli.main.PipelineManager') as mock_pm_class:
            mock_pm = Mock()
            mock_pm_class.return_value = mock_pm
            mock_pm.execute_pipeline.return_value = {"result": "data"}
            
            result = self.runner.invoke(cli, [
                'run', 'test-pipeline', '--stdin', '--output', 'output.yaml'
            ])
        
        assert result.exit_code == 0
        mock_file.assert_called_once_with('output.yaml', 'w')
        assert "saved to output.yaml" in result.output
    
    def test_run_error_handling(self):
        """Test run command error handling"""
        with patch('strataregula.cli.main.PipelineManager') as mock_pm_class:
            mock_pm = Mock()
            mock_pm_class.return_value = mock_pm
            mock_pm.execute_pipeline.side_effect = ValueError("Pipeline failed")
            
            result = self.runner.invoke(cli, ['run', 'test-pipeline', '--stdin'])
        
        assert result.exit_code == 1
        assert "Error: Pipeline failed" in result.output


class TestExamplesCommand:
    """Test examples command"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_examples(self):
        """Test examples command"""
        result = self.runner.invoke(cli, ['examples'])
        
        assert result.exit_code == 0
        assert "Basic Usage:" in result.output
        assert "Advanced Usage:" in result.output
        assert "strataregula process" in result.output
        assert "strataregula create" in result.output


class TestMainFunction:
    """Test main function and error handling"""
    
    @patch('strataregula.cli.main.cli')
    def test_main_success(self, mock_cli):
        """Test successful main execution"""
        mock_cli.return_value = None
        
        # Should not raise
        main()
        mock_cli.assert_called_once()
    
    @patch('strataregula.cli.main.cli')
    @patch('strataregula.cli.main.sys.exit')
    def test_main_keyboard_interrupt(self, mock_exit, mock_cli):
        """Test main with keyboard interrupt"""
        mock_cli.side_effect = KeyboardInterrupt()
        
        main()
        
        mock_exit.assert_called_once_with(130)
    
    @patch('strataregula.cli.main.cli')
    @patch('strataregula.cli.main.sys.exit')
    def test_main_unexpected_error(self, mock_exit, mock_cli):
        """Test main with unexpected error"""
        mock_cli.side_effect = RuntimeError("Unexpected error")
        
        main()
        
        mock_exit.assert_called_once_with(1)


class TestCLIIntegration:
    """Integration tests for CLI"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_cli_context_object(self):
        """Test CLI context object setup"""
        with patch('strataregula.cli.main.ProcessCommand') as mock_cmd:
            mock_instance = Mock()
            mock_cmd.return_value = mock_instance
            mock_instance.execute.return_value = {}
            
            result = self.runner.invoke(cli, ['--verbose', 'process', '--stdin'])
        
        # ProcessCommand should be called with context object
        mock_cmd.assert_called_once()
        ctx_obj = mock_cmd.call_args[0][0]
        
        assert 'verbose' in ctx_obj
        assert 'quiet' in ctx_obj
        assert 'pipeline_manager' in ctx_obj
        assert 'hook_manager' in ctx_obj
        assert ctx_obj['verbose'] is True
    
    @patch('strataregula.cli.main.ProcessCommand')
    @patch('strataregula.cli.main.PipelineCommand') 
    @patch('strataregula.cli.main.ListCommand')
    def test_command_objects_creation(self, mock_list, mock_pipeline, mock_process):
        """Test that command objects are created with context"""
        mock_list.return_value = Mock()
        mock_pipeline.return_value = Mock() 
        mock_process_instance = Mock()
        mock_process_instance.execute.return_value = {}
        mock_process.return_value = mock_process_instance
        
        # Test multiple commands use same context pattern
        self.runner.invoke(cli, ['process', '--stdin'])
        self.runner.invoke(cli, ['create', 'test'])
        self.runner.invoke(cli, ['list'])
        
        # All should be called with context object
        assert mock_process.called
        assert mock_pipeline.called  
        assert mock_list.called