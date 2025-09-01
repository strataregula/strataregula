# Bench Guard Origin & Rules (Golden Metrics) - SSOT

**目的**: サービス時間ルックアップの最速経路（Fast）が常に基準（Slow）より十分速いことをCIで保証し、性能回帰を即検知・即遮断

**作成日**: 2025-08-31  
**最終更新**: 2025-08-31  
**責任者**: Performance Team  
**SSOT**: このファイルが唯一の参照点

---

## 📋 起点プロンプト（保存版）

### 元指示 (2025-08-29)
```
## A. config_compiler の O(1) 直マップ化
- 仕様:
  1) --traffic と --prefectures を読み込み、全リソース(base)を列挙して DIRECT_MAPPING を生成
  2) 生成物 src/compiled_config.py には DIRECT_MAPPING: Dict[str, float]
  3) get_service_time(name:str)->float: 1) 直マップ参照 → 2) 役割ベースfallback → 3) 0.0

## C. ベンチマーク追加
- 新規: scripts/bench_service_time.py
- 3モード（fnmatch / compiled_tree / direct_map）で 1e5 回 lookup を 3回ずつ計測
- README に「目標: direct_map >= 50x fnmatch」を明記
```

### 設計意図
- **Fast実装**: O(1) 直マップルックアップ（事前展開辞書）
- **Slow実装**: O(n×m) fnmatchパターン照合（既存手法）
- **目標性能**: **50倍速化** (direct_map/fnmatch ≥ 50x)

---

## 🎯 アーキテクチャ定義

### API境界
```python
# scripts/config_compiler.py
def compile_traffic(traffic_path, prefectures_path) -> Dict[str, float]:
    """全baseを事前展開しDIRECT_MAPPINGを生成"""

# src/compiled_config.py (自動生成)
DIRECT_MAPPING: Dict[str, float] = {...}
def get_service_time(base: str) -> float:
    return DIRECT_MAPPING.get(base) or fallback_logic(base) or 0.0
```

### 比較軸
- **Fast**: `direct_map` - 事前展開辞書のO(1)ルックアップ
- **Slow**: `fnmatch` - パターン照合のO(n×m)処理
- **対象**: アルゴリズムのみ（I/O・YAML読み込み除外）

### 測定プロトコル
- **実行**: 100,000回×3セット
- **メトリクス**: avg/var/p95をJSON保存
- **出力**: `.cache/bench_guard.json`

---

## 📊 CI ガード基準

### 性能閾値
```yaml
# メイン基準（main branch）
direct_map/fnmatch >= 20x  # 最低基準
target: >= 50x             # 目標値

# PR基準（pull request）  
direct_map/fnmatch >= 10x  # 緩和基準
```

### 安定性基準
```yaml
p95_direct_map <= 10ms     # 100k実行でのP95上限
variance_coefficient < 0.1  # 実行時間の変動係数
```

### 運用緩和策
- **ラベル運用**:
  - `ci:bench-relaxed`: PR限定で閾値緩和
  - `ci:bench-skip`: 期限付きスキップ（2回連続で改善タスク必須）

---

## 🔧 変更手順・ガバナンス

### 閾値変更プロセス
1. **計測実施**: 直近3回の中央値を取得
2. **根拠記載**: 環境・計測値・JSONデータを添付
3. **PR作成**: このSSoTファイルに変更理由を記載
4. **レビュー**: 2名以上の承認必須
5. **検証**: 回帰テスト100%パス確認
6. **文書同期**: README・CI設定の同期更新

### 承認者
- **テックリード**: 設計・アーキテクチャ承認
- **パフォーマンス責任者**: 閾値・基準値承認
- **プロダクトオーナー**: 緊急スキップ承認

### 定期見直し
- **月次レビュー**: 第3金曜日に閾値妥当性確認
- **四半期調整**: リリース後2週間以内にベースライン更新
- **緊急見直し**: 連続失敗3回で即座トリアージ

---

## 🚨 エスカレーション・通知

### 自動通知
```yaml
CI失敗: Slack #performance 即座通知
連続失敗: 2回目でテックリードメンション  
緊急スキップ: 全開発者に理由付き通知
週次サマリ: 金曜日に成功率・傾向レポート
```

### 品質基準
- **False Positive許容率**: <5% (月間)
- **検出感度**: 20%以上の性能劣化は必ず検出
- **復旧時間**: CI障害から復旧まで<2時間

---

## 📈 履歴・変更ログ

### v1.0 (2025-08-31) - 初期設定
- **main基準**: 20x (最低) / 50x (目標)
- **PR基準**: 10x (緩和)
- **根拠**: 元指示の50倍速化要求
- **計測環境**: GitHub Actions Ubuntu-latest Python 3.11

### 変更テンプレート
```markdown
### v1.x (YYYY-MM-DD) - 変更理由
- **変更内容**: 閾値・基準・プロセスの変更
- **根拠**: 3回計測の中央値データ
- **影響範囲**: CI・README・文書の同期箇所
- **承認者**: [テックリード名] + [パフォーマンス責任者名]
```

---

## 🔍 実装チェックリスト

### 緊急復旧（Phase 1）
- [ ] `compile_traffic()` API追加でbench_guard.py修正
- [ ] CI閾値を main:20x / PR:10x に設定
- [ ] ラベル運用(`ci:bench-relaxed`/`ci:bench-skip`)導入

### 恒久対応（Phase 2）  
- [ ] 完全直マップ生成(`src/compiled_config.py`)
- [ ] Engine Fast Path固定化
- [ ] アルゴリズム限定ベンチマーク

### 整備完了（Phase 3）
- [ ] `.cache/bench_guard.json` CIアーティファクト化
- [ ] README同期(比較対象・目標・基準明記)
- [ ] SSOT更新フローの確立

---

## 📞 関連リソース

### ファイル
- **実装**: `scripts/bench_guard.py`, `strataregula/core/config_compiler.py`
- **CI**: `.github/workflows/bench-guard.yml`, `golden-metrics.yml`  
- **文書**: `AGENTS.md`, `README.md`

### コマンド
```bash
# 手動ベンチマーク
python scripts/bench_service_time.py --json .cache/bench_guard.json

# 閾値テスト
python scripts/bench_guard_check.py --min-multiplier 20 --vs fnmatch --mode direct_map

# 設定調整
SR_BENCH_MIN_RATIO=10 python scripts/bench_guard.py
```

---

**重要**: このファイルが Golden Metrics Guard に関する唯一の信頼できる情報源(SSOT)です。変更時は必ずここを更新し、関連文書との同期を確保してください。