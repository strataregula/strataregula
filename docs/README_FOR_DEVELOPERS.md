# 開発前に必ず読む資料

## 基本ポリシー
- 1 PR = 1 目的
- Runログは `docs/run/*.md` に必ず追加（Summary / Intent / Next actions）
- CI は常にグリーン維持

## よく使うコマンド
```bash
pytest -q
pytest --cov=src --cov-report=term-missing:skip-covered
```

## 開発フロー
1. ブランチ作成: `git checkout -b feature/your-feature`
2. 実装・テスト
3. コミット・プッシュ
4. PR作成（このテンプレートのチェックリスト確認）

## ディレクトリ構成
- `src/` - メインソースコード
- `tests/` - テストコード
- `docs/` - ドキュメント
- `docs/run/` - 開発作業ログ

