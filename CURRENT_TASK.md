# CURRENT_TASK.md

## Task ID

TASK-D004

## 目的

`source.lock.json`のJSON schemaと、それを構築・正準直列化・往復検証するモデルを実装する。chunk単位ダウンロード(ADR-016)を前提にした`files`配列を持つ。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D004を読んだ
- [x] `DATA_CONTRACTS.md` 2節のsource lock契約(本タスクでchunk対応へ更新済み)を確認した
- [x] `DECISIONS.md` ADR-016(chunk単位download)を確認した
- [x] `schemas/doctor-report.schema.json`とその検証パターン(`tests/test_doctor.py`)を確認した
- [x] TASK-D003の`ResolvedSnapshot`(`snapshot_identifier`/`version_identifier`/`chunk_identifiers`/`metadata_response_sha256`)を確認した

## 変更予定ファイル

- `schemas/source-lock.schema.json`
- `src/wikiepwing/source/lockfile.py`
- `tests/test_source_lockfile.py`
- `DATA_CONTRACTS.md`(完了)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_source_lockfile.py
make check
git diff --check
```

## 完了条件

- [x] `SourceLock`データモデルが`DATA_CONTRACTS.md`の必須フィールドを持つ
- [x] `files`は1 chunkにつき1エントリ、`chunk_identifier`重複拒否、相対path・`..`拒否
- [x] `snapshot_version`に`"latest"`を拒否する
- [x] `sha256`・`metadata_response_sha256`は64桁小文字hexのみ許可する
- [x] timestampはUTC(RFC3339)のみ許可する
- [x] 正準直列化(`canonical_json`)が決定的(同じ入力→同じbytes)である
- [x] 直列化したJSONを再度parseして同じモデルへ戻せる(round-trip)
- [x] JSON SchemaでJSON構造を検証できる(`tests/test_source_lockfile.py`から`jsonschema`で検証)
- [x] `make check`が成功する

## 非対象

- 実際のdownload・atomic rename(TASK-D005)
- `acquire`コマンドからのファイル書き込み(TASK-D007)
- git_commitの実行環境からの自動取得(呼び出し側が渡す)

## 実施結果

- `schemas/source-lock.schema.json`を`DATA_CONTRACTS.md`(本タスクで更新済み)に沿って作成した。`files`の`chunk_identifier`必須、`sha256`/`metadata_response_sha256`は64桁小文字hex、`snapshot_version`に`"latest"`を拒否するJSON Schemaを定義した。
- `src/wikiepwing/source/lockfile.py`に`SourceLockFile`/`SourceLockAcquirer`/`SourceLock`データクラス、`build_source_lock`(検証付き構築)、`canonical_json`(決定的直列化)、`parse_source_lock`(往復検証)を実装した。
- `files`はchunk_identifier重複・relative_path重複・絶対path・`.`/`..`セグメントを拒否し、chunk単位ダウンロード(ADR-016)を前提にした。
- timestampはtimezone-aware必須とし、`canonical_json`はUTCへ正規化して秒精度のRFC3339(`...Z`)へ固定した(non-UTCタイムゾーンの入力も正しく変換されることをテストで確認)。
- `DATA_CONTRACTS.md`のsource lock契約例を単一ファイルからchunk対応(`chunk_identifier`付き)へ更新した。
- `tests/test_source_lockfile.py`に22件のテスト(schema検証、canonical直列化の決定性、round-trip、各種不正値拒否)を追加した。
- format-check、ruff lint、mypy strict、標準スイート180件、`git diff --check`が成功した。

**判断・注意点**

- 実際のfile書き込み・atomic replaceはTASK-D007(acquireコマンド)の対象とし、本タスクはモデルと直列化/parseのみに限定した。
- `git_commit`はacquirer実行環境からの自動取得を行わず、呼び出し側が渡す前提とした(自動取得はacquireコマンド側の責務)。
