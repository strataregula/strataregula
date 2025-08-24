"""
Unit tests for core compiler module

Tests for PatternCache and PatternCompiler.
"""

import pytest
from pathlib import Path
import tempfile
import yaml
from unittest.mock import patch, mock_open

from strataregula.core.compiler import (
    PatternCache, PatternCompiler
)


class TestPatternCache:
    """Test PatternCache functionality"""
    
    def test_cache_initialization(self):
        """Test cache initialization with default size"""
        cache = PatternCache()
        
        assert cache.max_size == 10000
        assert len(cache._cache) == 0
    
    def test_cache_initialization_custom_size(self):
        """Test cache initialization with custom size"""
        cache = PatternCache(max_size=100)
        
        assert cache.max_size == 100
    
    def test_cache_get_set(self):
        """Test basic get/set operations"""
        cache = PatternCache()
        
        # Initially empty
        assert cache.get("key1") is None
        
        # Set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Set another
        cache.set("key2", {"nested": "value"})
        assert cache.get("key2") == {"nested": "value"}
    
    def test_cache_clear(self):
        """Test cache clearing"""
        cache = PatternCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache._cache) == 2
        
        cache.clear()
        assert len(cache._cache) == 0
        assert cache.get("key1") is None
    
    def test_cache_size_limit(self):
        """Test cache size limiting and cleanup"""
        cache = PatternCache(max_size=3)
        
        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        assert len(cache._cache) == 3
        
        # Add one more - should trigger cleanup
        cache.set("key4", "value4")
        assert len(cache._cache) <= 3  # Should be reduced
        
        # key4 should be present (most recent)
        assert cache.get("key4") == "value4"
    
    def test_cache_overwrite(self):
        """Test overwriting existing cache entries"""
        cache = PatternCache()
        
        cache.set("key", "old_value")
        assert cache.get("key") == "old_value"
        
        cache.set("key", "new_value")
        assert cache.get("key") == "new_value"


