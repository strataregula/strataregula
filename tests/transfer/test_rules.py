"""
Unit tests for Rules system

Tests for rule matching, priority resolution, and conflict handling.
"""

import pytest
import yaml
from strataregula.transfer.rules import (
    RuleSet, CopyRule, MatchExpr, MatchType, ConflictPolicy
)
from strataregula.transfer.deep_copy import CopyMode


class TestCopyRule:
    """Test individual copy rule functionality"""
    
    def test_rule_dict_matching(self):
        """Test rule matching with dictionary format"""
        rule = CopyRule(
            name="test_rule",
            match={"path": "$.users[*]", "kind": "user"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        
        # Should match
        meta1 = {"path": "$.users[0]", "kind": "user", "labels": []}
        assert rule.matches(meta1)
        
        # Should not match (wrong kind)
        meta2 = {"path": "$.users[0]", "kind": "admin", "labels": []}
        assert not rule.matches(meta2)
        
        # Should not match (wrong path)
        meta3 = {"path": "$.admins[0]", "kind": "user", "labels": []}
        assert not rule.matches(meta3)
    
    def test_rule_labels_matching(self):
        """Test rule matching with labels"""
        rule = CopyRule(
            name="pii_rule",
            match={"labels": ["pii"]},
            mode=CopyMode.DEEP,
            ops=[]
        )
        
        # Should match
        meta1 = {"path": "$.data", "labels": ["pii", "sensitive"]}
        assert rule.matches(meta1)
        
        # Should not match
        meta2 = {"path": "$.data", "labels": ["public"]}
        assert not rule.matches(meta2)
    
    def test_rule_path_matching(self):
        """Test JSONPath-style matching"""
        rule = CopyRule(
            name="user_rule",
            match={"path": "$.users[*]"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        
        # Should match (starts with pattern)
        meta1 = {"path": "$.users[0]"}
        assert rule.matches(meta1)
        
        meta2 = {"path": "$.users[42]"}
        assert rule.matches(meta2)
        
        # Should not match
        meta3 = {"path": "$.admins[0]"}
        assert not rule.matches(meta3)
    
    def test_rule_wildcard_matching(self):
        """Test wildcard matching"""
        rule = CopyRule(
            name="wildcard_rule",
            match={"path": "*"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        
        # Should match anything
        meta1 = {"path": "$.anything"}
        assert rule.matches(meta1)
        
        meta2 = {"path": "totally.different.path"}
        assert rule.matches(meta2)
    
    def test_rule_disabled(self):
        """Test disabled rule"""
        rule = CopyRule(
            name="disabled_rule",
            match={"path": "*"},
            mode=CopyMode.DEEP,
            ops=[],
            enabled=False
        )
        
        meta = {"path": "$.anything"}
        assert not rule.matches(meta)  # Should not match when disabled
    
    def test_rule_multiple_conditions(self):
        """Test rule with multiple matching conditions"""
        rule = CopyRule(
            name="multi_rule",
            match={
                "path": "$.users[*]",
                "kind": "user",
                "labels": ["pii"]
            },
            mode=CopyMode.DEEP,
            ops=[]
        )
        
        # Should match (all conditions met)
        meta1 = {
            "path": "$.users[0]",
            "kind": "user", 
            "labels": ["pii", "sensitive"]
        }
        assert rule.matches(meta1)
        
        # Should not match (missing kind)
        meta2 = {
            "path": "$.users[0]",
            "labels": ["pii"]
        }
        assert not rule.matches(meta2)
        
        # Should not match (wrong labels)
        meta3 = {
            "path": "$.users[0]",
            "kind": "user",
            "labels": ["public"]
        }
        assert not rule.matches(meta3)


class TestRuleSet:
    """Test RuleSet functionality"""
    
    def test_ruleset_creation_empty(self):
        """Test creating empty ruleset"""
        ruleset = RuleSet([])
        
        meta = {"path": "$.anything"}
        result = ruleset.match(meta)
        assert result is None
    
    def test_ruleset_single_match(self):
        """Test single rule matching"""
        rule = CopyRule(
            name="test_rule",
            match={"path": "$.users[*]"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        ruleset = RuleSet([rule])
        
        meta = {"path": "$.users[0]"}
        result = ruleset.match(meta)
        
        assert result is not None
        assert result.name == "test_rule"
    
    def test_ruleset_no_match(self):
        """Test no matching rules"""
        rule = CopyRule(
            name="user_rule",
            match={"path": "$.users[*]"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        ruleset = RuleSet([rule])
        
        meta = {"path": "$.admins[0]"}
        result = ruleset.match(meta)
        
        assert result is None
    
    def test_ruleset_priority_ordering(self):
        """Test priority-based rule ordering"""
        rule1 = CopyRule(
            name="low_priority",
            match={"path": "*"},
            mode=CopyMode.SHALLOW,
            ops=[],
            priority=1
        )
        rule2 = CopyRule(
            name="high_priority", 
            match={"path": "*"},
            mode=CopyMode.DEEP,
            ops=[],
            priority=10
        )
        
        ruleset = RuleSet([rule1, rule2])  # Add in wrong order
        
        meta = {"path": "$.anything"}
        result = ruleset.match(meta)
        
        # Higher priority rule should be selected
        assert result.name == "high_priority"
    
    def test_ruleset_conflict_auto_resolution(self):
        """Test automatic conflict resolution"""
        rule1 = CopyRule(
            name="general_rule",
            match={"path": "$.users[*]"},
            mode=CopyMode.SHALLOW,
            ops=[],
            priority=1
        )
        rule2 = CopyRule(
            name="specific_rule",
            match={"path": "$.users[*]"},
            mode=CopyMode.DEEP,
            ops=[],
            priority=5
        )
        
        ruleset = RuleSet([rule1, rule2], ConflictPolicy.AUTO)
        
        meta = {"path": "$.users[0]"}
        result = ruleset.match(meta)
        
        # Higher priority rule should win
        assert result.name == "specific_rule"
    
    def test_ruleset_conflict_fail_policy(self):
        """Test conflict fail policy"""
        rule1 = CopyRule(
            name="rule1",
            match={"path": "*"},
            mode=CopyMode.SHALLOW,
            ops=[],
            priority=1
        )
        rule2 = CopyRule(
            name="rule2",
            match={"path": "*"},
            mode=CopyMode.DEEP,
            ops=[],
            priority=1  # Same priority = conflict
        )
        
        ruleset = RuleSet([rule1, rule2], ConflictPolicy.FAIL)
        
        meta = {"path": "$.anything"}
        with pytest.raises(ValueError) as exc_info:
            ruleset.match(meta)
        
        assert "Multiple rules match" in str(exc_info.value)
    
    def test_ruleset_conflict_skip_policy(self):
        """Test conflict skip policy"""
        rule1 = CopyRule(
            name="rule1",
            match={"path": "*"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        rule2 = CopyRule(
            name="rule2",
            match={"path": "*"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        
        ruleset = RuleSet([rule1, rule2], ConflictPolicy.SKIP)
        
        meta = {"path": "$.anything"}
        result = ruleset.match(meta)
        
        # Should return None when skipping conflicts
        assert result is None
    
    def test_add_remove_rules(self):
        """Test adding and removing rules"""
        rule1 = CopyRule(
            name="rule1",
            match={"path": "$.users[*]"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        
        ruleset = RuleSet([])
        assert len(ruleset.list_rules()) == 0
        
        # Add rule
        ruleset.add_rule(rule1)
        assert len(ruleset.list_rules()) == 1
        assert ruleset.get_rule("rule1") is rule1
        
        # Remove rule
        removed = ruleset.remove_rule("rule1")
        assert removed is True
        assert len(ruleset.list_rules()) == 0
        
        # Try to remove nonexistent rule
        removed = ruleset.remove_rule("nonexistent")
        assert removed is False
    
    def test_enable_disable_rules(self):
        """Test enabling and disabling rules"""
        rule = CopyRule(
            name="test_rule",
            match={"path": "*"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        ruleset = RuleSet([rule])
        
        meta = {"path": "$.anything"}
        
        # Initially enabled
        result = ruleset.match(meta)
        assert result is not None
        
        # Disable rule
        ruleset.enable_rule("test_rule", False)
        result = ruleset.match(meta)
        assert result is None
        
        # Re-enable rule
        ruleset.enable_rule("test_rule", True)
        result = ruleset.match(meta)
        assert result is not None


class TestRuleSetFromYAML:
    """Test RuleSet creation from YAML"""
    
    def test_load_from_yaml(self, sample_copy_policy):
        """Test loading ruleset from YAML data"""
        ruleset = RuleSet.from_yaml(sample_copy_policy)
        
        rules = ruleset.list_rules()
        assert len(rules) == 2
        
        # Check first rule
        secure_rule = ruleset.get_rule("secure_user_copy")
        assert secure_rule is not None
        assert secure_rule.mode == CopyMode.DEEP
        assert len(secure_rule.ops) == 3
        
        # Check second rule
        simple_rule = ruleset.get_rule("simple_shallow_copy")
        assert simple_rule is not None
        assert simple_rule.mode == CopyMode.SHALLOW
        assert len(simple_rule.ops) == 0
    
    def test_yaml_rule_matching(self, sample_copy_policy):
        """Test matching with YAML-loaded rules"""
        ruleset = RuleSet.from_yaml(sample_copy_policy)
        
        # Should match secure_user_copy rule
        user_meta = {"path": "$.users[0]", "labels": ["pii"]}
        result = ruleset.match(user_meta)
        assert result is not None
        assert result.name == "secure_user_copy"
        
        # Should match simple_shallow_copy rule
        item_meta = {"path": "$.items[0]"}
        result = ruleset.match(item_meta)
        assert result is not None
        assert result.name == "simple_shallow_copy"
        
        # Should not match any rule
        admin_meta = {"path": "$.admins[0]"}
        result = ruleset.match(admin_meta)
        assert result is None
    
    def test_yaml_with_conflict_policy(self):
        """Test YAML with conflict policy"""
        yaml_data = {
            "conflict_policy": "fail",
            "copy_policies": [
                {
                    "name": "rule1",
                    "match": {"path": "*"},
                    "mode": "shallow",
                    "ops": []
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(yaml_data)
        assert ruleset.conflict_policy == ConflictPolicy.FAIL
    
    def test_yaml_rule_with_hooks(self):
        """Test YAML rule with hooks configuration"""
        yaml_data = {
            "copy_policies": [
                {
                    "name": "hooked_rule",
                    "match": {"path": "$.users[*]"},
                    "mode": "deep",
                    "ops": [],
                    "hooks": {
                        "before_object": ["audit.start"],
                        "after_object": ["audit.end"]
                    }
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(yaml_data)
        rule = ruleset.get_rule("hooked_rule")
        
        assert rule is not None
        assert rule.hooks is not None
        assert "before_object" in rule.hooks
        assert "audit.start" in rule.hooks["before_object"]
    
    def test_yaml_rule_priorities(self):
        """Test YAML rules with priorities"""
        yaml_data = {
            "copy_policies": [
                {
                    "name": "low_priority",
                    "match": {"path": "*"},
                    "mode": "shallow",
                    "ops": [],
                    "priority": 1
                },
                {
                    "name": "high_priority",
                    "match": {"path": "*"},
                    "mode": "deep", 
                    "ops": [],
                    "priority": 10
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(yaml_data)
        
        meta = {"path": "$.anything"}
        result = ruleset.match(meta)
        
        # High priority rule should be selected
        assert result.name == "high_priority"
    
    def test_yaml_disabled_rule(self):
        """Test YAML rule that is disabled"""
        yaml_data = {
            "copy_policies": [
                {
                    "name": "disabled_rule",
                    "match": {"path": "*"},
                    "mode": "deep",
                    "ops": [],
                    "enabled": False
                }
            ]
        }
        
        ruleset = RuleSet.from_yaml(yaml_data)
        
        meta = {"path": "$.anything"}
        result = ruleset.match(meta)
        
        assert result is None  # Disabled rule should not match


class TestRuleSetValidation:
    """Test RuleSet validation"""
    
    def test_validate_no_issues(self, sample_copy_policy):
        """Test validation with no issues"""
        ruleset = RuleSet.from_yaml(sample_copy_policy)
        issues = ruleset.validate()
        
        assert len(issues) == 0
    
    def test_validate_duplicate_names(self):
        """Test validation with duplicate rule names"""
        rule1 = CopyRule(
            name="duplicate",
            match={"path": "$.users[*]"},
            mode=CopyMode.DEEP,
            ops=[]
        )
        rule2 = CopyRule(
            name="duplicate",  # Same name
            match={"path": "$.admins[*]"},
            mode=CopyMode.SHALLOW,
            ops=[]
        )
        
        ruleset = RuleSet([rule1, rule2])
        issues = ruleset.validate()
        
        assert len(issues) > 0
        assert any("Duplicate rule names" in issue for issue in issues)
    
    def test_validate_invalid_mode(self):
        """Test validation with invalid copy mode"""
        # This would normally be caught by enum validation,
        # but we can test the validation logic
        rule = CopyRule(
            name="invalid_rule",
            match={"path": "*"},
            mode="invalid_mode",  # Invalid mode
            ops=[]
        )
        
        ruleset = RuleSet([rule])
        issues = ruleset.validate()
        
        assert len(issues) > 0
        assert any("Invalid copy mode" in issue for issue in issues)