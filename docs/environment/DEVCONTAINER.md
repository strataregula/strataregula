# DevContainer 使用ガイド 🧰

VS Code の Dev Containers を使うと、**全員が同一の開発環境**で作業できます。

---

## 1) 前提
- VS Code + Dev Containers 拡張
- Docker（Desktop など）

---

## 2) 使い方
1. リポジトリを開く  
2. 「**Reopen in Container**」を選択  
3. 初回ビルド後、ターミナルで:
   ```bash
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   pytest -q
   ```

> venv を**コンテナ内**で作ることで、依存をホストから分離できます。

---

## 3) よく使う操作

- **再ビルド（設定変更後）**: Command Palette → *Dev Containers: Rebuild Container*
- **ホストへ戻る**: Command Palette → *Reopen Folder Locally*

---

## 4) 設定ポイント（例）

`.devcontainer/devcontainer.json` の代表的オプション：

- `remoteUser` / `containerUser`: 権限問題がある場合にホスト UID/GID と合わせる
- `features`: `ghcr.io/devcontainers/...` 由来の追加ツール
- `mounts`/`workspaceMount`: 追加ボリュームが必要な場合に設定
- `postCreateCommand`: 依存一括インストールを自動化（例：`pip install -r requirements.txt`）

---

## 5) Proxy / ネットワーク

企業ネットワークでは以下が必要になる場合があります：

```jsonc
// devcontainer.json 内で
"containerEnv": {
  "HTTP_PROXY": "http://proxy.example:8080",
  "HTTPS_PROXY": "http://proxy.example:8080",
  "NO_PROXY": "localhost,127.0.0.1"
}
```

- `ghcr.io` / `docker.io` へのアクセスがブロックされるとビルド失敗 → 管理者へ許可申請
- 証明書ピン留め環境では CA 証明書の追加が必要な場合あり

---

## 6) トラブル対応（簡易）

- **403 / 407（認証系）**: Proxy 設定を Docker と VS Code の両方に設定
- **権限エラー**: `remoteUser` を UID/GID に合わせる
- **ボリュームに書けない**: ホスト側ディレクトリの権限確認、`chown -R` で調整
- **パフォーマンス低下**: Windows/Mac では bind mount 負荷が高い → 不要大容量フォルダは `mounts` から除外

---

## 7) 推奨運用

- 「**Dockerfile/DevContainer は最小限**、Python 依存は `requirements.txt` に集約」
- `pre-commit` を導入して Lint/Format を自動化
- CI と **Python 3.11** を合わせる（GitHub Actions と一致）

---

## 8) チェックリスト

- [ ] Reopen in Container が成功する
- [ ] venv 作成 & `pip install -r requirements.txt` 完了
- [ ] `pytest -q` がグリーン
- [ ] `ruff check .` が 0 件