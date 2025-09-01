# [0.4] perf_analyze - 原因特定ツール

**Labels**: `backlog`, `target-0.4`, `performance`, `enhancement`, `priority-p2`  
**Milestone**: `v0.4.0`  
**Priority**: P2 (価値向上実装)

## 📋 目的
パフォーマンス回帰の根本原因を特定するためのプロファイリングツール。`perf_diff`で検出された性能変化の「なぜ」を解明し、開発者が迅速に問題解決できる詳細分析を提供する。

## 🎯 具体的な仕様

### 基本CLI設計
```bash
# 基本的なプロファイリング実行
python -m performance.tools.perf_analyze --profile cProfile --top 10
python -m performance.tools.perf_analyze --profile py-spy --duration 30s

# 特定ベンチマークの深掘り分析
python -m performance.tools.perf_analyze \
  --benchmark pattern_compilation \
  --profile cProfile \
  --compare-with v0.3.0 \
  --output analysis_report.md

# 統合分析 (diff + analyze)
python -m performance.tools.perf_analyze \
  --auto-detect-regression \
  --base-ref v0.3.0 \
  --head-ref HEAD \
  --profile py-spy \
  --duration 60s
```

### 詳細コマンドオプション
```bash
# フルオプション例
python -m performance.tools.perf_analyze \
  --benchmark rule_expansion \
  --profile cProfile \
  --sort-by cumulative \
  --top-functions 20 \
  --include-callgraph \
  --memory-profiling \
  --output-format json \
  --output analysis_detailed.json \
  --compare-baseline results/baseline_profile.json \
  --threshold-percent 10.0 \
  --verbose
```

## 🔧 技術仕様

### サポートするプロファイラー

#### 1. cProfile (標準ライブラリ)
```python
# 実装例
import cProfile
import pstats
from io import StringIO

def run_cprofile_analysis(benchmark_func, sort_key='cumulative', top_n=20):
    """cProfileによる詳細プロファイリング"""
    pr = cProfile.Profile()
    pr.enable()
    
    # ベンチマーク実行
    result = benchmark_func()
    
    pr.disable()
    
    # 統計情報の生成
    s = StringIO()
    ps = pstats.Stats(pr, stream=s)
    ps.sort_stats(sort_key)
    ps.print_stats(top_n)
    
    return {
        'profile_data': s.getvalue(),
        'benchmark_result': result,
        'total_time': ps.total_tt,
        'function_stats': extract_function_stats(ps)
    }
```

#### 2. py-spy (サンプリングプロファイラー)
```python
import subprocess
import json
import tempfile

def run_pyspy_analysis(benchmark_command, duration_sec=30):
    """py-spyによる低オーバーヘッドプロファイリング"""
    with tempfile.NamedTemporaryFile(suffix='.json') as temp_file:
        # py-spy実行
        cmd = [
            'py-spy', 'record',
            '--pid', str(os.getpid()),
            '--duration', str(duration_sec),
            '--format', 'json',
            '--output', temp_file.name,
            '--'
        ] + benchmark_command.split()
        
        subprocess.run(cmd, check=True)
        
        # 結果解析
        with open(temp_file.name) as f:
            profile_data = json.load(f)
            
        return analyze_pyspy_output(profile_data)
```

#### 3. memory_profiler (メモリ使用量)
```python
from memory_profiler import profile, memory_usage

def run_memory_analysis(benchmark_func, interval=0.1):
    """メモリ使用量プロファイリング"""
    
    @profile
    def profiled_benchmark():
        return benchmark_func()
    
    # メモリ使用量測定
    mem_usage = memory_usage((profiled_benchmark, ()))
    
    return {
        'memory_usage': mem_usage,
        'peak_memory': max(mem_usage),
        'memory_delta': max(mem_usage) - min(mem_usage),
        'profile_output': get_line_profiler_output()
    }
```

### 分析レポート生成

