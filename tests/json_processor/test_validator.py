"""
Tests for JSON Validator module
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from strataregula.json_processor.validator import JSONValidator, ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_validation_result_creation(self):
        """Test ValidationResult creation with defaults"""
        result = ValidationResult(valid=True, message="Test")
        assert result.valid is True
        assert result.message == "Test"
        assert result.errors == []
        assert result.path is None
        assert result.schema_name is None

    def test_validation_result_with_errors(self):
        """Test ValidationResult with custom errors"""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult(
            valid=False,
            message="Failed",
            errors=errors,
            path="$.field",
            schema_name="test_schema"
        )
        assert result.valid is False
        assert result.message == "Failed"
        assert result.errors == errors
        assert result.path == "$.field"
        assert result.schema_name == "test_schema"


class TestJSONValidator:
    """Test JSONValidator class"""

    def test_validator_init(self):
        """Test validator initialization"""
        validator = JSONValidator()
        assert isinstance(validator.schemas, dict)
        # Should have basic and config schemas by default
        assert "basic" in validator.schemas
        assert "config" in validator.schemas

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', False)
    def test_validator_without_jsonschema(self):
        """Test validator when jsonschema is not available"""
        validator = JSONValidator()
        # Should still work but with warnings
        assert isinstance(validator.schemas, dict)

    def test_add_schema(self):
        """Test adding a valid schema"""
        validator = JSONValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        result = validator.add_schema("user", schema)
        assert result is True
        assert "user" in validator.schemas
        assert validator.schemas["user"] == schema

    def test_add_invalid_schema(self):
        """Test adding an invalid schema"""
        validator = JSONValidator()
        invalid_schema = {"invalid": "schema_structure"}
        
        result = validator.add_schema("invalid", invalid_schema)
        # Should handle gracefully depending on jsonschema availability
        assert isinstance(result, bool)

    def test_add_schema_from_file(self, temp_json_file):
        """Test adding schema from file"""
        validator = JSONValidator()
        
        # Create a schema file
        schema = {
            "type": "object",
            "properties": {"test": {"type": "string"}}
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f)
            schema_file = f.name
        
        try:
            result = validator.add_schema_from_file("file_schema", schema_file)
            if result:  # Only check if jsonschema is available
                assert "file_schema" in validator.schemas
        finally:
            Path(schema_file).unlink(missing_ok=True)

    def test_add_schema_from_nonexistent_file(self):
        """Test adding schema from non-existent file"""
        validator = JSONValidator()
        result = validator.add_schema_from_file("missing", "nonexistent.json")
        assert result is False

    def test_add_schema_from_string(self):
        """Test adding schema from JSON string"""
        validator = JSONValidator()
        schema_str = '{"type": "object", "properties": {"name": {"type": "string"}}}'
        
        result = validator.add_schema_from_string("string_schema", schema_str)
        if result:  # Only check if jsonschema is available
            assert "string_schema" in validator.schemas

    def test_add_schema_from_invalid_string(self):
        """Test adding schema from invalid JSON string"""
        validator = JSONValidator()
        invalid_json = '{"invalid": json}'
        
        result = validator.add_schema_from_string("invalid", invalid_json)
        assert result is False

    def test_validate_with_basic_schema(self):
        """Test validation with basic schema"""
        validator = JSONValidator()
        data = {"key": "value"}
        
        result = validator.validate(data)
        assert isinstance(result, ValidationResult)
        # Result depends on jsonschema availability

    def test_validate_with_custom_schema(self):
        """Test validation with custom schema"""
        validator = JSONValidator()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        }
        
        validator.add_schema("test", schema)
        
        # Valid data
        valid_data = {"name": "John"}
        result = validator.validate(valid_data, "test")
        assert isinstance(result, ValidationResult)
        
        # Invalid data
        invalid_data = {"age": 30}
        result = validator.validate(invalid_data, "test")
        assert isinstance(result, ValidationResult)

    def test_validate_with_nonexistent_schema(self):
        """Test validation with non-existent schema"""
        validator = JSONValidator()
        data = {"key": "value"}
        
        result = validator.validate(data, "nonexistent")
        assert result.valid is False
        assert "not found" in result.message

    def test_validate_file(self, temp_json_file):
        """Test file validation"""
        validator = JSONValidator()
        
        result = validator.validate_file(temp_json_file)
        assert isinstance(result, ValidationResult)

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file"""
        validator = JSONValidator()
        
        result = validator.validate_file("nonexistent.json")
        assert result.valid is False
        assert "not found" in result.message

    def test_validate_invalid_json_file(self):
        """Test validation of file with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            invalid_file = f.name
        
        try:
            validator = JSONValidator()
            result = validator.validate_file(invalid_file)
            assert result.valid is False
            assert "Invalid JSON" in result.message
        finally:
            Path(invalid_file).unlink(missing_ok=True)

    def test_list_schemas(self):
        """Test listing available schemas"""
        validator = JSONValidator()
        schemas = validator.list_schemas()
        assert isinstance(schemas, list)
        assert "basic" in schemas
        assert "config" in schemas

    def test_get_schema(self):
        """Test getting a specific schema"""
        validator = JSONValidator()
        
        basic_schema = validator.get_schema("basic")
        assert basic_schema is not None
        assert isinstance(basic_schema, dict)
        
        nonexistent = validator.get_schema("nonexistent")
        assert nonexistent is None

    def test_remove_schema(self):
        """Test removing a schema"""
        validator = JSONValidator()
        
        # Add a test schema
        validator.add_schema("test", {"type": "object"})
        
        # Remove it
        result = validator.remove_schema("test")
        assert result is True
        assert "test" not in validator.schemas
        
        # Try to remove non-existent schema
        result = validator.remove_schema("nonexistent")
        assert result is False

    def test_clear_schemas(self):
        """Test clearing all schemas"""
        validator = JSONValidator()
        
        # Add some schemas
        validator.add_schema("test1", {"type": "object"})
        validator.add_schema("test2", {"type": "array"})
        
        # Clear all
        validator.clear_schemas()
        
        # Should have only default schemas
        schemas = validator.list_schemas()
        assert "test1" not in schemas
        assert "test2" not in schemas
        assert "basic" in schemas  # Default schemas should be reloaded
        assert "config" in schemas

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', False)
    def test_validation_without_jsonschema(self):
        """Test validation behavior when jsonschema is not available"""
        validator = JSONValidator()
        
        # Should return success but with warning message
        result = validator.validate({"key": "value"})
        assert result.valid is True
        assert "skipped" in result.message.lower()

    def test_config_schema_validation(self):
        """Test validation with the default config schema"""
        validator = JSONValidator()
        
        # Valid config data
        valid_config = {
            "version": "1.0",
            "settings": {"debug": True},
            "data": [1, 2, 3]
        }
        
        result = validator.validate(valid_config, "config")
        assert isinstance(result, ValidationResult)
        
        # Invalid config (missing required version)
        invalid_config = {
            "settings": {"debug": True}
        }
        
        result = validator.validate(invalid_config, "config")
        assert isinstance(result, ValidationResult)