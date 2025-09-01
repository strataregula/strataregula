"""
InternPass: Config Value Interning and Deduplication

Implements hash-consing for configuration structures to reduce memory usage
through structural sharing of equivalent values.
"""

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

# Import the existing config interning functionality
try:
    from scripts.config_interning import Stats, intern_tree
except ImportError:
    # Fallback to relative import if scripts module not available
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
    from config_interning import Stats, intern_tree


@dataclass
class InternPass:
    """
    Compile pass that applies value interning to reduce memory usage.

    Uses hash-consing to ensure that equivalent values share the same
    memory reference, while maintaining immutability guarantees.
    """

    qfloat: Optional[float] = None
    collect_stats: bool = False

    def __post_init__(self) -> None:
        """Initialize statistics collection if requested."""
        self._stats = Stats() if self.collect_stats else None

    def run(self, model: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Apply interning to the entire configuration model.

        Args:
            model: Raw configuration data

        Returns:
            Interned configuration with structural sharing
        """
        print(f"🔍 InternPass.run() called with model size: {len(str(model))}")
        
        if self._stats:
            self._stats.__init__()  # Reset stats for this run
            print("📊 Stats collection enabled and reset")

        # Apply interning with optional float quantization
        print("🔄 Calling intern_tree...")
        interned = intern_tree(model, qfloat=self.qfloat, stats=self._stats)
        print(f"✅ intern_tree completed, result size: {len(str(interned))}")

        # Log stats if collection is enabled
        if self._stats and self.collect_stats:
            self._log_stats()

        return interned

    def _log_stats(self) -> None:
        """Log interning statistics to stderr."""
        if not self._stats:
            return

        hits = self._stats.hits
        misses = self._stats.misses
        total = hits + misses
        hit_rate = (hits / max(1, total)) * 100.0

        print(
            f"[intern] nodes={self._stats.nodes} unique={self._stats.unique} "
            f"hits={hits} misses={misses} hit_rate={hit_rate:.1f}%",
            file=sys.stderr,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get current interning statistics."""
        if not self._stats:
            return {}

        hits = self._stats.hits
        misses = self._stats.misses
        total = hits + misses
        hit_rate = (hits / max(1, total)) * 100.0

        return {
            "nodes_processed": self._stats.nodes,
            "unique_values": self._stats.unique,
            "cache_hits": hits,
            "cache_misses": misses,
            "hit_rate": hit_rate,
        }
