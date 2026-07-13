# CURRENT_TASK.md

## Task ID

TASK-D001

## 目的

Wikimedia Enterprise認証情報の環境変数名・読取・検証を1箇所へ固定し、`.env.example`で必要な環境変数名を明示する。値そのものはリポジトリへ書かない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D001を読んだ
- [x] `CONFIG_REFERENCE.md` 18節の環境変数一覧を確認した
- [x] `ARCHITECTURE.md` 9.3の認証優先順位を確認した
- [x] 未コミットだったTASK-A001〜C007実装一式をコミットした

## 変更予定ファイル

- `src/wikiepwing/secrets.py`
- `tests/test_secrets.py`
- `.env.example`
- `.gitignore`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_secrets.py
make check
git diff --check
```

## 完了条件

- [x] `WME_USERNAME`/`WME_PASSWORD`/`WME_ACCESS_TOKEN`/`WME_REFRESH_TOKEN`の名前が1箇所で定義される
- [x] 値は環境変数からのみ読み、DBやファイルへ永続化しない
- [x] username/passwordは対で必須、片方だけの設定を拒否する
- [x] 空文字は未設定として扱い、空白のみ・前後空白・制御文字は拒否する
- [x] 構造化ログ redaction へ渡す値の集合を取得できる
- [x] `.env.example`に実値を含まない
- [x] `make check`が成功する

## 非対象

- access/refresh/login優先順位に基づく実際のHTTP認証処理（TASK-D002）
- token更新・有効期限判定（TASK-D002）
- 設定TOMLへの秘密情報混在

## 実施結果

- `src/wikiepwing/secrets.py`に環境変数名定数、`EnterpriseSecrets`データクラス、`load_enterprise_secrets`、`redaction_values()`を実装した。
- 空文字は未設定として扱い、前後空白・空白のみ・制御文字を含む値は`SecretError`として拒否した。
- `WME_USERNAME`と`WME_PASSWORD`は対でのみ許可し、片方だけの設定を拒否した。
- `.env.example`に4変数の名前とコメントのみを記載し、`.gitignore`へ`.env`を追加した。
- 11件のオフラインテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート113件、`git diff --check`が成功した。
- セッション冒頭で発見した未コミットのTASK-A001〜C007実装一式をユーザー確認のうえ1コミットへまとめた。
