import warnings
import pytest

try:
    from strataregula import Kernel, CompiledConfig
except Exception as e:
    pytest.skip(f"strataregula import failed: {e}", allow_module_level=True)


def _read_hit_ratio(kernel) -> float:
    """
    kernel.cache_stats() or kernel.get_stats() のどちらにも対応して
    ヒット率を取り出すヘルパ。
    """
    if hasattr(kernel, "cache_stats") and callable(kernel.cache_stats):
        s = kernel.cache_stats()
    elif hasattr(kernel, "get_stats") and callable(kernel.get_stats):
        s = kernel.get_stats()
    else:
        return 0.0
    # 代表的なキー名を順に探す
    for k in ("ratio", "hit_ratio", "hit_rate"):
        if k in s and isinstance(s[k], (int, float)):
            return float(s[k])
    # cache_backend 内の hit_rate にも対応
    cb = s.get("cache_backend", {})
    if isinstance(cb, dict) and "hit_rate" in cb:
        return float(cb["hit_rate"])
    return 0.0


def test_precompile_and_cache_hits_recover():
    """precompile → query(compiled) で十分なヒット率が得られることのスモークテスト。"""
    k = Kernel()

    class BasicView:
        key = "basic_view"
        def materialize(self, model, **params):
            # 同一パラメータなら同一結果（キャッシュされる想定）
            return {"region": params.get("region"), "service": params.get("service")}

    k.register_view(BasicView())
    compiled = k.precompile({"region": "tokyo", "service": "web"})
    assert isinstance(compiled, CompiledConfig)

    # ウォームアップ
    for _ in range(1000):
        k.query("basic_view", {"region": "tokyo", "service": "web"}, compiled)
    # 本計測（同一キーで繰り返し）
    for _ in range(1000):
        k.query("basic_view", {"region": "tokyo", "service": "web"}, compiled)

    ratio = _read_hit_ratio(k)
    assert ratio >= 0.8, f"hit ratio too low: {ratio}"


def test_query_accepts_compiled_and_raw_equivalence():
    """Raw cfg と CompiledConfig の応答が等価であること（API等価性）。"""
    k = Kernel()

    class BasicView:
        key = "basic_view"
        def materialize(self, model, **params):
            return {"region": params.get("region"), "service": params.get("service")}

    k.register_view(BasicView())
    raw_cfg = {"region": "tokyo", "service": "web"}
    compiled = k.precompile(raw_cfg)

    a = k.query("basic_view", {"region": "tokyo", "service": "web"}, compiled)
    b = k.query("basic_view", {"region": "tokyo", "service": "web"}, raw_cfg)
    assert a == b


def test_compile_is_deprecated():
    """compile() は下位互換のため残すが DeprecationWarning を出す想定。"""
    k = Kernel()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        _ = k.compile({"x": 1})
        assert any(issubclass(m.category, DeprecationWarning) for m in w), \
            "DeprecationWarning not raised by Kernel.compile"
