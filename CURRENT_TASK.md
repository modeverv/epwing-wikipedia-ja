# CURRENT_TASK.md

## Task ID

TASK-K008

## 目的

`ARCHITECTURE.md` 11.6(InfoboxBlock: title/fields/images)の中間表現を、TASK-K007で検出したinfobox `<table>`から抽出する。MediaWikiのinfoboxは概ね次の行パターンで構成される: (1) 単一の結合ヘッダーセルからなるtitle行、(2) ラベルセル+値セルの2セルからなるfield行、(3) `<img>`のみを含む画像行。本タスクはこれらを機械的に抽出する`parse_infobox_dom()`を実装する(実際の`InfoboxBlock`/`InfoboxField`モデルへの変換、およびMini-profileでのレンダリングはTASK-K009)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K008(依存: K007)を読んだ
- [x] `ARCHITECTURE.md` 11.6(InfoboxField/InfoboxBlock)を再確認した
- [x] TASK-K001の`parse_table_dom`/`RawTable`を確認した(再利用する)
- [x] 画像の実ダウンロード・MediaReference化は別epic(15.1、EPIC O)であることを確認した。本タスクでは`<img>`の`src`属性の生文字列のみを抽出し、MediaReferenceへの変換は対象外とする

## 変更予定ファイル

- `src/wikiepwing/normalize/infobox_fields.py`(新規: `RawInfoboxField`, `RawInfobox`, `parse_infobox_dom()`)
- `tests/test_normalize_infobox_fields.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_infobox_fields.py
make check
git diff --check
```

## 完了条件

- [x] 単一の結合ヘッダーセル(1セルのみ、`is_header`)からなる先頭行をtitleとして抽出する
- [x] ラベルセル+値セルの2セルからなる行を`RawInfoboxField(name, value_nodes)`として抽出する
- [x] `<img>`要素のみを含む行(または`<img>`を含む単一セル行)の`src`属性を`image_srcs`として抽出する
- [x] 上記いずれにも該当しない行は静かにスキップする(既知の単純化としてdocstringに明記)
- [x] `make check`が成功する

## 非対象

- 実際の`InfoboxBlock`/`InfoboxField`モデルへの変換(TASK-K009)
- Mini-profileでのinfoboxレンダリング(TASK-K009)
- 画像の実ダウンロード・MediaReference化(別epic)

## 実施結果

- `src/wikiepwing/normalize/infobox_fields.py`に`RawInfoboxField`・`RawInfobox`・`parse_infobox_dom()`を実装した。TASK-K001の`parse_table_dom`を再利用し、1セル+is_header行をtitleとして、2セル行をfieldとして、`<img>`を含む行/セルの`src`を`image_srcs`として抽出する。それ以外の行構造は静かにスキップする(docstringに明記)。
- `tests/test_normalize_infobox_fields.py`(新規7件)で、title行抽出・2セルfield抽出・画像行の`src`抽出・field値内の画像抽出・title無し・未対応行構造のスキップ・`parse_table_dom`からのDiagnostic伝播を確認した。
- 実装中、Bashツールの一時的な障害(コード実行系コマンドのみ拒否、`ls`/`grep`/`cat`等の単純コマンドは動作)が長時間続いたため、その間に全ロジックを`RawTableCell`/`RawTableRow`の既存定義と突き合わせて手動でトレースし、正しさを確認してから復旧後にテストを実行した。
- `make check`(format-check/lint/mypy/pytest 896件)と`git diff --check`が成功した。
