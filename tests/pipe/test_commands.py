"""
Tests for pipe commands module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from strataregula.pipe.commands import (
    CommandInfo, BaseCommand, CommandRegistry,
    EchoCommand, FilterCommand, TransformCommand,
    _register_builtin_commands
)


class TestCommandInfo:
    """Test CommandInfo dataclass"""

    def test_command_info_creation(self):
        """Test creating CommandInfo"""
        info = CommandInfo(
            name="test_command",
            description="Test command description",
            version="1.0.0",
            author="Test Author",
            category="test",
            async_support=True,
            input_types=["dict"],
            output_types=["dict"],
            examples=["example usage"]
        )
        
        assert info.name == "test_command"
        assert info.description == "Test command description"
        assert info.version == "1.0.0"
        assert info.author == "Test Author"
        assert info.category == "test"
        assert info.async_support is True
        assert info.input_types == ["dict"]
        assert info.output_types == ["dict"]
        assert info.examples == ["example usage"]


class TestBaseCommand:
    """Test BaseCommand abstract class"""

    def create_test_command(self):
        """Create a concrete test command for testing"""
        class TestCommand(BaseCommand):
            description = "Test command for testing"
            version = "2.0.0"
            author = "Test Author"
            category = "test_category"
            input_types = ["dict", "list"]
            output_types = ["dict"]
            examples = ["test example"]
            
            async def execute(self, data, *args, **kwargs):
                return {"processed": data}
        
        return TestCommand()

    def test_base_command_init(self):
        """Test BaseCommand initialization"""
        command = self.create_test_command()
        
        assert command.name == "testcommand"
        assert command.description == "Test command for testing"
        assert command.version == "2.0.0"
        assert command.author == "Test Author"
        assert command.category == "test_category"
        assert command.input_types == ["dict", "list"]
        assert command.output_types == ["dict"]
        assert command.examples == ["test example"]
        assert hasattr(command, 'hooks')

    def test_base_command_init_defaults(self):
        """Test BaseCommand initialization with defaults"""
        class MinimalCommand(BaseCommand):
            async def execute(self, data, *args, **kwargs):
                return data
        
        command = MinimalCommand()
        
        assert command.name == "minimalcommand"
        assert command.description == "No description available"
        assert command.version == "1.0.0"
        assert command.author == "Unknown"
        assert command.category == "general"
        assert command.input_types == ["any"]
        assert command.output_types == ["any"]
        assert command.examples == []

    @pytest.mark.asyncio
    async def test_base_command_execute(self):
        """Test BaseCommand execute method"""
        command = self.create_test_command()
        
        result = await command.execute({"test": "data"})
        assert result == {"processed": {"test": "data"}}

    def test_base_command_execute_sync(self):
        """Test BaseCommand synchronous execute"""
        command = self.create_test_command()
        
        result = command.execute_sync({"test": "data"})
        assert result == {"processed": {"test": "data"}}

    def test_validate_input_any_type(self):
        """Test input validation with 'any' type"""
        class AnyCommand(BaseCommand):
            input_types = ["any"]
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        command = AnyCommand()
        
        assert command.validate_input("string") is True
        assert command.validate_input(123) is True
        assert command.validate_input({"dict": "data"}) is True
        assert command.validate_input([1, 2, 3]) is True

    def test_validate_input_specific_types(self):
        """Test input validation with specific types"""
        command = self.create_test_command()
        
        assert command.validate_input({"dict": "data"}) is True
        assert command.validate_input([1, 2, 3]) is True
        assert command.validate_input("string") is False
        assert command.validate_input(123) is False

    def test_get_info(self):
        """Test getting command information"""
        command = self.create_test_command()
        info = command.get_info()
        
        assert isinstance(info, CommandInfo)
        assert info.name == command.name
        assert info.description == command.description
        assert info.version == command.version
        assert info.author == command.author
        assert info.category == command.category
        assert info.async_support is True
        assert info.input_types == command.input_types
        assert info.output_types == command.output_types
        assert info.examples == command.examples

    def test_cannot_instantiate_abstract_base(self):
        """Test that BaseCommand cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseCommand()


