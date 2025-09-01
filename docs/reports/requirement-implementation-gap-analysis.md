# 要件vs実装ギャップ分析レポート

**作成日**: 2025-08-31  
**分析対象**: Config Compiler関連実装  
**起因**: 元指示とGolden Metrics Guard実装の乖離

## 📋 元指示の要件

### A. config_compiler の O(1) 直マップ化
- ✅ **実装状況**: `strataregula/core/config_compiler.py`で部分実装
- ❌ **ギャップ**: `src/compiled_config.py`が未生成
- ❌ **ギャップ**: `get_service_time(name:str)->float`未実装

### B. cli_run の自動コンパイル導線
- ❓ **要調査**: `--auto-compile`フラグの実装状況
- ❓ **要調査**: 自動生成ロジックの実装状況

### C. ベンチマーク追加
- ❌ **未実装**: `scripts/bench_service_time.py`が存在しない
- ❌ **未実装**: 3モード比較ベンチマーク
- ❌ **未実装**: 「目標: direct_map >= 50x fnmatch」の検証

### D. テスト追加
- ❓ **部分実装**: config_compilerのテストは存在
- ❌ **未確認**: 指定された具体的テストファイル

### E. ドキュメント反映
- ❓ **要調査**: README更新状況

## 🔍 Golden Metrics Guard問題の根本原因

### API不整合
```python
# bench_guard.pyの期待（❌存在しない）
result = compiler.compile_traffic(fake_traffic_data)

# 実際の実装（✅存在する）  
result = compiler.compile_traffic_config(traffic_file, prefectures_file, output_file)
```

### 処理フロー
1. `bench_guard.py` → `compile_traffic()` 呼び出し
2. **Exception発生**（メソッド未存在）
3. フォールバック → `config_compile_slow()` 実行
4. 結果: 重い「Fast」処理 vs 軽い「Slow」モック
5. **比率逆転** (0.0007倍 vs 期待50倍)

## 📊 実装vs要件マッピング

### 実装済み項目
- ✅ `ConfigCompiler`クラス
- ✅ `compile_traffic_config()`メソッド
- ✅ Template-based code generation
- ✅ Plugin system integration
- ✅ Memory-efficient compilation

### 未実装/不一致項目
- ❌ `compile_traffic()`メソッド（bench_guard用）
- ❌ `src/compiled_config.py`自動生成
- ❌ `DIRECT_MAPPING: Dict[str, float]`
- ❌ `get_service_time()`関数
- ❌ 50倍速化ベンチマーク検証

## 💡 修正アプローチ

### アプローチA: API整合
```python
class ConfigCompiler:
    def compile_traffic(self, traffic_data: dict) -> dict:
        """bench_guard.py用の軽量API"""
        # 軽量な直マップ処理を実装
        return self._fast_lookup(traffic_data)
```

### アプローチB: ベンチマーク修正
```python
def config_compile_fast(configs, compiler_class):
    """軽量な直マップ実装"""
    return direct_map_lookup(configs)
    
def config_compile_slow(configs):
    """従来のfnmatch実装"""  
    return fnmatch_based_lookup(configs)
```

### アプローチC: 要件完全実装
- `scripts/bench_service_time.py`作成
- `src/compiled_config.py`自動生成
- `get_service_time()`実装
- 50倍速化の実測検証

## 🎯 推奨対応順序

### 🚨 緊急対応（Golden Metrics Guard修正）
1. **APIエラー修正**: `compile_traffic()`メソッド追加
2. **ベンチマーク正常化**: Fast/Slow処理の適切な実装
3. **閾値調整**: 現実的な期待値設定

### 📋 中期対応（要件充足）
1. **missing deliverables実装**: 
   - `scripts/bench_service_time.py`
   - `src/compiled_config.py`生成ロジック
   - `get_service_time()`関数
2. **性能検証**: 50倍速化の実測確認
3. **テスト拡充**: 指定テストケース追加

### 📚 長期対応（品質向上）
1. **ドキュメント整備**: README、API文書更新
2. **CI統合**: ベンチマーク結果の継続監視
3. **エラーハンドリング**: 堅牢性向上

## ⚠️ リスク評価

### 高リスク
- **開発ブロック**: 現在全PRが失敗状態
- **設計意図不明**: 元指示との乖離が拡大

### 中リスク
- **性能期待**: 50倍速化が未検証
- **API安定性**: 後方互換性の考慮不足

### 低リスク
- **機能追加**: 既存機能への影響は限定的

## 📞 推奨アクション

### 即座実行
1. ✅ **本分析レポート**を設計者に共有
2. 🔧 **緊急修正**でCI復旧
3. 📋 **要件再確認**と実装方針決定

### 後続実行
1. 🏗️ **missing deliverables**の段階的実装
2. 🧪 **性能ベンチマーク**の体系的実施
3. 📖 **ドキュメント更新**と知識共有

---

**結論**: Golden Metrics Guardの問題は要件と実装の不一致から発生。APIエラーの修正で即座解決可能だが、根本的には元指示の完全実装が必要。