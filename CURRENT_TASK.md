# CURRENT_TASK.md

## Task ID

TASK-K007

## 目的

`ARCHITECTURE.md` 11.6(Infobox: TableBlockの単なる別名にせず、記事冒頭メタデータとして別型にする)の最初の段階として、`<table>`要素がMediaWikiのinfoboxかどうかを判定する。MediaWikiの`Template:Infobox`実装は`class="infobox ..."`という安定した慣習を持つため、`class`属性のトークンに`infobox`が含まれるかどうかで判定する(個別テンプレート名の列挙ではなく、Wikipedia全体で使われる共通クラス名1つに依拠する)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K007(依存: K001)を読んだ
- [x] `ARCHITECTURE.md` 11.6(InfoboxBlock)を再確認した
- [x] `html_parser.has_class()`(既存のclass判定ヘルパー)を確認した
- [x] MediaWikiの`Template:Infobox`が`class="infobox"`を安定して付与する慣習であることを確認した(個別テンプレート実装の調査はスコープ外、共通クラス名のみに依拠する判断根拠)

## 変更予定ファイル

- `src/wikiepwing/normalize/infobox.py`(新規: `is_infobox()`)
- `tests/test_normalize_infobox.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_infobox.py
make check
git diff --check
```

## 完了条件

- [x] `is_infobox(node)`が、`class`属性に`infobox`トークンを含む`<table>`要素に対して`True`を返す
- [x] `infobox`トークンを含まない`<table>`要素、`<table>`以外の要素に対して`False`を返す
- [x] `make check`が成功する

## 非対象

- Infoboxのフィールド抽出(TASK-K008)
- Infoboxレンダラ(TASK-K009)

## 実施結果

- `src/wikiepwing/normalize/infobox.py`に`is_infobox()`を実装した。既存の`is_table()`(TASK-K001)と`has_class()`(TASK-G001)を組み合わせ、`class`属性のトークンに`infobox`が含まれる`<table>`要素のみを検出する(部分文字列一致ではなく空白区切りトークンの完全一致)。
- `tests/test_normalize_infobox.py`(新規6件)で、単一class・複数class中の1つ・infobox無し・class属性無し・非table要素・"infoboxen"のような接頭辞一致の誤検出防止を確認した。
- `make check`(format-check/lint/mypy/pytest 889件)と`git diff --check`が成功した。
