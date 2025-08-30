# AGENTS

自動化エージェントの責務・手順・Runログ様式を定義します。

## 共通原則
- **1 PR = 1 目的**
- **Runログは必ず作成**（Summary は非空、JSTで保存）

## Run Log Agent
- 目的: コマンド実行結果を `docs/run/*.md` に記録して可観測性を高める
- 優先度:
  1) `scripts/new_run_log.py` がある場合（例: world-simulation）
  2) 無ければ `tools/runlog.py`（軽量版）
  3) さらに無ければ `tools/runlog.sh`

### 使い方
```bash
# Python (軽量版)
python tools/runlog.py \
  --label smoke \
  --summary "smoke for cli/tests" \
  --intent "verify unified env works"

# シェル版（最短）
./tools/runlog.sh smoke "smoke for cli/tests" "verify unified env works"
```

## Plugin Development Agent
- 目的: StrataRegula プラグインの開発・テスト・デプロイの自動化
- 決定論的実行: 同じプラグイン仕様 → 同じ動作を保証
- プラグインライフサイクル管理: 開発、テスト、パッケージ化、配布

### 使い方
```bash
# プラグイン開発
python -m strataregula plugin create --name MyPlugin --template basic

# プラグインテスト
python -m strataregula plugin test --plugin MyPlugin --coverage

# プラグインパッケージ化
python -m strataregula plugin build --plugin MyPlugin --format wheel
```

## Performance Benchmarking Agent
- 目的: ストリーム処理性能の継続的モニタリング
- ベンチマーク実行: 回帰検出とパフォーマンス追跡
- メトリクス収集: レイテンシ、スループット、メモリ使用量

### 使い方
```bash
# ベンチマーク実行
python bench_guard.py --run-benchmarks --store-results

# パフォーマンス比較
python bench_guard.py --compare --baseline v1.0.0 --target HEAD

# 回帰チェック
python bench_guard.py --check-regression --threshold 10%
```

## ログサンプル（JST）

```markdown
# Run Log - plugin-test
- When: 2025-08-30T20-00JST
- Repo: strataregula
- Summary: Plugin development smoke test

## Intent
verify plugin API compatibility and performance

## Commands
python -m strataregula plugin test --all
python scripts/bench_guard.py --run-benchmarks --quick

## Results
- plugin tests: 15 passed, 2 skipped
- benchmarks: all within 5% baseline
- coverage: 92%

## Next actions
- add integration tests for new plugin hooks
- optimize stream buffer allocation
```

**タグ**: #automation #agents #runlog #plugins #performance