class TestCommandRegistry:
    """Test CommandRegistry class"""

    def test_registry_init(self):
        """Test CommandRegistry initialization"""
        registry = CommandRegistry()
        
        assert registry._commands == {}
        assert registry._categories == {}
        assert hasattr(registry, 'hooks')

    def test_register_command(self):
        """Test registering a command"""
        registry = CommandRegistry()
        
        class TestCommand(BaseCommand):
            name = "test_cmd"
            category = "test"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        command = TestCommand()
        registry.register(command)
        
        assert "test_cmd" in registry._commands
        assert registry._commands["test_cmd"] is command
        assert "test" in registry._categories
        assert "test_cmd" in registry._categories["test"]

    def test_register_invalid_command(self):
        """Test registering invalid command"""
        registry = CommandRegistry()
        
        with pytest.raises(ValueError, match="Command must inherit from BaseCommand"):
            registry.register("not a command")

    def test_register_duplicate_command(self):
        """Test registering duplicate command"""
        registry = CommandRegistry()
        
        class TestCommand(BaseCommand):
            name = "duplicate"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        command1 = TestCommand()
        command2 = TestCommand()
        
        registry.register(command1)
        
        with pytest.raises(ValueError, match="Command 'duplicate' already registered"):
            registry.register(command2)

    def test_register_class(self):
        """Test registering a command class"""
        registry = CommandRegistry()
        
        class TestCommand(BaseCommand):
            name = "class_test"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        registry.register_class(TestCommand)
        
        assert "class_test" in registry._commands
        assert isinstance(registry._commands["class_test"], TestCommand)

    def test_unregister_command(self):
        """Test unregistering a command"""
        registry = CommandRegistry()
        
        class TestCommand(BaseCommand):
            name = "to_remove"
            category = "test"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        command = TestCommand()
        registry.register(command)
        
        assert "to_remove" in registry._commands
        assert "to_remove" in registry._categories["test"]
        
        registry.unregister("to_remove")
        
        assert "to_remove" not in registry._commands
        assert "to_remove" not in registry._categories["test"]

    def test_unregister_nonexistent_command(self):
        """Test unregistering non-existent command"""
        registry = CommandRegistry()
        
        # Should not raise an error
        registry.unregister("nonexistent")

    def test_get_command(self):
        """Test getting a command by name"""
        registry = CommandRegistry()
        
        class TestCommand(BaseCommand):
            name = "get_test"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        command = TestCommand()
        registry.register(command)
        
        retrieved = registry.get_command("get_test")
        assert retrieved is command
        
        # Test case insensitivity
        retrieved = registry.get_command("GET_TEST")
        assert retrieved is command
        
        # Test non-existent command
        assert registry.get_command("nonexistent") is None

    def test_get_commands_by_category(self):
        """Test getting commands by category"""
        registry = CommandRegistry()
        
        class TestCommand1(BaseCommand):
            name = "test1"
            category = "category1"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        class TestCommand2(BaseCommand):
            name = "test2"
            category = "category1"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        class TestCommand3(BaseCommand):
            name = "test3"
            category = "category2"
            
            async def execute(self, data, *args, **kwargs):
                return data
        
        registry.register(TestCommand1())
        registry.register(TestCommand2())
        registry.register(TestCommand3())
        
        category1_commands = registry.get_commands_by_category("category1")
        assert len(category1_commands) == 2
        
        category2_commands = registry.get_commands_by_category("category2")
        assert len(category2_commands) == 1
        
        empty_category = registry.get_commands_by_category("nonexistent")
        assert empty_category == []

    def test_get_all_commands(self):
        """Test getting all commands"""
        registry = CommandRegistry()
        
        class TestCommand1(BaseCommand):
            name = "cmd1"
            async def execute(self, data, *args, **kwargs): return data
        
        class TestCommand2(BaseCommand):
            name = "cmd2"
            async def execute(self, data, *args, **kwargs): return data
        
        registry.register(TestCommand1())
        registry.register(TestCommand2())
        
        all_commands = registry.get_all_commands()
        assert len(all_commands) == 2

    def test_get_categories(self):
        """Test getting all categories"""
        registry = CommandRegistry()
        
        class TestCommand1(BaseCommand):
            name = "cmd1"
            category = "cat1"
            async def execute(self, data, *args, **kwargs): return data
        
        class TestCommand2(BaseCommand):
            name = "cmd2"
            category = "cat2"
            async def execute(self, data, *args, **kwargs): return data
        
        registry.register(TestCommand1())
        registry.register(TestCommand2())
        
        categories = registry.get_categories()
        assert "cat1" in categories
        assert "cat2" in categories

    def test_search_commands(self):
        """Test searching commands"""
        registry = CommandRegistry()
        
        class TestCommand1(BaseCommand):
            name = "data_processor"
            description = "Process data efficiently"
            category = "data"
            async def execute(self, data, *args, **kwargs): return data
        
        class TestCommand2(BaseCommand):
            name = "file_reader"
            description = "Read files from disk"
            category = "io"
            async def execute(self, data, *args, **kwargs): return data
        
        registry.register(TestCommand1())
        registry.register(TestCommand2())
        
        # Search by name
        results = registry.search_commands("data")
        assert len(results) == 1
        assert results[0].name == "data_processor"
        
        # Search by description
        results = registry.search_commands("efficiently")
        assert len(results) == 1
        assert results[0].name == "data_processor"
        
        # Search by category
        results = registry.search_commands("io")
        assert len(results) == 1
        assert results[0].name == "file_reader"

    def test_list_commands(self):
        """Test listing command information"""
        registry = CommandRegistry()
        
        class TestCommand1(BaseCommand):
            name = "cmd1"
            category = "cat1"
            async def execute(self, data, *args, **kwargs): return data
        
        class TestCommand2(BaseCommand):
            name = "cmd2"
            category = "cat2"
            async def execute(self, data, *args, **kwargs): return data
        
        registry.register(TestCommand1())
        registry.register(TestCommand2())
        
        # List all commands
        all_info = registry.list_commands()
        assert len(all_info) == 2
        assert all(isinstance(info, CommandInfo) for info in all_info)
        
        # List by category
        cat1_info = registry.list_commands("cat1")
        assert len(cat1_info) == 1
        assert cat1_info[0].name == "cmd1"


