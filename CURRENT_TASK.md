# CURRENT_TASK.md

## Task ID

TASK-S001

## 目的

`ARCHITECTURE.md` 26.3(「生成物にBUILD-INFO.jsonを添付します」)・28.1(「BUILD-INFOにWikimedia projectとsnapshot版を記載」)・`DATA_CONTRACTS.md` 12(build artifact contractでの`BUILD-INFO.json`の配置)を実装する。`SourceLock`(TASK-I001以前に確立済みのschema)が既に持つproject/snapshot情報を再利用し、profile・build時刻・software provenance(git commit・image digest、既存のstage manifest `software`フィールドと同じ形)を組み合わせたBUILD-INFO.jsonを構築・書き込む。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S001(依存: I001)を読んだ
- [x] `ARCHITECTURE.md` 26.3・28.1・`DATA_CONTRACTS.md` 3(Stage manifestの`software`フィールド: `git_commit`/`app_image_digest`/`toolchain_image_digest`)・12(build artifact contract)を再確認した
- [x] `SourceLock`(project/snapshot_identifier/snapshot_version/date_modified/acquirer)を再利用し、BUILD-INFO固有のfield抽出を重複実装しない方針にした

## 変更予定ファイル

- `src/wikiepwing/build_info.py`(新規: `SoftwareProvenance`, `build_build_info`, `write_build_info`)
- `tests/test_build_info.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_build_info.py
make check
git diff --check
```

## 完了条件

- [x] `build_build_info`が`SourceLock`から`project`/`snapshot_identifier`/`snapshot_version`/`snapshot_date_modified`を取り込み、`profile`・`built_at`・`software`(`git_commit`/`app_image_digest`/`toolchain_image_digest`)を含むJSON-serializableなdictを返す
- [x] `write_build_info`が原子的にJSONファイルを書き込む
- [x] `app_image_digest`/`toolchain_image_digest`が未知の場合は`None`を許容する
- [x] `make check`が成功する

## 非対象

- Logical content hash(TASK-S002)
- 実際のbuild pipelineへの統合配線(将来、EPWING generate/package stageから呼び出す形になる想定だが、本タスクはBUILD-INFOの構築・書き込み機能のみ)

## 実施結果

- `src/wikiepwing/build_info.py`(新規)に`SoftwareProvenance`・`build_build_info`・`write_build_info`を実装した。`SourceLock`から`project`/`snapshot_identifier`/`snapshot_version`/`snapshot_date_modified`を取り込み、`profile`・`built_at`・stage manifestと同じ形の`software`ブロックを組み合わせる。
- `tests/test_build_info.py`(新規8件)で、SourceLockフィールドの取り込み・software provenanceの反映・None digestの許容・naive datetimeの拒否・JSON serializable・原子的書き込み・ディレクトリ自動作成を確認した。
- `make check`(format-check/lint/mypy/pytest 1324件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- 実際のbuild pipelineへの統合配線(EPWING generate/package stageからの呼び出し)は対象外(BUILD-INFOの構築・書き込み機能のみ)。
