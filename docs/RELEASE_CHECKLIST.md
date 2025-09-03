# Release Checklist ✅

本プロジェクトのリリース前に **必ず** 実行・確認するチェックリストです。  
目的は「**品質保証・再現性の担保（Speed Without Surprises）**」。

---

## 0. 事前確認（作業ルール）
- [ ] `.development-rules.md` に準拠（1 PR = 1 目的、必要ファイル更新、レビュー観点）
- [ ] Runログ（`docs/run/*.md`）の **Summary 非空**（`CONTRIBUTING.md` 準拠）

---

## 1. バージョニング & 変更履歴
- [ ] `pyproject.toml` / `requirements.txt` / 他関連ファイルのバージョン更新
- [ ] `docs/changes/CHANGELOG.md` に該当バージョンのエントリ追加（要点・破壊的変更・移行手順）
- [ ] タグ作成／プッシュ  
  ```bash
  git tag vX.Y.Z && git push --tags
  ```

---

## 2. テスト & カバレッジ
- [ ] 全テスト成功  
  ```bash
  pytest -q
  ```
- [ ] カバレッジ ≥ **90%**  
  ```bash
  pytest --cov=src --cov-report=term-missing:skip-covered
  ```

---

## 3. コード品質（Lint/Format）
- [ ] Lint（ruff）エラー 0  
  ```bash
  ruff check .
  ```
- [ ] フォーマット適用（black/isort 等）／差分なし

---

## 4. パフォーマンス・ガード（Golden Metrics）
- [ ] Golden Bench 実行（`docs/GOLDEN_METRICS_GUARD.md` 準拠）  
  ```bash
  python scripts/bench_service_time.py
  ```
- [ ] 基準達成：`direct_map ≥ 50x fnmatch`、かつ変動 ±10% 以内

---

## 5. セキュリティ & 依存関係
- [ ] 依存脆弱性チェック（例）  
  ```bash
  pip install pip-audit && pip-audit
  ```
- [ ] 不要・重複依存の排除／ロック再生成の要否確認

---

## 6. ドキュメント & アーティファクト
- [ ] `README.md` / `CONTRIBUTING.md` / `docs/` の整合性確認
- [ ] Runログ更新（最新コミットの diff・実行コマンド・結果・次アクションを記録）
- [ ] 参考出力（オプション）  
  ```bash
  python scripts/bench_service_time.py > docs/changes/bench.last.txt
  ```

---

## 7. リリース手順
1. コミット & タグ
2. GitHub Release Draft（要点／既知の注意事項／導入手順）
3. TestPyPI → 本番 PyPI（必要な場合）
4. インストール再現性確認  
   ```bash
   pip install strataregula==X.Y.Z
   ```

---

## 付録：CI による自動ゲート例（抜粋）

```yaml
- name: Tests & Coverage
  run: |
    pytest -q
    pytest --cov=src --cov-report=term-missing:skip-covered

- name: Lint
  run: ruff check .

- name: Golden Bench
  run: |
    python scripts/bench_service_time.py > bench.txt
    python - <<'PY'
import re,sys
txt=open('bench.txt','r',encoding='utf-8').read()
m=re.search(r'direct_map/fnmatch:\s*([\d\.]+)x',txt)
val=float(m.group(1)) if m else 0.0
print('ratio',val)
sys.exit(0 if val>=50.0 else 1)
PY
```