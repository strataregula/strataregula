# Runログテンプレート

**実行日時 (JST)**: [YYYY-MM-DD HH:MM]  
**タスク**: [作業内容の1行説明]

## Summary
[作業の概要・目的を記述。空にしない。]

## Intent
[なぜこの作業を行ったかの意図・背景]

## Commands
```bash
# 実行したコマンド例
pytest -q
pytest --cov=src --cov-report=term-missing:skip-covered
python -m strataregula.cli --help
make test
make build
```

## Results
- [結果の要点]
- [発生した問題と解決方法]
- [成功/失敗の判定]

## Artifacts
- [生成されたファイル・アウトプット]
- [更新されたドキュメント]
- [作成されたPR・イシュー]

## Next actions
- [次に実行すべきアクション]
- [今後の課題・改善点]
- [他のリポジトリへの展開予定]

---

## Notes
- **Summary必須**: 空の Summary は禁止
- **JST時刻**: 日本標準時で記録
- **コマンド記録**: 再現可能性のため実際のコマンドを記載
- **1PR=1目的**: ログも単一の目的に集中
- **コアフレームワーク**: StrataRegula コアフレームワーク開発用