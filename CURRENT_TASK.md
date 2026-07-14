# CURRENT_TASK.md

## Task ID

TASK-M004

## 目的

`ARCHITECTURE.md` 18.3(Gaiji registry: Unicode sequence/normalized sequence/width class/font source identifier/bitmap hash/assigned gaiji code/usage count、"同じ文字列は一度だけbitmap生成します")の永続化スキーマを実装する。既存の`ingest/database.py`・`model/database.py`・`reference/database.py`と同じ明示的migrationエンジンパターン(重複は既存の方針として許容されている)を`gaiji/database.py`として複製する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M004(依存: M002)を読んだ
- [x] `ARCHITECTURE.md` 18.3(Gaiji registryのフィールド一覧)を再確認した
- [x] `model/database.py`(migrationエンジンの既存実装、raw/reference/modelで重複が許容されている前例)を確認した
- [x] 既存3つのDBの`application_id`が4文字ASCIIコードの big-endian uint32("MODL"/"RAWD")であることに気づき、gaijiには"GAJI"(1195461193)を採用した

## 変更予定ファイル

- `migrations/gaiji/001_initial.sql`(新規: `schema_migrations`、`gaiji_registry`テーブル)
- `src/wikiepwing/gaiji/database.py`(新規: `connect_gaiji_database()`, `initialize_gaiji_database()`, `GaijiDatabaseError`)
- `tests/test_gaiji_database.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_database.py
make check
git diff --check
```

## 完了条件

- [x] `gaiji_registry`テーブルが18.3の全フィールド(unicode_sequence, normalized_sequence, width_class, font_source_identifier, bitmap_hash, assigned_gaiji_code, usage_count)を持つ
- [x] `normalized_sequence`にUNIQUE制約を持つ(同じ文字列は一度だけbitmap生成するという18.3の要件を、重複INSERTをDBレベルで拒否する形で保証する)
- [x] `initialize_gaiji_database`が既存3 DBと同じmigration適用・検証(integrity_check、履歴照合)を行う
- [x] `make check`が成功する

## 非対象

- 実際のbitmap生成(TASK-M005)・gaiji code割当ロジック(TASK-M006)
- FreePWING連携(TASK-M007)

## 実施結果

- `migrations/gaiji/001_initial.sql`に`schema_migrations`・`gaiji_registry`(18.3の全フィールド、`normalized_sequence`にUNIQUE制約、`width_class`/`usage_count`にCHECK制約)を実装した。`application_id`は"GAJI"のbig-endian uint32(1195461193)を採用した(既存3 DBが4文字ASCIIコードを使っていることに気づき、同じ慣習に従った)。
- `src/wikiepwing/gaiji/database.py`に`connect_gaiji_database()`・`initialize_gaiji_database()`・`GaijiDatabaseError`を実装した。`model/database.py`のmigrationエンジンをそのまま複製した(既存3 DBモジュール間の重複が許容されている前例に従った)。
- `tests/test_gaiji_database.py`(新規10件)で、初期migration・有効行のINSERT・重複normalized_sequenceの拒否・不正width_classの拒否・負のusage_countの拒否・migrationの冪等性とチェックサム不一致検出・失敗migrationのロールバック・不正migration集合(gap/symlink/oversized)の拒否を確認した。
- `make check`(format-check/lint/mypy/pytest 978件)と`git diff --check`が成功した。
