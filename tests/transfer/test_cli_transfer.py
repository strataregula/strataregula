"""
Unit tests for Transfer CLI

Tests for CLI commands, argument parsing, and integration.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from strataregula.transfer.cli_transfer import (
    TransferCLI, transfer_plan_command, transfer_apply_command
)


class TestTransferCLI:
    """Test TransferCLI functionality"""
    
    def test_cli_initialization(self):
        """Test CLI initialization"""
        cli = TransferCLI()
        
        assert cli.hooks is None
        assert cli.di is None
    
    def test_cli_initialization_with_dependencies(self, mock_hook_manager, mock_di_container):
        """Test CLI initialization with dependencies"""
        cli = TransferCLI(hooks=mock_hook_manager, di=mock_di_container)
        
        assert cli.hooks is mock_hook_manager
        assert cli.di is mock_di_container


class TestTransferCLIPlan:
    """Test transfer plan CLI command"""
    
    def test_plan_basic(self, temp_json_file, temp_policy_file):
        """Test basic plan command"""
        cli = TransferCLI()
        
        result = cli.plan(
            source_file=temp_json_file,
            policy_file=temp_policy_file
        )
        
        assert result == 0  # Success exit code
    
    def test_plan_no_policy(self, temp_json_file):
        """Test plan command without policy file"""
        cli = TransferCLI()
        
        result = cli.plan(source_file=temp_json_file)
        
        assert result == 0  # Should succeed with empty ruleset
    
    def test_plan_nonexistent_file(self):
        """Test plan command with nonexistent file"""
        cli = TransferCLI()
        
        result = cli.plan(source_file="nonexistent.json")
        
        assert result == 1  # Error exit code
    
    def test_plan_with_output_file(self, temp_json_file, temp_policy_file):
        """Test plan command with output file"""
        cli = TransferCLI()
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as out_file:
            output_file = out_file.name
        
        try:
            result = cli.plan(
                source_file=temp_json_file,
                policy_file=temp_policy_file,
                output=output_file
            )
            
            assert result == 0
            
            # Check output file was created
            output_path = Path(output_file)
            assert output_path.exists()
            
            # Check output content
            plan_data = json.loads(output_path.read_text())
            assert "stats" in plan_data
            assert "provenance" in plan_data
            assert "items" in plan_data
            
        finally:
            Path(output_file).unlink(missing_ok=True)
    
    @patch('builtins.print')
    def test_plan_display_output(self, mock_print, temp_json_file):
        """Test plan display output"""
        cli = TransferCLI()
        
        result = cli.plan(source_file=temp_json_file)
        
        assert result == 0
        # Check that output was printed
        assert mock_print.called
        
        # Check for expected output elements
        printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
        assert "Transfer Plan Summary" in printed_text
    
    def test_plan_invalid_json_file(self):
        """Test plan with invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            cli = TransferCLI()
            result = cli.plan(source_file=temp_path)
            
            assert result == 1  # Error exit code
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_plan_invalid_policy_file(self, temp_json_file):
        """Test plan with invalid policy file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name
        
        try:
            cli = TransferCLI()
            result = cli.plan(
                source_file=temp_json_file,
                policy_file=temp_path
            )
            
            assert result == 1  # Error exit code
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestTransferCLIApply:
    """Test transfer apply CLI command"""
    
    def test_apply_basic(self, temp_json_file, temp_policy_file):
        """Test basic apply command"""
        cli = TransferCLI()
        
        result = cli.apply(
            source_file=temp_json_file,
            policy_file=temp_policy_file
        )
        
        assert result == 0  # Success exit code
    
    def test_apply_with_output_file(self, temp_json_file, temp_policy_file):
        """Test apply command with output file"""
        cli = TransferCLI()
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as out_file:
            output_file = out_file.name
        
        try:
            result = cli.apply(
                source_file=temp_json_file,
                policy_file=temp_policy_file,
                output=output_file
            )
            
            assert result == 0
            
            # Check output file was created and contains data
            output_path = Path(output_file)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
        finally:
            Path(output_file).unlink(missing_ok=True)
    
    def test_apply_with_provenance(self, temp_json_file, temp_policy_file):
        """Test apply command with provenance"""
        cli = TransferCLI()
        
        result = cli.apply(
            source_file=temp_json_file,
            policy_file=temp_policy_file,
            provenance=True
        )
        
        assert result == 0
    
    def test_apply_with_diff_output(self, temp_json_file, temp_policy_file):
        """Test apply command with diff output"""
        cli = TransferCLI()
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as diff_file:
            diff_output = diff_file.name
        
        try:
            result = cli.apply(
                source_file=temp_json_file,
                policy_file=temp_policy_file,
                diff=diff_output
            )
            
            assert result == 0
            
            # Check diff file was created
            diff_path = Path(diff_output)
            assert diff_path.exists()
            
        finally:
            Path(diff_output).unlink(missing_ok=True)
    
    @patch('builtins.print')
    def test_apply_dry_run(self, mock_print, temp_json_file, temp_policy_file):
        """Test apply command with dry run"""
        cli = TransferCLI()
        
        result = cli.apply(
            source_file=temp_json_file,
            policy_file=temp_policy_file,
            dry_run=True
        )
        
        assert result == 0
        
        # Check dry run output
        printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
        assert "DRY RUN" in printed_text
    
    @patch('builtins.print')
    def test_apply_display_result(self, mock_print, temp_json_file):
        """Test apply result display"""
        cli = TransferCLI()
        
        result = cli.apply(source_file=temp_json_file)
        
        assert result == 0
        assert mock_print.called
        
        # Check for expected output elements
        printed_text = ' '.join([str(call.args[0]) for call in mock_print.call_args_list])
        assert "Transfer Complete" in printed_text
    
    def test_apply_nonexistent_file(self):
        """Test apply with nonexistent file"""
        cli = TransferCLI()
        
        result = cli.apply(source_file="nonexistent.json")
        
        assert result == 1  # Error exit code
    
    def test_apply_with_validation_schema(self, temp_json_file):
        """Test apply with validation schema"""
        # Create dummy schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"type": "object"}, f)
            schema_file = f.name
        
        try:
            cli = TransferCLI()
            result = cli.apply(
                source_file=temp_json_file,
                validate_schema=schema_file
            )
            
            assert result == 0  # Should succeed (validation is placeholder)
            
        finally:
            Path(schema_file).unlink(missing_ok=True)


class TestTransferCLIFileHandling:
    """Test CLI file handling functionality"""
    
    def test_load_json_file(self, temp_json_file):
        """Test loading JSON file"""
        cli = TransferCLI()
        
        data = cli._load_data(temp_json_file)
        
        assert isinstance(data, dict)
        assert "users" in data
        assert len(data["users"]) == 2
    
    def test_load_yaml_file(self, temp_policy_file):
        """Test loading YAML file"""
        cli = TransferCLI()
        
        data = cli._load_data(temp_policy_file)
        
        assert isinstance(data, dict)
        assert "copy_policies" in data
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file"""
        cli = TransferCLI()
        
        with pytest.raises(FileNotFoundError):
            cli._load_data("nonexistent.json")
    
    def test_load_invalid_file(self):
        """Test loading invalid file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json or yaml")
            temp_path = f.name
        
        try:
            cli = TransferCLI()
            
            with pytest.raises(ValueError):
                cli._load_data(temp_path)
                
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_load_policy_file(self, temp_policy_file):
        """Test loading policy file"""
        cli = TransferCLI()
        
        ruleset = cli._load_policy(temp_policy_file)
        
        assert ruleset is not None
        rules = ruleset.list_rules()
        assert len(rules) > 0
    
    def test_get_output_stream_stdout(self):
        """Test getting stdout stream"""
        cli = TransferCLI()
        
        stream = cli._get_output_stream(None)
        
        import sys
        assert stream is sys.stdout
    
    def test_get_output_stream_file(self):
        """Test getting file stream"""
        cli = TransferCLI()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            stream = cli._get_output_stream(temp_path)
            
            assert stream is not None
            assert hasattr(stream, 'write')
            
            # Clean up
            stream.close()
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestTransferCLIIntegration:
    """Integration tests for Transfer CLI"""
    
    def test_full_plan_apply_workflow(self, temp_json_file, temp_policy_file):
        """Test complete plan -> apply workflow"""
        cli = TransferCLI()
        
        # First, create a plan
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as plan_file:
            plan_path = plan_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # Plan
            plan_result = cli.plan(
                source_file=temp_json_file,
                policy_file=temp_policy_file,
                output=plan_path
            )
            assert plan_result == 0
            
            # Apply
            apply_result = cli.apply(
                source_file=temp_json_file,
                policy_file=temp_policy_file,
                output=output_path,
                provenance=True
            )
            assert apply_result == 0
            
            # Verify output files exist
            assert Path(plan_path).exists()
            assert Path(output_path).exists()
            
            # Verify plan content
            plan_data = json.loads(Path(plan_path).read_text())
            assert "stats" in plan_data
            assert "provenance" in plan_data
            
        finally:
            Path(plan_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)
    
    def test_cli_with_hooks_integration(self, temp_json_file, mock_hook_manager):
        """Test CLI with hooks integration"""
        cli = TransferCLI(hooks=mock_hook_manager)
        
        result = cli.apply(source_file=temp_json_file)
        
        assert result == 0
        
        # Check that hooks were called
        events = mock_hook_manager.get_events()
        assert len(events) > 0
        
        # Should have start and finish events at minimum
        event_names = [e["event"] for e in events]
        assert "copy:start" in event_names
        assert "copy:finish" in event_names


class TestTransferCommandFunctions:
    """Test CLI command functions for integration"""
    
    def test_transfer_plan_command(self, temp_json_file, temp_policy_file):
        """Test transfer plan command function"""
        # Mock args object
        args = Mock()
        args.source = temp_json_file
        args.policy = temp_policy_file
        args.select = None
        args.output = None
        
        result = transfer_plan_command(args)
        
        assert result == 0
    
    def test_transfer_apply_command(self, temp_json_file, temp_policy_file):
        """Test transfer apply command function"""
        # Mock args object
        args = Mock()
        args.source = temp_json_file
        args.policy = temp_policy_file
        args.output = None
        args.provenance = False
        args.diff = None
        args.dry_run = False
        args.validate = None
        
        result = transfer_apply_command(args)
        
        assert result == 0
    
    def test_transfer_plan_command_missing_args(self, temp_json_file):
        """Test transfer plan command with missing optional args"""
        args = Mock()
        args.source = temp_json_file
        # Missing optional attributes should use getattr defaults
        
        result = transfer_plan_command(args)
        
        assert result == 0
    
    def test_transfer_apply_command_missing_args(self, temp_json_file):
        """Test transfer apply command with missing optional args"""
        args = Mock()
        args.source = temp_json_file
        # Missing optional attributes should use getattr defaults
        
        result = transfer_apply_command(args)
        
        assert result == 0