# CURRENT_TASK.md

## Task ID

TASK-K006

## 目的

`ARCHITECTURE.md` 16.3(oversized: "configured row上限で分割"、"続きentryを作るか、要約とtruncate diagnostic")を実装する。続きentry(continuation entry)を作る仕組みは`RenderedEntry`にまだ存在しない(TASK-H006/H007の範囲外、複数entry分割の基盤が無い)ため、本タスクでは後者の選択肢――行数上限を超えるテーブルを切り詰め、truncateしたことをDiagnosticとして記録する――を採用する。`build_table_block`(TASK-K004)に行数上限を追加し、超過分を切り詰めた上で`TABLE_OVERSIZED_ROWS` Diagnosticを記録する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K006(依存: K004-K005)を読んだ
- [x] `ARCHITECTURE.md` 16.3(oversized policy)・16.4(Entry size budget)を再確認した
- [x] `RenderedEntry`/`render/generate.py`に複数entry分割(続きentry)の基盤が存在しないことを確認した(本タスクでは非対応と判断する根拠)
- [x] `DECISIONS.md`にoversized関連の既存ADRが無いことを確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/table_block.py`(`build_table_block`に`max_rows`引数を追加し、超過時に切り詰め+Diagnostic)
- `tests/test_normalize_table_block.py`(oversized切り詰めの回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_table_block.py
make check
git diff --check
```

## 完了条件

- [x] `build_table_block(table_element, max_rows=...)`が、`RawTable`の行数が`max_rows`を超える場合、先頭`max_rows`行のみを`TableBlock.rows`へ含める
- [x] 切り詰めが発生した場合、`TABLE_OVERSIZED_ROWS`のDiagnosticを記録する(実際の行数と保持した行数を`details`に含める)
- [x] 切り詰めが発生しない場合は`TABLE_OVERSIZED_ROWS`を記録しない
- [x] `max_rows`のデフォルト値を明記する
- [x] `make check`が成功する

## 非対象

- 続きentry(continuation entry)の生成(RenderedEntry分割の基盤自体が無いため対象外)
- Entry size budget全体(16.4、nav/reference重複削除・sectionの続きentry分割等、TASK-K006の対象は表の行数上限のみ)

## 実施結果

- `build_table_block`に`max_rows: int = DEFAULT_MAX_ROWS`(100)引数を追加した。行数が`max_rows`を超える場合、先頭`max_rows`行のみをセル変換・`TableBlock.rows`へ含め、`TABLE_OVERSIZED_ROWS`のDiagnostic(details: `total_rows`/`kept_rows`)を記録する。複雑度分類は切り詰め前の完全なテーブルに対して行う(行数だけで表示方針が変わるべきではないため)。
- `RenderedEntry`に複数entry分割(続きentry)の基盤が無いことを確認し、16.3の選択肢のうち「要約とtruncate diagnostic」を採用する判断をdocstringに明記した。
- `tests/test_normalize_table_block.py`への追加3件(閾値以内で切り詰め無し・閾値超過で切り詰め+Diagnostic・デフォルト値での小規模テーブル)を実装した。
- `make check`(format-check/lint/mypy/pytest 883件)と`git diff --check`が成功した。
