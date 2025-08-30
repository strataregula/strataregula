#!/usr/bin/env python3
"""
Bench Guard - パフォーマンス回帰検知システム

compiled_config.get_service_time（高速経路）と、簡易 fnmatch（低速の疑似フォールバック）を
同一ワークロードで比較し、パフォーマンスの閾値をチェックする。

判定基準:
- スループット比 fast/slow ≥ MIN_RATIO (デフォルト: 30x)
- fast の p95 ≤ MAX_P95_US (デフォルト: 100us)

失敗時: exit 1（PR落とす）
成果物: bench_guard.json を保存（GitHub Actionsのアーティファクトで閲覧可能）
"""

import os
import sys
import time
import json
import random
import statistics
import fnmatch
import importlib
from pathlib import Path
from typing import Dict, Any, List, Callable

# 環境変数での設定可能な閾値
MIN_RATIO = float(os.getenv("SR_BENCH_MIN_RATIO", "30"))
MAX_P95_US = float(os.getenv("SR_BENCH_MAX_P95_US", "100"))
WARMUP = int(os.getenv("SR_BENCH_WARMUP", "1000"))
N = int(os.getenv("SR_BENCH_N", "100000"))

# 再現可能なベンチマークのためのシード固定
random.seed(42)

def load_compiled():
    """compiled_config.get_service_time をロードする"""
    try:
        # 最初に標準的なパスを試す
        cc = importlib.import_module("compiled_config")
        return cc.get_service_time
    except ImportError:
        try:
            # プロジェクト構造に合わせた代替パス
            cc = importlib.import_module("src.simroute.config.compiled")
            return cc.get_service_time
        except Exception as e:
            print(f"[bench_guard] ERROR: compiled config module not found", file=sys.stderr)
            print(f"[bench_guard] Tried: compiled_config, src.simroute.config.compiled", file=sys.stderr)
            print(f"[bench_guard] Error: {e}", file=sys.stderr)
            sys.exit(2)

def create_test_data():
    """ベンチマーク用のテストデータを生成"""
    # サービス名の基礎パターン
    bases = [f"svc.region{r}.tier{t}.endpoint{e}"
             for r in range(1, 9) for t in range(1, 4) for e in range(1, 51)]
    
    # パターンマッチング用の設定（フォールバック用）
    patterns = [
        "svc.*.tier1.*",
        "svc.region?.tier2.endpoint*",
        "svc.region7.*.endpoint*", 
        "svc.region3.tier3.endpoint*",
        "*.region*.tier*.endpoint*",
    ]
    
    # パターンと値のマッピング（簡易フォールバック実装）
    legacy_map = {p: float(1 + i * 0.1) for i, p in enumerate(patterns)}
    
    return bases, legacy_map

def get_service_time_slow(name: str, legacy_map: Dict[str, float]) -> float:
    """fnmatch を使った低速なフォールバック実装"""
    for pattern, value in legacy_map.items():
        if fnmatch.fnmatch(name, pattern):
            return value
    return 0.0

def benchmark_function(func: Callable[[str], float], queries: List[str], 
                      warmup: int = WARMUP, repeat: int = N) -> Dict[str, float]:
    """関数のベンチマークを実行"""
    # ウォームアップ
    warmup_queries = [random.choice(queries) for _ in range(warmup)]
    for query in warmup_queries:
        func(query)
    
    # 実際のベンチマーク
    latencies = []
    start_time = time.perf_counter()
    
    for query in queries[:repeat]:
        t0 = time.perf_counter()
        func(query)
        latencies.append((time.perf_counter() - t0) * 1e6)  # us
    
    elapsed = time.perf_counter() - start_time
    ops_per_sec = repeat / elapsed
    
    # 統計計算
    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)
    p50 = latencies_sorted[int(0.50 * n)]
    p95 = latencies_sorted[int(0.95 * n) - 1]
    p99 = latencies_sorted[int(0.99 * n) - 1]
    
    return {
        "ops": ops_per_sec,
        "p50_us": p50,
        "p95_us": p95,
        "p99_us": p99,
        "min_us": min(latencies),
        "max_us": max(latencies),
        "mean_us": statistics.mean(latencies),
        "std_us": statistics.stdev(latencies) if n > 1 else 0.0
    }