#### Console出力形式
```
🔍 Performance Analysis Report

📊 Summary
  Benchmark: pattern_compilation
  Profiler: cProfile
  Total Time: 2.847s (1000 iterations)
  
🔥 Top Bottlenecks (by cumulative time)
┌─────────┬──────────────────────┬──────────┬──────────┬──────────┬─────────┐
│ Rank    │ Function             │ Calls    │ Time     │ Cumul    │ Per Call│
├─────────┼──────────────────────┼──────────┼──────────┼──────────┼─────────┤
│ 1       │ compile_patterns     │ 1000     │ 1.234s   │ 1.234s   │ 1.23ms  │
│ 2       │ regex_optimization   │ 5000     │ 0.890s   │ 2.124s   │ 0.18ms  │
│ 3       │ string_processing    │ 15000    │ 0.456s   │ 0.456s   │ 0.03ms  │
└─────────┴──────────────────────┴──────────┴──────────┴──────────┴─────────┘

⚠️  Performance Concerns
  • compile_patterns: 43% of total time (expected ~20%)
  • regex_optimization: High call frequency (5x normal)
  • string_processing: Memory allocation inefficient

🔧 Optimization Suggestions
  1. Cache compiled regex patterns (estimated 30% improvement)
  2. Reduce regex_optimization calls via memoization
  3. Pre-allocate string buffers for processing

📈 Historical Comparison (vs v0.3.0)
  compile_patterns: 0.890s → 1.234s (+38.6% regression)  ⚠️
  regex_optimization: 0.756s → 0.890s (+17.7% regression)  ⚠️
  string_processing: 0.445s → 0.456s (+2.5% normal variance)  ✅
```

#### JSON出力形式
```json
{
  "metadata": {
    "timestamp": "2025-09-01T15:30:00Z",
    "benchmark": "pattern_compilation",
    "profiler": "cProfile",
    "total_time_seconds": 2.847,
    "iterations": 1000,
    "base_ref": "v0.3.0",
    "current_ref": "HEAD"
  },
  "top_functions": [
    {
      "rank": 1,
      "function_name": "compile_patterns",
      "module": "strataregula.core.compiler",
      "calls": 1000,
      "total_time": 1.234,
      "cumulative_time": 1.234,
      "per_call_ms": 1.23,
      "percentage_of_total": 43.4
    }
  ],
  "performance_issues": [
    {
      "severity": "high",
      "function": "compile_patterns",
      "issue": "Consuming 43% of total time (expected ~20%)",
      "suggestion": "Cache compiled regex patterns",
      "estimated_improvement": "30%"
    }
  ],
  "regression_analysis": [
    {
      "function": "compile_patterns",
      "base_time": 0.890,
      "current_time": 1.234,
      "change_percent": 38.6,
      "status": "regression",
      "significance": "high"
    }
  ],
  "optimization_suggestions": [
    {
      "priority": "high",
      "description": "Cache compiled regex patterns",
      "rationale": "Eliminates redundant compilation overhead",
      "estimated_impact": "30% performance improvement",
      "implementation_complexity": "medium"
    }
  ]
}
```

### perf_diffとの統合
```python
# performance/tools/perf_analyze.py
class PerformanceAnalyzer:
    def auto_analyze_regression(self, base_ref: str, current_ref: str):
        """回帰自動検出→原因分析"""
        
        # 1. perf_diff実行で回帰検出
        diff_result = perf_diff.compare_commits(base_ref, current_ref)
        
        # 2. 回帰のあるベンチマークを特定
        regressions = [
            comp for comp in diff_result.comparisons 
            if comp.diff.status == "regression" and comp.diff.significance > 0.95
        ]
        
        # 3. 各回帰について詳細分析
        analysis_results = []
        for regression in regressions:
            analysis = self.analyze_benchmark(
                benchmark=regression.benchmark,
                profiler="cProfile"  # デフォルト
            )
            analysis_results.append(analysis)
        
        # 4. 統合レポート生成
        return self.generate_integrated_report(diff_result, analysis_results)
```

