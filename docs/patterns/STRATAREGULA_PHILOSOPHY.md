# StrataRegula Philosophy — Speed Without Surprises

## 1) Hot path is O(1)
- ルックアップは **直マップ（hash/dict）**で解決する。
- ワイルドカードや複雑な照合は **生成時に解決**し、実行時に持ち込まない。
- 目標: `direct_map ≥ 50x fnmatch`（実測の安定にあわせ段階的に引き上げ）。

## 2) Fast / Slow の意味を固定
- **Fast** = 最適化（直マップ）、**Slow** = 旧来/非最適化（fnmatch/ツリー）。
- ベンチ/CIガードも同じ定義で評価する。

## 3) 計測で決める（Mean + P95）
- ガードは比率と P95 を監視。しきい値はまず現実的に、安定後に厳格化。
- 逆転時は CI ブロック、原因は「設計/実装/しきい値」に分類して是正する。

## 4) "足さない"運用
- ホットパスに分岐・正規表現・I/O を **足さない**。
- 重い処理は **precompile** に寄せ、実行時は生成物を読むだけにする。

## 5) 単一の真実源（SSOT）
- 本ドキュメントを唯一の定義書とし、README からリンクする。
- 期待値の変更は **ここ → CI設定 → 実装** の順に同期する。

## 6) API 形状（速度のための型）
- 推奨フロー: `precompile(raw_cfg) → query(view, params, CompiledConfig)`。
- `compile(raw_cfg)` は互換のため残すが **Deprecated**（次のメジャーで除去方針）。
