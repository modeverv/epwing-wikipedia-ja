# CURRENT_TASK.md

## Task ID

TASK-G006

## 目的

`TASKS.md` TASK-G006を実装する。`normalize/paragraphs.py`(TASK-G005)の`_convert_one`ディスパッチへ、`<b>`/`<strong>`→`StrongInline`、`<i>`/`<em>`→`EmphasisInline`、`<code>`→`CodeInline`、`<br>`→`LineBreakInline`のハンドラを追加する。`StrongInline`/`EmphasisInline`はネストしたinlineを保持する(`model/inline.py`の`inlines: tuple[Inline, ...]`)ため子要素を`convert_inline_nodes`で再帰変換し、`CodeInline`は`value: str`のみを持つ型のため子要素のテキストを平坦化する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G006(依存: G005)を読んだ
- [x] `normalize/paragraphs.py`(TASK-G005で実装した`convert_inline_nodes`/`_convert_one`の拡張ポイント)を確認した
- [x] `model/inline.py`の`StrongInline`/`EmphasisInline`(`inlines: tuple[Inline,...]`)と`CodeInline`(`value: str`)・`LineBreakInline`(フィールド無し)を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/paragraphs.py`
- `tests/test_normalize_inline_markup.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_inline_markup.py tests/test_normalize_paragraphs.py
make check
git diff --check
```

## 完了条件

- [x] `<b>`/`<strong>`を`StrongInline`へ変換し、子要素を再帰的にinline変換する(nested markupを保持する)
- [x] `<i>`/`<em>`を`EmphasisInline`へ変換し、同様に再帰する
- [x] `<code>`を`CodeInline`へ変換し、子要素のテキストを平坦化する(空なら省略)
- [x] `<br>`を`LineBreakInline`へ変換する
- [x] `<b><i>text</i></b>`のような入れ子が正しくネストした`StrongInline(EmphasisInline(...))`になる
- [x] 未知の要素は引き続き透過的に再帰する(既存のG005挙動を壊さない)
- [x] `make check`が成功する

## 非対象

- リスト/定義リスト/引用/preformatted等の他ブロック変換(TASK-G007以降)
- リンク(internal/external)のinline変換(別途、内部リンク解決は`ARCHITECTURE.md` 12.5、実装タイミングは未定)

## 実施結果

- `src/wikiepwing/normalize/paragraphs.py`の`_convert_one`へ`<b>`/`<strong>`/`<i>`/`<em>`/`<code>`/`<br>`ハンドラを追加した。
- `tests/test_normalize_inline_markup.py`に9件のテストを追加。既存の`tests/test_normalize_paragraphs.py`の1件を、真に未知の要素を使うよう更新した。
- `uv run pytest tests/test_normalize_inline_markup.py tests/test_normalize_paragraphs.py`: 17 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート540件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G006チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-G007 Ordered/unordered lists。
