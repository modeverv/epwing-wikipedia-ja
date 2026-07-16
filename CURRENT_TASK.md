# CURRENT_TASK.md

## Task ID

TASK-S006

## 目的

`PLAN.md` 29(`wikiepwing update --project jawiki --profile full`、出口条件「source version naming」「update report」)を実装する。既存の`source.lock.json`(あれば)と新規`acquire_snapshot`結果を比較し、差分(バージョン変更・追加/削除/変更chunk・サイズ差分)を計算して更新レポートを書き出す`update`コマンドを追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S006(依存: D007 Acquire command, I006 `--from-stage`/`--force-stage`。両方完了済み)を読んだ
- [x] `PLAN.md` 29を再確認した。「same media/math cache reuse」は既存のcontent-hashキー付きcache(media/math)がすでに満たしており本タスクでの追加実装は不要、「old runs cleanup」はTASK-S008の`clean`コマンドが既に担当、「old outputを自動削除しない」は`update`が`paths.output`に一切触れない設計で満たす
- [x] `acquire_snapshot`は`sources_root/project/version_identifier/source.lock.json`にバージョンごとの別ディレクトリで書き込むため、旧ロックは自動的に残る(削除しない)ことを確認した

## 変更予定ファイル

- `src/wikiepwing/source_diff.py`(新規: `SourceDiff`, `compute_source_diff`, `build_update_report`, `write_update_report`)
- `src/wikiepwing/cli.py`(`update`サブコマンド追加)
- `tests/test_source_diff.py`(新規)
- `tests/test_cli.py`(追記)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_source_diff.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `compute_source_diff`が`previous`が`None`の場合(初回acquire)と、chunk追加/削除/sha256変更/バージョン変更を検出できる
- [x] サイズ差分(`size_delta_bytes`)が正しく計算される
- [x] `write_update_report`がJSONを決定的に書き出す
- [x] `wikiepwing update`が`--previous-lock-path`省略時に`paths.sources/<project>/*/source.lock.json`から最新(mtime)のロックを自動検出する
- [x] `wikiepwing update`が新規acquireを実行し、レポートを`paths.reports/update-report.json`に書き出す
- [x] `paths.output`に一切触れない
- [x] `make check`が成功する

## 非対象

- pipeline再実行(ingest/normalize/generate/build)の自動実行(ユーザーが既存コマンドを個別に実行する運用を想定)
- media/mathキャッシュの再利用ロジック自体(既存のcontent-hashキー付きcacheで既に満たされているため対象外)
- old runsの削除(TASK-S008の`clean`コマンドが担当)

## 実施結果

`src/wikiepwing/source_diff.py`(新規)に`SourceDiff`・`compute_source_diff`(初回acquire・chunk追加/削除/sha256変更・バージョン変更・サイズ差分を検出)・`build_update_report`・`write_update_report`(決定的JSON、atomic write)を実装した。`cli.py`に`update`サブコマンド(`--namespace`, `--snapshot-version`, `--previous-lock-path`, `--report-path`, `--git-commit`)を追加し、既存`acquire`コマンドと同じ`acquire_snapshot`呼び出しを再利用しつつ、`--previous-lock-path`省略時は`_latest_source_lock_path`で`paths.sources/<project>/*/source.lock.json`のうち最も新しくmodifyされたものを自動検出するようにした。レポートは`paths.reports/update-report.json`に書き出し、`paths.output`には一切触れない。`tests/test_source_diff.py`(6件)、`tests/test_cli.py`への追記(help確認1件、`_latest_source_lock_path`の単体テスト3件)を含め、`uv run ruff format .`/`uv run ruff check .`、`make check`(1374 passed, 6 skipped)、`git diff --check`が成功した。
