# CURRENT_TASK.md

## Task ID

TASK-I003

## 目的

`ARCHITECTURE.md` 7.2(Orchestratorの責務: "lock取得")を実装する。manifestの`status`確認だけでは真の同時実行を防げない(read-then-writeの間に競合が起きうる)ため、`fcntl.flock`によるOS-levelのadvisory lockを実装し、同一stageの同時実行を確実に防ぐ。本プロジェクトはDocker/Linuxコンテナ上でのみ実行される前提(既存のtoolchain Dockerイメージ運用と整合)のため、POSIX専用の`fcntl`を用いる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-I003(依存: I001)を読んだ
- [x] `ARCHITECTURE.md` 7.2(Orchestratorの責務一覧、"lock取得")を確認した
- [x] manifestベースの"running"status確認(既存の`read_manifest_status`)が実際のmutexではないことを確認し、本タスクで補完する設計とした

## 変更予定ファイル

- `src/wikiepwing/pipeline/stage_lock.py`
- `tests/test_pipeline_stage_lock.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_pipeline_stage_lock.py
make check
git diff --check
```

## 完了条件

- [x] `acquire_stage_lock(lock_path)`がcontext managerとして`fcntl.flock`による排他ロックを取得する
- [x] 同一lock pathに対する2つ目の取得試行が`StageLockError`を送出する(同一プロセス内での再入も含む)
- [x] context manager終了時にlockが解放され、以降の取得が成功する
- [x] 例外発生時もlockが確実に解放される
- [x] lock fileに取得プロセスのPIDが記録される
- [x] `make check`が成功する

## 非対象

- Atomic stage output(TASK-I004)
- Resume判定・`--from-stage`/`--force-stage`(TASK-I005-I006)
- 既存のorchestrate 3モジュールへのlock統合(将来のtaskで結線する)

## 実施結果

- `src/wikiepwing/pipeline/stage_lock.py`に`acquire_stage_lock`/`StageLockError`を実装した。
- `tests/test_pipeline_stage_lock.py`に6件のテストを追加。
- `uv run pytest tests/test_pipeline_stage_lock.py`: 6 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート749件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(I003チェック)、`LOG.md`(新規エントリ)を更新した。
- 既存orchestrateモジュールへの実際のlock統合は将来のtaskに委ねた。
- 次タスク: TASK-I004 Atomic stage output。
