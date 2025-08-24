# 📅 Strataregula マイルストーン計画

## 🎯 Phase 2: MVP完成 (目標: 2025年2月末)

**目標**: IaC階層マージ + JSON検証 + チャンクETL + 安全Transfer/Copy の4点セット完成

### 🔥 優先実装項目 (Critical Path)

#### 1. JSONPath処理完成 (FR-07)
**期限**: 2024年12月末  
**担当モジュール**: `strataregula/json_processor/`

- [ ] **Issue #TBD**: JSONPathProcessor基本実装
  - パス選択: `$.field`, `$..recursive`, `$[0:5]`
  - フィルタ: `$[?(@.field == "value")]`
  - 集約: `sum()`, `count()`, `avg()`, `min()`, `max()`
- [ ] **Issue #TBD**: JSONPathコマンドCLI統合
  - `sr jsonpath '$.users[?(@.active)]' --agg count`
  - ストリーミング対応 (stdin/pipe)
- [ ] **Issue #TBD**: JSONPath性能最適化
  - 大容量JSON対応 (>100MB)
  - メモリ効率化

#### 2. チャンク処理拡張 (FR-08)
**期限**: 2025年1月中旬  
**担当モジュール**: `strataregula/stream/`

- [ ] **Issue #TBD**: ChunkProcessor完全実装
  - 固定サイズ & 自動サイズチャンク
  - メモリ境界管理 (目標: <200MB常駐)  
  - バックプレッシャ対応
- [ ] **Issue #TBD**: StreamProcessor統合
  - チャンク処理を既存StreamProcessorに統合
  - 設定可能なチャンクサイズ (64KB - 1MB)
- [ ] **Issue #TBD**: 大容量ファイル性能テスト
  - 10GB NDJSONの処理テスト
  - メモリ使用量監視・測定

#### 3. CLI統合・ユーザビリティ改善
**期限**: 2025年1月下旬  
**担当モジュール**: `strataregula/cli/`

- [ ] **Issue #TBD**: validate コマンド実装
  - `sr validate data.json --schema schema.json --strict`
  - エラー詳細表示 (パス、期待値、実際値)
- [ ] **Issue #TBD**: convert コマンド実装  
  - `sr convert config.yaml --to json --output config.json`
  - YAML ↔ JSON双方向変換
- [ ] **Issue #TBD**: エラーメッセージ改善
  - did-you-mean 候補表示
  - 終了コード標準化

#### 4. Transfer/Copyサブシステム (FR-16)
**期限**: 2025年2月中旬  
**担当モジュール**: `strataregula/transfer/`

- [ ] **Issue #TBD**: CopyEngine基盤実装
  - Plan/Apply処理フロー
  - ルールマッチング (JSONPath/labels)
  - イベント発火 (copy:start/before_object/after_object)
- [ ] **Issue #TBD**: DeepCopyVisitor実装
  - deep/shallow/link/cow モード
  - 循環参照検出 (visited_ids set)
  - 最大深度制限 (デフォルト64)
  - 型制限・エラーハンドリング
- [ ] **Issue #TBD**: 基本Transforms実装
  - exclude/mask/rename/map/default
  - マスクスタイル: hash/stars/last4
  - ID再割当 (prefix/suffix付与)
- [ ] **Issue #TBD**: Transfer CLI統合
  - `sr transfer plan/apply` コマンド
  - ポリシーファイル読み込み (YAML)
  - プロビナンス・差分出力
- [ ] **Issue #TBD**: ストリーミング対応
  - チャンク境界でのオブジェクト分割
  - 低メモリ処理 (O(チャンク) メモリ)
  - NDJSON入出力対応

### 🎯 MVP受け入れテスト

#### AC-01: 再現性テスト
```bash
# 同一入力・パイプで同一出力確認
sr merge base.yaml prod.yaml --seed 12345 > out1.yaml  
sr merge base.yaml prod.yaml --seed 12345 > out2.yaml
diff out1.yaml out2.yaml  # 差分なし
```

#### AC-02: 大容量処理テスト  
```bash
# 10GB NDJSON を <200MB メモリで処理
cat 10gb-logs.ndjson | sr jsonpath '$.events[*].timestamp' --memory-limit 200MB
```

#### AC-03: 階層マージ衝突検出テスト
```bash
# 衝突発生時の詳細レポート確認
sr merge base.yaml conflict.yaml --strategy merge --report conflicts.json
# conflicts.json に衝突キー、勝者・敗者、由来ファイルが記載される
```

