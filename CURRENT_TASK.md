# CURRENT_TASK.md

## Task ID

TASK-G011

## 目的

`ARCHITECTURE.md` 13.1(保存用本文の処理: Unicode validation/CRLF→LF/不正制御文字除去/ゼロ幅文字の方針適用/連続空白の文脈別整理)を実装する、pass `N120 Normalize whitespace`を実装する。すでに構築済みのBlock木を再帰的に走査し、prose的なテキスト(`TextInline.value`等)は空白を正規化するが、`PreformattedBlock.text`/`CodeInline.value`/`CodeBlock.text`/`MathBlock.source`はverbatim保持のため対象外とする(`ARCHITECTURE.md` 13.1「本文は過剰にNFKCしません」およびG009で確立した"preformatted/codeはverbatim"方針を踏襲)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G011(依存: G010)を読んだ
- [x] `ARCHITECTURE.md` 13.1・13.2(索引用文字列は別関数であり、本文とは混同しない)を確認した
- [x] `model/blocks.py`/`model/inline.py`の全variantを確認し、再構築ロジックを網羅する

## 変更予定ファイル

- `src/wikiepwing/normalize/whitespace.py`
- `tests/test_normalize_whitespace.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_whitespace.py
make check
git diff --check
```

## 完了条件

- [x] `normalize_text(text) -> str`がCRLF→LF、C0/C1制御文字除去(`\n`は保持)、ゼロ幅文字除去、連続空白の単一スペースへの圧縮を行う
- [x] `normalize_block_whitespace(block) -> Block`がBlock/Inlineの全variantを再帰的に処理する
- [x] `PreformattedBlock.text`/`CodeInline.value`/`CodeBlock.text`/`MathBlock.source`は変更されない
- [x] `ParagraphBlock`/`HeadingBlock`/list/definition list/quote内のネストした`TextInline`が正しく正規化される
- [x] `UnsupportedBlock.fallback_text`/`UnsupportedInline.fallback_text`も正規化される
- [x] `make check`が成功する

## 非対象

- Article/model DBへの統合(TASK-G012)
- 索引用文字列の正規化(`ARCHITECTURE.md` 13.2、別の関数・別タスク)

## 実施結果

- `src/wikiepwing/normalize/whitespace.py`に`normalize_text`/`normalize_block_whitespace`を実装した。
- `tests/test_normalize_whitespace.py`に14件のテストを追加。
- `uv run pytest tests/test_normalize_whitespace.py`: 14 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート593件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G011チェック)、`LOG.md`(新規エントリ)を更新した。
- ゼロ幅文字対象(ZWSP/ZWNJ/ZWJ/BOM)はdocumented assumption。
- 次タスク: TASK-G012 Normalize command and model DB write。