class TestBuiltinCommands:
    """Test built-in commands"""

    @pytest.mark.asyncio
    async def test_echo_command(self):
        """Test EchoCommand"""
        command = EchoCommand()
        
        test_data = {"test": "data"}
        result = await command.execute(test_data)
        
        assert result == test_data
        assert command.name == "echo"
        assert command.category == "utility"

    @pytest.mark.asyncio
    async def test_filter_command_list(self):
        """Test FilterCommand with list data"""
        command = FilterCommand()
        
        test_data = [1, 2, 3, 4, 5]
        result = await command.execute(test_data, condition="item > 3")
        
        assert result == [4, 5]

    @pytest.mark.asyncio
    async def test_filter_command_dict(self):
        """Test FilterCommand with dict data"""
        command = FilterCommand()
        
        test_data = {"a": 1, "b": 2, "c": 3}
        result = await command.execute(test_data, condition="item > 1")
        
        assert result == {"b": 2, "c": 3}

    @pytest.mark.asyncio
    async def test_filter_command_no_condition(self):
        """Test FilterCommand without condition"""
        command = FilterCommand()
        
        test_data = [1, 2, 3]
        result = await command.execute(test_data)
        
        assert result == test_data

    @pytest.mark.asyncio
    async def test_filter_command_invalid_condition(self):
        """Test FilterCommand with invalid condition"""
        command = FilterCommand()
        
        test_data = [1, 2, 3]
        result = await command.execute(test_data, condition="invalid syntax]")
        
        # Should return empty list due to evaluation error
        assert result == []

    @pytest.mark.asyncio
    async def test_transform_command(self):
        """Test TransformCommand"""
        command = TransformCommand()
        
        test_data = {"value": 10}
        result = await command.execute(test_data, expression="data['value'] * 2")
        
        assert result == 20

    @pytest.mark.asyncio
    async def test_transform_command_no_expression(self):
        """Test TransformCommand without expression"""
        command = TransformCommand()
        
        test_data = {"test": "data"}
        result = await command.execute(test_data)
        
        assert result == test_data

    @pytest.mark.asyncio
    async def test_transform_command_invalid_expression(self):
        """Test TransformCommand with invalid expression"""
        command = TransformCommand()
        
        test_data = {"test": "data"}
        
        with pytest.raises(ValueError, match="Invalid transform expression"):
            await command.execute(test_data, expression="invalid syntax]")

    def test_register_builtin_commands(self):
        """Test registering built-in commands"""
        registry = CommandRegistry()
        
        _register_builtin_commands(registry)
        
        # Check that built-in commands are registered
        assert registry.get_command("echo") is not None
        assert registry.get_command("filter") is not None
        assert registry.get_command("transform") is not None
        
        # Verify they are the correct types
        assert isinstance(registry.get_command("echo"), EchoCommand)
        assert isinstance(registry.get_command("filter"), FilterCommand)
        assert isinstance(registry.get_command("transform"), TransformCommand)