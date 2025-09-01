# [0.4] CI完全統合 - GitHub Actions ワークフロー

**Labels**: `backlog`, `target-0.4`, `ci`, `enhancement`, `priority-p0`  
**Milestone**: `v0.4.0`  
**Priority**: P0 (必須実装)

## 📋 目的
MVP Performance Toolsを既存のGitHub Actionsワークフローに完全統合し、現在の`bench_guard.py`を新しい`perf_suite`→`perf_guard`→`perf_reporter`フローに置換する。

## 🎯 具体的な仕様

### 新しいワークフロー設計
```yaml
# .github/workflows/performance.yml (新規)
name: Performance Testing
on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Dependencies
        run: |
          pip install -e .
          pip install -r requirements-dev.txt
          
      - name: Run Performance Suite
        run: |
          python -m performance.tools.perf_suite \
            --profile github-hosted \
            --iterations 3 \
            --warmup 100 \
            --output bench_results.json
            
      - name: Performance Gate Evaluation
        run: |
          python -m performance.tools.perf_guard \
            --input bench_results.json \
            --p50x 15.0 \
            --p95x 12.0 \
            --absolute-ms 100 \
            --output gate_results.json
            
      - name: Generate Performance Report
        if: always()
        run: |
          python -m performance.tools.perf_reporter \
            --input bench_results.json \
            --gate gate_results.json \
            --format markdown \
            --output bench_report.md
            
      - name: Upload Performance Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: |
            bench_results.json
            gate_results.json
            bench_report.md
            
      - name: Comment PR with Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const reportContent = fs.readFileSync('bench_report.md', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🚀 Performance Report\n\n${reportContent}`
            });
```

### 既存ワークフローの統合・置換
```yaml
# .github/workflows/bench-guard.yml (更新)
# 既存の bench_guard.py 呼び出しを新システムに置換

# Before:
- name: Run benchmark guard
  run: python scripts/bench_guard.py

# After:
- name: Performance Testing (Integrated)
  uses: ./.github/workflows/performance.yml
```

## 🔧 技術仕様

### パフォーマンスプロファイル
```python
# performance/profiles/github_hosted.py
GITHUB_HOSTED_PROFILE = {
    "iterations": 3,
    "warmup_runs": 100,
    "timeout_seconds": 300,
    "memory_limit_mb": 1024,
    "cpu_quota": "2.0",
    "platform_adjustments": {
        "ubuntu-latest": {"multiplier": 1.0},
        "windows-latest": {"multiplier": 1.2},
        "macos-latest": {"multiplier": 0.9}
    }
}
```

### ゲート設定標準化
```python
# performance/gates/standard.py
STANDARD_GATES = {
    "development": {
        "p50x_min": 10.0,
        "p95x_min": 8.0,
        "absolute_p95_max_ms": 150
    },
    "release": {
        "p50x_min": 15.0,
        "p95x_min": 12.0, 
        "absolute_p95_max_ms": 100
    },
    "production": {
        "p50x_min": 20.0,
        "p95x_min": 15.0,
        "absolute_p95_max_ms": 80
    }
}
```

### レポート形式統一
```markdown
# 自動生成されるPRコメント形式
## 🚀 Performance Report

### Summary
- **Status**: ✅ PASS / ❌ FAIL
- **P50 Speedup**: 16.6x (target: ≥15.0x)
- **P95 Speedup**: 15.8x (target: ≥12.0x)
- **P95 Absolute**: 87ms (target: ≤100ms)
- **Headroom**: 10.6% safety margin

### Detailed Results
| Metric | Current | Target | Status |
|--------|---------|--------|---------|
| P50 Speedup | 16.6x | ≥15.0x | ✅ |
| P95 Speedup | 15.8x | ≥12.0x | ✅ |
| P95 Absolute | 87ms | ≤100ms | ✅ |

### Historical Trend
```

## 📊 成功指標

### パフォーマンス目標
- **CI実行時間増加**: < 2分 (現在の bench_guard.py: ~1分30秒)
- **成功率**: > 95% (flaky test排除)
- **レポート生成時間**: < 10秒
- **アーティファクトサイズ**: < 5MB

### 機能要件
- ✅ 3-run median による安定性確保
- ✅ Two-tier gating (relative + absolute)
- ✅ 自動PR comment生成
- ✅ アーティファクト保存・ダウンロード対応
- ✅ 複数プラットフォーム対応準備

## 🚫 非目標・制限事項

### 現在のスコープ外
- **複数OS同時実行**: まずはubuntu-latestのみ
- **セルフホストランナー**: GitHub-hostedのみ
- **リアルタイム監視**: CI内での実行のみ
- **ベンチマーク自動更新**: 手動baseline管理

### 互換性維持
- 既存の`scripts/bench_guard.py`は0.4リリースまで併存
- `bench_results.json`形式の後方互換性
- 環境変数設定の既存CI設定との整合性

## 🔗 関連・依存 Issues

### 前提条件
- ✅ Performance Tools MVP実装完了 (0.3.0)
- ✅ CP932/UTF-8互換性確保 (0.3.0)
- ✅ Secret detection CI安定化 (0.3.0)

### 同時開発推奨
- `perf_diff` - 基準比較ツール (P1)
- Performance Engineering ドキュメント (P2)

### 後続作業
- マルチプラットフォーム対応 (0.5.0)
- リアルタイム監視基盤 (0.5.0)

## 🔄 実装戦略

### Phase 1: 基本統合 (Week 1-2)
1. `.github/workflows/performance.yml` 作成
2. `perf_suite`→`perf_guard`→`perf_reporter` フロー確認
3. アーティファクト生成・アップロード確認

### Phase 2: レポート自動化 (Week 2-3) 
1. PR comment自動生成実装
2. マークダウンレポート形式統一
3. Historical trend表示対応

### Phase 3: 置換・検証 (Week 3-4)
1. 既存`bench-guard.yml`更新
2. 並行実行による結果比較検証
3. `bench_guard.py`の段階的非推奨化

### Phase 4: 最適化・安定化 (Week 4)
1. CI実行時間最適化
2. エラーハンドリング強化
3. ドキュメント更新

## ✅ 完了条件 (Definition of Done)

### 技術要件
- [ ] `.github/workflows/performance.yml` 動作確認
- [ ] PR comment自動生成機能動作
- [ ] アーティファクト生成・ダウンロード確認
- [ ] 既存CIとの性能比較 (実行時間・精度)
- [ ] エラー時の適切なfail動作確認

### 品質要件
- [ ] 10回連続CI成功 (flaky test排除)
- [ ] パフォーマンス基準全クリア
- [ ] レポート可読性確認
- [ ] ドキュメント更新完了

### 運用要件
- [ ] 開発者向け移行ガイド作成
- [ ] 既存`bench_guard.py`非推奨アナウンス
- [ ] トラブルシューティング手順整備

---

**推定工数**: 2-3 weeks  
**担当者**: TBD  
**レビュワー**: Performance Engineering Team  
**作成日**: 2025-09-01  
**最終更新**: 2025-09-01