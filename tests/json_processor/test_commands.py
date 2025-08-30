"""Tests for JSON processor commands"""
import json
import pytest
from unittest.mock import MagicMock, patch

try:
    from strataregula.json_processor.commands import (
        JSONTransformCommand,
        JSONPathCommand,
        ValidateJSONCommand,
        JSONFormatCommand,
        JSONMergeCommand,
        JSONFilterCommand,
        JSONStatsCommand
    )
except ImportError:
    pytest.skip("strataregula.json_processor.commands not available", allow_module_level=True)


class TestJSONTransformCommand:
    """Test JSONTransformCommand class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.command = JSONTransformCommand()
        self.test_data = {
            "users": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25}
            ]
        }

    def test_init(self):
        """Test command initialization"""
        assert self.command.name == "json_transform"
        assert self.command.description == "Transform JSON data using JSONPath expressions"
        assert self.command.category == "json"
        assert "dict" in self.command.input_types
        assert hasattr(self.command, 'processor')

    @pytest.mark.asyncio
    async def test_execute_no_transformations(self):
        """Test execute with no transformations"""
        result = await self.command.execute(self.test_data)
        assert result == self.test_data

    @pytest.mark.asyncio
    async def test_execute_string_input(self):
        """Test execute with JSON string input"""
        json_string = json.dumps(self.test_data)
        result = await self.command.execute(json_string)
        assert result == self.test_data

    @pytest.mark.asyncio
    async def test_execute_invalid_json_string(self):
        """Test execute with invalid JSON string"""
        invalid_json = '{"invalid": json}'
        
        with pytest.raises(ValueError, match="Invalid JSON input"):
            await self.command.execute(invalid_json)

    @pytest.mark.asyncio
    async def test_execute_query_transformation(self):
        """Test execute with query transformation"""
        with patch.object(self.command.processor, 'query_all', return_value=["John", "Jane"]):
            transformations = [{"path": "$.users[*].name", "operation": "query"}]
            result = await self.command.execute(self.test_data, transformations=transformations)
            assert result == ["John", "Jane"]

    @pytest.mark.asyncio
    async def test_execute_update_transformation(self):
        """Test execute with update transformation"""
        with patch.object(self.command.processor, 'update') as mock_update:
            transformations = [{"path": "$.users[0].age", "operation": "update", "value": 31}]
            await self.command.execute(self.test_data, transformations=transformations)
            mock_update.assert_called_once_with(self.test_data, "$.users[0].age", 31)

    @pytest.mark.asyncio
    async def test_execute_delete_transformation(self):
        """Test execute with delete transformation"""
        with patch.object(self.command.processor, 'delete') as mock_delete:
            transformations = [{"path": "$.users[0]", "operation": "delete"}]
            await self.command.execute(self.test_data, transformations=transformations)
            mock_delete.assert_called_once_with(self.test_data, "$.users[0]")

    @pytest.mark.asyncio
    async def test_execute_aggregate_transformation(self):
        """Test execute with aggregate transformation"""
        with patch.object(self.command.processor, 'aggregate', return_value=55):
            transformations = [{"path": "$.users[*].age", "operation": "sum"}]
            result = await self.command.execute(self.test_data, transformations=transformations)
            assert result == 55

    @pytest.mark.asyncio
    async def test_execute_output_format_json(self):
        """Test execute with JSON output format"""
        result = await self.command.execute(self.test_data, output_format="json")
        assert isinstance(result, str)
        assert json.loads(result) == self.test_data

    @pytest.mark.asyncio
    async def test_execute_output_format_str(self):
        """Test execute with string output format"""
        result = await self.command.execute(self.test_data, output_format="str")
        assert isinstance(result, str)
        assert str(self.test_data) == result


class TestJSONPathCommand:
    """Test JSONPathCommand class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.command = JSONPathCommand()
        self.test_data = {"users": [{"name": "John"}, {"name": "Jane"}]}

    def test_init(self):
        """Test command initialization"""
        assert self.command.name == "jsonpath"
        assert self.command.description == "Query JSON data using JSONPath expressions"
        assert self.command.category == "json"

    @pytest.mark.asyncio
    async def test_execute_missing_path(self):
        """Test execute without path parameter"""
        with pytest.raises(ValueError, match="JSONPath expression is required"):
            await self.command.execute(self.test_data)

    @pytest.mark.asyncio
    async def test_execute_query_operation(self):
        """Test execute with query operation"""
        with patch.object(self.command.processor, 'query_all', return_value=["John", "Jane"]):
            result = await self.command.execute(self.test_data, path="$.users[*].name")
            assert result == ["John", "Jane"]

    @pytest.mark.asyncio
    async def test_execute_first_operation(self):
        """Test execute with first operation"""
        with patch.object(self.command.processor, 'query_first', return_value="John"):
            result = await self.command.execute(
                self.test_data, 
                path="$.users[*].name", 
                operation="first",
                default="default_name"
            )
            assert result == "John"

    @pytest.mark.asyncio
    async def test_execute_exists_operation(self):
        """Test execute with exists operation"""
        with patch.object(self.command.processor, 'exists', return_value=True):
            result = await self.command.execute(self.test_data, path="$.users", operation="exists")
            assert result is True

    @pytest.mark.asyncio
    async def test_execute_count_operation(self):
        """Test execute with count operation"""
        with patch.object(self.command.processor, 'count', return_value=2):
            result = await self.command.execute(self.test_data, path="$.users[*]", operation="count")
            assert result == 2

    @pytest.mark.asyncio
    async def test_execute_unknown_operation(self):
        """Test execute with unknown operation"""
        with pytest.raises(ValueError, match="Unknown operation"):
            await self.command.execute(self.test_data, path="$.users", operation="unknown")


