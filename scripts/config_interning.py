#!/usr/bin/env python3
"""
Config Interning v2: freeze + hash-consing + weak pool + optional float quantization.

Usage (CLI):
  python -m scripts.config_interning --input configs/routes.yaml --stats
  python -m scripts.config_interning --input configs/routes.yaml --qfloat 1e-9 --out .cache/routes.interned.yaml

Library:
  from scripts.config_interning import intern, intern_tree
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import sys
import sys as pysys
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any

try:
    import yaml  # pyyaml
except Exception:
    yaml = None

# ---------- intern pool ----------
# Note: WeakValueDictionary doesn't support MappingProxyType, using regular dict
_pool: dict[str, Any] = {}


class Stats:
    __slots__ = ("hits", "misses", "nodes", "unique")

    def __init__(self) -> None:
        self.nodes = 0
        self.hits = 0
        self.misses = 0
        self.unique = 0


def _qf(x: float, q: float | None) -> float:
    if q is None:
        return x
    if x == 0.0:
        return 0.0
    return round(x / q) * q


def _freeze(x: Any, qfloat: float | None, stats: Stats | None) -> Any:
    # normalize primitives
    if isinstance(x, str):
        # intern small/duplicate strings
        return pysys.intern(x)
    if isinstance(x, bool) or x is None:
        return x
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        if not math.isfinite(x):
            return x
        return _qf(x, qfloat)

    # recursively freeze containers
    if isinstance(x, Mapping):
        # sort keys for stability
        items = tuple(
            (pysys.intern(str(k)), _freeze(v, qfloat, stats))
            for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))
        )
        if stats:
            stats.nodes += 1  # count dict nodes
        return ("__dict__", items)
    if isinstance(x, Sequence) and not isinstance(x, bytes | bytearray):
        items = tuple(_freeze(v, qfloat, stats) for v in x)
        if stats:
            stats.nodes += 1  # count list nodes
        return ("__list__", items)
    if isinstance(x, set):
        items = tuple(sorted((_freeze(v, qfloat, stats) for v in x), key=repr))
        if stats:
            stats.nodes += 1  # count set nodes
        return ("__set__", items)
    return x  # others


def _key(frozen: Any) -> str:
    s = json.dumps(
        frozen, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str
    )
    return hashlib.blake2b(s.encode("utf-8"), digest_size=16).hexdigest()


def intern(
    value: Any, *, qfloat: float | None = None, stats: Stats | None = None
) -> Any:
    """Return a canonical, immutable, shared instance for semantically equal values."""
    if stats:
        stats.nodes += 1
    frozen = _freeze(value, qfloat, stats)
    k = _key(frozen)
    obj = _pool.get(k)
    if obj is not None:
        if stats:
            stats.hits += 1
        return obj

    # materialize immutable view
    if isinstance(frozen, tuple) and frozen and frozen[0] == "__dict__":
        # items: tuple[(k, v)]
        materialized = MappingProxyType(dict(frozen[1]))  # read-only dict view
    elif isinstance(frozen, tuple) and frozen and frozen[0] == "__list__":
        materialized = frozen[1]  # tuple
    elif isinstance(frozen, tuple) and frozen and frozen[0] == "__set__":
        materialized = frozenset(frozen[1])
    else:
        materialized = frozen

    _pool[k] = materialized
    if stats:
        stats.misses += 1
        stats.unique += 1
    return materialized


def intern_tree(
    obj: Any, *, qfloat: float | None = None, stats: Stats | None = None
) -> Any:
    """Intern recursively: walk the tree and replace subtrees with pooled immutable instances."""
    # NOTE: intern() already freezes recursively; this function is an alias for clarity
    return intern(obj, qfloat=qfloat, stats=stats)


def thaw(obj: Any) -> Any:
    """Convert immutable interned structures back to mutable for serialization."""
    if isinstance(obj, MappingProxyType):
        return {k: thaw(v) for k, v in obj.items()}
    elif isinstance(obj, tuple) and len(obj) == 2 and obj[0] == "__dict__":
        # This is an interned dict: ("__dict__", ((k, v), ...))
        return {k: thaw(v) for k, v in obj[1]}
    elif isinstance(obj, tuple) and len(obj) == 2 and obj[0] == "__list__":
        # This is an interned list: ("__list__", (v1, v2, ...))
        return [thaw(v) for v in obj[1]]
    elif isinstance(obj, tuple) and len(obj) == 2 and obj[0] == "__set__":
        # This is an interned set: ("__set__", (v1, v2, ...))
        return {thaw(v) for v in obj[1]}
    elif isinstance(obj, tuple) and not isinstance(obj, str):
        # Regular tuple
        return [thaw(v) for v in obj]
    elif isinstance(obj, frozenset):
        return {thaw(v) for v in obj}
    else:
        return obj


# ---------- CLI ----------
def _load(path: str) -> Any:
    with open(path, "rb") as f:
        data = f.read()
    # auto-detect yaml/json by extension
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        if yaml is None:
            raise RuntimeError("pyyaml not installed. pip install pyyaml")
        return yaml.safe_load(io.BytesIO(data))
    return json.loads(data.decode("utf-8"))


def _dump(data: Any, path: str | None) -> None:
    if path is None:
        # write JSON to stdout
        sys.stdout.write(
            json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n"
        )
    else:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".yaml", ".yml") and yaml is not None:
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=True, allow_unicode=True)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", required=True, help="Input YAML/JSON")
    ap.add_argument(
        "--out", "-o", help="Output path (.yaml/.json); omit to print JSON to stdout"
    )
    ap.add_argument(
        "--qfloat",
        type=float,
        default=None,
        help="Optional float quantization (e.g., 1e-9)",
    )
    ap.add_argument(
        "--stats", action="store_true", help="Print interning stats to stderr"
    )
    args = ap.parse_args(argv)

    raw = _load(args.input)
    st = Stats()
    out = intern_tree(raw, qfloat=args.qfloat, stats=st)

    _dump(out, args.out)

    if args.stats:
        hits = st.hits
        uniq = st.unique
        nodes = st.nodes
        misses = st.misses
        rate = (hits / max(1, hits + misses)) * 100.0
        print(
            f"[intern-stats] nodes={nodes} unique={uniq} hits={hits} misses={misses} hit_rate={rate:.2f}%",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
