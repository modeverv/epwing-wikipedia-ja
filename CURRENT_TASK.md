# CURRENT_TASK.md

## Task ID

TASK-S008

## 目的

`PLAN.md` 29(`wikiepwing clean --keep-runs 2`、出口条件「old outputを自動削除しない」)を実装する。`paths.work/runs/<run-id>/`配下の古い実行ディレクトリのみを対象とし(`paths.output`の最終成果物は対象外)、最新のN件を残して削除する`clean_old_runs`と、実際に削除する前に対象を確認できる`dry_run`オプションを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S008(依存: S007)を読んだ
- [x] `PLAN.md` 29(`wikiepwing clean --keep-runs 2`、「old outputを自動削除しない」という出口条件)を再確認した
- [x] 削除は破壊的操作であるため、`dry_run`を実装し、実際の削除はCLIコマンドとしてユーザー自身が明示的に実行する場合のみ行われる設計にした(このタスク自体はテストのみで、実ディレクトリに対して削除を実行しない)

## 変更予定ファイル

- `src/wikiepwing/clean.py`(新規: `find_removable_runs`, `clean_old_runs`)
- `src/wikiepwing/cli.py`(`clean`サブコマンド追加、`--keep-runs`・`--dry-run`)
- `tests/test_clean.py`(新規)
- `tests/test_cli.py`(追記)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_clean.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `find_removable_runs`が`runs_dir`配下のディレクトリをmtime降順でsortし、最新`keep_runs`件を除いた残りを返す
- [x] `runs_dir`が存在しない場合は空タプルを返す(クラッシュしない)
- [x] `keep_runs`が負の場合は`ValueError`を送出する
- [x] `clean_old_runs`が`dry_run=True`の場合は実際には削除せず、削除対象のリストのみ返す
- [x] `clean_old_runs`が`dry_run=False`の場合は実際にディレクトリを削除する
- [x] `wikiepwing clean --keep-runs N [--dry-run]`が`paths.work/runs`のみを対象にする(`paths.output`は触らない)
- [x] `make check`が成功する

## 非対象

- Monthly update report(TASK-S009)
- output保持ポリシー自体(「old outputを自動削除しない」という制約を満たすため、そもそも対象にしない)

## 実施結果

`src/wikiepwing/clean.py`(新規)に`find_removable_runs`(mtime降順sort、`keep_runs`件を超える古いディレクトリを返す。`runs_dir`不在時は空タプル、`keep_runs<0`は`ValueError`)と`clean_old_runs`(`dry_run`オプション付き、実削除時は対象がシンボリックリンクでないことを確認してから`shutil.rmtree`)を実装した。`cli.py`に`clean`サブコマンド(`--keep-runs`必須, `--dry-run`フラグ)を追加し、`config.paths.work / "runs"`のみを対象にして`paths.output`には一切触れないようにした。`tests/test_clean.py`(8件)と`tests/test_cli.py`への追記(3件)を含め、`uv run ruff format .`/`uv run ruff check .`(2ファイル整形、全チェック成功)、`make check`(1364 passed, 6 skipped)、`git diff --check`が成功した。