class TestPatternCompiler:
    """Test PatternCompiler functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.compiler = PatternCompiler()
    
    def test_compiler_initialization(self):
        """Test compiler initialization"""
        assert isinstance(self.compiler.data_sources, dict)
        assert isinstance(self.compiler.pattern_rules, dict)
        assert len(self.compiler.data_sources) == 0
        assert len(self.compiler.pattern_rules) == 0
    
    def test_load_config_valid(self):
        """Test loading valid configuration"""
        config_data = {
            'data_sources': {
                'regions': ['us-east', 'us-west', 'eu-central']
            },
            'pattern_rules': {
                'service.*': {
                    'data_source': 'regions',
                    'template': 'service.{}'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            self.compiler.load_config(config_path)
            
            assert 'regions' in self.compiler.data_sources
            assert self.compiler.data_sources['regions'] == ['us-east', 'us-west', 'eu-central']
            assert 'service.*' in self.compiler.pattern_rules
            
        finally:
            config_path.unlink()
    
    def test_load_config_invalid_file(self):
        """Test loading invalid configuration file"""
        with pytest.raises(ValueError, match="Failed to load configuration"):
            self.compiler.load_config(Path("nonexistent.yaml"))
    
    def test_load_config_invalid_yaml(self):
        """Test loading malformed YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            config_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Failed to load configuration"):
                self.compiler.load_config(config_path)
        finally:
            config_path.unlink()
    
    def test_load_config_non_dict(self):
        """Test loading YAML that isn't a dictionary"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(["not", "a", "dict"], f)
            config_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Configuration must be a dictionary"):
                self.compiler.load_config(config_path)
        finally:
            config_path.unlink()
    
    def test_set_data_sources(self):
        """Test setting data sources programmatically"""
        data_sources = {
            'regions': ['us-east', 'us-west'],
            'services': ['api', 'web', 'db']
        }
        
        self.compiler.set_data_sources(data_sources)
        
        assert self.compiler.data_sources == data_sources
        # Should not be the same object (copied)
        assert self.compiler.data_sources is not data_sources
    
    def test_set_pattern_rules(self):
        """Test setting pattern rules programmatically"""
        pattern_rules = {
            'service.*': {
                'data_source': 'regions',
                'template': 'service.{}'
            }
        }
        
        self.compiler.set_pattern_rules(pattern_rules)
        
        assert self.compiler.pattern_rules == pattern_rules
        # Should not be the same object (copied)
        assert self.compiler.pattern_rules is not pattern_rules
    
    def test_compile_patterns_no_wildcards(self):
        """Test compiling patterns without wildcards"""
        patterns = {
            'simple.key': 'value1',
            'another.key': 'value2'
        }
        
        result = self.compiler.compile_patterns(patterns)
        
        assert result == patterns
    
    def test_compile_patterns_with_wildcards(self):
        """Test compiling patterns with wildcards"""
        self.compiler.set_data_sources({
            'regions': ['us-east', 'us-west']
        })
        self.compiler.set_pattern_rules({
            'service.*': {
                'data_source': 'regions',
                'template': 'service.{}'
            }
        })
        
        patterns = {
            'service.*': 'api-endpoint'
        }
        
        result = self.compiler.compile_patterns(patterns)
        
        expected = {
            'service.us-east': 'api-endpoint',
            'service.us-west': 'api-endpoint'
        }
        assert result == expected
    
    def test_compile_patterns_caching(self):
        """Test pattern compilation caching"""
        self.compiler.set_data_sources({
            'regions': ['us-east']
        })
        self.compiler.set_pattern_rules({
            'service.*': {
                'data_source': 'regions'
            }
        })
        
        patterns = {'service.*': 'value'}
        
        # First compilation
        result1 = self.compiler.compile_patterns(patterns)
        
        # Second compilation should use cache
        result2 = self.compiler.compile_patterns(patterns)
        
        assert result1 == result2
        assert len(self.compiler._pattern_cache._cache) > 0
    
    def test_find_matching_rule(self):
        """Test finding matching rules"""
        self.compiler.set_pattern_rules({
            'exact.match': {'rule': 'exact'},
            'service.*': {'rule': 'wildcard'},
            '*.global': {'rule': 'prefix_wildcard'}
        })
        
        # Exact match
        rule = self.compiler._find_matching_rule('exact.match')
        assert rule == {'rule': 'exact'}
        
        # Wildcard match
        rule = self.compiler._find_matching_rule('service.api')
        assert rule == {'rule': 'wildcard'}
        
        # Prefix wildcard match
        rule = self.compiler._find_matching_rule('config.global')
        assert rule == {'rule': 'prefix_wildcard'}
        
        # No match
        rule = self.compiler._find_matching_rule('no.match.here')
        assert rule is None
    
    def test_patterns_match(self):
        """Test pattern matching logic"""
        # Exact match
        assert self.compiler._patterns_match('exact', 'exact')
        
        # Wildcard matches
        assert self.compiler._patterns_match('service.api', 'service.*')
        assert self.compiler._patterns_match('config.global', '*.global')
        assert self.compiler._patterns_match('a.b.c', 'a.*')
        
        # Non-matches
        assert not self.compiler._patterns_match('service.api', 'config.*')
        assert not self.compiler._patterns_match('a.b.c', 'b.*')
    
    def test_expand_with_template_single_wildcard(self):
        """Test expansion with single wildcard"""
        pattern = 'service.*'
        template = 'service.{}'
        data_items = ['api', 'web', 'db']
        value = 'endpoint'
        
        result = self.compiler._expand_with_template(pattern, template, data_items, value)
        
        expected = {
            'service.api': 'endpoint',
            'service.web': 'endpoint', 
            'service.db': 'endpoint'
        }
        assert result == expected
    
    def test_expand_with_template_multiple_wildcards(self):
        """Test expansion with multiple wildcards"""
        pattern = '*.service.*'
        template = '{}.service.{}'
        data_items = ['us', 'eu']
        value = 'config'
        
        result = self.compiler._expand_with_template(pattern, template, data_items, value)
        
        expected = {
            'us.service.us': 'config',
            'us.service.eu': 'config',
            'eu.service.us': 'config',
            'eu.service.eu': 'config'
        }
        assert result == expected
    
    def test_expand_with_template_no_wildcards(self):
        """Test expansion without wildcards"""
        pattern = 'simple.key'
        template = 'simple.key'
        data_items = ['item1', 'item2']
        value = 'value'
        
        result = self.compiler._expand_with_template(pattern, template, data_items, value)
        
        # Should return original pattern when no wildcards
        assert result == {'simple.key': 'value'}
    
    def test_split_pattern_cached(self):
        """Test cached pattern splitting"""
        pattern = 'service.region.component'
        
        result1 = self.compiler._split_pattern_cached(pattern)
        result2 = self.compiler._split_pattern_cached(pattern)
        
        assert result1 == ('service', 'region', 'component')
        assert result1 is result2  # Should be same object from cache
