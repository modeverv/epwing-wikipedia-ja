# CURRENT_TASK.md

## Task ID

TASK-K004

## 目的

`PLAN.md` Phase 11("simple renderer")と`ARCHITECTURE.md` 16.3("simple": 小列数・短いcell・grid-like text)を実装する。TASK-K001-K003は`<table>` DOM→中間表現→複雑度分類までを行ったが、まだ実際の`TableBlock`(モデル型)を組み立てる処理が存在しない。本タスクで(1)`RawTable`+分類結果から実際の`TableBlock`(`TableCell`にセル内容をBlockへ変換して格納)を組み立てる`build_table_block()`と、(2)`complexity=="simple"`な`TableBlock`をMini-profileのgrid-likeプレーンテキストへレンダリングする処理を実装し、`mini_layout.py`の`_render_block`ディスパッチへ接続する。他のcomplexity(wide/complex/unsupported)は、まだ専用レンダラが無いため劣化表示のプレースホルダ+Diagnosticで扱い、TASK-K005/K006で置き換える前提とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K004(依存: K003,H007)を読んだ
- [x] `PLAN.md` Phase 11・`ARCHITECTURE.md` 16.3を再確認した
- [x] `model/blocks.py`の`TableCell`/`TableBlock`(caption: `tuple[Inline,...]`、rows: DOM順そのまま)を確認した
- [x] `convert_block.convert_document`(セル内容→Block変換)・`paragraphs.convert_inline_nodes`(caption→Inline変換)を確認した
- [x] "complex"用の専用レンダラtaskが無く、16.3の"wide"(縦record)と"complex"(row/sectionごとのkey-value)が類似の方針であることに気づいた(complexの本格対応はTASK-K005以降に譲る)

## 変更予定ファイル

- `src/wikiepwing/normalize/table_block.py`(新規: `build_table_block()`)
- `src/wikiepwing/render/mini_layout.py`(TableBlockの`_render_block`ケースを追加、simpleのみgrid-like text、他は劣化プレースホルダ)
- `tests/test_normalize_table_block.py`(新規)
- `tests/test_render_mini_layout.py`(TableBlock renderingの回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_table_block.py tests/test_render_mini_layout.py
make check
git diff --check
```

## 完了条件

- [x] `build_table_block(table_element)`が、caption・各セルの内容をBlock変換し、`TableCell.row_span`/`col_span`/`is_header`を保持した`TableBlock`を組み立てる
- [x] `complexity`は`classify_table_complexity`(TASK-K003)の結果をそのまま使う
- [x] `complexity=="simple"`な`TableBlock`が、grid-likeなプレーンテキスト(行ごとに1行、セルを区切り文字で連結)としてMini-profileへレンダリングされる
- [x] 他のcomplexity(wide/complex/unsupported)は、データを失わない劣化表示(caption+プレースホルダ)で扱う
- [x] `make check`が成功する

## 非対象

- wide/complexの本格的なrenderer(TASK-K005)
- oversized(行上限による分割、TASK-K006)
- infobox(TASK-K007-K009)

## 実施結果

- `src/wikiepwing/normalize/table_block.py`に`build_table_block()`を実装した。K001(DOM解析)→K002(span正規化、列数計算用)→K003(複雑度分類)を連結し、各セルの内容を`convert_document`でBlockへ、captionを`convert_inline_nodes`でInlineへ変換して実際の`TableBlock`/`TableCell`を組み立てる。
- `render/mini_layout.py`の`_render_block`に`TableBlock`のケースを追加した。`complexity=="simple"`ならcaption+各行を` | `区切りのgrid-likeテキストへ、それ以外(wide/complex)はcaption+行数プレースホルダへ、空(unsupported)はcaptionのみへレンダリングする。
- `tests/test_normalize_table_block.py`(新規9件)で、simple組み立て・セル内容のBlock変換・captionのInline変換・header/span保持・class名保持・wide/complex分類・空テーブル・Diagnostic伝播を確認した。
- `tests/test_render_mini_layout.py`への追加3件(simple tableのgrid text・非simpleのプレースホルダ・空テーブルのcaptionのみ)を実装した。
- `make check`(format-check/lint/mypy/pytest 878件)と`git diff --check`が成功した。
