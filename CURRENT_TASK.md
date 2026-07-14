# CURRENT_TASK.md

## Task ID

TASK-K001

## 目的

`ARCHITECTURE.md` 11.5(Table)のHTML-to-Table変換の最初の段階として、生の`<table>` DOM要素を中間表現(`RawTable`/`RawTableRow`/`RawTableCell`)へ解析する。row/col span正規化(TASK-K002)・複雑度分類(TASK-K003)・実際の`TableBlock`への変換(TASK-K004-K006)はまだ行わない。G001(html_parser)が作るDOM木から、`<table>`要素1つを受け取り、caption・行・セル(rowspan/colspan/is_header)を機械的に取り出すだけの狭いスコープとする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K001(依存: G001,F003)を読んだ
- [x] `ARCHITECTURE.md` 11.5(TableCell/TableBlock)を再確認した(本タスクはこの最終型ではなく中間表現を作る)
- [x] `model/blocks.py`に`TableBlock`/`TableCell`が既存(HTML変換は別epicとdocstringに明記済み)であることを確認した
- [x] `normalize/headings.py`(TASK-G004)の属性読み取り・Diagnostic生成パターンを参考にした

## 変更予定ファイル

- `src/wikiepwing/normalize/tables.py`(新規: `RawTable`, `RawTableRow`, `RawTableCell`, `is_table()`, `parse_table_dom()`)
- `tests/test_normalize_tables.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_tables.py
make check
git diff --check
```

## 完了条件

- [x] `parse_table_dom(node)`が、`<caption>`・各`<tr>`の`<td>`/`<th>`セル(rowspan/colspan/is_header)を中間表現へ変換する
- [x] ネストされた`<table>`内の`<tr>`を、外側テーブルの行として誤って取り込まない
- [x] rowspan/colspan属性が非数値・非正の場合は1にフォールバックし、Diagnosticを記録する
- [x] `make check`が成功する

## 非対象

- row/col span正規化(セル展開、TASK-K002)
- 複雑度分類・最終`TableBlock`への変換(TASK-K003-K006)
- Infobox検出(`<table>`がinfoboxかどうかの判定、TASK-K007)

## 実施結果

- `src/wikiepwing/normalize/tables.py`に`RawTableCell`/`RawTableRow`/`RawTable`・`is_table()`・`parse_table_dom()`を実装した。`<caption>`・`thead`/`tbody`/`tfoot`配下も含めた`<tr>`・各セルのrowspan/colspan/is_headerを中間表現へ変換する。ネストされた`<table>`は行探索が内側テーブルへ再帰的に降りない設計(`_find_rows`が`<table>`タグに達したら止まる)にした。
- rowspan/colspanが非数値または非正の場合は1へフォールバックし、`TABLE_INVALID_SPAN`のDiagnosticを記録するようにした。
- `tests/test_normalize_tables.py`(新規15件)で、table判定・非table拒否・行/セル解析・th判定・span読み取り・span欠落時のデフォルト・不正span時のフォールバック+Diagnostic・caption有無・thead/tbody/tfoot・ネストテーブルの除外・class名取得を確認した。
- `make check`(format-check/lint/mypy/pytest 850件)と`git diff --check`が成功した。
