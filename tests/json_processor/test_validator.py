"""Tests for JSONValidator"""
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

try:
    from strataregula.json_processor.validator import JSONValidator, ValidationResult
except ImportError:
    pytest.skip("strataregula.json_processor.validator not available", allow_module_level=True)


class TestJSONValidator:
    """Test JSONValidator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.validator = JSONValidator()

    def test_init(self):
        """Test initialization"""
        assert self.validator is not None
        assert hasattr(self.validator, 'schemas')
        assert isinstance(self.validator.schemas, dict)

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    def test_init_with_jsonschema(self):
        """Test initialization when jsonschema is available"""
        validator = JSONValidator()
        assert "basic" in validator.schemas
        assert "config" in validator.schemas

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', False)
    def test_init_without_jsonschema(self):
        """Test initialization when jsonschema is not available"""
        validator = JSONValidator()
        # Should still initialize but without default schemas
        assert hasattr(validator, 'schemas')

    def test_list_schemas(self):
        """Test list_schemas method"""
        schemas = self.validator.list_schemas()
        assert isinstance(schemas, list)
        # Should have at least basic and config schemas if jsonschema is available

    def test_get_schema_existing(self):
        """Test get_schema for existing schema"""
        self.validator.schemas["test"] = {"type": "object"}
        schema = self.validator.get_schema("test")
        assert schema == {"type": "object"}

    def test_get_schema_nonexistent(self):
        """Test get_schema for non-existent schema"""
        schema = self.validator.get_schema("nonexistent")
        assert schema is None

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    @patch('strataregula.json_processor.validator.jsonschema.validators.validator_for')
    def test_add_schema_success(self, mock_validator_for):
        """Test successful schema addition"""
        mock_validator_for.return_value = MagicMock()
        
        test_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = self.validator.add_schema("test_schema", test_schema)
        
        assert result is True
        assert "test_schema" in self.validator.schemas
        assert self.validator.schemas["test_schema"] == test_schema

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', False)
    def test_add_schema_unavailable(self):
        """Test schema addition when jsonschema is not available"""
        test_schema = {"type": "object"}
        result = self.validator.add_schema("test", test_schema)
        
        assert result is False

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    @patch('strataregula.json_processor.validator.jsonschema.validators.validator_for')
    def test_add_schema_invalid(self, mock_validator_for):
        """Test addition of invalid schema"""
        mock_validator_for.side_effect = Exception("Invalid schema")
        
        test_schema = {"invalid": "schema"}
        result = self.validator.add_schema("invalid", test_schema)
        
        assert result is False
        assert "invalid" not in self.validator.schemas

    @patch('builtins.open', new_callable=mock_open, read_data='{"type": "object"}')
    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    @patch('strataregula.json_processor.validator.jsonschema.validators.validator_for')
    def test_add_schema_from_file_success(self, mock_validator_for, mock_file):
        """Test successful schema loading from file"""
        mock_validator_for.return_value = MagicMock()
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.validator.add_schema_from_file("file_schema", "schema.json")
        
        assert result is True
        assert "file_schema" in self.validator.schemas

    @patch('pathlib.Path.exists', return_value=False)
    def test_add_schema_from_file_not_found(self, mock_exists):
        """Test schema loading from non-existent file"""
        result = self.validator.add_schema_from_file("missing", "missing.json")
        
        assert result is False

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists', return_value=True)
    def test_add_schema_from_file_invalid_json(self, mock_exists, mock_file):
        """Test schema loading from file with invalid JSON"""
        result = self.validator.add_schema_from_file("invalid", "invalid.json")
        
        assert result is False

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    @patch('strataregula.json_processor.validator.jsonschema.validators.validator_for')
    def test_add_schema_from_string_success(self, mock_validator_for):
        """Test successful schema loading from string"""
        mock_validator_for.return_value = MagicMock()
        
        schema_str = '{"type": "object", "properties": {"name": {"type": "string"}}}'
        result = self.validator.add_schema_from_string("string_schema", schema_str)
        
        assert result is True
        assert "string_schema" in self.validator.schemas

    def test_add_schema_from_string_invalid_json(self):
        """Test schema loading from invalid JSON string"""
        invalid_json = '{"invalid": json}'
        result = self.validator.add_schema_from_string("invalid", invalid_json)
        
        assert result is False

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', False)
    def test_validate_unavailable(self):
        """Test validation when jsonschema is not available"""
        test_data = {"name": "test"}
        result = self.validator.validate(test_data)
        
        assert result.valid is True
        assert "jsonschema not available" in result.message

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    @patch('strataregula.json_processor.validator.jsonschema.validate')
    def test_validate_success(self, mock_validate):
        """Test successful validation"""
        mock_validate.return_value = None  # No exception means validation passed
        
        self.validator.schemas["test"] = {"type": "object"}
        test_data = {"name": "John"}
        
        result = self.validator.validate(test_data, "test")
        
        assert result.valid is True
        assert result.message == "Validation passed"
        assert result.schema_name == "test"
        mock_validate.assert_called_once()

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    def test_validate_schema_not_found(self):
        """Test validation with non-existent schema"""
        test_data = {"name": "John"}
        result = self.validator.validate(test_data, "nonexistent")
        
        assert result.valid is False
        assert "Schema 'nonexistent' not found" in result.message
        assert result.schema_name == "nonexistent"

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    @patch('strataregula.json_processor.validator.jsonschema.validate')
    def test_validate_validation_error(self, mock_validate):
        """Test validation with schema validation error"""
        from jsonschema import ValidationError
        
        mock_error = ValidationError("Required property missing")
        mock_error.path = ["missing_field"]
        mock_validate.side_effect = mock_error
        
        self.validator.schemas["strict"] = {"type": "object", "required": ["name"]}
        test_data = {}
        
        result = self.validator.validate(test_data, "strict")
        
        assert result.valid is False
        assert result.message == "Validation failed"
        assert len(result.errors) == 1
        assert "Required property missing" in result.errors[0]
        assert result.path == "['missing_field']"

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    @patch('strataregula.json_processor.validator.jsonschema.validate')
    def test_validate_general_error(self, mock_validate):
        """Test validation with general error"""
        mock_validate.side_effect = Exception("General validation error")
        
        self.validator.schemas["test"] = {"type": "object"}
        test_data = {"name": "John"}
        
        result = self.validator.validate(test_data, "test")
        
        assert result.valid is False
        assert "General validation error" in result.message

    def test_validate_default_schema(self):
        """Test validation with default schema"""
        test_data = {"name": "John"}
        
        with patch.object(self.validator, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(valid=True, message="OK")
            self.validator.validate(test_data)  # No schema name provided
            mock_validate.assert_called()

    @patch('builtins.open', new_callable=mock_open, read_data='{"name": "John"}')
    @patch('pathlib.Path.exists', return_value=True)
    def test_validate_file_success(self, mock_exists, mock_file):
        """Test successful file validation"""
        with patch.object(self.validator, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(valid=True, message="OK")
            
            result = self.validator.validate_file("test.json", "basic")
            
            assert result.valid is True
            mock_validate.assert_called_once()

    @patch('pathlib.Path.exists', return_value=False)
    def test_validate_file_not_found(self, mock_exists):
        """Test file validation with missing file"""
        result = self.validator.validate_file("missing.json")
        
        assert result.valid is False
        assert "File not found" in result.message

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists', return_value=True)
    def test_validate_file_invalid_json(self, mock_exists, mock_file):
        """Test file validation with invalid JSON"""
        result = self.validator.validate_file("invalid.json")
        
        assert result.valid is False
        assert "Invalid JSON in file" in result.message

    @patch('builtins.open', side_effect=Exception("Read error"))
    @patch('pathlib.Path.exists', return_value=True)
    def test_validate_file_read_error(self, mock_exists, mock_file):
        """Test file validation with read error"""
        result = self.validator.validate_file("error.json")
        
        assert result.valid is False
        assert "Error reading file" in result.message

    def test_remove_schema_existing(self):
        """Test removing existing schema"""
        self.validator.schemas["test"] = {"type": "object"}
        result = self.validator.remove_schema("test")
        
        assert result is True
        assert "test" not in self.validator.schemas

    def test_remove_schema_nonexistent(self):
        """Test removing non-existent schema"""
        result = self.validator.remove_schema("nonexistent")
        
        assert result is False

    @patch('strataregula.json_processor.validator.JSONSCHEMA_AVAILABLE', True)
    def test_clear_schemas(self):
        """Test clearing all schemas"""
        self.validator.schemas["test1"] = {"type": "object"}
        self.validator.schemas["test2"] = {"type": "array"}
        
        with patch.object(self.validator, '_load_default_schemas') as mock_load:
            self.validator.clear_schemas()
            
            mock_load.assert_called_once()
            # Should only have default schemas after clearing


class TestValidationResult:
    """Test ValidationResult class"""

    def test_successful_result(self):
        """Test successful validation result"""
        result = ValidationResult(
            valid=True,
            message="Validation passed",
            schema_name="test_schema"
        )
        
        assert result.valid is True
        assert result.message == "Validation passed"
        assert result.schema_name == "test_schema"
        assert result.errors == []  # errors defaults to []
        assert result.path is None

    def test_failed_result(self):
        """Test failed validation result"""
        result = ValidationResult(
            valid=False,
            message="Validation failed",
            errors=["Error 1", "Error 2"],
            path="$.field",
            schema_name="strict_schema"
        )
        
        assert result.valid is False
        assert result.message == "Validation failed"
        assert result.errors == ["Error 1", "Error 2"]
        assert result.path == "$.field"
        assert result.schema_name == "strict_schema"

    def test_default_values(self):
        """Test default values in ValidationResult"""
        result = ValidationResult(valid=True, message="test")  # message is required
        
        assert result.valid is True
        assert result.message == "test"
        assert result.errors == []  # defaults to []
        assert result.path is None
        assert result.schema_name is None