"""
CLI commands for Transfer/Copy subsystem

Provides 'sr transfer' command with plan/apply subcommands.
"""

import json
import yaml
import sys
import logging
from typing import Any, Dict, Optional
from pathlib import Path

from .copy_engine import CopyEngine, CopyPlan
from .rules import RuleSet
from .deep_copy import DeepCopyVisitor  
from .transforms import TransformRegistry
from .diff import CopyDiff

logger = logging.getLogger(__name__)


class TransferCLI:
    """CLI interface for Transfer/Copy operations"""
    
    def __init__(self, hooks=None, di=None):
        self.hooks = hooks
        self.di = di
    
    def plan(
        self,
        source_file: str,
        policy_file: Optional[str] = None,
        select: Optional[str] = None,
        output: Optional[str] = None
    ) -> int:
        """
        Create and display execution plan
        
        Args:
            source_file: Input data file
            policy_file: Copy policy YAML file
            select: JSONPath selector for subset
            output: Output file for plan (JSON)
            
        Returns:
            Exit code
        """
        try:
            # Load source data
            source_data = self._load_data(source_file)
            if select:
                # TODO: Apply JSONPath selector
                pass
            
            # Load policy
            if policy_file:
                ruleset = self._load_policy(policy_file)
            else:
                # Use default empty ruleset
                ruleset = RuleSet([])
            
            # Create engine and generate plan
            engine = CopyEngine(
                ruleset=ruleset,
                hooks=self.hooks,
                di=self.di
            )
            
            plan = engine.plan(source_data, {"source_file": source_file})
            
            # Display plan summary
            self._display_plan(plan)
            
            # Save plan to file if requested
            if output:
                self._save_plan(plan, output)
            
            return 0
            
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            return 1
    
    def apply(
        self,
        source_file: str,
        policy_file: Optional[str] = None,
        output: Optional[str] = None,
        provenance: bool = False,
        diff: Optional[str] = None,
        dry_run: bool = False,
        validate_schema: Optional[str] = None
    ) -> int:
        """
        Execute copy operation
        
        Args:
            source_file: Input data file
            policy_file: Copy policy YAML file  
            output: Output file for results
            provenance: Include provenance information
            diff: Output file for diff report
            dry_run: Show what would be done without executing
            validate_schema: JSON schema file for validation
            
        Returns:
            Exit code
        """
        try:
            # Load source data
            source_data = self._load_data(source_file)
            
            # Load policy  
            if policy_file:
                ruleset = self._load_policy(policy_file)
            else:
                ruleset = RuleSet([])
            
            # Validate input if schema provided
            if validate_schema:
                self._validate_data(source_data, validate_schema)
            
            # Create engine
            engine = CopyEngine(
                ruleset=ruleset,
                hooks=self.hooks,
                di=self.di
            )
            
            # Generate plan
            plan = engine.plan(source_data, {"source_file": source_file})
            
            if dry_run:
                print("DRY RUN - would execute the following plan:")
                self._display_plan(plan)
                return 0
            
            # Execute plan
            out_stream = self._get_output_stream(output)
            diff_stream = self._get_output_stream(diff) if diff else None
            
            try:
                result = engine.apply(
                    plan=plan,
                    out_stream=out_stream,
                    provenance=provenance,
                    diff_out=diff_stream
                )
                
                # Display execution summary
                self._display_result(result)
                
                return 0 if not result["errors"] else 1
                
            finally:
                if out_stream and output:
                    out_stream.close()
                if diff_stream and diff:
                    diff_stream.close()
            
        except Exception as e:
            logger.error(f"Apply operation failed: {e}")
            return 1
    
    def _load_data(self, file_path: str) -> Any:
        """Load data from file (JSON/YAML)"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        content = path.read_text(encoding='utf-8')
        
        try:
            # Try JSON first
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # Try YAML  
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse {file_path} as JSON or YAML: {e}")
    
    def _load_policy(self, file_path: str) -> RuleSet:
        """Load copy policy from YAML file"""
        policy_data = self._load_data(file_path)
        return RuleSet.from_yaml(policy_data)
    
    def _validate_data(self, data: Any, schema_file: str) -> None:
        """Validate data against JSON schema"""
        # TODO: Implement JSON schema validation
        # For now, just a placeholder
        logger.info(f"Validation against {schema_file} - not implemented yet")
    
    def _display_plan(self, plan: CopyPlan) -> None:
        """Display execution plan to console"""
        print(f"\n📋 Transfer Plan Summary")
        print(f"{'=' * 50}")
        print(f"Items to process: {plan.stats.items_planned}")
        print(f"Estimated memory: {plan.estimated_memory:,} bytes")
        print(f"Estimated time: {plan.estimated_time_ms} ms")
        
        if plan.items:
            print(f"\n📝 Planned Operations:")
            for i, item in enumerate(plan.items[:10]):  # Show first 10
                print(f"  {i+1}. {item.meta.get('path', 'unknown')} -> {item.rule.name} ({item.mode.value})")
                if item.ops:
                    for op in item.ops[:3]:  # Show first 3 ops
                        op_name = next(iter(op.keys()))
                        print(f"     • {op_name}")
            
            if len(plan.items) > 10:
                print(f"     ... and {len(plan.items) - 10} more items")
        
        print(f"\n🔍 Provenance:")
        print(f"  Source hash: {plan.provenance.get('source_hash', 'unknown')}")
        print(f"  Timestamp: {plan.provenance.get('timestamp', 'unknown')}")
        print()
    
    def _display_result(self, result: Dict[str, Any]) -> None:
        """Display execution result to console"""
        stats = result["stats"]
        
        print(f"\n✅ Transfer Complete")
        print(f"{'=' * 50}")
        print(f"Items processed: {stats.items_processed}")
        print(f"Successful: {stats.items_success}")
        print(f"Failed: {stats.items_failed}")
        
        if result["errors"]:
            print(f"\n❌ Errors ({len(result['errors'])}):")
            for error in result["errors"][:5]:  # Show first 5 errors
                print(f"  • {error['item_meta'].get('path', 'unknown')}: {error['error']}")
            
            if len(result["errors"]) > 5:
                print(f"  ... and {len(result['errors']) - 5} more errors")
        
        print()
    
    def _save_plan(self, plan: CopyPlan, output_file: str) -> None:
        """Save plan to JSON file"""
        plan_data = {
            "stats": {
                "items_planned": plan.stats.items_planned,
                "estimated_memory": plan.estimated_memory,
                "estimated_time_ms": plan.estimated_time_ms
            },
            "provenance": plan.provenance,
            "items": [
                {
                    "meta": item.meta,
                    "rule": item.rule.name,
                    "mode": item.mode.value,
                    "ops": item.ops
                }
                for item in plan.items
            ]
        }
        
        Path(output_file).write_text(
            json.dumps(plan_data, indent=2),
            encoding='utf-8'
        )
        
        logger.info(f"Plan saved to: {output_file}")
    
    def _get_output_stream(self, output_file: Optional[str]):
        """Get output stream (file or stdout)"""
        if output_file:
            return open(output_file, 'w', encoding='utf-8')
        else:
            return sys.stdout


# Command line interface functions for integration with main CLI

def transfer_plan_command(args):
    """CLI command: sr transfer plan"""
    cli = TransferCLI()
    return cli.plan(
        source_file=args.source,
        policy_file=getattr(args, 'policy', None),
        select=getattr(args, 'select', None),
        output=getattr(args, 'output', None)
    )


def transfer_apply_command(args):
    """CLI command: sr transfer apply"""
    cli = TransferCLI()
    return cli.apply(
        source_file=args.source,
        policy_file=getattr(args, 'policy', None),
        output=getattr(args, 'output', None),
        provenance=getattr(args, 'provenance', False),
        diff=getattr(args, 'diff', None),
        dry_run=getattr(args, 'dry_run', False),
        validate_schema=getattr(args, 'validate', None)
    )


def add_transfer_commands(subparsers):
    """Add transfer commands to CLI parser"""
    # sr transfer
    transfer_parser = subparsers.add_parser(
        'transfer',
        help='Safe object copying and transfer operations'
    )
    transfer_subparsers = transfer_parser.add_subparsers(dest='transfer_command')
    
    # sr transfer plan
    plan_parser = transfer_subparsers.add_parser(
        'plan',
        help='Create and display transfer execution plan'
    )
    plan_parser.add_argument('source', help='Source data file (JSON/YAML)')
    plan_parser.add_argument('--policy', '-p', help='Copy policy file (YAML)')
    plan_parser.add_argument('--select', '-s', help='JSONPath selector')
    plan_parser.add_argument('--output', '-o', help='Save plan to file')
    plan_parser.set_defaults(func=transfer_plan_command)
    
    # sr transfer apply
    apply_parser = transfer_subparsers.add_parser(
        'apply', 
        help='Execute transfer operation'
    )
    apply_parser.add_argument('source', help='Source data file (JSON/YAML)')
    apply_parser.add_argument('--policy', '-p', help='Copy policy file (YAML)')
    apply_parser.add_argument('--output', '-o', help='Output file')
    apply_parser.add_argument('--provenance', action='store_true', help='Include provenance info')
    apply_parser.add_argument('--diff', help='Output diff report to file')
    apply_parser.add_argument('--dry-run', action='store_true', help='Show plan without executing')
    apply_parser.add_argument('--validate', help='JSON schema file for validation')
    apply_parser.set_defaults(func=transfer_apply_command)