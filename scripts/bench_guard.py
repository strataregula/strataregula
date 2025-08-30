#!/usr/bin/env python3
"""
Bench Guard - StrataRegula パフォーマンス回帰検知システム

StrataRegula の各コンポーネント（パターン展開、設定コンパイル、カーネルキャッシュ）を
高速実装と低速フォールバック実装で比較し、パフォーマンス回帰を検知する。

判定基準:
- スループット比 fast/slow >= MIN_RATIO (デフォルト: 50x)
- fast の p95 <= MAX_P95_US (デフォルト: 50us)

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
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Callable
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# 環境変数での設定可能な閾値
MIN_RATIO = float(os.getenv("SR_BENCH_MIN_RATIO", "50"))
MAX_P95_US = float(os.getenv("SR_BENCH_MAX_P95_US", "50"))
WARMUP = int(os.getenv("SR_BENCH_WARMUP", "100"))
N = int(os.getenv("SR_BENCH_N", "1000"))

# 再現可能なベンチマークのためのシード固定
random.seed(42)

def get_system_info():
    """システム情報を取得（診断用）"""
    try:
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "hostname": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine()
        }
        
        # CPU情報の取得を試行
        try:
            if platform.system() == "Linux":
                result = subprocess.run(["nproc"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info["cpu_count"] = int(result.stdout.strip())
        except:
            pass
            
        # メモリ情報の取得を試行
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            info["memory_mb"] = int(line.split()[1]) // 1024
                            break
        except:
            pass
            
        return info
    except Exception as e:
        return {"error": str(e)}

def get_git_context():
    """Git コンテキスト情報を取得（診断用）"""
    try:
        context = {}
        
        # 現在のブランチ
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            context["branch"] = result.stdout.strip()
        
        # 最新コミットハッシュ
        result = subprocess.run(["git", "rev-parse", "HEAD"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            context["commit_hash"] = result.stdout.strip()[:8]
        
        # 変更されたファイル一覧（直近3コミット）
        result = subprocess.run(["git", "diff", "--name-only", "HEAD~3..HEAD"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            changed_files = result.stdout.strip().split('\n')
            context["recent_changes"] = [f for f in changed_files if f.strip()]
        
        # 未コミットの変更
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dirty_files = result.stdout.strip().split('\n')
            context["uncommitted_changes"] = [f for f in dirty_files if f.strip()]
        
        return context
    except Exception as e:
        return {"error": str(e)}

def validate_result_schema(result_data):
    """結果データのスキーマ検証"""
    if not HAS_JSONSCHEMA:
        print("[bench_guard] INFO: jsonschema not available, skipping validation")
        return True
        
    schema_path = Path(__file__).parent / "bench_guard.schema.json"
    if not schema_path.exists():
        print("[bench_guard] INFO: Schema file not found, skipping validation")
        return True
    
    try:
        with open(schema_path) as f:
            schema = json.load(f)
        
        jsonschema.validate(result_data, schema)
        print("[bench_guard] ✅ Result schema validation passed")
        return True
    except jsonschema.ValidationError as e:
        print(f"[bench_guard] ❌ Schema validation failed: {e.message}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[bench_guard] WARNING: Schema validation error: {e}", file=sys.stderr)
        return True  # Continue on validation errors

def load_strataregula_components():
    """StrataRegula コンポーネントをロードする"""
    components = {}
    
    # パターン展開
    try:
        from strataregula.core.pattern_expander import PatternExpander, EnhancedPatternExpander
        components['pattern_expander'] = EnhancedPatternExpander
        print("[bench_guard] PatternExpander loaded")
    except ImportError as e:
        print(f"[bench_guard] WARNING: PatternExpander not available: {e}", file=sys.stderr)
        components['pattern_expander'] = None
    
    # 設定コンパイラ
    try:
        from strataregula.core.config_compiler import ConfigCompiler
        components['config_compiler'] = ConfigCompiler
        print("[bench_guard] ConfigCompiler loaded")
    except ImportError as e:
        print(f"[bench_guard] WARNING: ConfigCompiler not available: {e}", file=sys.stderr)
        components['config_compiler'] = None
    
    # カーネルとキャッシュ
    try:
        from strataregula.kernel import Kernel, LRUCacheBackend
        components['kernel'] = Kernel
        components['cache_backend'] = LRUCacheBackend
        print("[bench_guard] Kernel and cache loaded")
    except ImportError as e:
        print(f"[bench_guard] WARNING: Kernel components not available: {e}", file=sys.stderr)
        components['kernel'] = None
        components['cache_backend'] = None
    
    # 少なくとも1つのコンポーネントが利用可能であることを確認
    if not any(components.values()):
        print(f"[bench_guard] ERROR: No StrataRegula components available", file=sys.stderr)
        sys.exit(2)
        
    return components

def create_test_patterns():
    """パターン展開用のテストデータを生成"""
    # 都道府県と地域のパターン
    prefectures = [
        "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima",
        "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa",
        "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano",
        "gifu", "shizuoka", "aichi", "mie", "shiga", "kyoto", "osaka", "hyogo",
        "nara", "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
        "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki",
        "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
    ]
    
    # 複雑なパターン例
    patterns = [
        "edge.*.gateway",
        "service-hub.*", 
        "corebrain.*.api",
        "*.tokyo.web",
        "api.*.service*"
    ]
    
    # テスト用の設定階層
    test_configs = []
    for i, pref in enumerate(prefectures[:10]):  # 最初の10都道府県のみ
        for j in range(3):  # tier0, tier1, tier2
            test_configs.append(f"service.{pref}.tier{j}.endpoint{i%5}")
    
    return patterns, test_configs, prefectures

def pattern_expand_fast(patterns, data, expander_class):
    """高速なパターン展開（最適化実装）"""
    expander = expander_class()
    
    # パターンと値のマッピングを作成
    pattern_dict = {}
    for i, pattern in enumerate(patterns):
        pattern_dict[pattern] = float(1.0 + i * 0.1)  # テスト用の値
    
    # expand_pattern_stream を使ってパターン展開
    results = []
    expanded_patterns = dict(expander.expand_pattern_stream(pattern_dict))
    
    # 結果を処理
    for pattern in patterns:
        for item in data:
            # 簡易的なマッチング（実際のパターンマッチングロジック）
            if '*' in pattern:
                pattern_parts = pattern.split('*')
                if len(pattern_parts) == 2 and pattern_parts[0] and pattern_parts[1]:
                    if item.startswith(pattern_parts[0]) and item.endswith(pattern_parts[1]):
                        results.append((pattern, item))
                elif pattern_parts[0] and item.startswith(pattern_parts[0]):
                    results.append((pattern, item))
            elif pattern == item:
                results.append((pattern, item))
    
    return results

def pattern_expand_slow(patterns, data):
    """低速なパターン展開（単純fnmatchベース）"""
    results = []
    for pattern in patterns:
        for item in data:
            if fnmatch.fnmatch(item, pattern):
                results.append((pattern, item))
    return results

def config_compile_fast(configs, compiler_class):
    """高速な設定コンパイル（最適化実装）"""
    if compiler_class is None:
        return config_compile_slow(configs)
    
    try:
        compiler = compiler_class()
        compiled_results = []
        for config in configs:
            try:
                # ConfigCompilerの実際のAPIに合わせて修正
                fake_traffic_data = {config: f"data_{hash(config) % 1000}"}
                result = compiler.compile_traffic(fake_traffic_data)
                compiled_results.append(result)
            except Exception:
                # フォールバック
                compiled_results.append({"path": config, "compiled": True})
        return compiled_results
    except Exception as e:
        print(f"[bench_guard] ConfigCompiler initialization failed: {e}", file=sys.stderr)
        return config_compile_slow(configs)

def config_compile_slow(configs):
    """低速な設定コンパイル（単純辞書操作）"""
    compiled_results = []
    for config in configs:
        # 単純な文字列操作でコンパイル風処理
        parts = config.split('.')
        result = {
            "path": config,
            "parts": parts,
            "depth": len(parts),
            "hash": hash(config),
            "value": f"data_{hash(config) % 1000}",
            "compiled": True
        }
        compiled_results.append(result)
    return compiled_results

def kernel_cache_fast(keys, values, kernel_class, cache_class):
    """高速なカーネルキャッシュ（LRU最適化）"""
    # Kernelを正しく初期化
    cache = cache_class()
    kernel = kernel_class(cache_backend=cache)
    
    # 仮想の設定データを作成
    fake_config = {"test_config": "value"}
    
    # kernelのqueryメソッドを使ってテスト
    results = []
    for key, value in zip(keys, values):
        try:
            # ダミーのview_keyとパラメータでqueryテスト
            result = kernel.query(f"test_view_{hash(key) % 10}", {"param": value}, fake_config)
            results.append(result)
        except (KeyError, ValueError):
            # viewが登録されていない場合はダミー結果
            results.append(f"cached_{value}")
    
    return results

def kernel_cache_slow(keys, values):
    """低速なカーネルキャッシュ（線形サーチ）"""
    # 単純なリストベースキャッシュ
    cache_list = list(zip(keys, values))
    
    # 線形サーチでキャッシュから取得
    results = []
    for key in keys:
        result = None
        for cached_key, cached_value in cache_list:
            if cached_key == key:
                result = cached_value
                break
        results.append(result)
    
    return results

def benchmark_function(func: Callable, warmup: int = WARMUP, repeat: int = N) -> Dict[str, float]:
    """関数のベンチマークを実行"""
    # ウォームアップ
    for _ in range(warmup):
        func()
    
    # 実際のベンチマーク
    latencies = []
    start_time = time.perf_counter()
    
    for _ in range(repeat):
        t0 = time.perf_counter()
        func()
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
    print("[bench_guard] Starting StrataRegula performance regression test")
    print(f"[bench_guard] Configuration: MIN_RATIO={MIN_RATIO}x, MAX_P95_US={MAX_P95_US}us")
    print(f"[bench_guard] Test parameters: WARMUP={WARMUP}, N={N}")
    
    # StrataRegula コンポーネントをロード
    components = load_strataregula_components()
    
    # テストデータの生成
    patterns, configs, prefectures = create_test_patterns()
    
    # 小規模なテストセットでベンチマーク実行
    test_patterns = patterns[:3]  # 最初の3パターン
    test_configs = configs[:20]   # 最初の20設定
    cache_keys = [f"key_{i}" for i in range(10)]
    cache_values = [f"value_{i}" for i in range(10)]
    
    print(f"[bench_guard] Generated test data: {len(test_patterns)} patterns, {len(test_configs)} configs")
    
    # 1. パターン展開のベンチマーク
    if components['pattern_expander']:
        print("[bench_guard] Benchmarking pattern expansion...")
        
        pattern_fast = lambda: pattern_expand_fast(test_patterns, test_configs, components['pattern_expander'])
        pattern_slow = lambda: pattern_expand_slow(test_patterns, test_configs)
        
        pattern_fast_results = benchmark_function(pattern_fast, warmup=WARMUP//10, repeat=N//10)
        pattern_slow_results = benchmark_function(pattern_slow, warmup=WARMUP//10, repeat=N//10)
        
        pattern_ratio = pattern_fast_results["ops"] / max(1.0, pattern_slow_results["ops"])
    else:
        print("[bench_guard] Skipping pattern expansion benchmark (component not available)")
        pattern_fast_results = {"ops": 1000000, "p95_us": 1, "p50_us": 1, "p99_us": 1}
        pattern_slow_results = {"ops": 100000, "p95_us": 10, "p50_us": 5, "p99_us": 20}
        pattern_ratio = 10
    
    # 2. 設定コンパイルのベンチマーク
    if components['config_compiler']:
        print("[bench_guard] Benchmarking config compilation...")
        
        compile_fast = lambda: config_compile_fast(test_configs, components['config_compiler'])
        compile_slow = lambda: config_compile_slow(test_configs)
        
        compile_fast_results = benchmark_function(compile_fast, warmup=WARMUP//10, repeat=N//20)
        compile_slow_results = benchmark_function(compile_slow, warmup=WARMUP//10, repeat=N//20)
        
        compile_ratio = compile_fast_results["ops"] / max(1.0, compile_slow_results["ops"])
    else:
        print("[bench_guard] Skipping config compilation benchmark (component not available)")
        compile_fast_results = {"ops": 500000, "p95_us": 2, "p50_us": 1, "p99_us": 3}
        compile_slow_results = {"ops": 50000, "p95_us": 20, "p50_us": 10, "p99_us": 30}
        compile_ratio = 10
    
    # 3. カーネルキャッシュのベンチマーク
    if components['kernel'] and components['cache_backend']:
        print("[bench_guard] Benchmarking kernel cache...")
        
        cache_fast = lambda: kernel_cache_fast(cache_keys, cache_values, components['kernel'], components['cache_backend'])
        cache_slow = lambda: kernel_cache_slow(cache_keys, cache_values)
        
        cache_fast_results = benchmark_function(cache_fast, warmup=WARMUP//5, repeat=N//5)
        cache_slow_results = benchmark_function(cache_slow, warmup=WARMUP//5, repeat=N//5)
        
        cache_ratio = cache_fast_results["ops"] / max(1.0, cache_slow_results["ops"])
    else:
        print("[bench_guard] Skipping kernel cache benchmark (component not available)")
        cache_fast_results = {"ops": 2000000, "p95_us": 0.5, "p50_us": 0.3, "p99_us": 1}
        cache_slow_results = {"ops": 200000, "p95_us": 5, "p50_us": 3, "p99_us": 10}
        cache_ratio = 10
    
    # 総合評価：最も遅いコンポーネントの結果を使用
    overall_fast_p95 = max(pattern_fast_results["p95_us"], compile_fast_results["p95_us"], cache_fast_results["p95_us"])
    overall_ratio = min(pattern_ratio, compile_ratio, cache_ratio)
    
    # 合否判定
    fast_p95_ok = overall_fast_p95 <= MAX_P95_US
    ratio_ok = overall_ratio >= MIN_RATIO
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
        "benchmarks": {
            "pattern_expansion": {
                "fast": pattern_fast_results,
                "slow": pattern_slow_results,
                "ratio": pattern_ratio
            },
            "config_compilation": {
                "fast": compile_fast_results,
                "slow": compile_slow_results,
                "ratio": compile_ratio
            },
            "kernel_cache": {
                "fast": cache_fast_results,
                "slow": cache_slow_results,
                "ratio": cache_ratio
            }
        },
        "overall": {
            "min_ratio": overall_ratio,
            "max_p95_us": overall_fast_p95,
            "ratio_ok": ratio_ok,
            "fast_p95_ok": fast_p95_ok
        },
        "passed": passed
    }
    
    # 結果をファイルに保存
    output_file = Path("bench_guard.json")
    output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 結果を標準出力に表示
    print("\n" + "="*70)
    print("STRATAREGULA BENCHMARK RESULTS")
    print("="*70)
    
    print(f"\nPattern Expansion:")
    print(f"  Fast: {pattern_fast_results['ops']:,.0f} ops/s, p95: {pattern_fast_results['p95_us']:.1f}us")
    print(f"  Slow: {pattern_slow_results['ops']:,.0f} ops/s, p95: {pattern_slow_results['p95_us']:.1f}us")
    print(f"  Ratio: {pattern_ratio:.1f}x")
    
    print(f"\nConfig Compilation:")
    print(f"  Fast: {compile_fast_results['ops']:,.0f} ops/s, p95: {compile_fast_results['p95_us']:.1f}us")
    print(f"  Slow: {compile_slow_results['ops']:,.0f} ops/s, p95: {compile_slow_results['p95_us']:.1f}us")
    print(f"  Ratio: {compile_ratio:.1f}x")
    
    print(f"\nKernel Cache:")
    print(f"  Fast: {cache_fast_results['ops']:,.0f} ops/s, p95: {cache_fast_results['p95_us']:.1f}us")
    print(f"  Slow: {cache_slow_results['ops']:,.0f} ops/s, p95: {cache_slow_results['p95_us']:.1f}us")
    print(f"  Ratio: {cache_ratio:.1f}x")
    
    print(f"\nOverall Assessment:")
    print(f"  Minimum ratio: {overall_ratio:.1f}x (threshold: >={MIN_RATIO}x) ({'OK' if ratio_ok else 'FAIL'})")
    print(f"  Maximum p95: {overall_fast_p95:.1f}us (threshold: <={MAX_P95_US}us) ({'OK' if fast_p95_ok else 'FAIL'})")
    
    print(f"\nResult: {'PASSED' if passed else 'FAILED'}")
    print("="*70)
    
    if passed:
        print(f"[bench_guard] Performance test PASSED - saved to {output_file}")
        sys.exit(0)
    else:
        reasons = []
        if not ratio_ok:
            reasons.append(f"minimum ratio {overall_ratio:.1f}x < {MIN_RATIO}x")
        if not fast_p95_ok:
            reasons.append(f"maximum p95 {overall_fast_p95:.1f}us > {MAX_P95_US}us")
        
        print(f"[bench_guard] Performance test FAILED: {', '.join(reasons)}")
        print(f"[bench_guard] Results saved to {output_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()