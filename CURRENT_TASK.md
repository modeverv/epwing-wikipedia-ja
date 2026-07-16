# CURRENT_TASK.md

## Task ID

TASK-S007

## 目的

`PLAN.md` 29(月次更新ワークフロー、`wikiepwing disk-usage`コマンド)を実装する。`config.paths`配下の各ディレクトリ(sources/reference/work/cache/output/reports/logs)のディスク使用量を集計し、JSON/テキストで報告する`compute_disk_usage`と、それを呼び出す`disk-usage` CLIサブコマンドを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S007(依存: A007)を読んだ
- [x] `PLAN.md` 29(`wikiepwing disk-usage`が引数なしで呼ばれる例)を再確認した
- [x] `doctor.py`の`_free_disk_check`(`shutil.disk_usage`の使用パターン)・`AppConfig.paths`(sources/reference/work/cache/output/reports/logs)を確認した

## 変更予定ファイル

- `src/wikiepwing/disk_usage.py`(新規: `PathUsage`, `DiskUsageReport`, `compute_disk_usage`)
- `src/wikiepwing/cli.py`(`disk-usage`サブコマンド追加)
- `tests/test_disk_usage.py`(新規)
- `tests/test_cli.py`(追記)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_disk_usage.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `compute_disk_usage`が`config.paths`の各named directory(sources/reference/work/cache/output/reports/logs)のバイト数を再帰的に集計する
- [x] 存在しないディレクトリは`exists=False`・`size_bytes=0`になる(クラッシュしない)
- [x] symlinkは二重計上しない
- [x] `total_bytes`が各pathの合計と一致する
- [x] `wikiepwing disk-usage`(引数なし)がJSON形式で結果を出力する
- [x] `make check`が成功する

## 非対象

- Safe clean command(TASK-S008、実際の削除操作)
- Update command(TASK-S006)

## 実施結果

- `src/wikiepwing/disk_usage.py`(新規)に`PathUsage`・`DiskUsageReport`・`compute_disk_usage`を実装した。`config.paths`の各named directoryを再帰的に集計し(symlinkは除外)、存在しないディレクトリは`exists=False`/`size_bytes=0`にする。
- `cli.py`に`disk-usage`サブコマンド(引数なし、`--config`のみ)を追加した。
- `tests/test_disk_usage.py`(新規7件)・`tests/test_cli.py`(新規2件)で、欠落ディレクトリ・存在するディレクトリの集計・再帰・symlink非二重計上・total_bytesの一致・JSON serializable・free_bytesの非負性・CLIのhelp/実行を確認した。
- `make check`(format-check/lint/mypy/pytest 1353件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
