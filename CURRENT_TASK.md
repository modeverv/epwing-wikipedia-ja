# CURRENT_TASK.md

## Task ID

TASK-K002

## 目的

`ARCHITECTURE.md` 11.5(TableBlock/TableCellがrow_span/col_spanをそのまま保持する設計)を踏まえ、TASK-K001の`RawTable`(DOM順のセル列、rowspan/colspan未解決)を、各セルの実際のグリッド上の行・列位置("HTML table grid formation algorithm"相当)へ正規化する。TableBlock自体はspan値を保持したまま(グリッド展開済みの値は保存しない)ため、本タスクは複雑度分類(TASK-K003)やレンダラ(TASK-K004-K005)が必要とする「各セルが実際にどの行・列に位置するか」「テーブル全体の列数」を計算する中間ステップとして実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K002(依存: K001)を読んだ
- [x] `ARCHITECTURE.md` 11.5の`TableCell`/`TableBlock`がspan値をそのまま保持する設計であることを再確認した(グリッド展開結果はモデルに保存せず、後続タスクが必要とする中間計算として位置づける)
- [x] TASK-K001の`RawTable`/`RawTableRow`/`RawTableCell`を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/table_grid.py`(新規: `PositionedCell`, `NormalizedTable`, `normalize_table_spans()`)
- `tests/test_normalize_table_grid.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_table_grid.py
make check
git diff --check
```

## 完了条件

- [x] `normalize_table_spans(table)`が、各セルの開始行・開始列(`row_index`/`col_index`)を、前の行からのrowspanが占有する列をスキップして正しく計算する
- [x] colspanが同一行内の後続セルの列位置を正しくずらす
- [x] rowspan+colspanを組み合わせたセルが正しい矩形領域を占有する(後続行がその領域をスキップする)
- [x] テーブル全体の列数(`column_count`)を計算する(全行の最大到達列)
- [x] `make check`が成功する

## 非対象

- 複雑度分類(TASK-K003)
- 実際のレンダラ(TASK-K004 simple/K005 wide)
- 不正な重複span(仕様上のedge case)の完全な仕様準拠処理(現実のWikipediaテーブルを想定した素直な実装に留める)

## 実施結果

- `src/wikiepwing/normalize/table_grid.py`に`PositionedCell`・`NormalizedTable`・`normalize_table_spans()`を実装した。HTML仕様の"table grid formation algorithm"相当のアルゴリズムで、各セルの開始行・開始列を、前の行からのrowspanが占有する列をスキップしながら計算する。
- rowspan/colspanを組み合わせたセルが正しく矩形領域を占有し、その領域の有効期限(残り行数)が切れると後続行がその列を再利用できるようにした。
- テーブル全体の列数は、全セルの`col_index + col_span`の最大値として計算した(トレイリングのスパン追跡ではなく、セル単位の最大値を取ることでシンプルかつ正確にした)。
- `tests/test_normalize_table_grid.py`(新規8件)で、単純グリッド・colspanによる列ずれ・rowspanによる次行の列スキップ・rowspan+colspan組み合わせ・rowspanの期限切れ・最大幅による列数計算・空テーブル・caption/class名の保持を確認した。
- `make check`(format-check/lint/mypy/pytest 858件)と`git diff --check`が成功した。