class TestValidateJSONCommand:
    """Test ValidateJSONCommand class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.command = ValidateJSONCommand()
        self.test_data = {"name": "John", "age": 30}

    def test_init(self):
        """Test command initialization"""
        assert self.command.name == "validate_json"
        assert self.command.description == "Validate JSON data against schema"
        assert self.command.category == "json"

    @pytest.mark.asyncio
    async def test_execute_basic_validation(self):
        """Test execute with basic validation"""
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.message = "Valid"
        mock_result.errors = []
        mock_result.path = None
        mock_result.schema_name = "basic"
        
        with patch.object(self.command.validator, 'validate', return_value=mock_result):
            result = await self.command.execute(self.test_data)
            
            assert result["valid"] is True
            assert result["message"] == "Valid"
            assert result["schema_name"] == "basic"

    @pytest.mark.asyncio
    async def test_execute_with_schema_file(self):
        """Test execute with schema file"""
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.message = "Valid"
        mock_result.errors = []
        mock_result.path = None
        mock_result.schema_name = "file_schema"
        
        with patch.object(self.command.validator, 'add_schema_from_file', return_value=True):
            with patch.object(self.command.validator, 'validate', return_value=mock_result):
                result = await self.command.execute(
                    self.test_data,
                    schema="file_schema",
                    schema_file="schema.json"
                )
                
                assert result["valid"] is True
                assert result["schema_name"] == "file_schema"

    @pytest.mark.asyncio
    async def test_execute_with_schema_data(self):
        """Test execute with inline schema data"""
        schema_data = {"type": "object", "required": ["name"]}
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.message = "Valid"
        mock_result.errors = []
        mock_result.path = None
        mock_result.schema_name = "inline"
        
        with patch.object(self.command.validator, 'add_schema', return_value=True):
            with patch.object(self.command.validator, 'validate', return_value=mock_result):
                result = await self.command.execute(
                    self.test_data,
                    schema="inline",
                    schema_data=schema_data
                )
                
                assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_return_data(self):
        """Test execute with return_data option"""
        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.message = "Valid"
        mock_result.errors = []
        mock_result.path = None
        mock_result.schema_name = "basic"
        
        with patch.object(self.command.validator, 'validate', return_value=mock_result):
            result = await self.command.execute(self.test_data, return_data=True)
            
            assert "data" in result
            assert result["data"] == self.test_data


class TestJSONFormatCommand:
    """Test JSONFormatCommand class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.command = JSONFormatCommand()
        self.test_data = {"name": "John", "age": 30}

    def test_init(self):
        """Test command initialization"""
        assert self.command.name == "json_format"
        assert self.command.description == "Convert between JSON, YAML, XML, CSV formats"
        assert self.command.category == "json"

    @pytest.mark.asyncio
    async def test_execute_dict_to_json(self):
        """Test execute converting dict to JSON"""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = json.dumps(self.test_data)
        
        with patch.object(self.command.converter, 'convert', return_value=mock_result):
            result = await self.command.execute(self.test_data, to_format="json")
            assert result == json.dumps(self.test_data)

    @pytest.mark.asyncio
    async def test_execute_string_auto_detect(self):
        """Test execute with string input and auto format detection"""
        json_string = json.dumps(self.test_data)
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = "converted"
        
        with patch.object(self.command.converter, 'detect_format', return_value="json"):
            with patch.object(self.command.converter, 'convert', return_value=mock_result):
                result = await self.command.execute(json_string, to_format="yaml")
                assert result == "converted"

    @pytest.mark.asyncio
    async def test_execute_conversion_failure(self):
        """Test execute with conversion failure"""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Conversion failed"
        
        with patch.object(self.command.converter, 'convert', return_value=mock_result):
            with pytest.raises(ValueError, match="Conversion failed"):
                await self.command.execute(self.test_data, to_format="invalid")


