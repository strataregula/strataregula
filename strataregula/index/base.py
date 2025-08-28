from __future__ import annotations
from typing import Protocol, Iterable, List, Dict, Any, Optional, Set
from pathlib import Path

class IndexProvider(Protocol):
    """
    インデックス抽象。
    - 最小要件：`changed_py` と `stats`
    - 追加機能（`search` など）は capabilities で宣言
    """
    name: str
    version: str
    capabilities: Set[str]

    def build(self, entries: Iterable[Path] | None = None) -> None: ...
    def changed_py(
        self,
        base: Optional[str],
        roots: List[str],
        repo_root: Path,
        verbose: bool = False,
    ) -> List[Path]: ...
    def search(self, pattern: str, paths: List[Path]) -> List[str]: ...
    def stats(self) -> Dict[str, Any]: ...
