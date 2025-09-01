# Golden Metrics Guard 設計問題調査レポート

**作成日**: 2025-08-31  
**調査対象**: scripts/bench_guard.py  
**問題**: Golden Metrics Guard が常にエラーになる設計

## 📋 問題の概要

Golden Metrics Guard（2025-08-29実装の新機能）が「Fast vs Slow実装比較」において、実装が逆転しており常にエラーになる設計となっている。

## 🔍 詳細分析

### 現在の実装状況

#### Config Compilation ベンチマーク
```python
# Fast実装（実際は重い）
def config_compile_fast(configs, compiler_class):
    compiler = compiler_class()  # ConfigCompilerクラスのインスタンス化
    result = compiler.compile_traffic(fake_traffic_data)  # 重いCompiler処理
    
# Slow実装（実際は軽い） 
def config_compile_slow(configs):
    result = {"path": config, "parts": parts, "hash": hash(config)}  # 軽い辞書操作
```

### 実測値
- **Fast実装**: 33,113μs（期待値: <50μs）
- **Slow実装**: 21μs 
- **比率**: 0.0007倍（期待値: >50倍）

→ **Fast実装がSlow実装より1,575倍遅い**

## 📊 bench_guard.json 結果

```json
{
  "config_compilation": {
    "fast": {
      "p95_us": 45316.50,
      "mean_us": 34755.57,
      "ops": 28.77
    },
    "slow": {
      "p95_us": 67.50,
      "mean_us": 26.98,
      "ops": 36713.41
    },
    "ratio": 0.0007836809811105018
  },
  "overall": {
    "ratio_ok": false,
    "fast_p95_ok": false
  },
  "passed": false
}
```

## 🏗️ 設計意図の推測

### 本来の設計意図（推測）
1. **Fast**: 最適化されたConfigCompiler実装
2. **Slow**: 非最適化または旧実装
3. **目的**: 最適化効果の継続的監視

### 現状の実装
1. **Fast**: 実際のConfigCompiler処理（重い）
2. **Slow**: 軽量なモック処理（軽い）
3. **結果**: 逆転により常にエラー

## 💡 考えられる原因

### シナリオ1: 開発中の実装変更
- 初期：Fast = 最適化実装、Slow = 非最適化実装
- 開発中：Fast実装を実際のCompilerに変更
- 結果：意図せず逆転

### シナリオ2: 設計意図の誤解
- Fast = Real実装のテスト
- Slow = Mock実装との比較
- 結果：パフォーマンステストではなく機能テスト

### シナリオ3: ベースライン調整不備
- 実装は正しい
- 閾値（50x、50μs）が不適切

## 🎯 確認すべき設計意図

### 質問1: ベンチマーク目的
- [ ] 最適化効果の測定？
- [ ] 実装正当性の検証？
- [ ] パフォーマンス回帰検知？

### 質問2: Fast/Slow定義
- [ ] Fast = 最適化実装 vs Slow = 非最適化実装？
- [ ] Fast = Real実装 vs Slow = Mock実装？
- [ ] Fast = 新実装 vs Slow = 旧実装？

### 質問3: 閾値設定根拠
- [ ] 50倍速度差の根拠は？
- [ ] 50μs以下の根拠は？
- [ ] 実測に基づく設定？

## 📋 対応選択肢

### 選択肢A: 実装修正
```python
# FastとSlowを入れ替え
def config_compile_fast(configs):
    # 軽量な最適化実装
    
def config_compile_slow(configs, compiler_class):
    # 重い非最適化実装
```

### 選択肢B: 閾値調整
```python
# 現実的な閾値に変更
MIN_RATIO = 0.1  # Fast が Slow の 1/10 でも OK
MAX_P95_US = 50000  # 50ms まで許容
```

### 選択肢C: 機能無効化
```yaml
# 一時的にCI skip
- name: Golden Metrics Guard
  if: false  # 設計修正まで無効化
```

### 選択肢D: 設計見直し
- ベンチマーク対象の再定義
- 測定指標の見直し
- CI統合方針の再検討

## ⚠️ 現在の影響

### 開発への影響
- **全PRがGolden Metrics Guardで失敗**
- DevContainer rollout等の無関係な変更もブロック
- 開発速度の著しい低下

### 緊急度
- **高**: 開発作業が停止状態
- 一時的な回避策が必要
- 根本的な設計見直しが必要

## 📞 次のアクション

1. **設計者への確認事項**
   - 上記の「確認すべき設計意図」
   - 緊急回避策の承認
   - 修正方針の決定

2. **緊急回避策**
   - 一時的なCI skip設定
   - または現実的閾値への調整

3. **根本修正**
   - 設計意図の明確化
   - 実装の修正または閾値調整
   - テスト・検証の実施

---

**関連ファイル**:
- `scripts/bench_guard.py`
- `.github/workflows/golden-metrics.yml`
- `bench_guard.json`
- `tests/golden/baseline/metrics.json`

**タグ**: #GoldenMetrics #設計問題 #緊急 #パフォーマンス