#### AC-04: Transfer/Copy安全性テスト
```bash
# 循環参照・深度制限テスト
sr transfer apply circular_ref.json --policy deep_copy.yaml --dry-run
# エラー: "Circular reference detected at $.user.manager.user"

# PII マスキング・ID再割当テスト
sr transfer apply users.json --policy secure_copy.yaml --out masked_users.json
# 出力: email="hash:a1b2c3...", id="dev_12345"
```

#### AC-05: Transfer/Copy再現性テスト
```bash
# 同一ルール・入力で同一出力確認
sr transfer apply data.json --policy copy.yaml --seed 12345 > out1.json
sr transfer apply data.json --policy copy.yaml --seed 12345 > out2.json  
diff out1.json out2.json  # 差分なし（マスキング・ID再割当含む）
```

## 📊 Phase 3: 拡張機能 (目標: 2025年2-3月)

### 🌐 プロトコル対応 (FR-09)
- [ ] WebSocket双方向通信
- [ ] HTTP GET/POST入力ソース  
- [ ] Server-Sent Events (SSE)

### 🔄 フォーマット拡張 (FR-07)
- [ ] CSV ↔ JSON変換
- [ ] XML ↔ JSON変換  
- [ ] CBOR出力サポート

### ⚡ パフォーマンス最適化
- [ ] 並列処理対応
- [ ] キャッシュ機能
- [ ] プロファイル機能強化

## 🧪 Phase 4: 品質・運用強化 (目標: 2025年4月)

### 🧪 テスト強化
- [ ] プロパティベーステスト  
- [ ] 大規模ベンチマークテスト
- [ ] CI/CD統合テスト

### 📚 ドキュメント完成
- [ ] 完全なAPI仕様書
- [ ] ユースケース別チュートリアル
- [ ] 運用ベストプラクティス

### 🔒 セキュリティ・監査
- [ ] セキュリティ監査
- [ ] 脆弱性テスト
- [ ] コンプライアンス検証

## 📈 リリース計画

| バージョン | 目標日 | 主要機能 | ステータス |
|-----------|--------|---------|-----------|
| v0.2.0-alpha | 2024年12月末 | JSONPath基本実装 | 🔄 進行中 |
| v0.2.0-beta | 2025年1月中旬 | チャンク処理完成 | ⏳ 予定 |
| v0.2.0-rc | 2025年2月上旬 | Transfer/Copy基本実装 | ⏳ 予定 |
| v0.2.0 | 2025年2月末 | MVP完成 (4点セット) | ⏳ 予定 |
| v0.3.0 | 2025年3月末 | プロトコル対応 | ⏳ 予定 |
| v1.0.0 | 2025年4月末 | 品質・運用完成 | ⏳ 予定 |

## 🚀 次の行動項目

### 今週 (2024年12月第4週)
1. **JSONPathProcessor** の基本実装開始
2. **validate/convert CLI** の設計・実装  
3. **大容量テストデータ** の準備

### 来週以降
1. **チャンク処理** の詳細設計  
2. **Transfer/Copyサブシステム** の実装開始
   - CopyEngine基盤・DeepCopyVisitor
   - ルールDSLパーサー・マッチング
3. **WebSocket対応** の調査・設計
4. **CI/CD** 環境の改善

## 📝 リスク・課題

### 🚨 高リスク項目
- **JSONPath仕様の範囲**: どこまで対応するか要決定
- **メモリ効率**: 10GB処理で200MB制約は技術的に挑戦的
- **既存コードとの統合**: StreamProcessorへのチャンク統合の複雑さ
- **Transfer/Copy複雑性**: 循環参照検出・型制限・変換の組み合わせ爆発
- **Transfer/Copy性能**: 大容量データの深いコピーでの性能劣化リスク
- **ルールDSLの設計**: ユーザビリティと機能性のバランス

### 💡 対策案
- JSONPath: 最小機能セット → 段階的拡張
- メモリ: プロトタイプでメモリ使用量検証
- 統合: 既存APIの後方互換性維持
- Transfer/Copy: 最小核（exclude/mask/rename）→ 段階拡張
- 性能: shallow copy をデフォルト、deep copy は明示的指定
- ルールDSL: 既存JSONPath + 最小語彙から開始

---

**最終更新**: 2024年12月  
**管理責任者**: 開発チーム  
**レビューサイクル**: 週次