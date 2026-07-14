# CURRENT_TASK.md

## Task ID

TASK-G010

## 目的

`TASKS.md` TASK-G010(依存: G004-G009)を実装する。これまでのG004-G009各変換関数(heading/paragraph/list/definition list/quote/preformatted)を1つにまとめる`convert_block`ディスパッチャと、文書レベルで隣接する非ブロック要素(素のテキスト/inline要素の並び)をひとつの`ParagraphBlock`にまとめる`convert_document`を実装する。認識できない要素(`<table>`/`<div>`ラッパー等、Table/Infobox/Image/Math/Referencesの実変換はEpic K/L/N/O以降)は`UnsupportedBlock`+`DOM_UNKNOWN_ELEMENT`診断で確実に情報を残す(`ARCHITECTURE.md` 11.7の例に合わせる)。`<hr>`は`PLAN.md` Phase 6の初期scopeにあるため`HorizontalRuleBlock`へ直接変換する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G010(依存: G004-G009)を読んだ
- [x] `ARCHITECTURE.md` 11.7のdiagnostic code例(`DOM_UNKNOWN_ELEMENT`)を確認した
- [x] これまで実装した`normalize/headings.py`/`paragraphs.py`/`lists.py`/`definition_lists.py`/`quotes.py`の`is_x`/`convert_x`関数群を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/convert_block.py`
- `tests/test_normalize_convert_block.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_convert_block.py
make check
git diff --check
```

## 完了条件

- [x] `convert_block(node) -> (Block, tuple[Diagnostic, ...])`がheading/paragraph/unordered list/ordered list/definition list/quote/preformattedそれぞれを正しくディスパッチする
- [x] `<hr>`を`HorizontalRuleBlock`へ変換する
- [x] 未知の要素(`<table>`等)を`UnsupportedBlock`(`element_name`/`fallback_text`(平坦化テキスト)/`diagnostic_code="DOM_UNKNOWN_ELEMENT"`)へ変換し、diagnosticを記録する
- [x] `convert_document(nodes) -> (tuple[Block, ...], tuple[Diagnostic, ...])`が、連続する素のテキスト/inline要素を1つの`ParagraphBlock`にまとめ、ブロック要素が現れるとそこで区切る
- [x] `make check`が成功する

## 非対象

- 空白正規化(TASK-G011)
- Article/model DBへの実際の統合(TASK-G012)
- Table/Infobox/Image/Math/Referencesの実HTML変換(Epic K/L/N/O)

## 実施結果

- `src/wikiepwing/normalize/convert_block.py`に`convert_block`/`convert_document`を実装した。
- `tests/test_normalize_convert_block.py`に11件のテストを追加。テスト作成中に、未知のblock-level要素(`<table>`)がinline bufferへ誤って蓄積されるバグを発見し、`_is_block_level`にHTML標準のblock-level tag集合を追加して修正した。
- `uv run pytest tests/test_normalize_convert_block.py`: 11 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート579件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G010チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-G011 Whitespace normalization。
