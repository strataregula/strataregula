"""
Unit tests for CopyEngine

Tests for plan generation, execution, hooks integration, and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock
from strataregula.transfer.copy_engine import (
    CopyEngine, CopyPlan, CopyItem, CopyStats
)
from strataregula.transfer.rules import RuleSet, CopyRule
from strataregula.transfer.deep_copy import DeepCopyVisitor, CopyMode
from strataregula.transfer.transforms import TransformRegistry


class TestCopyEngine:
    """Test CopyEngine functionality"""
    
    def test_engine_initialization(self):
        """Test engine initialization with dependencies"""
        ruleset = RuleSet([])
        hooks = Mock()
        di = Mock()
        
        engine = CopyEngine(
            ruleset=ruleset,
            hooks=hooks,
            di=di
        )
        
        assert engine.ruleset is ruleset
        assert engine.hooks is hooks
        assert engine.di is di
        assert engine.deep_copy is not None
        assert engine.transforms is not None
    
    def test_engine_initialization_defaults(self):
        """Test engine initialization with default dependencies"""
        ruleset = RuleSet([])
        
        engine = CopyEngine(ruleset=ruleset)
        
        assert engine.ruleset is ruleset
        assert engine.hooks is None
        assert engine.di is None
        assert isinstance(engine.deep_copy, DeepCopyVisitor)
        assert isinstance(engine.transforms, TransformRegistry)


class TestCopyEnginePlan:
    """Test CopyEngine plan generation"""
    
    def test_plan_empty_data(self):
        """Test planning with empty data"""
        ruleset = RuleSet([])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan({})
        
        assert isinstance(plan, CopyPlan)
        assert len(plan.items) == 0
        assert plan.stats.items_planned == 1  # Empty dict is one object
        assert plan.provenance is not None
    
    def test_plan_simple_data_no_rules(self, sample_user_data):
        """Test planning with data but no matching rules"""
        ruleset = RuleSet([])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        assert len(plan.items) == 0  # No rules match
        assert plan.stats.items_planned == 1  # One top-level object
    
    def test_plan_with_matching_rule(self, sample_user_data):
        """Test planning with matching rule"""
        rule = CopyRule(
            name="user_rule",
            match={"path": "$"},  # Match root object
            mode=CopyMode.DEEP,
            ops=[{"exclude": ["password"]}]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        assert len(plan.items) == 1
        assert plan.items[0].rule.name == "user_rule"
        assert plan.items[0].mode == CopyMode.DEEP
        assert len(plan.items[0].ops) == 1
    
    def test_plan_with_hooks(self, sample_user_data, mock_hook_manager):
        """Test planning with hooks integration"""
        rule = CopyRule(
            name="test_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        plan = engine.plan(sample_user_data)
        
        # Check that copy:plan event was emitted
        plan_events = mock_hook_manager.get_events("copy:plan")
        assert len(plan_events) == 1
        assert "plan" in plan_events[0]["data"]
    
    def test_plan_array_data(self):
        """Test planning with array data"""
        rule = CopyRule(
            name="item_rule",
            match={"path": "$[0]"},  # Match first array item
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset)
        
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        plan = engine.plan(data)
        
        assert len(plan.items) == 1  # Only first item matches
        assert plan.items[0].obj == {"id": 1}
        assert plan.stats.items_planned == 3  # Three array items planned
    
    def test_plan_provenance(self, sample_user_data):
        """Test provenance information in plan"""
        ruleset = RuleSet([])
        engine = CopyEngine(ruleset=ruleset)
        
        context = {"source_file": "test.json"}
        plan = engine.plan(sample_user_data, context)
        
        assert plan.provenance is not None
        assert "timestamp" in plan.provenance
        assert "source_hash" in plan.provenance
        assert "engine_version" in plan.provenance
        assert plan.provenance["context"] == context
    
    def test_plan_memory_estimation(self, sample_user_data):
        """Test memory estimation in plan"""
        rule = CopyRule(
            name="deep_rule",
            match={"path": "$"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        assert plan.estimated_memory > 0
        assert plan.estimated_time_ms > 0


class TestCopyEngineApply:
    """Test CopyEngine execution"""
    
    def test_apply_empty_plan(self, mock_hook_manager):
        """Test applying empty plan"""
        ruleset = RuleSet([])
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        plan = CopyPlan(items=[], stats=CopyStats(), provenance={})
        result = engine.apply(plan)
        
        assert len(result["results"]) == 0
        assert result["stats"].items_processed == 0
        assert result["stats"].items_success == 0
        assert len(result["errors"]) == 0
        
        # Check hooks were called
        start_events = mock_hook_manager.get_events("copy:start")
        finish_events = mock_hook_manager.get_events("copy:finish")
        assert len(start_events) == 1
        assert len(finish_events) == 1
    
    def test_apply_simple_copy(self, sample_user_data, mock_hook_manager):
        """Test applying simple copy operation"""
        rule = CopyRule(
            name="simple_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        plan = engine.plan(sample_user_data)
        result = engine.apply(plan)
        
        assert len(result["results"]) == 1
        assert result["stats"].items_processed == 1
        assert result["stats"].items_success == 1
        assert result["stats"].items_failed == 0
        assert len(result["errors"]) == 0
        
        # Check result content
        copied_data = result["results"][0]["obj"]
        assert copied_data == sample_user_data
        assert copied_data is not sample_user_data  # Different object
    
    def test_apply_with_transforms(self, sample_user_data, mock_hook_manager):
        """Test applying copy with transforms"""
        rule = CopyRule(
            name="transform_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[{"exclude": ["password"]}]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        plan = engine.plan(sample_user_data)
        result = engine.apply(plan)
        
        assert len(result["results"]) == 1
        copied_data = result["results"][0]["obj"]
        
        # Transform should have been applied - but this will fail
        # because our sample data structure doesn't directly contain password
        # This is testing the transform application flow
        assert copied_data != sample_user_data  # Should be different due to transform
    
    def test_apply_with_provenance(self, sample_user_data):
        """Test applying with provenance information"""
        rule = CopyRule(
            name="prov_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        result = engine.apply(plan, provenance=True)
        
        assert len(result["results"]) == 1
        assert result["results"][0]["provenance"] == "prov_rule"
        assert result["provenance"] is not None
    
    def test_apply_with_output_stream(self, sample_user_data):
        """Test applying with output stream"""
        rule = CopyRule(
            name="stream_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        # Mock output stream
        output_stream = Mock()
        result = engine.apply(plan, out_stream=output_stream)
        
        # Check that output stream was written to
        assert output_stream.write.called
        assert output_stream.write.call_count == 1
    
    def test_apply_with_diff_output(self, sample_user_data):
        """Test applying with diff output"""
        rule = CopyRule(
            name="diff_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[{"exclude": ["nonexistent"]}]  # Safe transform
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        # Mock diff stream
        diff_stream = Mock()
        result = engine.apply(plan, diff_out=diff_stream)
        
        # Check that diff stream was written to
        assert diff_stream.write.called
    
    def test_apply_error_handling(self, mock_hook_manager):
        """Test error handling during apply"""
        # Create a rule that will cause an error
        rule = CopyRule(
            name="error_rule",
            match={"path": "$"},
            mode=CopyMode.DEEP,
            ops=[{"invalid_transform": []}]  # This will cause an error
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        data = {"test": "data"}
        plan = engine.plan(data)
        result = engine.apply(plan)
        
        assert result["stats"].items_processed == 1
        assert result["stats"].items_success == 0
        assert result["stats"].items_failed == 1
        assert len(result["errors"]) == 1
        
        # Check error details
        error = result["errors"][0]
        assert "error" in error
        assert "item_meta" in error
        assert "rule" in error
        
        # Check error hook was called
        error_events = mock_hook_manager.get_events("copy:error")
        assert len(error_events) == 1
    
    def test_apply_object_hooks(self, sample_user_data, mock_hook_manager):
        """Test object-level hooks during apply"""
        rule = CopyRule(
            name="hook_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        plan = engine.plan(sample_user_data)
        result = engine.apply(plan)
        
        # Check object hooks were called
        before_events = mock_hook_manager.get_events("copy:before_object")
        after_events = mock_hook_manager.get_events("copy:after_object")
        
        assert len(before_events) == 1
        assert len(after_events) == 1
        
        # Check event data
        assert "meta" in before_events[0]["data"]
        assert "meta" in after_events[0]["data"]
        assert "obj" in after_events[0]["data"]
    
    def test_apply_commit_hooks(self, sample_user_data, mock_hook_manager):
        """Test commit hooks during apply"""
        rule = CopyRule(
            name="commit_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset, hooks=mock_hook_manager)
        
        plan = engine.plan(sample_user_data)
        result = engine.apply(plan)
        
        # Check commit hook was called
        commit_events = mock_hook_manager.get_events("copy:commit")
        assert len(commit_events) == 1
        assert "results" in commit_events[0]["data"]


class TestCopyEngineIntegration:
    """Integration tests for CopyEngine"""
    
    def test_full_copy_workflow(self, sample_user_data):
        """Test complete copy workflow from plan to apply"""
        # Create rule with multiple operations
        rule = CopyRule(
            name="full_workflow",
            match={"path": "$"},
            mode=CopyMode.DEEP,
            ops=[
                {"exclude": ["password"]},
                {"mask": {"fields": ["email"], "style": "stars"}},
                {"rename": {"from": "name", "to": "full_name"}}
            ]
        )
        ruleset = RuleSet([rule])
        engine = CopyEngine(ruleset=ruleset)
        
        # Plan
        plan = engine.plan(sample_user_data)
        assert len(plan.items) == 1
        assert len(plan.items[0].ops) == 3
        
        # Apply
        result = engine.apply(plan)
        assert result["stats"].items_success == 1
        assert len(result["errors"]) == 0
        
        # Check final result
        copied_data = result["results"][0]["obj"]
        assert copied_data != sample_user_data
        assert copied_data is not sample_user_data
    
    def test_multiple_rules_priority(self, sample_user_data):
        """Test multiple rules with priority handling"""
        rule1 = CopyRule(
            name="general_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[],
            priority=1
        )
        rule2 = CopyRule(
            name="specific_rule",
            match={"path": "$"},
            mode=CopyMode.DEEP,
            ops=[{"exclude": ["password"]}],
            priority=10
        )
        
        ruleset = RuleSet([rule1, rule2])
        engine = CopyEngine(ruleset=ruleset)
        
        plan = engine.plan(sample_user_data)
        
        # Higher priority rule should be selected
        assert len(plan.items) == 1
        assert plan.items[0].rule.name == "specific_rule"
        assert plan.items[0].mode == CopyMode.DEEP
    
    def test_copy_mode_differences(self, sample_user_data):
        """Test different copy modes produce different results"""
        shallow_rule = CopyRule(
            name="shallow_rule",
            match={"path": "$"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        deep_rule = CopyRule(
            name="deep_rule", 
            match={"path": "$"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        
        # Test shallow copy
        shallow_engine = CopyEngine(RuleSet([shallow_rule]))
        shallow_plan = shallow_engine.plan(sample_user_data)
        shallow_result = shallow_engine.apply(shallow_plan)
        
        # Test deep copy
        deep_engine = CopyEngine(RuleSet([deep_rule]))
        deep_plan = deep_engine.plan(sample_user_data)
        deep_result = deep_engine.apply(deep_plan)
        
        # Both should succeed
        assert shallow_result["stats"].items_success == 1
        assert deep_result["stats"].items_success == 1
        
        # Results should be equivalent but different objects
        shallow_data = shallow_result["results"][0]["obj"]
        deep_data = deep_result["results"][0]["obj"]
        
        assert shallow_data == deep_data
        assert shallow_data is not sample_user_data
        assert deep_data is not sample_user_data