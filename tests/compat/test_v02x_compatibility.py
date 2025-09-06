"""
Backward compatibility tests for StrataRegula v0.2.x API.

These tests ensure that code written for v0.2.x continues to work
with appropriate deprecation warnings in v0.3.0+.
"""

import warnings

import pytest

from strataregula.kernel import Kernel

# Test both old and new imports
from strataregula.legacy import (
    DEPRECATION_VERSION,
    LEGACY_API_VERSION,
    REMOVAL_VERSION,
    ConfigLoader,
    Engine,
    TemplateEngine,
    cli_run,
    compile_config,
    load_yaml,
)


class TestEngineCompatibility:
    """Test v0.2.x Engine API compatibility."""

    def test_engine_creation_shows_deprecation_warning(self):
        """Engine creation should emit DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Engine(config_path="test.yaml")

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "Engine class is deprecated" in str(w[0].message)
            assert "v0.3.0" in str(w[0].message)
            assert "v1.0.0" in str(w[0].message)

    def test_engine_with_template_dir_warns(self):
        """Template dir parameter should warn as deprecated."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Engine(template_dir="/templates")

            # Should have two warnings: Engine deprecation + template_dir
            assert len(w) >= 2
            assert any(
                "template_dir parameter is deprecated" in str(warning.message)
                for warning in w
            )

    def test_engine_compile_works_with_warning(self, tmp_path):
        """Engine.compile() should work but warn."""
        # Create test config
        config_file = tmp_path / "test.yaml"
        config_file.write_text("""
        version: "1.0"
        services:
          - name: test
            port: 8080
        """)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            engine = Engine(config_path=str(config_file))
            result = engine.compile()

            # Should get deprecation warnings
            assert any(
                issubclass(warning.category, DeprecationWarning) for warning in w
            )
            # But should still work
            assert isinstance(result, dict)

    def test_engine_expand_pattern_deprecated(self):
        """Engine.expand_pattern() should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            engine = Engine()
            result = engine.expand_pattern("test-{1..3}")

            assert any(
                "expand_pattern is deprecated" in str(warning.message) for warning in w
            )
            assert isinstance(result, list)

    def test_engine_validate_deprecated(self):
        """Engine.validate() should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            engine = Engine()
            result = engine.validate()

            assert any(
                "validate is deprecated" in str(warning.message) for warning in w
            )
            assert isinstance(result, bool)

    def test_engine_service_time_deprecated(self):
        """Engine.service_time() should warn about deprecation."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            engine = Engine()
            result = engine.service_time("edge.tokyo.gateway:0")

            assert any(
                "service_time() is deprecated" in str(warning.message) for warning in w
            )
            assert isinstance(result, float)

    def test_engine_get_metrics_deprecated(self):
        """Engine.get_metrics() should return v0.2.x format with warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            engine = Engine()
            metrics = engine.get_metrics()

            assert any(
                "get_metrics is deprecated" in str(warning.message) for warning in w
            )

            # Check v0.2.x metric format
            assert "compile_count" in metrics
            assert "cache_hits" in metrics
            assert "cache_misses" in metrics
            assert "total_time" in metrics
            assert "memory_usage" in metrics


