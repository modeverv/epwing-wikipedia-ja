# CURRENT_TASK.md

## Task ID

TASK-G009

## 目的

`ARCHITECTURE.md` 12.2のpass `N60`(引用/preformatted変換)を実装する。`<blockquote>`要素を`QuoteBlock`(`blocks: tuple[Block, ...]`)へ、`<pre>`要素を`PreformattedBlock`(`text: str`)へ変換する。blockquote内は典型パターン(`<p>`の並び、またはinline contentの並び)のみを扱い、preformattedはテキストを一切正規化せず(空白・改行をそのまま)保持する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G009(依存: G005)を読んだ
- [x] `model/blocks.py`の`QuoteBlock`/`PreformattedBlock`を確認した
- [x] `normalize/paragraphs.py`(`convert_paragraph`/`convert_inline_nodes`)、`normalize/lists.py`/`normalize/definition_lists.py`のモジュール構成パターンを踏襲する
- [x] `ARCHITECTURE.md` 13.1("本文は過剰にNFKCしません")を確認し、preformattedのtext抽出でも正規化を行わない方針とした

## 変更予定ファイル

- `src/wikiepwing/normalize/quotes.py`
- `tests/test_normalize_quotes.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_quotes.py
make check
git diff --check
```

## 完了条件

- [x] `is_quote`/`is_preformatted`が`<blockquote>`/`<pre>`要素を判定する
- [x] `convert_quote`が`<p>`子要素をそれぞれ`ParagraphBlock`へ変換する
- [x] `convert_quote`が`<p>`以外のinline/テキスト内容を1つの`ParagraphBlock`にまとめる(`<p>`との混在時は分離される)
- [x] `convert_preformatted`がテキストを空白・改行を保持したまま抽出する(NFKC等の正規化を行わない)
- [x] 非対応要素を渡すとそれぞれ`ValueError`を送出する
- [x] `make check`が成功する

## 非対象

- 任意のDOMノードをBlockへ振り分ける汎用dispatcher(TASK-G010/G012)
- `<pre>`内のinline要素(`<code>`等)の変換(テキストとして平坦化するのみ)

## 実施結果

- `src/wikiepwing/normalize/quotes.py`に`is_quote`/`is_preformatted`/`convert_quote`/`convert_preformatted`を実装した。
- `tests/test_normalize_quotes.py`に10件のテストを追加。
- `uv run pytest tests/test_normalize_quotes.py`: 10 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート568件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G009チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-G010 Unknown DOM fallback。
