# CURRENT_TASK.md

## Task ID

TASK-S009

## 目的

`PLAN.md` 29(月次更新ワークフロー、「release notes」)を実装する。TASK-S006の`update`コマンドが書き出す`update-report.json`(機械可読な差分)から、人間が読める月次更新レポート(Markdown形式のrelease notes)を生成する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S009(依存: S006、完了済み)を読んだ
- [x] `PLAN.md` 29を再確認した。「old outputを自動削除しない」「same media/math cache reuse」「old runs cleanup」は既にS006/S007/S008で満たされているため、本タスクは「release notes」の生成のみを対象とする
- [x] `src/wikiepwing/source_diff.py`(TASK-S006)の`SourceDiff`/`build_update_report`のペイロード形状を確認し、それを入力として再利用する設計にした(差分計算ロジックを再実装しない)

## 変更予定ファイル

- `src/wikiepwing/release_notes.py`(新規: `render_release_notes`)
- `src/wikiepwing/cli.py`(`update`コマンドに`--release-notes-path`を追加し、`update-report.json`と併せてMarkdownを書き出す)
- `tests/test_release_notes.py`(新規)
- `tests/test_cli.py`(追記)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_release_notes.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `render_release_notes`が初回acquire(previous無し)とバージョン更新ありの両方で読める形式のMarkdownを生成する
- [x] 追加/削除/変更chunk数とサイズ差分(人間可読な単位)がMarkdownに含まれる
- [x] バージョン変更が無い場合はその旨が明示される
- [x] `wikiepwing update`が`--release-notes-path`(デフォルト: `paths.reports/release-notes.md`)にMarkdownを書き出す
- [x] `paths.output`に一切触れない
- [x] `make check`が成功する

## 非対象

- release notesの自動配布・通知(メール/Slack等) — 生成のみを対象とする
- 複数回のupdate履歴を跨いだ集約(今回のupdate 1回分のみを対象とする)

## 実施結果

`src/wikiepwing/release_notes.py`(新規)に`render_release_notes`を実装し、TASK-S006の`update-report.json`ペイロードをそのまま入力として、初回acquire/バージョン変更あり/バージョン変更なしの3パターンでMarkdownを生成できるようにした(差分計算ロジックは再実装せず`source_diff`の出力を再利用)。サイズは`_human_size`でB/KB/MB/GB/TB単位に変換して表示する。`cli.py`の`update`サブコマンドに`--release-notes-path`(デフォルト`paths.reports/release-notes.md`)を追加し、`update-report.json`と併せてMarkdownを書き出すようにした(`paths.output`には触れない)。`tests/test_release_notes.py`(新規4件)、`tests/test_cli.py`への追記(help確認に`--release-notes-path`を追加)を含め、`uv run ruff format .`/`uv run ruff check .`、`make check`(1378 passed, 6 skipped)、`git diff --check`が成功した。
