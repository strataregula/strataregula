"""
Pytest configuration and shared fixtures
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "users": [
            {
                "id": 1,
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "password": "secret123",
                "profile": {
                    "age": 30,
                    "department": "engineering"
                },
                "created_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Bob Smith",
                "email": "bob@example.com", 
                "password": "pass456",
                "profile": {
                    "age": 25,
                    "department": "sales"
                },
                "created_at": "2023-01-02T00:00:00Z"
            }
        ]
    }


@pytest.fixture
def circular_reference_data():
    """Data with circular reference for testing"""
    data = {
        "user": {
            "id": 1,
            "name": "Alice",
            "manager": None
        },
        "manager": {
            "id": 2,
            "name": "Boss"
        }
    }
    # Create circular reference
    data["user"]["manager"] = data["manager"]
    data["manager"]["subordinate"] = data["user"]
    return data


@pytest.fixture
def deep_nested_data():
    """Deeply nested data for depth testing"""
    def create_nested(depth: int) -> Dict[str, Any]:
        if depth <= 0:
            return {"value": "leaf"}
        return {"level": depth, "nested": create_nested(depth - 1)}
    
    return create_nested(100)


@pytest.fixture
def large_array_data():
    """Large array data for size testing"""
    return {
        "items": [{"id": i, "value": f"item_{i}"} for i in range(10000)]
    }


@pytest.fixture
def sample_copy_policy():
    """Sample copy policy YAML content"""
    return {
        "copy_policies": [
            {
                "name": "secure_user_copy",
                "match": {
                    "path": "$.users[*]",
                    "labels": ["pii"]
                },
                "mode": "deep",
                "ops": [
                    {"exclude": ["password"]},
                    {
                        "mask": {
                            "fields": ["email"],
                            "style": "hash"
                        }
                    },
                    {
                        "rename": {
                            "from": "name",
                            "to": "full_name"
                        }
                    }
                ]
            },
            {
                "name": "simple_shallow_copy",
                "match": {
                    "path": "$.items[*]"
                },
                "mode": "shallow",
                "ops": []
            }
        ]
    }


@pytest.fixture
def temp_json_file(sample_user_data):
    """Create temporary JSON file with sample data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_user_data, f, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_policy_file(sample_copy_policy):
    """Create temporary policy file"""
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_copy_policy, f, default_flow_style=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_hook_manager():
    """Mock hook manager for testing"""
    class MockHookManager:
        def __init__(self):
            self.events = []
        
        def emit(self, event_name: str, data: Dict[str, Any]):
            self.events.append({"event": event_name, "data": data})
        
        def get_events(self, event_name: str = None):
            if event_name:
                return [e for e in self.events if e["event"] == event_name]
            return self.events
        
        def clear_events(self):
            self.events.clear()
    
    return MockHookManager()


@pytest.fixture
def mock_di_container():
    """Mock DI container for testing"""
    class MockContainer:
        def __init__(self):
            self.services = {}
        
        def register(self, service_type, implementation):
            self.services[service_type] = implementation
        
        def resolve(self, service_type):
            return self.services.get(service_type)
    
    return MockContainer()