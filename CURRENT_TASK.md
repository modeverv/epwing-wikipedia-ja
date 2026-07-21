# CURRENT_TASK.md

## Task ID

TASK-T046

## 目的

FreePWING の仕様上、内部リンク修飾 (`add_reference_start`) がアクティブな最中に `add_newline()` が呼ばれると発生する `modifier not terminated before newline` エラーを防止するため、リンクラベル内の改行をスペースへ変換し、リンク処理中の `add_newline()` 呼び出しをガードする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した

## 変更予定ファイル

- `docker/toolchain/freepwing_build_entries.pl`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
make toolchain-image
make build MODEL_DB=data/work/model-diff-ram8.sqlite3
```

## 完了条件

- [x] `freepwing_build_entries.pl` 内で内部リンクのラベルに含まれる改行をスペースへ置換すること
- [x] `add_body_ops` 内で `$in_reference` フラグにより修飾実行中の `add_newline()` 呼出をガードすること
- [x] ツールチェーンの Docker イメージ（`wikiepwing-toolchain:dev`）が更新されること

## 結果

- 内部リンク内での改行呼出による `modifier not terminated before newline` エラーを完全に防ぐ二重安全回路を実装。

## 非対象

- 他の非ツールチェーンファイルの変更
