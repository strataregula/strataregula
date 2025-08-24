"""
Unit tests for core compiler module

Tests for PatternCache, PatternCompiler, and YAMLConfigCompiler.
"""

import pytest
from pathlib import Path
import tempfile
import yaml
from unittest.mock import patch, mock_open

from strataregula.core.compiler import (
    PatternCache, PatternCompiler, YAMLConfigCompiler
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


class TestYAMLConfigCompiler:
    """Test YAMLConfigCompiler functionality"""
    
    def test_compiler_initialization_no_config(self):
        """Test compiler initialization without config"""
        compiler = YAMLConfigCompiler()
        
        assert isinstance(compiler.compiler, PatternCompiler)
        assert compiler.regions == []
        assert compiler.prefectures == []
    
    def test_compiler_initialization_with_config(self):
        """Test compiler initialization with config file"""
        config_data = {
            'data_sources': {'regions': ['us-east']},
            'pattern_rules': {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            compiler = YAMLConfigCompiler(config_path)
            assert 'regions' in compiler.compiler.data_sources
        finally:
            config_path.unlink()
    
    def test_load_yaml(self):
        """Test loading YAML files"""
        compiler = YAMLConfigCompiler()
        
        test_data = {'key': 'value', 'nested': {'inner': 'data'}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_data, f)
            yaml_path = Path(f.name)
        
        try:
            result = compiler.load_yaml(yaml_path)
            assert result == test_data
        finally:
            yaml_path.unlink()
    
    def test_set_regions(self):
        """Test setting regions"""
        compiler = YAMLConfigCompiler()
        regions = ['us-east', 'us-west', 'eu-central']
        
        compiler.set_regions(regions)
        
        assert compiler.regions == regions
        assert 'regions' in compiler.compiler.data_sources
        assert compiler.compiler.data_sources['regions'] == regions
    
    def test_set_prefectures(self):
        """Test setting prefectures"""
        compiler = YAMLConfigCompiler()
        prefectures = ['tokyo', 'osaka', 'kyoto']
        
        compiler.set_prefectures(prefectures)
        
        assert compiler.prefectures == prefectures
        assert 'prefectures' in compiler.compiler.data_sources
        assert compiler.compiler.data_sources['prefectures'] == prefectures
    
    def test_compile_service_map_simple(self):
        """Test compiling simple service map"""
        compiler = YAMLConfigCompiler()
        
        service_map = {
            'api': 'api-service',
            'web': 'web-service',
            'db.primary': 'database-primary'
        }
        
        result = compiler.compile_service_map(service_map)
        
        assert 'direct_mapping' in result
        assert 'component_mapping' in result
        
        # Direct mappings (no dots)
        assert result['direct_mapping']['api'] == 'api-service'
        assert result['direct_mapping']['web'] == 'web-service'
        
        # Component mappings (with dots)
        assert result['component_mapping']['db.primary'] == 'database-primary'
    
    def test_compile_service_map_with_patterns(self):
        """Test compiling service map with patterns"""
        compiler = YAMLConfigCompiler()
        compiler.set_regions(['us-east', 'us-west'])
        compiler.compiler.set_pattern_rules({
            'api.*': {
                'data_source': 'regions'
            }
        })
        
        service_map = {
            'api.*': 'api-endpoint'
        }
        
        result = compiler.compile_service_map(service_map)
        
        # Should expand pattern
        assert 'api.us-east' in result['component_mapping']
        assert 'api.us-west' in result['component_mapping']
        assert result['component_mapping']['api.us-east'] == 'api-endpoint'
    
    def test_compile_service_map_empty(self):
        """Test compiling empty service map"""
        compiler = YAMLConfigCompiler()
        
        result = compiler.compile_service_map({})
        
        assert result == {
            "direct_mapping": {},
            "component_mapping": {}
        }
    
    def test_compile_service_map_invalid_input(self):
        """Test compiling with invalid input"""
        compiler = YAMLConfigCompiler()
        
        with pytest.raises(ValueError, match="Service map must be a dictionary"):
            compiler.compile_service_map("not a dict")
        
        with pytest.raises(ValueError, match="Service map must be a dictionary"):
            compiler.compile_service_map(["not", "a", "dict"])
    
    def test_get_performance_stats(self):
        """Test getting performance statistics"""
        compiler = YAMLConfigCompiler()
        compiler.set_regions(['us-east', 'us-west'])
        compiler.set_prefectures(['tokyo', 'osaka'])
        
        # Add some data to caches
        compiler.compiler.compile_patterns({'test.key': 'value'})
        compiler.compiler._split_pattern_cached('test.pattern')
        
        stats = compiler.get_performance_stats()
        
        assert 'pattern_cache_size' in stats
        assert 'split_cache_size' in stats
        assert 'data_sources_count' in stats
        assert 'pattern_rules_count' in stats
        assert 'regions_count' in stats
        assert 'prefectures_count' in stats
        
        assert stats['regions_count'] == 2
        assert stats['prefectures_count'] == 2
        assert stats['data_sources_count'] >= 2  # regions + prefectures


class TestBackwardCompatibility:
    """Test backward compatibility aliases"""
    
    def test_fast_yaml_compiler_alias(self):
        """Test FastYAMLCompiler alias"""
        from strataregula.core.compiler import FastYAMLCompiler
        
        compiler = FastYAMLCompiler()
        assert isinstance(compiler, YAMLConfigCompiler)
    
    def test_wildcard_expander_alias(self):
        """Test WildcardExpander alias"""
        from strataregula.core.compiler import WildcardExpander
        
        expander = WildcardExpander()
        assert isinstance(expander, PatternCompiler)


class TestCompilerIntegration:
    """Integration tests for compiler components"""
    
    def test_full_compilation_workflow(self):
        """Test complete compilation workflow"""
        compiler = YAMLConfigCompiler()
        
        # Setup data sources and rules
        compiler.set_regions(['us-east', 'us-west'])
        compiler.compiler.set_pattern_rules({
            'service.*': {
                'data_source': 'regions'
            },
            'config.*': {
                'data_source': 'regions'  
            }
        })
        
        # Service map with mixed patterns
        service_map = {
            'api': 'api-service',           # Direct mapping
            'service.*': 'service-endpoint', # Pattern expansion
            'config.*.database': 'db-config', # Complex pattern (would expand if implemented)
            'web.frontend': 'web-app'        # Component mapping
        }
        
        result = compiler.compile_service_map(service_map)
        
        # Verify results
        assert result['direct_mapping']['api'] == 'api-service'
        assert result['component_mapping']['web.frontend'] == 'web-app'
        assert result['component_mapping']['service.us-east'] == 'service-endpoint'
        assert result['component_mapping']['service.us-west'] == 'service-endpoint'
        
        # Check stats
        stats = compiler.get_performance_stats()
        assert stats['pattern_cache_size'] > 0
    
    def test_caching_performance(self):
        """Test caching improves performance"""
        compiler = YAMLConfigCompiler()
        compiler.set_regions(['region1', 'region2', 'region3'])
        compiler.compiler.set_pattern_rules({
            'service.*': {'data_source': 'regions'}
        })
        
        service_map = {'service.*': 'endpoint'}
        
        # First compilation - should populate cache
        result1 = compiler.compile_service_map(service_map)
        cache_size_after_first = len(compiler.compiler._pattern_cache._cache)
        
        # Second compilation - should use cache
        result2 = compiler.compile_service_map(service_map)
        cache_size_after_second = len(compiler.compiler._pattern_cache._cache)
        
        assert result1 == result2
        assert cache_size_after_first == cache_size_after_second  # No new cache entries
    
    def test_complex_pattern_expansion(self):
        """Test complex pattern expansion scenarios"""
        compiler = YAMLConfigCompiler()
        compiler.set_regions(['us', 'eu'])
        compiler.compiler.set_data_sources({
            **compiler.compiler.data_sources,
            'services': ['api', 'web'],
            'environments': ['prod', 'staging']
        })
        
        compiler.compiler.set_pattern_rules({
            'region.*': {'data_source': 'regions'},
            'service.*': {'data_source': 'services'},
            'env.*': {'data_source': 'environments'}
        })
        
        service_map = {
            'region.*': 'regional-config',
            'service.*': 'service-config',
            'env.*': 'environment-config'
        }
        
        result = compiler.compile_service_map(service_map)
        
        # Check all expansions occurred
        component_mapping = result['component_mapping']
        
        # Region expansions
        assert 'region.us' in component_mapping
        assert 'region.eu' in component_mapping
        
        # Service expansions
        assert 'service.api' in component_mapping
        assert 'service.web' in component_mapping
        
        # Environment expansions
        assert 'env.prod' in component_mapping
        assert 'env.staging' in component_mapping