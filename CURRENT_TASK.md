# CURRENT_TASK.md

## Task ID

TASK-T043

## 目的

`Makefile` の `ENTRIES` パスに `data/work/entries-mini.jsonl` への自動フォールバックロジックを追加し、`entries.jsonl` 不在時の `entries.jsonl not found` エラーを解決する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した

## 変更予定ファイル

- `Makefile`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
make generate MODEL_DB=data/work/model-diff-ram8.sqlite3 FORCE=1
make build
```

## 完了条件

- [x] `Makefile` で `data/work/entries.jsonl` 不在時に手元の `data/work/entries-mini.jsonl` へ自動フォールバックすること
- [x] `make generate` 実行時に新しい `data/work/entries.jsonl` が作成され、`make build` がそれを読み込んでビルドすること
- [x] `make check` がすべて成功すること

## 結果

- `Makefile` の `ENTRIES` 変数定義を改修し、`data/work/entries.jsonl` または既存の `data/work/entries-mini.jsonl` を自動検出・使用するように改善。
- 1,485件の全テストおよび `make check` を通過。

## 非対象

- 他の無関係な変数の変更
