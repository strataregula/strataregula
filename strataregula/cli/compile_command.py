"""
CLI Command for Configuration Compilation

Provides the 'sr compile' command that replaces config_compiler.py
with enhanced features and backward compatibility.
"""

import click
import sys
from pathlib import Path
from typing import Optional
import logging

from ..core.config_compiler import ConfigCompiler, CompilationConfig
from ..core.pattern_expander import EnhancedPatternExpander, ExpansionRule

logger = logging.getLogger(__name__)


@click.command()
@click.option('--traffic', 
              type=click.Path(exists=True, path_type=Path),
              required=True,
              help='Traffic/service configuration file (YAML or JSON)')
@click.option('--prefectures', 
              type=click.Path(exists=True, path_type=Path),
              help='Prefecture/region configuration file (YAML or JSON)')
@click.option('--out', '--output',
              type=click.Path(path_type=Path),
              help='Output file path (default: stdout)')
@click.option('--format', 'output_format',
              type=click.Choice(['python', 'json', 'yaml']),
              default='python',
              help='Output format (default: python)')
@click.option('--template',
              type=click.Path(exists=True, path_type=Path),
              help='Custom template file for output generation')
@click.option('--chunk-size',
              type=int,
              default=1024,
              help='Chunk size for memory-efficient processing (default: 1024)')
@click.option('--max-memory',
              type=int,
              default=200,
              help='Maximum memory usage in MB (default: 200)')
@click.option('--no-metadata',
              is_flag=True,
              help='Exclude metadata from output')
@click.option('--no-provenance',
              is_flag=True,
              help='Exclude provenance tracking from output')
@click.option('--no-optimize',
              is_flag=True,
              help='Disable lookup optimizations')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Verbose output')
@click.option('--plan',
              is_flag=True,
              help='Show compilation plan without executing')
@click.option('--stats',
              is_flag=True,
              help='Show detailed compilation statistics')
@click.option('--validate-only',
              is_flag=True,
              help='Validate input files without compilation')
