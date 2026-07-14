# CURRENT_TASK.md

## Task ID

TASK-E010

## 目的

ingest実行が中断された場合の検出("running"のまま残るmanifest)と、再実行時の安全性(rerun semantics)を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E010を読んだ(依存: E008,E009完了済み)
- [x] `DATA_CONTRACTS.md` 3節のmanifest `status` enum(running/complete/failed/interrupted/invalid、「complete以外をcache reuseしてはいけない」)を確認した
- [x] TASK-E008の`run_ingest`/`IngestManifest`実装を確認した
- [x] EPIC I(Pipeline resume)がstage lock・resume判定の汎用実装を担当することを`TASKS.md`で確認し、本タスクはingest stage専用の最小実装に留めることとした

## 変更予定ファイル

- `src/wikiepwing/ingest/orchestrate.py`
- `tests/test_ingest_orchestrate.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_ingest_orchestrate.py
make check
git diff --check
```

## 完了条件

- [x] `run_ingest`開始直後に`status="running"`のmanifestをatomic書込し、成功時"complete"・例外時"failed"で必ず上書きする(例外は再raiseする)
- [x] 既存manifestが`status="running"`のまま残っている場合、既定では新規実行を拒否し明確なエラーを返す(前回実行が中断された可能性を示す)
- [x] `force=True`で明示的にrunning状態を上書きして再実行できる
- [x] articles tableへの書込はrevision/hashに基づき冪等(同じ内容の再実行は`IGNORED_IDENTICAL_DUPLICATE`として安全に無視される)ことを既存の重複解決ロジックにより確認する
- [x] diagnostics/ingest_duplicates tableは現schemaでrun単位追跡fieldを持たないため、再実行時に監査ログ行が重複しうることを既知の制約として明記する
- [x] `make check`が成功する

## 非対象

- 汎用stage manifest・stage lock・`--from-stage`/`--force-stage`(EPIC I)
- diagnostics/ingest_duplicatesへのrun_id列追加(将来のschema変更、EPIC I以降で検討)

## 実施結果

- `run_ingest`を、開始直後に`status="running"`のmanifestをatomic書込し、成功時"complete"・例外時"failed"を`finally`で必ず書き込んで例外を再raiseする構造へ変更した。
- `read_manifest_status(manifest_path)`を追加した。fileが無ければNone、既存fileが`status="running"`のまま残っていれば`force=True`が無い限り`IngestError`で新規実行を拒否する。壊れたmanifest(JSON不正・status欠落)も`IngestError`として明確に拒否する(DATA_CONTRACTS.mdの"invalid" status概念に対応)。
- `run_ingest`/CLIへ`force: bool = False`引数を追加し、`wikiepwing ingest --force`で明示的にrunning状態を上書きして再実行できるようにした。
- articles tableへの書込はrevision/hashに基づく既存の重複解決ロジックにより冪等であることを、同じsource.lock.jsonに対する2回連続run_ingest実行(force=True)で実際に確認した(2回目もaccepted件数が変わらず、同じ内容が`IGNORED_IDENTICAL_DUPLICATE`として安全に無視された)。
- diagnostics/ingest_duplicates tableが現schemaでrun単位追跡fieldを持たないため、再実行時にこれらの監査ログ行が重複しうることをdocstring・LOG.mdに明記した(既知の制約、将来のschema変更で対応)。
- chunk streaming中の失敗(tar member名不正等)でmanifestが正しく"failed"になり、例外が呼び出し元へ伝播することをテストで確認した。
- `tests/test_ingest_orchestrate.py`に7件、`tests/test_cli.py`に1件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート369件、`git diff --check`が成功した。

**判断・注意点**

- 汎用的なstage lock・resume判定・`--from-stage`/`--force-stage`はEPIC I(Pipeline resume)の対象として残し、本タスクはingest stage専用の最小実装(manifestのrunning検出+force override)に留めた。
- diagnostics/ingest_duplicatesへのrun_id列追加は、DBスキーマ変更を伴うため本タスクの対象外とし、既知の制約として文書化するに留めた。