def main():
    """メイン処理"""
    print("[bench_guard] Starting performance regression test")
    print(f"[bench_guard] Configuration: MIN_RATIO={MIN_RATIO}x, MAX_P95_US={MAX_P95_US}us")
    print(f"[bench_guard] Test parameters: WARMUP={WARMUP}, N={N}")
    
    # 高速実装をロード
    get_service_time_fast = load_compiled()
    
    # テストデータの生成
    bases, legacy_map = create_test_data()
    queries = [random.choice(bases) for _ in range(N)]
    
    print(f"[bench_guard] Generated {len(queries)} queries from {len(bases)} base patterns")
    
    # 高速実装のベンチマーク
    print("[bench_guard] Benchmarking fast implementation (compiled_config)...")
    fast_results = benchmark_function(
        get_service_time_fast, 
        queries, 
        warmup=WARMUP, 
        repeat=N
    )
    
    # 低速実装のベンチマーク  
    print("[bench_guard] Benchmarking slow implementation (fnmatch fallback)...")
    slow_func = lambda name: get_service_time_slow(name, legacy_map)
    slow_results = benchmark_function(
        slow_func,
        queries,
        warmup=WARMUP,
        repeat=N
    )
    
    # 比率計算と判定
    ratio = fast_results["ops"] / max(1.0, slow_results["ops"])
    fast_p95_ok = fast_results["p95_us"] <= MAX_P95_US
    ratio_ok = ratio >= MIN_RATIO
    passed = ratio_ok and fast_p95_ok
    
    # 結果構造化
    result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S JST", time.localtime()),
        "config": {
            "min_ratio": MIN_RATIO,
            "max_p95_us": MAX_P95_US,
            "warmup": WARMUP,
            "n": N
        },
        "fast": fast_results,
        "slow": slow_results,
        "comparison": {
            "ratio_fast_over_slow": ratio,
            "ratio_ok": ratio_ok,
            "fast_p95_ok": fast_p95_ok
        },
        "passed": passed
    }
    
    # 結果をファイルに保存
    output_file = Path("bench_guard.json")
    output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 結果を標準出力に表示
    print("\n" + "="*60)
    print("BENCHMARK RESULTS")
    print("="*60)
    print(f"Fast implementation (compiled_config):")
    print(f"  - Operations/sec: {fast_results['ops']:,.0f}")
    print(f"  - p50: {fast_results['p50_us']:.1f}us")
    print(f"  - p95: {fast_results['p95_us']:.1f}us")
    print(f"  - p99: {fast_results['p99_us']:.1f}us")
    
    print(f"\nSlow implementation (fnmatch fallback):")
    print(f"  - Operations/sec: {slow_results['ops']:,.0f}")
    print(f"  - p50: {slow_results['p50_us']:.1f}us")
    print(f"  - p95: {slow_results['p95_us']:.1f}us")
    print(f"  - p99: {slow_results['p99_us']:.1f}us")
    
    print(f"\nComparison:")
    print(f"  - Speed ratio (fast/slow): {ratio:.1f}x")
    print(f"  - Threshold: >={MIN_RATIO}x ({'OK' if ratio_ok else 'FAIL'})")
    print(f"  - Fast p95: {fast_results['p95_us']:.1f}us")
    print(f"  - p95 threshold: <={MAX_P95_US}us ({'OK' if fast_p95_ok else 'FAIL'})")
    
    print(f"\nOverall result: {'PASSED' if passed else 'FAILED'}")
    print("="*60)
    
    if passed:
        print(f"[bench_guard] Performance test PASSED - saved to {output_file}")
        sys.exit(0)
    else:
        reasons = []
        if not ratio_ok:
            reasons.append(f"speed ratio {ratio:.1f}x < {MIN_RATIO}x")
        if not fast_p95_ok:
            reasons.append(f"fast p95 {fast_results['p95_us']:.1f}us > {MAX_P95_US}us")
        
        print(f"[bench_guard] Performance test FAILED: {', '.join(reasons)}")
        print(f"[bench_guard] Results saved to {output_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()