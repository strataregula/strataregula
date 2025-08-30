# 開発者必読資料 🚀

> 🔗 必読: [AGENTS.md](../AGENTS.md) – 自動化手順／Run Log ルール（Summary 非空・JST）

このプロジェクト（StrataRegula コアフレームワーク）に貢献する前に、以下の資料を必ず読んでください。

## 1. 開発ルール
- [CONTRIBUTING.md](../CONTRIBUTING.md)  
  → PR ルール（1PR=1目的）、Runログ Summary 必須など
- **基本ポリシー**: 1 PR = 1 目的、CI は常にグリーン維持

## 2. 実行・テスト方法
- `pytest -q` / `pytest --cov=src --cov-report=term-missing:skip-covered` でカバレッジ測定
- **品質チェック**: `ruff check .` / `ruff format .` / `mypy src`
- **カバレッジ要求**: 85%以上必須

## 3. Runログ文化
- Runログは `docs/run/*.md` に保存  
- [docs/run/_TEMPLATE.md](run/_TEMPLATE.md) に従い記入  
- **Summary は必ず非空** - 作業内容・意図・次のアクションを明記

## 4. StrataRegula コアフレームワーク固有情報
- **CLI**: `python -m strataregula.cli compile config.yaml`
- **プラグインアーキテクチャ**: 拡張可能なプラグインシステム
- **設定コンパイラ**: YAML設定の効率的なコンパイル・検証
- **階層処理**: 設定階層の統合・マージ機能

## 5. プラグイン連携
- プラグインエントリーポイント: `strataregula.plugins.*`
- DOE Runner プラグイン: `strataregula.plugins.doe_runner`
- カスタムプラグイン開発: [developer-guide/PLUGIN_QUICKSTART.md](developer-guide/PLUGIN_QUICKSTART.md)

## 6. DevContainer 利用
- VS Code で "Reopen in Container" → 自動的に本資料が表示されます
- Python 3.11 / pytest / ruff / mypy 統一環境
- **セットアップ**: `pip install -e ".[dev]"` で開発依存関係インストール

## よく使うコマンド
```bash
# テスト実行
pytest -q
pytest --cov=src --cov-report=term-missing:skip-covered

# コード品質チェック  
ruff check .
ruff format .
mypy src

# CLI実行例
python -m strataregula.cli compile config.yaml
python -m strataregula.cli --help

# ベンチマーク実行
python scripts/bench_guard.py
```

## 7. 重要な開発ガイドライン
- **プラグインアーキテクチャ**: 拡張性を重視した設計
- **設定処理**: 効率的なYAML解析・コンパイル
- **タイムゾーン**: ログは必ずJST記録  
- **終了コード**: 0=成功, 1=一般エラー, 2=設定エラー
- **pre-commit**: `pre-commit run --all-files` で品質確認

## 8. コアフレームワーク構成
- **CLI**: `strataregula.cli` - コマンドライン インターフェース
- **コア**: `strataregula.core` - コンパイラ・設定処理エンジン
- **プラグイン**: `strataregula.plugins` - 拡張システム
- **階層処理**: `strataregula.hierarchy` - 設定階層管理
- **ゴールデンメトリクス**: パフォーマンス回帰検知

## 9. 関連プロジェクト
- **DOE Runner**: `strataregula-doe-runner` - 実験設計・実行プラグイン
- **Restaurant Config**: `sr-restaurant-config` - レストラン設定管理
- **World Simulation**: 統合シミュレーション環境

## 困ったときは
- [docs/getting-started/](getting-started/) - 基本的な使い方
- [docs/developer-guide/](developer-guide/) - 開発者向け詳細ガイド
- [docs/api-reference/](api-reference/) - API リファレンス
- **Issues**: GitHub Issues でバグ報告・機能要求