def compile_cmd(traffic: Path,
                prefectures: Optional[Path],
                out: Optional[Path],
                output_format: str,
                template: Optional[Path],
                chunk_size: int,
                max_memory: int,
                no_metadata: bool,
                no_provenance: bool,
                no_optimize: bool,
                verbose: bool,
                plan: bool,
                stats: bool,
                validate_only: bool):
    """
    Compile configuration patterns into optimized static mappings.
    
    This command replaces config_compiler.py with enhanced features:
    - Regional/prefecture hierarchy support
    - Memory-efficient processing for large files
    - Multiple output formats (Python, JSON, YAML)
    - Provenance tracking and fingerprinting
    - Runtime optimization for O(1) lookups
    
    Examples:
    
        # Basic compilation (config_compiler.py replacement)
        sr compile --traffic configs/traffic.yaml --prefectures configs/prefectures.yaml --out compiled_config.py
        
        # Compile large configuration with memory limit
        sr compile --traffic large_config.json --max-memory 100 --chunk-size 512 --out optimized.py
        
        # Generate JSON output with statistics
        sr compile --traffic traffic.yaml --format json --stats --out config.json
        
        # Preview compilation plan
        sr compile --traffic traffic.yaml --plan
        
        # Validate configuration files only
        sr compile --traffic traffic.yaml --prefectures prefectures.yaml --validate-only
    """
    
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Create compilation config
        config = CompilationConfig(
            output_format=output_format,
            template_path=template,
            include_metadata=not no_metadata,
            include_provenance=not no_provenance,
            optimize_lookups=not no_optimize,
            chunk_size=chunk_size,
            max_memory_mb=max_memory
        )
        
        # Validation mode
        if validate_only:
            return _validate_files(traffic, prefectures)
        
        # Plan mode
        if plan:
            return _show_compilation_plan(traffic, prefectures, config)
        
        # Create compiler
        compiler = ConfigCompiler(config)
        
        # Set up progress callback for large files
        def progress_callback(current: int, total: int):
            if verbose:
                percentage = (current / total) * 100 if total > 0 else 0
                click.echo(f"Processing: {current}/{total} chunks ({percentage:.1f}%)", err=True)
        
        # Compile configuration
        click.echo("Starting compilation...", err=True)
        
        if _is_large_file(traffic):
            # Use streaming compilation for large files
            if not out:
                click.echo("Error: Output file required for large file compilation", err=True)
                sys.exit(1)
            
            compiler.compile_large_config(traffic, out, progress_callback if verbose else None)
            compiled_content = ""  # Already written to file
            
        else:
            # Standard compilation
            compiled_content = compiler.compile_traffic_config(traffic, prefectures, out)
        
        # Output results
        if not out and compiled_content:
            click.echo(compiled_content)
        elif out:
            click.echo(f"Compilation successful. Output written to: {out}", err=True)
        
        # Show statistics if requested
        if stats:
            _show_compilation_stats(compiler)
        
        click.echo("Compilation completed successfully.", err=True)
        
    except Exception as e:
        click.echo(f"Compilation failed: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _validate_files(traffic_file: Path, prefectures_file: Optional[Path]) -> None:
    """Validate input configuration files."""
    click.echo("Validating configuration files...", err=True)
    
    errors = []
    
    # Validate traffic file
    try:
        compiler = ConfigCompiler()
        traffic_data = compiler._load_file(traffic_file)
        if not traffic_data:
            errors.append(f"Traffic file is empty or invalid: {traffic_file}")
        else:
            patterns = compiler._extract_service_patterns(traffic_data)
            if not patterns:
                errors.append(f"No service patterns found in traffic file: {traffic_file}")
            else:
                click.echo(f"✓ Traffic file valid: {len(patterns)} patterns found", err=True)
        
    except Exception as e:
        errors.append(f"Invalid traffic file {traffic_file}: {e}")
    
    # Validate prefectures file if provided
    if prefectures_file:
        try:
            compiler = ConfigCompiler()
            pref_data = compiler._load_file(prefectures_file)
            if not pref_data:
                errors.append(f"Prefectures file is empty or invalid: {prefectures_file}")
            else:
                click.echo(f"✓ Prefectures file valid", err=True)
                
                # Check for expected structure
                if 'prefectures' in pref_data:
                    pref_count = len(pref_data['prefectures'])
                    click.echo(f"  - {pref_count} prefectures configured", err=True)
                
                if 'regions' in pref_data:
                    region_count = len(pref_data['regions'])
                    click.echo(f"  - {region_count} regions configured", err=True)
        
        except Exception as e:
            errors.append(f"Invalid prefectures file {prefectures_file}: {e}")
    
    # Report validation results
    if errors:
        click.echo("Validation failed with errors:", err=True)
        for error in errors:
            click.echo(f"  ✗ {error}", err=True)
        sys.exit(1)
    else:
        click.echo("✓ All files validated successfully", err=True)


def _show_compilation_plan(traffic_file: Path, 
                          prefectures_file: Optional[Path], 
                          config: CompilationConfig) -> None:
    """Show compilation plan without executing."""
    click.echo("=== Compilation Plan ===", err=True)
    click.echo(f"Input files:", err=True)
    click.echo(f"  Traffic: {traffic_file}", err=True)
    click.echo(f"  Prefectures: {prefectures_file or 'Not provided'}", err=True)
    click.echo("", err=True)
    
    click.echo(f"Configuration:", err=True)
    click.echo(f"  Output format: {config.output_format}", err=True)
    click.echo(f"  Chunk size: {config.chunk_size}", err=True)
    click.echo(f"  Max memory: {config.max_memory_mb} MB", err=True)
    click.echo(f"  Include metadata: {config.include_metadata}", err=True)
    click.echo(f"  Include provenance: {config.include_provenance}", err=True)
    click.echo(f"  Optimize lookups: {config.optimize_lookups}", err=True)
    click.echo("", err=True)
    
    # Analyze input files
    try:
        compiler = ConfigCompiler(config)
        traffic_data = compiler._load_file(traffic_file)
        patterns = compiler._extract_service_patterns(traffic_data)
        
        click.echo(f"Analysis:", err=True)
        click.echo(f"  Service patterns: {len(patterns)}", err=True)
        
        # Estimate expansion
        expander = EnhancedPatternExpander()
        if prefectures_file:
            pref_data = compiler._load_file(prefectures_file)
            compiler._setup_hierarchy_from_config(pref_data)
            expander = compiler.expander
        
        # Sample expansion to estimate output size
        sample_patterns = dict(list(patterns.items())[:min(10, len(patterns))])
        sample_result = expander.compile_to_static_mapping(sample_patterns)
        
        estimated_direct = len(sample_result['direct_mapping'])
        estimated_component = len(sample_result['component_mapping'])
        expansion_ratio = (estimated_direct + estimated_component) / len(sample_patterns) if sample_patterns else 1
        
        total_estimated = int(len(patterns) * expansion_ratio)
        
        click.echo(f"  Estimated expanded mappings: {total_estimated}", err=True)
        click.echo(f"  Expected direct mappings: {int(total_estimated * 0.3)}", err=True)
        click.echo(f"  Expected component mappings: {int(total_estimated * 0.7)}", err=True)
        click.echo("", err=True)
        
        # Memory estimation
        estimated_memory_mb = (total_estimated * 64) / (1024 * 1024)  # Rough estimate
        use_streaming = estimated_memory_mb > config.max_memory_mb
        
        click.echo(f"Processing strategy:", err=True)
        click.echo(f"  Estimated memory usage: {estimated_memory_mb:.1f} MB", err=True)
        click.echo(f"  Use streaming: {use_streaming}", err=True)
        click.echo(f"  Estimated processing time: {_estimate_processing_time(len(patterns))} seconds", err=True)
        
    except Exception as e:
        click.echo(f"Unable to analyze input files: {e}", err=True)


def _show_compilation_stats(compiler: ConfigCompiler) -> None:
    """Show detailed compilation statistics."""
    click.echo("\n=== Compilation Statistics ===", err=True)
    
    try:
        # Get expansion stats
        expansion_stats = compiler.expander.get_expansion_stats()
        
        click.echo("Pattern Expansion:", err=True)
        click.echo(f"  Rules loaded: {expansion_stats['rules_count']}", err=True)
        click.echo(f"  Cache entries: {expansion_stats['cache_size']}", err=True)
        click.echo(f"  Cache max size: {expansion_stats['cache_max_size']}", err=True)
        
        click.echo("\nHierarchy Information:", err=True)
        hierarchy = expansion_stats['hierarchy_stats']
        for key, value in hierarchy.items():
            click.echo(f"  {key.capitalize()}: {value}", err=True)
        
        click.echo(f"\nData Sources: {', '.join(expansion_stats['data_sources'])}", err=True)
        
    except Exception as e:
        click.echo(f"Unable to gather statistics: {e}", err=True)


def _is_large_file(file_path: Path) -> bool:
    """Check if file is large and needs streaming processing."""
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        return size_mb > 10  # Files larger than 10MB use streaming
    except:
        return False


def _estimate_processing_time(pattern_count: int) -> float:
    """Estimate processing time based on pattern count."""
    # Very rough estimation: 1000 patterns per second base rate
    base_rate = 1000
    return max(1.0, pattern_count / base_rate)


# Add to main CLI
def add_compile_command(cli_group):
    """Add compile command to the main CLI group."""
    cli_group.add_command(compile_cmd, name='compile')