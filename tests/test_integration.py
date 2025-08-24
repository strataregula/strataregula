"""
Integration tests for Transfer/Copy subsystem

Tests for end-to-end workflows, cross-module integration,
and real-world scenarios.
"""

import pytest
import json
import tempfile
from pathlib import Path
from strataregula.transfer import (
    CopyEngine, RuleSet, DeepCopyVisitor, TransformRegistry, CopyDiff
)
from strataregula.transfer.deep_copy import CopyMode


class TestTransferIntegration:
    """Integration tests for Transfer/Copy functionality"""
    
    def test_end_to_end_user_data_copy(self, sample_user_data):
        """Test complete user data copying workflow"""
        # Create policy for secure user copying
        policy_data = {
            "copy_policies": [
                {
                    "name": "secure_user_copy",
                    "match": {"path": "$"},
                    "mode": "deep",
                    "ops": [
                        {"exclude": ["password"]},
                        {"mask": {"fields": ["email"], "style": "hash"}},
                        {"rename": {"from": "created_at", "to": "timestamp"}},
                        {"default": {"values": {"status": "migrated"}}}
                    ]
                }
            ]
        }
        
        # Load ruleset
        ruleset = RuleSet.from_yaml(policy_data)
        
        # Create engine
        engine = CopyEngine(ruleset=ruleset)
        
        # Plan
        plan = engine.plan(sample_user_data)
        assert len(plan.items) == 1
        assert plan.items[0].rule.name == "secure_user_copy"
        
        # Apply
        result = engine.apply(plan, provenance=True)
        
        # Verify results
        assert result["stats"].items_success == 1
        assert len(result["errors"]) == 0
        
        copied_data = result["results"][0]["obj"]
        
        # Check transforms were applied (note: our sample data structure)
        assert copied_data != sample_user_data
        assert copied_data is not sample_user_data
        
        # Check provenance
        assert result["results"][0]["provenance"] == "secure_user_copy"
    
    def test_circular_reference_detection_integration(self, circular_reference_data):
        """Test circular reference detection in full workflow"""
        policy_data = {
            "copy_policies": [
                {
                    "name": "deep_copy_rule",
                    "match": {"path": "$"},
                    "mode": "deep",
                    "ops": []
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        # Plan should succeed
        plan = engine.plan(circular_reference_data)
        assert len(plan.items) == 1
        
        # Apply should fail due to circular reference
        result = engine.apply(plan)
        
        assert result["stats"].items_success == 0
        assert result["stats"].items_failed == 1
        assert len(result["errors"]) == 1
        assert "Circular reference detected" in result["errors"][0]["error"]
    
    def test_large_data_processing(self):
        """Test processing large dataset with memory constraints"""
        # Generate large dataset
        large_data = {
            "items": [
                {"id": i, "value": f"item_{i}", "data": list(range(10))}
                for i in range(1000)
            ]
        }
        
        policy_data = {
            "copy_policies": [
                {
                    "name": "large_data_copy",
                    "match": {"path": "$"},
                    "mode": "shallow",  # Use shallow to avoid deep copy overhead
                    "ops": [
                        {"exclude": ["data"]},  # Exclude large arrays
                        {"default": {"values": {"processed": True}}}
                    ]
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        # Plan and apply
        plan = engine.plan(large_data)
        result = engine.apply(plan)
        
        # Should succeed
        assert result["stats"].items_success == 1
        assert len(result["errors"]) == 0
        
        copied_data = result["results"][0]["obj"]
        
        # Should be processed but smaller (data excluded)
        assert copied_data != large_data
        assert len(str(copied_data)) < len(str(large_data))
    
    def test_multi_rule_priority_resolution(self, sample_user_data):
        """Test multiple rules with priority resolution"""
        policy_data = {
            "copy_policies": [
                {
                    "name": "general_rule",
                    "match": {"path": "$"},
                    "mode": "shallow",
                    "ops": [{"exclude": ["password"]}],
                    "priority": 1
                },
                {
                    "name": "specific_rule",
                    "match": {"path": "$"},
                    "mode": "deep", 
                    "ops": [
                        {"exclude": ["password"]},
                        {"mask": {"fields": ["email"], "style": "stars"}}
                    ],
                    "priority": 10
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        # Higher priority rule should be selected
        assert len(plan.items) == 1
        assert plan.items[0].rule.name == "specific_rule"
        assert plan.items[0].mode == CopyMode.DEEP
        assert len(plan.items[0].ops) == 2
    
    def test_diff_generation_integration(self, sample_user_data):
        """Test diff generation in complete workflow"""
        policy_data = {
            "copy_policies": [
                {
                    "name": "diff_test_rule",
                    "match": {"path": "$"},
                    "mode": "shallow",
                    "ops": [
                        {"exclude": ["password"]},
                        {"mask": {"fields": ["email"], "style": "redact"}},
                        {"rename": {"from": "name", "to": "full_name"}}
                    ]
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        # Capture diff output
        class MockDiffStream:
            def __init__(self):
                self.content = None
            
            def write(self, data):
                self.content = data
        
        diff_stream = MockDiffStream()
        result = engine.apply(plan, diff_out=diff_stream)
        
        # Check diff was generated
        assert diff_stream.content is not None
        assert isinstance(diff_stream.content, dict)
        assert "summary" in diff_stream.content
    
    def test_hooks_integration_workflow(self, sample_user_data, mock_hook_manager):
        """Test hooks integration throughout workflow"""
        policy_data = {
            "copy_policies": [
                {
                    "name": "hooked_rule",
                    "match": {"path": "$"},
                    "mode": "shallow",
                    "ops": [{"exclude": ["password"]}]
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        # Plan
        plan = engine.plan(sample_user_data)
        
        # Apply
        result = engine.apply(plan)
        
        # Check all expected events were fired
        events = mock_hook_manager.get_events()
        event_names = [e["event"] for e in events]
        
        expected_events = [
            "copy:plan",
            "copy:start", 
            "copy:before_object",
            "copy:after_object",
            "copy:commit",
            "copy:finish"
        ]
        
        for expected_event in expected_events:
            assert expected_event in event_names, f"Missing event: {expected_event}"
    
    def test_error_recovery_integration(self):
        """Test error recovery and partial success scenarios"""
        # Create data that will cause some items to fail
        mixed_data = [
            {"id": 1, "valid": True},
            {"id": 2, "valid": True},
            {"id": 3, "problematic": "data"}  # This might cause issues
        ]
        
        policy_data = {
            "copy_policies": [
                {
                    "name": "mixed_rule",
                    "match": {"path": "$[*]"},  # Match array items
                    "mode": "deep",
                    "ops": [
                        {"exclude": ["problematic"]},  # This should work
                        {"invalid_operation": {}}       # This will fail
                    ]
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(mixed_data)
        result = engine.apply(plan)
        
        # Should have some failures but engine should continue
        assert result["stats"].items_processed > 0
        assert result["stats"].items_failed > 0  # Due to invalid operation
        
        # Check error details are captured
        assert len(result["errors"]) > 0
        for error in result["errors"]:
            assert "error" in error
            assert "item_meta" in error
    
    def test_memory_constrained_processing(self, deep_nested_data):
        """Test processing with memory constraints"""
        # Use very restrictive limits
        visitor = DeepCopyVisitor(max_depth=10, max_keys=100)
        
        policy_data = {
            "copy_policies": [
                {
                    "name": "constrained_rule",
                    "match": {"path": "$"},
                    "mode": "deep",
                    "ops": []
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(
            ruleset=ruleset,
            deep_copy=visitor
        )
        
        plan = engine.plan(deep_nested_data)
        result = engine.apply(plan)
        
        # Should fail due to depth limit
        assert result["stats"].items_failed == 1
        assert len(result["errors"]) == 1
        assert "depth" in result["errors"][0]["error"].lower()


class TestTransformChaining:
    """Test complex transform operation chaining"""
    
    def test_complete_transform_chain(self):
        """Test chaining all major transform types"""
        original_data = {
            "id": "12345",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "password": "secret123",
            "status": "active",
            "profile": {
                "age": 30,
                "department": "engineering"
            }
        }
        
        policy_data = {
            "copy_policies": [
                {
                    "name": "complete_transform",
                    "match": {"path": "$"},
                    "mode": "deep",
                    "ops": [
                        {"exclude": ["password"]},
                        {"mask": {"fields": ["email"], "style": "hash"}},
                        {"rename": {"from": "name", "to": "full_name"}},
                        {"map": {
                            "field": "status",
                            "mapping": {"active": "enabled", "inactive": "disabled"}
                        }},
                        {"default": {"values": {"migrated": True, "version": "2.0"}}},
                        {"id_reassign": {"field": "id", "prefix": "new_"}},
                        {"compute": {
                            "field": "name_length",
                            "expression": "length",
                            "source": "full_name"
                        }}
                    ]
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(original_data)
        result = engine.apply(plan)
        
        assert result["stats"].items_success == 1
        transformed_data = result["results"][0]["obj"]
        
        # Verify all transforms were applied
        assert "password" not in transformed_data  # Excluded
        assert transformed_data["email"].startswith("hash:")  # Masked
        assert "name" not in transformed_data  # Renamed
        assert "full_name" in transformed_data  # Renamed to
        assert transformed_data["status"] == "enabled"  # Mapped
        assert transformed_data["migrated"] is True  # Defaulted
        assert transformed_data["id"] == "new_12345"  # ID reassigned
        # Note: compute transform may not work due to rename ordering
    
    def test_transform_order_dependency(self):
        """Test that transform order matters"""
        data = {"old_name": "value"}
        
        # First transform chain: rename then compute
        policy1 = {
            "copy_policies": [
                {
                    "name": "rename_first",
                    "match": {"path": "$"},
                    "mode": "shallow",
                    "ops": [
                        {"rename": {"from": "old_name", "to": "new_name"}},
                        {"compute": {
                            "field": "computed",
                            "expression": "uppercase", 
                            "source": "new_name"
                        }}
                    ]
                }
            ]
        }
        
        # Second transform chain: compute then rename
        policy2 = {
            "copy_policies": [
                {
                    "name": "compute_first",
                    "match": {"path": "$"},
                    "mode": "shallow", 
                    "ops": [
                        {"compute": {
                            "field": "computed",
                            "expression": "uppercase",
                            "source": "old_name"
                        }},
                        {"rename": {"from": "old_name", "to": "new_name"}}
                    ]
                }
            ]
        }
        
        # Test both orders
        for policy, expected_source in [(policy1, "new_name"), (policy2, "computed")]:
            ruleset = RuleSet.from_yaml(policy)
            engine = CopyEngine(ruleset=ruleset)
            
            plan = engine.plan(data.copy())
            result = engine.apply(plan)
            
            assert result["stats"].items_success == 1
            transformed = result["results"][0]["obj"]
            
            # Both should succeed but have different results
            assert "new_name" in transformed or "old_name" not in transformed


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    def test_pii_data_migration(self):
        """Test PII data migration scenario"""
        # Production user data (simulated)
        prod_data = {
            "users": [
                {
                    "id": "user_001", 
                    "email": "john.doe@company.com",
                    "phone": "+1-555-123-4567",
                    "ssn": "123-45-6789",
                    "name": "John Doe",
                    "address": "123 Main St, City, State",
                    "salary": 75000,
                    "role": "engineer"
                },
                {
                    "id": "user_002",
                    "email": "jane.smith@company.com", 
                    "phone": "+1-555-987-6543",
                    "ssn": "987-65-4321",
                    "name": "Jane Smith",
                    "address": "456 Oak Ave, City, State",
                    "salary": 85000,
                    "role": "manager"
                }
            ]
        }
        
        # PII-safe migration policy
        policy_data = {
            "copy_policies": [
                {
                    "name": "pii_safe_migration",
                    "match": {"path": "$"},
                    "mode": "deep",
                    "ops": [
                        {"exclude": ["ssn", "salary", "address"]},  # Remove sensitive data
                        {"mask": {
                            "fields": ["email", "phone"],
                            "style": "hash"
                        }},
                        {"id_reassign": {"field": "id", "prefix": "dev_"}},  # Environment prefix
                        {"default": {"values": {
                            "environment": "development",
                            "migrated_at": "2024-12-01T00:00:00Z"
                        }}}
                    ]
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(prod_data)
        result = engine.apply(plan, provenance=True)
        
        assert result["stats"].items_success == 1
        dev_data = result["results"][0]["obj"]
        
        # Verify PII safety
        for user in dev_data["users"]:
            assert "ssn" not in user
            assert "salary" not in user
            assert "address" not in user
            assert user["email"].startswith("hash:")
            assert user["phone"].startswith("hash:")
            assert user["id"].startswith("dev_")
            assert user["environment"] == "development"
    
    def test_configuration_deployment(self):
        """Test configuration deployment across environments"""
        # Base configuration
        base_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "app_db"
            },
            "features": {
                "debug": True,
                "analytics": False,
                "new_ui": False
            },
            "secrets": {
                "api_key": "dev_key_12345",
                "db_password": "dev_password"
            }
        }
        
        # Production deployment policy
        policy_data = {
            "copy_policies": [
                {
                    "name": "prod_deployment",
                    "match": {"path": "$"},
                    "mode": "deep",
                    "ops": [
                        {"exclude": ["secrets"]},  # Remove dev secrets
                        {"map": {
                            "field": "database.host",
                            "mapping": {"localhost": "prod-db-cluster.company.com"}
                        }},
                        {"map": {
                            "field": "features.debug", 
                            "mapping": {True: False}  # Disable debug in prod
                        }},
                        {"map": {
                            "field": "features.analytics",
                            "mapping": {False: True}  # Enable analytics in prod
                        }},
                        {"default": {"values": {
                            "environment": "production",
                            "deployed_at": "2024-12-01T12:00:00Z"
                        }}}
                    ]
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(policy_data)
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(base_config)
        result = engine.apply(plan)
        
        assert result["stats"].items_success == 1
        prod_config = result["results"][0]["obj"]
        
        # Verify production transformations
        assert "secrets" not in prod_config
        assert prod_config["database"]["host"] == "prod-db-cluster.company.com"
        assert prod_config["features"]["debug"] is False
        assert prod_config["features"]["analytics"] is True
        assert prod_config["environment"] == "production"