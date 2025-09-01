#!/usr/bin/env python3
"""
最適化されたベンチマーク - 測定オーバーヘッドを最小化
Optimized Benchmark - Minimal Measurement Overhead
"""

import time

from micro_patterns import *


# ❌ 元のコード（重い）
def slow_measurement(func, iterations=1000):
    """遅い測定 - 典型的な罠"""
    import gc
    import sys

    gc.collect()  # 重い！全メモリをスキャン
    sys.getsizeof(gc.get_objects())  # 超重い！全オブジェクト取得

    start_time = time.perf_counter()
    for _ in range(iterations):
        func()  # 関数呼び出しオーバーヘッド
    end_time = time.perf_counter()

    gc.collect()  # また重い！
    sys.getsizeof(gc.get_objects())  # また超重い！

    return (end_time - start_time) / iterations * 1000


# ✅ 最適化版（軽い）
def fast_measurement(func, iterations=1000):
    """高速測定 - オーバーヘッド最小化"""
    # ウォームアップ（JIT最適化など）
    func()

    # 測定のみ（メモリ測定は重いので除外）
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()

    # 最小計算
    return (end - start) * 1000000 / iterations  # μs per operation


# 🔬 オーバーヘッド比較デモ
def demonstrate_measurement_overhead():
    """測定オーバーヘッドの実演"""
    print("MEASUREMENT OVERHEAD ANALYSIS")
    print("=" * 50)

    # 軽量なテスト関数
    def lightweight_func():
        return 42

    # 測定オーバーヘッドを測定
    iterations = 1000

    print("1. 測定コード自体の速度:")

    # 空のループ（最小基準）
    start = time.perf_counter()
    for _ in range(iterations):
        pass  # 何もしない
    empty_loop_time = time.perf_counter() - start
    print(f"   Empty loop: {empty_loop_time * 1000:.4f}ms")

    # 関数呼び出しのみ
    start = time.perf_counter()
    for _ in range(iterations):
        lightweight_func()
    function_call_time = time.perf_counter() - start
    print(f"   Function calls: {function_call_time * 1000:.4f}ms")

    # 遅い測定（GC付き）
    start = time.perf_counter()
    slow_measurement(lightweight_func, 100)  # 回数減らす
    slow_measurement_time = time.perf_counter() - start
    print(f"   Slow measurement: {slow_measurement_time * 1000:.4f}ms")

    # 高速測定
    start = time.perf_counter()
    fast_measurement(lightweight_func, iterations)
    fast_measurement_time = time.perf_counter() - start
    print(f"   Fast measurement: {fast_measurement_time * 1000:.4f}ms")

    print("\n2. オーバーヘッド分析:")
    function_overhead = function_call_time - empty_loop_time
    slow_overhead = slow_measurement_time - function_call_time
    fast_overhead = fast_measurement_time - function_call_time

    print(f"   Function call overhead: {function_overhead * 1000:.4f}ms")
    print(f"   Slow measurement overhead: {slow_overhead * 1000:.4f}ms")
    print(f"   Fast measurement overhead: {fast_overhead * 1000:.4f}ms")
    print(f"   Overhead ratio (slow/fast): {slow_overhead / fast_overhead:.1f}x")


# 🚀 最適化されたパターンベンチマーク
def optimized_pattern_benchmark():
    """最適化されたパターンベンチマーク"""
    print("\nOPTIMIZED PATTERN BENCHMARK")
    print("=" * 40)

    # 事前準備（測定ループ外で実行）
    Config()  # Singleton instance
    query = Query()  # Builder instance
    strategy = Sorter(sorted)  # Strategy instance

    @memoize
    def fib(n):
        return n if n <= 1 else fib(n - 1) + fib(n - 2)

    # テスト関数（クロージャで最適化）
    test_functions = {
        "singleton": lambda: Config(),
        "builder": lambda: query.select("test"),
        "strategy": lambda: strategy.sort([3, 1, 2]),
        "memoize": lambda: fib(10),  # キャッシュヒット
        "pipe": lambda: pipe(5, lambda x: x * 2, lambda x: x + 1),
    }

    results = {}
    iterations = 10000  # 多くの反復で精度向上

    for name, func in test_functions.items():
        time_us = fast_measurement(func, iterations)
        results[name] = time_us
        print(f"{name:<10}: {time_us:.3f}μs/op")

    return results


# 📊 バッチ処理デモ
def batch_processing_demo():
    """バッチ処理による高速化デモ"""
    print("\nBATCH PROCESSING OPTIMIZATION")
    print("=" * 35)

    # テストデータ
    test_data = list(range(1000))

    # ❌ 個別処理（遅い）
    def individual_processing():
        results = []
        for item in test_data:
            # 各アイテムで測定（重い）
            start = time.perf_counter()
            processed = item * 2 + 1
            end = time.perf_counter()
            results.append((processed, end - start))
        return results

    # ✅ バッチ処理（速い）
    def batch_processing():
        # 測定は外側で1回だけ
        start = time.perf_counter()
        results = [item * 2 + 1 for item in test_data]
        end = time.perf_counter()
        return results, end - start

    # 比較
    start = time.perf_counter()
    individual_results = individual_processing()
    individual_time = time.perf_counter() - start

    start = time.perf_counter()
    batch_results, batch_time = batch_processing()
    batch_total_time = time.perf_counter() - start

    print(f"Individual processing: {individual_time * 1000:.2f}ms")
    print(f"Batch processing: {batch_total_time * 1000:.2f}ms")
    print(f"Speedup: {individual_time / batch_total_time:.1f}x")

    # 結果は同じ
    individual_values = [r[0] for r in individual_results]
    print(f"Results match: {individual_values == batch_results}")


# 🎯 プロファイリング最適化のヒント
def profiling_tips():
    """プロファイリング最適化のヒント"""
    print("\nPROFILING OPTIMIZATION TIPS")
    print("=" * 30)

    tips = [
        "1. 測定は最小限に - 本当に必要な指標のみ",
        "2. バッチ処理 - 個別測定を避ける",
        "3. プール再利用 - オブジェクト生成を避ける",
        "4. 遅延初期化 - 必要時のみインスタンス生成",
        "5. システムコール削減 - I/Oは最小限に",
        "6. 文字列生成回避 - ログ出力は条件付きに",
        "7. GC回避 - 不要なメモリ割当てを避ける",
    ]

    for tip in tips:
        print(f"   {tip}")


if __name__ == "__main__":
    demonstrate_measurement_overhead()
    optimized_pattern_benchmark()
    batch_processing_demo()
    profiling_tips()

    print("\nKEY INSIGHT: 測定コードは測定対象より軽くあるべし！")