class TestConfigLoaderCompatibility:
    """Test v0.2.x ConfigLoader API compatibility."""

    def test_config_loader_deprecated(self):
        """ConfigLoader should warn on creation."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ConfigLoader(search_paths=["/configs"])

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "ConfigLoader is deprecated" in str(w[0].message)

    def test_config_loader_load_deprecated(self, tmp_path):
        """ConfigLoader.load() should work with warning."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loader = ConfigLoader()
            result = loader.load(str(config_file))

            assert any("load is deprecated" in str(warning.message) for warning in w)
            assert result == {"key": "value"}

    def test_config_loader_merge_deprecated(self):
        """ConfigLoader.merge() should work with warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loader = ConfigLoader()
            result = loader.merge({"a": 1}, {"b": 2})

            assert any("merge is deprecated" in str(warning.message) for warning in w)
            assert result == {"a": 1, "b": 2}


class TestTemplateEngineCompatibility:
    """Test v0.2.x TemplateEngine API compatibility."""

    def test_template_engine_deprecated(self):
        """TemplateEngine should warn on creation."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            TemplateEngine(template_dir="/templates")

            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "TemplateEngine is deprecated" in str(w[0].message)

    def test_template_render_deprecated(self):
        """TemplateEngine.render() should work with warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            engine = TemplateEngine()
            result = engine.render("test.j2", {"var": "value"})

            assert any("render is deprecated" in str(warning.message) for warning in w)
            assert isinstance(result, str)


class TestLegacyFunctions:
    """Test standalone legacy function compatibility."""

    def test_cli_run_deprecated(self):
        """cli_run() should warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Don't actually run CLI, just check warning
            try:
                cli_run(["--help"])
            except SystemExit:
                pass  # CLI may exit, that's ok

            assert any("cli_run is deprecated" in str(warning.message) for warning in w)

    def test_compile_config_deprecated(self, tmp_path):
        """compile_config() should work with warning."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("""
        version: "1.0"
        data: test
        """)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = compile_config(str(config_file))

            assert any(
                "compile_config is deprecated" in str(warning.message) for warning in w
            )
            assert isinstance(result, dict)

    def test_load_yaml_deprecated(self, tmp_path):
        """load_yaml() should work with warning."""
        yaml_file = tmp_path / "data.yaml"
        yaml_file.write_text("test: data")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = load_yaml(str(yaml_file))

            assert any(
                "load_yaml is deprecated" in str(warning.message) for warning in w
            )
            assert result == {"test": "data"}


class TestMigrationPath:
    """Test that migration from v0.2.x to v0.3.0 is smooth."""

    def test_old_code_pattern_still_works(self, tmp_path):
        """Common v0.2.x code pattern should still work."""
        # Simulate typical v0.2.x usage
        config_file = tmp_path / "app.yaml"
        config_file.write_text("""
        app:
          name: legacy-app
          version: "1.0"
        """)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Old pattern
            engine = Engine(config_path=str(config_file))
            result = engine.compile()
            valid = engine.validate()
            metrics = engine.get_metrics()

            # Should work but with warnings
            assert isinstance(result, dict)
            assert isinstance(valid, bool)
            assert isinstance(metrics, dict)

            # Should have multiple deprecation warnings
            deprecation_warnings = [
                w for w in w if issubclass(w.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) > 0

    def test_new_api_does_not_warn(self, tmp_path):
        """New v0.3.0 API should not produce deprecation warnings."""
        config_file = tmp_path / "app.yaml"
        config_file.write_text("""
        app:
          name: modern-app
          version: "1.0"
        """)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # New pattern - should have NO deprecation warnings
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            kernel = Kernel()
            compiled = kernel.precompile(config_data)

            # Check no deprecation warnings from new API
            deprecation_warnings = [
                w for w in w if issubclass(w.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0

    def test_version_constants_available(self):
        """Version constants should be available for version checking."""
        assert LEGACY_API_VERSION == "0.2.x"
        assert DEPRECATION_VERSION == "0.3.0"
        assert REMOVAL_VERSION == "1.0.0"


class TestDeprecationMessages:
    """Test that deprecation messages are helpful."""

    def test_deprecation_suggests_alternative(self):
        """Deprecation warnings should suggest alternatives."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            engine = Engine()
            engine.compile()

            compile_warnings = [
                w for w in w if "compile is deprecated" in str(w.message)
            ]
            assert len(compile_warnings) > 0
            assert "Use Kernel.compile() instead" in str(compile_warnings[0].message)

    def test_deprecation_includes_removal_version(self):
        """Deprecation warnings should mention removal version."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Engine()

            assert any(
                "will be removed in v1.0.0" in str(warning.message) for warning in w
            )


@pytest.mark.parametrize("legacy_class", [Engine, ConfigLoader, TemplateEngine])
def test_all_legacy_classes_warn(legacy_class):
    """All legacy classes should produce deprecation warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        legacy_class()

        assert len(w) >= 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