## 📊 成功指標

### パフォーマンス要件
- **プロファイル取得オーバーヘッド**: < 10% (py-spy: < 1%)
- **分析結果生成時間**: < 5秒
- **メモリ使用量**: < 100MB (プロファイルデータ含む)
- **レポート生成速度**: < 1秒 (JSON/Markdown)

### 機能要件
- ✅ 3種類プロファイラー対応 (cProfile, py-spy, memory_profiler)
- ✅ 回帰分析統合 (`perf_diff`との連携)
- ✅ 最適化提案システム
- ✅ 複数出力形式 (Console/JSON/Markdown)
- ✅ Historical comparison (baseline対比)

### 精度要件
- ✅ Bottleneck特定精度 > 95%
- ✅ 最適化提案の有効性 > 80%
- ✅ False positive rate < 5%
- ✅ 統計的有意性検証組み込み

## 🔧 実装詳細

### プロファイラー統合クラス
```python
# performance/profilers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class ProfileResult:
    profiler_type: str
    total_time: float
    function_stats: List[Dict]
    bottlenecks: List[Dict]
    suggestions: List[Dict]
    raw_data: Any

class ProfilerInterface(ABC):
    @abstractmethod
    def profile_benchmark(self, benchmark_func, **kwargs) -> ProfileResult:
        pass
    
    @abstractmethod
    def analyze_results(self, profile_data) -> Dict[str, Any]:
        pass

class CProfileProfiler(ProfilerInterface):
    def profile_benchmark(self, benchmark_func, **kwargs):
        # cProfile実装
        pass

class PySpyProfiler(ProfilerInterface):  
    def profile_benchmark(self, benchmark_func, **kwargs):
        # py-spy実装
        pass

class MemoryProfiler(ProfilerInterface):
    def profile_benchmark(self, benchmark_func, **kwargs):
        # memory_profiler実装
        pass
```

### 最適化提案エンジン
```python
# performance/analysis/optimizer.py
class OptimizationEngine:
    def __init__(self):
        self.suggestion_rules = self.load_suggestion_rules()
    
    def analyze_bottlenecks(self, profile_result: ProfileResult) -> List[Dict]:
        """ボトルネック分析→最適化提案生成"""
        suggestions = []
        
        for func_stat in profile_result.function_stats:
            # ルールベース提案
            for rule in self.suggestion_rules:
                if rule.matches(func_stat):
                    suggestion = rule.generate_suggestion(func_stat)
                    suggestions.append(suggestion)
        
        return self.prioritize_suggestions(suggestions)
    
    def load_suggestion_rules(self):
        """最適化ルール定義"""
        return [
            RegexCompilationRule(),
            MemoryAllocationRule(), 
            LoopOptimizationRule(),
            CachingOpportunityRule(),
            StringProcessingRule()
        ]

class RegexCompilationRule:
    def matches(self, func_stat):
        return (
            "compile" in func_stat["function_name"].lower() and
            func_stat["calls"] > 100 and
            func_stat["per_call_time"] > 0.001  # 1ms
        )
    
    def generate_suggestion(self, func_stat):
        return {
            "priority": "high",
            "description": "Cache compiled regex patterns",
            "rationale": f"Function called {func_stat['calls']} times, each taking {func_stat['per_call_time']:.3f}ms",
            "estimated_impact": "20-40% improvement",
            "implementation": "Use @lru_cache decorator or class-level pattern storage"
        }
```

## 🔄 使用例・ワークフロー

