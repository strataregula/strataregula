"""
Rule System for Transfer/Copy operations

Provides rule matching, priority resolution, and conflict handling.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re
from abc import ABC, abstractmethod

from .deep_copy import CopyMode


class MatchType(Enum):
    """Types of rule matching"""
    PATH = "path"           # JSONPath expression
    LABELS = "labels"       # Label matching
    KIND = "kind"          # Object kind/type
    REGEX = "regex"        # Regular expression
    CUSTOM = "custom"      # Custom function


class ConflictPolicy(Enum):
    """Conflict resolution policies"""
    FAIL = "fail"          # Fail on conflict
    WARN = "warn"          # Warn and continue
    AUTO = "auto"          # Auto-resolve by priority
    SKIP = "skip"          # Skip conflicting items


@dataclass
class MatchExpr:
    """Rule matching expression"""
    type: MatchType
    pattern: str
    negate: bool = False


@dataclass
class CopyRule:
    """Individual copy rule definition"""
    name: str
    match: Union[MatchExpr, List[MatchExpr], Dict[str, Any]]
    mode: CopyMode
    ops: List[Dict[str, Any]]
    priority: int = 0
    hooks: Optional[Dict[str, List[str]]] = None
    enabled: bool = True
    
    def matches(self, obj_meta: Dict[str, Any]) -> bool:
        """Check if this rule matches object metadata"""
        if not self.enabled:
            return False
            
        if isinstance(self.match, dict):
            return self._match_dict(self.match, obj_meta)
        elif isinstance(self.match, list):
            # AND logic for multiple expressions
            return all(self._match_expr(expr, obj_meta) for expr in self.match)
        else:
            return self._match_expr(self.match, obj_meta)
    
    def _match_dict(self, match_dict: Dict[str, Any], obj_meta: Dict[str, Any]) -> bool:
        """Match using dictionary-style rule (YAML format)"""
        for key, value in match_dict.items():
            if key == "path":
                if not self._match_path(value, obj_meta.get("path", "")):
                    return False
            elif key == "labels":
                if not self._match_labels(value, obj_meta.get("labels", [])):
                    return False
            elif key == "kind":
                if obj_meta.get("kind") != value:
                    return False
            else:
                # Custom metadata matching
                if obj_meta.get(key) != value:
                    return False
        return True
    
    def _match_expr(self, expr: MatchExpr, obj_meta: Dict[str, Any]) -> bool:
        """Match using expression object"""
        if expr.type == MatchType.PATH:
            result = self._match_path(expr.pattern, obj_meta.get("path", ""))
        elif expr.type == MatchType.LABELS:
            result = self._match_labels([expr.pattern], obj_meta.get("labels", []))
        elif expr.type == MatchType.KIND:
            result = obj_meta.get("kind") == expr.pattern
        elif expr.type == MatchType.REGEX:
            result = bool(re.match(expr.pattern, str(obj_meta.get("path", ""))))
        else:
            result = False
            
        return not result if expr.negate else result
    
    def _match_path(self, pattern: str, obj_path: str) -> bool:
        """Match JSONPath patterns (simplified)"""
        # TODO: Implement proper JSONPath matching
        # For now, use simple glob-style matching
        if pattern == "*":
            return True
        if pattern.startswith("$."):
            return obj_path.startswith(pattern[2:])
        return pattern in obj_path
    
    def _match_labels(self, required_labels: List[str], obj_labels: List[str]) -> bool:
        """Match labels (any required label must be present)"""
        return any(label in obj_labels for label in required_labels)


class RuleSet:
    """Collection of copy rules with priority and conflict resolution"""
    
    def __init__(self, rules: List[CopyRule], conflict_policy: ConflictPolicy = ConflictPolicy.AUTO):
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)  # Higher priority first
        self.conflict_policy = conflict_policy
        self.version = "1.0"
    
    def match(self, obj_meta: Dict[str, Any]) -> Optional[CopyRule]:
        """Find first matching rule for object metadata"""
        matching_rules = [rule for rule in self.rules if rule.matches(obj_meta)]
        
        if not matching_rules:
            return None
        
        if len(matching_rules) == 1:
            return matching_rules[0]
        
        # Handle conflicts
        return self._resolve_conflict(matching_rules, obj_meta)
    
    def _resolve_conflict(self, rules: List[CopyRule], obj_meta: Dict[str, Any]) -> Optional[CopyRule]:
        """Resolve conflicts between multiple matching rules"""
        if self.conflict_policy == ConflictPolicy.FAIL:
            rule_names = [r.name for r in rules]
            raise ValueError(f"Multiple rules match {obj_meta.get('path', 'object')}: {rule_names}")
        
        elif self.conflict_policy == ConflictPolicy.WARN:
            # TODO: Emit warning
            return rules[0]  # Return highest priority
        
        elif self.conflict_policy == ConflictPolicy.AUTO:
            return rules[0]  # Return highest priority
        
        elif self.conflict_policy == ConflictPolicy.SKIP:
            return None  # Skip this object
        
        return rules[0]
    
    @classmethod
    def from_yaml(cls, yaml_data: Dict[str, Any]) -> 'RuleSet':
        """Create RuleSet from YAML configuration"""
        rules = []
        
        copy_policies = yaml_data.get('copy_policies', [])
        conflict_policy = ConflictPolicy(yaml_data.get('conflict_policy', 'auto'))
        
        for policy_data in copy_policies:
            rule = cls._parse_rule(policy_data)
            rules.append(rule)
        
        return cls(rules, conflict_policy)
    
    @classmethod
    def _parse_rule(cls, policy_data: Dict[str, Any]) -> CopyRule:
        """Parse individual rule from YAML policy data"""
        name = policy_data['name']
        match_data = policy_data['match']
        mode = CopyMode(policy_data.get('mode', 'shallow'))
        ops = policy_data.get('ops', [])
        priority = policy_data.get('priority', 0)
        hooks = policy_data.get('hooks')
        enabled = policy_data.get('enabled', True)
        
        return CopyRule(
            name=name,
            match=match_data,
            mode=mode,
            ops=ops,
            priority=priority,
            hooks=hooks,
            enabled=enabled
        )
    
    def add_rule(self, rule: CopyRule) -> None:
        """Add rule and resort by priority"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, name: str) -> bool:
        """Remove rule by name"""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < initial_count
    
    def get_rule(self, name: str) -> Optional[CopyRule]:
        """Get rule by name"""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
    
    def enable_rule(self, name: str, enabled: bool = True) -> bool:
        """Enable/disable rule by name"""
        rule = self.get_rule(name)
        if rule:
            rule.enabled = enabled
            return True
        return False
    
    def list_rules(self, enabled_only: bool = True) -> List[CopyRule]:
        """List all rules, optionally filtered by enabled status"""
        if enabled_only:
            return [r for r in self.rules if r.enabled]
        return self.rules.copy()
    
    def validate(self) -> List[str]:
        """Validate ruleset configuration and return list of issues"""
        issues = []
        
        # Check for duplicate rule names
        names = [r.name for r in self.rules]
        duplicates = set([name for name in names if names.count(name) > 1])
        if duplicates:
            issues.append(f"Duplicate rule names: {duplicates}")
        
        # Check for valid modes and operations
        for rule in self.rules:
            if not isinstance(rule.mode, CopyMode):
                issues.append(f"Rule '{rule.name}': Invalid copy mode '{rule.mode}'")
            
            # TODO: Validate operations syntax
            
        return issues