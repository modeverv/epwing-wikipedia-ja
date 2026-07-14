# CURRENT_TASK.md

## Task ID

TASK-G007

## 目的

`ARCHITECTURE.md` 12.2のpass `N60 Convert lists`を実装する。`<ul>`/`<ol>`要素を`UnorderedListBlock`/`OrderedListBlock`へ、`<li>`要素を`ListItem`(`blocks: tuple[Block, ...]`)へ変換する。`<li>`直下のテキスト/inline要素は`ParagraphBlock`一つへまとめ、ネストした`<ul>`/`<ol>`は独立したBlockとして`ListItem.blocks`に追加する(汎用的な「任意のDOMノードをBlockへ振り分ける」dispatcherはG010/G012の範囲であるため、本タスクではlist itemの典型パターン(inline content + optional nested list)のみを扱う)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G007(依存: G005)を読んだ
- [x] `ARCHITECTURE.md` 12.2(pass `N60`)、`DATA_CONTRACTS.md`のunordered_list JSON例(`{"items": [{"blocks": []}]}`)を確認した
- [x] `model/blocks.py`の`UnorderedListBlock`/`OrderedListBlock`/`ListItem`を確認した
- [x] `normalize/paragraphs.py`(`convert_inline_nodes`/`convert_paragraph`)を再利用する

## 変更予定ファイル

- `src/wikiepwing/normalize/lists.py`
- `tests/test_normalize_lists.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_lists.py
make check
git diff --check
```

## 完了条件

- [x] `is_unordered_list`/`is_ordered_list`が`<ul>`/`<ol>`要素を判定する
- [x] `convert_unordered_list`/`convert_ordered_list`が`<li>`要素を`ListItem`へ変換する
- [x] `<li>`直下のテキスト/inline要素が単一の`ParagraphBlock`にまとめられる
- [x] `<li>`内にネストした`<ul>`/`<ol>`が独立した`Block`として`ListItem.blocks`に保持される(前後のinline contentがあれば別々のParagraphBlockとして分離される)
- [x] ネストしたlist内のdiagnosticsが呼び出し元へ伝播する
- [x] `<ul>`/`<ol>`以外の要素を渡すと`ValueError`を送出する
- [x] `make check`が成功する

## 非対象

- 定義リスト(TASK-G008)
- 引用/preformatted(TASK-G009)
- 任意のDOMノードをBlockへ振り分ける汎用dispatcher(TASK-G010/G012)
- 空白正規化(TASK-G011)によるwhitespace-onlyテキストノードのクリーンアップ

## 実施結果

- `src/wikiepwing/normalize/lists.py`に`is_unordered_list`/`is_ordered_list`/`convert_unordered_list`/`convert_ordered_list`を実装した。
- `tests/test_normalize_lists.py`に10件のテストを追加。
- `uv run pytest tests/test_normalize_lists.py`: 10 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート550件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G007チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-G008 Definition lists。
