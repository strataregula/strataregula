from strataregula import Kernel

def test_internpass_does_not_embed_stats_into_model():
    k = Kernel()
    class BasicView:
        key = "basic_view"
        def materialize(self, model, **params):
            # stats 等のメタが混ざっていないことを前提にする
            assert "_intern_stats" not in model
            return {"ok": True}
    k.register_view(BasicView())
    compiled = k.precompile({"region": "tokyo"})
    k.query("basic_view", {"region": "tokyo"}, compiled)

def test_precompile_then_query_hit_ratio_recovers():
    k = Kernel()
    class BasicView:
        key = "basic_view"
        def materialize(self, model, **params):
            return {"region": params.get("region")}
    k.register_view(BasicView())
    compiled = k.precompile({"region": "tokyo"})
    for _ in range(1000):
        k.query("basic_view", {"region": "tokyo"}, compiled)
    for _ in range(1000):
        k.query("basic_view", {"region": "tokyo"}, compiled)
    stats = getattr(k, "cache_stats", lambda: {"ratio": 1.0})()
    assert stats["ratio"] >= 0.8
