# CURRENT_TASK.md

## Task ID

TASK-E001

## 目的

`raw.sqlite3`のSQL migrationと、それを安全に適用・検証・接続するmoduleを実装する。`DATA_CONTRACTS.md` 4節のschema draft(articles/redirects/categories/templates/licenses/article_licenses/main_images/ingest_duplicates/diagnostics)を正本として使う。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E001を読んだ(依存: A003, D010、いずれも完了済み)
- [x] `ARCHITECTURE.md` 10.3(`RawArticle`)・10.4(raw.sqlite3主要テーブル)を確認した
- [x] `DATA_CONTRACTS.md` 4節のraw.sqlite3 schema draftを正本として確認した
- [x] `migrations/reference/001_initial.sql`と`src/wikiepwing/reference/database.py`の既存migration engineパターン(schema_migrations追跡、STRICT table、PRAGMA application_id、integrity_check/foreign_key_check)を確認した
- [x] `tests/test_reference_database.py`のテスト構成を確認した

## 変更予定ファイル

- `migrations/raw/001_initial.sql`
- `src/wikiepwing/ingest/__init__.py`
- `src/wikiepwing/ingest/database.py`
- `tests/test_raw_database.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_raw_database.py
make check
git diff --check
```

## 完了条件

- [x] `migrations/raw/001_initial.sql`が`DATA_CONTRACTS.md` 4節のtableをすべてSTRICT/適切なCHECK・FOREIGN KEYで作成する
- [x] `schema_migrations`でmigration履歴を追跡し、checksum不一致・欠番・symlink・サイズ超過を拒否する
- [x] migration適用は失敗時にロールバックし、部分適用済みschemaを残さない
- [x] `connect_raw_database`/`initialize_raw_database`が`PRAGMA foreign_keys`/`busy_timeout`を設定し、適用後に`integrity_check`/`foreign_key_check`を検証する
- [x] `docker/app.Dockerfile`の`COPY migrations ./migrations`で`migrations/raw`も自動的に含まれることを確認する
- [x] `make check`が成功する

## 非対象

- 実際のNDJSON parsing・record挿入・重複解決ロジック(TASK-E002以降)
- zstd圧縮(TASK-E002)
- ingestコマンド自体(TASK-E008)

## 実施結果

- `migrations/raw/001_initial.sql`に`DATA_CONTRACTS.md` 4節のtable(articles/redirects/categories/templates/licenses/article_licenses/main_images/ingest_duplicates/diagnostics/metadata)を作成した。全tableをSTRICTとし(`WITHOUT ROWID`とも組み合わせ)、draftにない長さCHECK制約を`migrations/reference`の慣例に合わせて追加した。
- `PRAGMA application_id = 1380013892`(ASCII "RAWD")を設定し、reference DBと区別できるようにした。
- `src/wikiepwing/ingest/database.py`に`connect_raw_database`/`initialize_raw_database`/`RawDatabaseError`を実装した。`reference/database.py`と同じmigration engineパターン(schema_migrations追跡、checksum検証、失敗時rollback、symlink/欠番/サイズ超過拒否、integrity_check/foreign_key_check)を踏襲した。
- `tests/test_raw_database.py`に8件(`test_reference_database.py`と同構成)のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート274件、`git diff --check`が成功した。
- `docker/app.Dockerfile`の`COPY migrations ./migrations`はディレクトリ全体をコピーするため、`migrations/raw`も変更なく自動的に含まれることを確認した。

**判断・注意点**

- `reference/database.py`と`ingest/database.py`はmigration engineロジックがほぼ同一だが、既存の動作確認済みmoduleへの影響を避けるため共通化はせず、意図的に別moduleとして実装した(重複は認識済み。将来model/rendered/index dbが増える際に共通化を検討する)。
- `DATA_CONTRACTS.md`のdraftでは`WITHOUT ROWID`のみのtable(redirects/categories/templates/article_licenses)にSTRICTを明記していないが、SQLiteは両者を組み合わせ可能であり、reference DBの全STRICT方針との一貫性のため追加した。挙動に影響しない強化のため契約違反とはみなさない。
