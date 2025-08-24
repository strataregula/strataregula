"""
Copy Engine - Core orchestration for Transfer/Copy operations

Provides Plan/Apply pattern for safe, auditable copying operations.
"""

from typing import Any, Dict, List, Optional, Iterator, Protocol
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import logging
from datetime import datetime

from .rules import RuleSet, CopyRule
from .deep_copy import DeepCopyVisitor, CopyMode
from .transforms import TransformRegistry
from .diff import CopyDiff


@dataclass
class CopyItem:
    """Individual item to be copied"""
    obj: Any
    meta: Dict[str, Any]  # path, kind, labels
    rule: CopyRule
    mode: CopyMode
    ops: List[Dict[str, Any]]


@dataclass
class CopyStats:
    """Statistics for copy operation"""
    items_planned: int = 0
    items_processed: int = 0
    items_success: int = 0
    items_failed: int = 0
    bytes_processed: int = 0
    transforms_applied: int = 0
    conflicts_detected: int = 0


@dataclass
class CopyPlan:
    """Execution plan for copy operation"""
    items: List[CopyItem]
    stats: CopyStats
    provenance: Dict[str, Any]
    estimated_memory: int = 0
    estimated_time_ms: int = 0


class CopyEngine:
    """
    Main Copy Engine - orchestrates planning and execution
    
    Workflow:
    1. plan() - Analyze input, match rules, generate execution plan
    2. apply() - Execute plan with hooks, transforms, and monitoring
    3. Optional: diff() - Generate change report
    """
    
    def __init__(
        self,
        ruleset: RuleSet,
        hooks = None,  # HookManager
        di = None,     # Container  
        deep_copy: Optional[DeepCopyVisitor] = None,
        transforms: Optional[TransformRegistry] = None
    ):
        self.ruleset = ruleset
        self.hooks = hooks
        self.di = di
        self.deep_copy = deep_copy or DeepCopyVisitor()
        self.transforms = transforms or TransformRegistry()
        self.logger = logging.getLogger(__name__)

    def plan(self, src_data: Any, context: Optional[Dict[str, Any]] = None) -> CopyPlan:
        """
        Create execution plan by analyzing data and matching rules
        
        Args:
            src_data: Source data to copy
            context: Additional context (source path, metadata)
            
        Returns:
            CopyPlan with items, stats, provenance
        """
        context = context or {}
        items = []
        stats = CopyStats()
        
        # Extract objects based on structure (JSON/YAML/etc)
        objects = self._extract_objects(src_data, context)
        stats.items_planned = len(objects)
        
        for obj_info in objects:
            # Match rules against object metadata
            matched_rule = self.ruleset.match(obj_info['meta'])
            if matched_rule:
                item = CopyItem(
                    obj=obj_info['obj'],
                    meta=obj_info['meta'],
                    rule=matched_rule,
                    mode=matched_rule.mode,
                    ops=matched_rule.ops
                )
                items.append(item)
        
        # Generate provenance info
        provenance = self._generate_provenance(src_data, context)
        
        # Estimate resource usage
        estimated_memory = self._estimate_memory(items)
        estimated_time = self._estimate_time(items)
        
        plan = CopyPlan(
            items=items,
            stats=stats,
            provenance=provenance,
            estimated_memory=estimated_memory,
            estimated_time_ms=estimated_time
        )
        
        if self.hooks:
            self.hooks.emit("copy:plan", {"plan": plan})
            
        return plan

    def apply(
        self, 
        plan: CopyPlan, 
        out_stream = None,
        provenance: bool = False,
        diff_out = None
    ) -> Dict[str, Any]:
        """
        Execute copy plan with hooks and monitoring
        
        Args:
            plan: Execution plan from plan()
            out_stream: Output stream for results
            provenance: Include provenance information
            diff_out: Optional diff output stream
            
        Returns:
            Execution result with stats, errors
        """
        if self.hooks:
            self.hooks.emit("copy:start", {"plan": plan})
            
        results = []
        errors = []
        diffs = []
        
        try:
            for item in plan.items:
                try:
                    if self.hooks:
                        self.hooks.emit("copy:before_object", {"meta": item.meta})
                    
                    # Perform deep copy based on mode
                    copied_obj = self.deep_copy.copy(item.obj, mode=item.mode)
                    
                    # Apply transforms
                    transformed_obj = self._apply_ops(copied_obj, item.ops, item.meta)
                    
                    # Track changes for diff
                    if diff_out:
                        diff = CopyDiff.create(item.obj, transformed_obj, item.meta)
                        diffs.append(diff)
                    
                    results.append({
                        "obj": transformed_obj,
                        "meta": item.meta,
                        "provenance": item.rule.name if provenance else None
                    })
                    
                    plan.stats.items_success += 1
                    
                    if self.hooks:
                        self.hooks.emit("copy:after_object", {
                            "meta": item.meta, 
                            "obj": transformed_obj
                        })
                        
                except Exception as e:
                    error = {
                        "item_meta": item.meta,
                        "error": str(e),
                        "rule": item.rule.name
                    }
                    errors.append(error)
                    plan.stats.items_failed += 1
                    
                    if self.hooks:
                        self.hooks.emit("copy:error", error)
                
                plan.stats.items_processed += 1
            
            # Output results
            if out_stream:
                for result in results:
                    out_stream.write(result)
            
            # Output diff if requested
            if diff_out and diffs:
                diff_summary = CopyDiff.summarize(diffs)
                diff_out.write(diff_summary)
            
            if self.hooks:
                self.hooks.emit("copy:commit", {"results": results})
                
        finally:
            if self.hooks:
                self.hooks.emit("copy:finish", {
                    "stats": plan.stats,
                    "errors": errors
                })
        
        return {
            "results": results,
            "stats": plan.stats,
            "errors": errors,
            "provenance": plan.provenance if provenance else None
        }

    def _extract_objects(self, data: Any, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual objects from input data"""
        objects = []
        
        # TODO: Implement object extraction based on data type
        # For now, assume flat object structure
        if isinstance(data, dict):
            objects.append({
                "obj": data,
                "meta": {
                    "path": "$",
                    "kind": context.get("kind", "object"),
                    "labels": context.get("labels", [])
                }
            })
        elif isinstance(data, list):
            for i, item in enumerate(data):
                objects.append({
                    "obj": item,
                    "meta": {
                        "path": f"$[{i}]",
                        "kind": context.get("kind", "object"),
                        "labels": context.get("labels", [])
                    }
                })
        
        return objects

    def _apply_ops(self, obj: Any, ops: List[Dict[str, Any]], meta: Dict[str, Any]) -> Any:
        """Apply transformation operations to object"""
        result = obj
        
        for op in ops:
            if self.hooks:
                self.hooks.emit("copy:on_transform", {
                    "op": op,
                    "meta": meta,
                    "before": result
                })
            
            result = self.transforms.apply(result, op, meta)
        
        return result

    def _generate_provenance(self, src_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate provenance information"""
        data_hash = hashlib.sha256(
            json.dumps(src_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source_hash": data_hash,
            "engine_version": "0.1.0",
            "ruleset_version": getattr(self.ruleset, 'version', 'unknown'),
            "context": context
        }

    def _estimate_memory(self, items: List[CopyItem]) -> int:
        """Estimate memory usage for execution"""
        # Simple heuristic: assume deep copy doubles memory
        total_size = 0
        for item in items:
            if item.mode == CopyMode.DEEP:
                total_size += len(json.dumps(item.obj)) * 2
            else:
                total_size += len(json.dumps(item.obj))
        return total_size

    def _estimate_time(self, items: List[CopyItem]) -> int:
        """Estimate execution time in milliseconds"""
        # Simple heuristic: 1ms per transform + 0.1ms per object
        total_time = len(items) * 0.1
        for item in items:
            total_time += len(item.ops) * 1
        return int(total_time * 1000)