### 開発者の問題解決フロー
```bash
# 1. 性能回帰検出 (perf_diff)
python -m performance.tools.perf_diff --base v0.3.0 --head HEAD
# → pattern_compilation で 38% 劣化を検出

# 2. 原因分析開始
python -m performance.tools.perf_analyze \
  --benchmark pattern_compilation \
  --profile cProfile \
  --compare-with v0.3.0

# 3. メモリ使用量も確認
python -m performance.tools.perf_analyze \
  --benchmark pattern_compilation \
  --profile memory_profiler \
  --include-line-by-line

# 4. 統合レポート生成 (PR用)
python -m performance.tools.perf_analyze \
  --auto-detect-regression \
  --base-ref v0.3.0 \
  --format markdown \
  --output regression_analysis.md
```

### CI統合での自動分析
```yaml
# .github/workflows/performance-analysis.yml
- name: Detect Performance Regression
  run: |
    python -m performance.tools.perf_diff \
      --base ${{ github.event.pull_request.base.sha }} \
      --head ${{ github.sha }} \
      --output diff_report.json

- name: Auto-Analyze Regressions
  if: contains(fromJSON(steps.diff.outputs.result).summary.regressions, '> 0')
  run: |
    python -m performance.tools.perf_analyze \
      --auto-detect-regression \
      --base-ref ${{ github.event.pull_request.base.sha }} \
      --head-ref ${{ github.sha }} \
      --output analysis_report.md
      
- name: Comment Detailed Analysis
  uses: actions/github-script@v6
  with:
    script: |
      const fs = require('fs');
      const analysis = fs.readFileSync('analysis_report.md', 'utf8');
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `## 🔍 Performance Regression Analysis\n\n${analysis}`
      });
```

## 🚫 非目標・制限事項

### 現在のスコープ外
- **リアルタイムプロファイリング**: バッチ実行のみ
- **本番環境対応**: 開発・テスト環境専用
- **マルチプロセス対応**: シングルプロセスのみ
- **GUI可視化**: CLI/テキストベース出力
- **自動最適化**: 提案生成のみ、実装は手動

### 制限事項
- **py-spy依存**: py-spyインストールが必要
- **権限要件**: プロファイリング権限が必要な場合
- **メモリ制約**: 大規模アプリケーションでの制限
- **Python限定**: Python codeベースのみ対応

## 🔗 関連・依存 Issues

### 前提条件
- ✅ Performance Tools MVP (0.3.0) - ベンチマーク基盤
- ⏳ **perf_diff** (P1) - 回帰検出機能との統合
- ✅ JSON出力標準化 - 統合レポート生成

### 連携強化
- **perf_diff** (P1) - 自動回帰分析ワークフロー
- **CI完全統合** (P0) - 自動分析トリガー
- **Performance ドキュメント** (P2) - 最適化ガイド統合

### 後続展開
- **perf_optimize** (0.5.0) - 自動最適化適用
- **Performance Dashboard** (0.5.0) - Web UI可視化
- **Historical Analysis** (0.5.0) - 長期トレンド分析

## ✅ 完了条件 (Definition of Done)

### 技術要件
- [ ] 3種類プロファイラー統合動作確認
- [ ] 自動回帰分析機能 (`--auto-detect-regression`) 動作
- [ ] 最適化提案エンジン精度検証
- [ ] 複数出力形式品質確認
- [ ] perf_diff統合テスト完了

### 品質要件
- [ ] 単体テスト Coverage > 85%
- [ ] プロファイリング精度検証
- [ ] 最適化提案有効性テスト (実際の改善確認)
- [ ] パフォーマンスオーバーヘッド測定

### ドキュメント要件
- [ ] プロファイラー比較・選択ガイド
- [ ] 最適化提案実装例集
- [ ] トラブルシューティング手順
- [ ] CI統合設定手順

### 検証要件
- [ ] 既知のボトルネック検出確認
- [ ] 回帰原因特定精度測定
- [ ] ユーザビリティテスト (開発者feedback)
- [ ] 大規模コードベースでの動作確認

---

**推定工数**: 3-4 weeks  
**担当者**: Performance Engineering Team  
**レビュワー**: Core Development + Performance Experts  
**作成日**: 2025-09-01  
**最終更新**: 2025-09-01