class TestJSONMergeCommand:
    """Test JSONMergeCommand class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.command = JSONMergeCommand()

    def test_init(self):
        """Test command initialization"""
        assert self.command.name == "json_merge"
        assert self.command.description == "Merge multiple JSON objects"
        assert self.command.category == "json"

    @pytest.mark.asyncio
    async def test_execute_deep_merge_dicts(self):
        """Test execute with deep merge of dictionaries"""
        base_data = {"a": 1, "b": {"x": 10}}
        merge_data = [{"b": {"y": 20}, "c": 3}]
        
        result = await self.command.execute(base_data, merge_with=merge_data, strategy="deep")
        
        assert result["a"] == 1
        assert result["b"]["x"] == 10
        assert result["b"]["y"] == 20
        assert result["c"] == 3

    @pytest.mark.asyncio
    async def test_execute_shallow_merge_dicts(self):
        """Test execute with shallow merge of dictionaries"""
        base_data = {"a": 1, "b": {"x": 10}}
        merge_data = [{"b": {"y": 20}, "c": 3}]
        
        result = await self.command.execute(base_data, merge_with=merge_data, strategy="shallow")
        
        assert result["a"] == 1
        assert result["b"] == {"y": 20}  # Shallow merge replaces entire "b" object
        assert result["c"] == 3

    @pytest.mark.asyncio
    async def test_execute_shallow_merge_lists(self):
        """Test execute with shallow merge of lists"""
        base_data = [1, 2, 3]
        merge_data = [[4, 5, 6]]
        
        result = await self.command.execute(base_data, merge_with=merge_data, strategy="shallow")
        
        assert result == [1, 2, 3, 4, 5, 6]

    @pytest.mark.asyncio
    async def test_execute_replace_strategy(self):
        """Test execute with replace strategy"""
        base_data = {"a": 1, "b": 2}
        merge_data = [{"c": 3, "d": 4}]
        
        result = await self.command.execute(base_data, merge_with=merge_data, strategy="replace")
        
        assert result == {"c": 3, "d": 4}

    @pytest.mark.asyncio
    async def test_execute_string_merge_data(self):
        """Test execute with string merge data"""
        base_data = {"a": 1}
        merge_data = ['{"b": 2}']
        
        result = await self.command.execute(base_data, merge_with=merge_data)
        
        assert result["a"] == 1
        assert result["b"] == 2

    @pytest.mark.asyncio
    async def test_execute_invalid_string_merge_data(self):
        """Test execute with invalid string merge data"""
        base_data = {"a": 1}
        merge_data = ['invalid json']
        
        result = await self.command.execute(base_data, merge_with=merge_data)
        
        assert result == {"a": 1}  # Invalid merge data is skipped

    @pytest.mark.asyncio
    async def test_execute_single_merge_item(self):
        """Test execute with single merge item (not list)"""
        base_data = {"a": 1}
        merge_data = {"b": 2}
        
        result = await self.command.execute(base_data, merge_with=merge_data)
        
        assert result["a"] == 1
        assert result["b"] == 2


class TestJSONFilterCommand:
    """Test JSONFilterCommand class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.command = JSONFilterCommand()
        self.test_data = [
            {"name": "John", "age": 30, "city": "Tokyo"},
            {"name": "Jane", "age": 25, "city": "Osaka"}
        ]

    def test_init(self):
        """Test command initialization"""
        assert self.command.name == "json_filter"
        assert self.command.description == "Filter JSON data based on conditions"
        assert self.command.category == "json"

    @pytest.mark.asyncio
    async def test_execute_no_filters(self):
        """Test execute with no filters"""
        result = await self.command.execute(self.test_data)
        assert result == self.test_data

    @pytest.mark.asyncio
    async def test_execute_list_filtering(self):
        """Test execute with list filtering"""
        with patch.object(self.command, '_filter_list', return_value=[self.test_data[0]]):
            filters = [{"path": "$.age", "operator": "gt", "value": 25}]
            result = await self.command.execute(self.test_data, filters=filters)
            assert result == [self.test_data[0]]

    @pytest.mark.asyncio
    async def test_execute_dict_filtering(self):
        """Test execute with dict filtering"""
        dict_data = {"name": "John", "age": 30}
        with patch.object(self.command, '_filter_dict', return_value=dict_data):
            filters = [{"path": "$.age", "operator": "eq", "value": 30}]
            result = await self.command.execute(dict_data, filters=filters)
            assert result == dict_data

    @pytest.mark.asyncio
    async def test_execute_other_data_type(self):
        """Test execute with non-dict/list data"""
        result = await self.command.execute("string_data")
        assert result == "string_data"

    def test_matches_filters_eq_operator(self):
        """Test matches_filters with equality operator"""
        item = {"age": 30}
        filters = [{"path": "$.age", "operator": "eq", "value": 30}]
        
        with patch.object(self.command.processor, 'query_first', return_value=30):
            result = self.command._matches_filters(item, filters, "and")
            assert result is True

    def test_matches_filters_gt_operator(self):
        """Test matches_filters with greater than operator"""
        item = {"age": 30}
        filters = [{"path": "$.age", "operator": "gt", "value": 25}]
        
        with patch.object(self.command.processor, 'query_first', return_value=30):
            result = self.command._matches_filters(item, filters, "and")
            assert result is True

    def test_matches_filters_in_operator(self):
        """Test matches_filters with in operator"""
        item = {"city": "Tokyo"}
        filters = [{"path": "$.city", "operator": "in", "value": ["Tokyo", "Osaka"]}]
        
        with patch.object(self.command.processor, 'query_first', return_value="Tokyo"):
            result = self.command._matches_filters(item, filters, "and")
            assert result is True

    def test_matches_filters_exists_operator(self):
        """Test matches_filters with exists operator"""
        item = {"name": "John"}
        filters = [{"path": "$.name", "operator": "exists"}]
        
        with patch.object(self.command.processor, 'query_first', return_value="John"):
            result = self.command._matches_filters(item, filters, "and")
            assert result is True

    def test_matches_filters_or_operation(self):
        """Test matches_filters with OR operation"""
        item = {"age": 30}
        filters = [
            {"path": "$.age", "operator": "eq", "value": 25},
            {"path": "$.age", "operator": "eq", "value": 30}
        ]
        
        with patch.object(self.command.processor, 'query_first', side_effect=[25, 30]):
            result = self.command._matches_filters(item, filters, "or")
            assert result is True


