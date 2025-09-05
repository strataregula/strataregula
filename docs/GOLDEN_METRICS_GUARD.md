# Golden Metrics Guard 📊

**狙い**：サービス時間解決（service-time lookup）の性能回帰を **即検知** し、リリース前に止める。

---

## 1) 測定対象とモード
- スクリプト：`scripts/bench_service_time.py`
- 比較モード：
  - `fnmatch`（旧来ベースライン）
  - `compiled_tree`（ツリー探索）
  - `direct_map`（O(1) 直マップ）

---

## 2) 合格基準（門番）
- **必須**：`direct_map / fnmatch ≥ 50x`
- **安定性**：直近の計測と比較し **±10% 以内** を目安
- 未達 → **PR/リリースをブロック**（原因分析・Issue化・根拠付き例外運用）

---

## 3) 実行方法
```bash
python scripts/bench_service_time.py
```

出力例：
```
fnmatch:      avg=0.350s ops/sec=285,393
compiled_tree:avg=0.035s ops/sec=2,830,207
direct_map:   avg=0.0059s ops/sec=16,865,586
direct_map/fnmatch: 59.1x
compiled_tree/fnmatch: 9.9x
```

---

## 4) CI 統合（例）

```yaml
- name: Golden Metrics
  run: |
    python scripts/bench_service_time.py > bench.txt
    python - <<'PY'
import re,sys,statistics,json
txt=open('bench.txt','r',encoding='utf-8').read()
m=re.search(r'direct_map/fnmatch:\s*([\d\.]+)x',txt)
ratio=float(m.group(1)) if m else 0.0
print(json.dumps({"ratio": ratio}))
sys.exit(0 if ratio>=50.0 else 1)
PY
```

---

## 5) 回帰発生時の対応フロー

1. **失敗の可視化**（CIログ・ベンチ出力）
2. **原因切り分け**：変更点（ルックアップ経路・データ構造・Python バージョン・依存）
3. **対処**：アルゴリズム/データ構造/メモリアロケーション最適化
4. **記録**：Issue に根拠・比較値・再現手順・修正 PR リンク
5. **例外運用**：やむを得ない場合のみ、期間限定で基準値を一時緩和（理由と期限を明記）

---

## 6) ベストプラクティス

- 単一指標でなく **比率（×）** を基準にする（環境差に強い）
- ベンチは 3 回以上の平均／分散を出す（既存スクリプトが対応）
- しきい値は **ドキュメントと CI の双方** に記述し、齟齬を出さない