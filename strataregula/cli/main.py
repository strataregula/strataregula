"""
Main CLI entry point for strataregula.
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .compile_command import compile_cmd

console = Console()


@click.group()
@click.version_option(version="0.1.1", prog_name="strataregula")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress output')
@click.pass_context
def cli(ctx, verbose, quiet):
    """Strataregula - YAML Configuration Pattern Compiler with PiPE Command Chaining.
    
    A powerful tool for processing YAML configurations through command chains,
    supporting STDIN input, hooks, and plugin-based transformations.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    
    if verbose:
        console.print("[bold blue]Verbose mode enabled[/bold blue]")
    
    if not quiet:
        console.print(Panel(
            Text("Strataregula", style="bold blue"),
            subtitle="YAML Configuration Pattern Compiler",
            border_style="blue"
        ))


# @cli.command()
# @click.argument('input_file', required=False)
# @click.option('--stdin', '-i', is_flag=True, help='Read from STDIN')
# @click.option('--format', '-f', default='auto', 
#               type=click.Choice(['yaml', 'yml', 'json', 'text', 'auto']),
#               help='Input format (auto-detect if not specified)')
# @click.option('--output', '-o', help='Output file (default: STDOUT)')
# @click.option('--output-format', '-of', default='yaml',
#               type=click.Choice(['yaml', 'yml', 'json', 'text']),
#               help='Output format')
# @click.option('--pipeline', '-p', help='Pipeline configuration file')
# @click.option('--command', '-c', multiple=True, help='Command to execute')
# @click.pass_context
# def process(ctx, input_file, stdin, format, output, output_format, pipeline, command):
#     """Process input data through commands or pipeline."""
#     # Temporarily disabled - requires missing commands module
#     pass


# @cli.command()
# @click.argument('name')
# @click.option('--description', '-d', help='Pipeline description')
# @click.option('--input-format', '-if', default='auto',
#               type=click.Choice(['yaml', 'yml', 'json', 'text', 'auto']),
#               help='Input format')
# @click.option('--output-format', '-of', default='yaml',
#               type=click.Choice(['yaml', 'yml', 'json', 'text']),
#               help='Output format')
# @click.option('--command', '-c', multiple=True, help='Command to add')
# @click.option('--save', '-s', help='Save pipeline to file')
# @click.pass_context
# def create(ctx, name, description, input_format, output_format, command, save):
#     """Create a new pipeline."""
#     # Temporarily disabled - requires missing commands module
#     pass


# @cli.command()
# @click.option('--category', '-c', help='Filter by category')
# @click.option('--search', '-s', help='Search commands')
# @click.pass_context
# def list(ctx, category, search):
#     """List available commands and pipelines."""
#     # Temporarily disabled - requires missing commands module
#     pass


# @cli.command()
# @click.argument('pipeline_name')
# @click.argument('input_file', required=False)
# @click.option('--stdin', '-i', is_flag=True, help='Read from STDIN')
# @click.option('--output', '-o', help='Output file')
# @click.pass_context
# def run(ctx, pipeline_name, input_file, stdin, output):
#     """Run a saved pipeline."""
#     # Temporarily disabled - requires missing commands module
#     pass


@cli.command()
def examples():
    """Show usage examples."""
    examples_text = """
[bold]Basic Usage:[/bold]

[blue]Process YAML file:[/blue]
  strataregula process config.yaml

[blue]Process from STDIN:[/blue]
  cat config.yaml | strataregula process --stdin

[blue]Apply commands:[/blue]
  strataregula process config.yaml -c "filter:condition='item.active'" -c "transform:expression='data.items'"

[blue]Create pipeline:[/blue]
  strataregula create my-pipeline -d "Process user configs" -c "filter:condition='user.enabled'" -s pipeline.yaml

[blue]Run pipeline:[/blue]
  strataregula run my-pipeline config.yaml

[bold]Advanced Usage:[/bold]

[blue]Chain multiple commands:[/blue]
  strataregula process input.yaml \\
    -c "filter:condition='item.type == \"user\"'" \\
    -c "transform:expression='[u for u in data if u.get(\"active\")]'" \\
    -c "echo"

[blue]Use with other tools:[/blue]
  cat data.yaml | strataregula process --stdin | jq '.items[] | select(.active)'
    """
    
    console.print(Panel(examples_text, title="Usage Examples", border_style="blue"))


# Add compile command to CLI
cli.add_command(compile_cmd, name='compile')


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        console.print_exception()
        sys.exit(1)


if __name__ == '__main__':
    main()