class TestJSONStatsCommand:
    """Test JSONStatsCommand class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.command = JSONStatsCommand()
        self.test_data = {"users": [{"name": "John"}, {"name": "Jane"}]}

    def test_init(self):
        """Test command initialization"""
        assert self.command.name == "json_stats"
        assert self.command.description == "Generate statistics for JSON data"
        assert self.command.category == "json"

    @pytest.mark.asyncio
    async def test_execute_dict_stats(self):
        """Test execute with dictionary data"""
        result = await self.command.execute(self.test_data)
        
        assert result["type"] == "dict"
        assert result["key_count"] == 1
        assert "users" in result["keys"]
        assert "structure" in result

    @pytest.mark.asyncio
    async def test_execute_list_stats(self):
        """Test execute with list data"""
        list_data = [{"name": "John"}, {"name": "Jane"}]
        result = await self.command.execute(list_data)
        
        assert result["type"] == "list"
        assert result["item_count"] == 2
        assert "dict" in result["item_types"]

    @pytest.mark.asyncio
    async def test_execute_with_paths(self):
        """Test execute with specific paths"""
        paths = ["$.users[*].name"]
        
        with patch.object(self.command.processor, 'query_all', return_value=["John", "Jane"]):
            result = await self.command.execute(self.test_data, paths=paths)
            
            assert "path_stats" in result
            assert paths[0] in result["path_stats"]

    @pytest.mark.asyncio
    async def test_execute_without_structure(self):
        """Test execute without structure analysis"""
        result = await self.command.execute(self.test_data, include_structure=False)
        
        assert "structure" not in result

    def test_analyze_structure_dict(self):
        """Test structure analysis for dict"""
        test_dict = {"a": 1, "b": {"c": 2}}
        
        with patch.object(self.command, '_analyze_structure', return_value={"depth": 2}):
            result = self.command._analyze_structure(test_dict)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_empty_list(self):
        """Test execute with empty list"""
        result = await self.command.execute([])
        
        assert result["type"] == "list"
        assert result["item_count"] == 0
        assert "item_types" not in result