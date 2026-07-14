# CURRENT_TASK.md

## Task ID

TASK-F007

## 目的

`DATA_CONTRACTS.md` 5節の"model.sqlite3 schema draft"を実マイグレーションとして実装し、`migrations/raw/001_initial.sql` + `src/wikiepwing/ingest/database.py`と同じ既存パターンをmodel.sqlite3向けに再現する(`src/wikiepwing/model/database.py`)。本タスクはschemaと接続/マイグレーション適用モジュールまでを対象とし、実際の書き込みRepository(TASK-G012が`F007-F008,G011`に依存して実装)は対象外とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F007(依存: F006)とTASK-G012(依存: F007-F008,G011、"Normalize command and model DB write")を読んだ。model DB書き込みの実装はG012側であることを確認した
- [x] `DATA_CONTRACTS.md` 5節(model.sqlite3 schema draft: articles/links/media_references/diagnostics)・6節(Article JSON contract)を確認した
- [x] `ARCHITECTURE.md`のpipeline図・§20.1 manifest例(`model.sqlite3`の`logical_hash`)・§22.3 disk見積りを確認した
- [x] `migrations/raw/001_initial.sql`と`src/wikiepwing/ingest/database.py`(`RawDatabaseError`/`Migration`/`connect_raw_database`/`initialize_raw_database`)を実装パターンとして踏襲する

## 変更予定ファイル

- `migrations/model/001_initial.sql`
- `src/wikiepwing/model/database.py`
- `tests/test_model_database.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_database.py
make check
git diff --check
```

## 完了条件

- [x] `migrations/model/001_initial.sql`が`schema_migrations`/`articles`/`links`/`media_references`/`diagnostics`/`metadata`テーブルを`DATA_CONTRACTS.md` 5節通りに定義する(STRICT、`WITHOUT ROWID, STRICT`、CHECK制約、`PRAGMA application_id`)
- [x] `src/wikiepwing/model/database.py`が`connect_model_database`/`initialize_model_database`/`ModelDatabaseError`/`Migration`を提供し、`ingest/database.py`と同じ安全策(busy_timeout, foreign_keys, integrity_check, foreign_key_check, migration sha256検証, versionの連番検証)を持つ
- [x] 初期化後に`PRAGMA integrity_check`/`PRAGMA foreign_key_check`が成功する
- [x] 2回目の初期化(既に適用済み)がidempotentに成功する
- [x] マイグレーションのchecksum不一致・versionの欠番・シンボリックリンク・サイズ超過を拒否する
- [x] `make check`が成功する

## 非対象

- Model repository(実際のarticle書き込み、TASK-G012で実装)
- Logical hash計算(TASK-F008)
- normalize orchestration(Epic G)

## 実施結果

- `migrations/model/001_initial.sql`を新規作成した(schema_migrations/articles/links/media_references/diagnostics/metadata、STRICT/WITHOUT ROWID, STRICT/CHECK制約、`PRAGMA application_id = 1297040460`)。
- `src/wikiepwing/model/database.py`に`ModelDatabaseError`/`Migration`/`connect_model_database`/`initialize_model_database`を実装した。
- `tests/test_model_database.py`に7件のテストを追加。
- `uv run pytest tests/test_model_database.py`: 7 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート478件)すべて成功。
- `git diff --check`: 問題なし。
- `docker/app.Dockerfile`の`COPY migrations ./migrations`により`migrations/model/`は変更不要で自動的に含まれることを確認した。
- `TASKS.md`(F007チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-F008 Logical hash。
