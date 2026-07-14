# CURRENT_TASK.md

## Task ID

TASK-I004

## 目的

`ARCHITECTURE.md`のstage output全般に対して、書き込み中のクラッシュで不完全なファイルが残らないよう、汎用のatomic file write primitiveを実装する。既存の`write_stage_manifest_payload`(TASK-I001)がすでにtempfile+`os.replace`パターンを個別実装していたのに対し、`write_entries_jsonl`(TASK-H009)は`destination.open("w")`で直接書き込んでおり、途中でクラッシュすると不完全な`entries.jsonl`が残る(後続の`verify`/toolchainが壊れたJSON Linesを読む恐れがある)ことに気づいた。共有primitiveを実装し、両方の書き込み処理をこれに統一する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-I004(依存: I001)を読んだ
- [x] `pipeline/stage_manifest.py`(`write_stage_manifest_payload`)の既存tempfile+`os.replace`パターンを確認した
- [x] `render/freepwing_source.py`の`write_entries_jsonl`が非atomicに直接書き込んでいることに気づいた

## 変更予定ファイル

- `src/wikiepwing/pipeline/atomic_write.py`
- `src/wikiepwing/pipeline/stage_manifest.py`(共有primitiveを使うようリファクタ)
- `src/wikiepwing/render/freepwing_source.py`(`write_entries_jsonl`をatomicにする)
- `tests/test_pipeline_atomic_write.py`
- `tests/test_render_freepwing_source.py`(atomic性の確認を追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_pipeline_atomic_write.py tests/test_render_freepwing_source.py tests/test_pipeline_stage_manifest.py
make check
git diff --check
```

## 完了条件

- [x] `atomic_write_text(destination, text)`がtempfile+fsync+`os.replace`で書き込む
- [x] 書き込み途中で例外が発生しても`destination`に不完全な内容が現れない(一時ファイルのまま残るか削除される)
- [x] `write_entries_jsonl`が`atomic_write_text`を使うようリファクタされ、既存の全内容を一度に書き込む(部分書き込みを避ける)
- [x] `write_stage_manifest_payload`が同じprimitiveを使うようリファクタされる(重複排除)
- [x] `make check`が成功する

## 非対象

- Resume判定・`--from-stage`/`--force-stage`(TASK-I005-I006)
- raw.sqlite3/model.sqlite3自体のatomic性(SQLiteは複数トランザクションで漸進的に更新されるため、単純なtempfile+renameパターンの対象外)

## 実施結果

- `src/wikiepwing/pipeline/atomic_write.py`に`atomic_write_bytes`/`atomic_write_text`を実装した(tempfile書き込み→`fsync`→`os.replace`)。
- `write_entries_jsonl`を全文をメモリ上で組み立ててから`atomic_write_text`を1回呼ぶ形にリファクタリングした。
- `write_stage_manifest_payload`の重複したtempfile+`os.replace`実装を`atomic_write_text`呼び出しに置き換えた(未使用importを削除)。
- `tests/test_pipeline_atomic_write.py`(新規6件)と`tests/test_render_freepwing_source.py`への追加テスト(`os.replace`失敗時に宛先が変更されないことを確認)を実装した。
- `uv run ruff format`で`tests/test_pipeline_atomic_write.py`のフォーマット違反を修正した後、`make check`(format-check/lint/mypy/pytest 756件)と`git diff --check`が成功した。
- TASKS.mdのTASK-I004を`[x]`にし、LOG.mdに実施記録を追記した。
