# CURRENT_TASK.md

## Task ID

TASK-G005

## 目的

`ARCHITECTURE.md` 12.2のpass `N50 Convert paragraphs and inline markup`の基礎部分を実装する。`<p>`要素を`ParagraphBlock`へ変換する構造的処理と、汎用的なinlineノード変換(`convert_inline_nodes`)を実装する。太字/斜体/code/line break等の具体的なinline要素認識は`TASKS.md`の依存グラフ上G006(依存: G005)が担うため、本タスクでは未知のinline要素を透過的に子要素へ再帰するdefault挙動のみを実装し、G006がdispatch tableへ具体的なtagハンドラを追加できる拡張可能な設計とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G005(依存: G003)とG006(依存: G005、strong/emphasis/code/line break)の依存関係を確認した
- [x] `ARCHITECTURE.md` 12.2(pass `N50`)を確認した
- [x] `model/blocks.py`の`ParagraphBlock`、`model/inline.py`の`TextInline`を確認した
- [x] `normalize/headings.py`(G004)のモジュール構成(`is_x`/`convert_x -> (Block, diagnostics)`パターン)を踏襲する

## 変更予定ファイル

- `src/wikiepwing/normalize/paragraphs.py`
- `tests/test_normalize_paragraphs.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_paragraphs.py
make check
git diff --check
```

## 完了条件

- [x] `convert_inline_nodes(nodes) -> tuple[Inline, ...]`がテキストノードを`TextInline`へ変換する
- [x] 未知のinline要素(G006未実装のためすべて未知)は透過的に子要素を再帰変換する(内容を失わない)
- [x] 連続するテキストノードや透過的要素をまたいだテキストが個別の`TextInline`として保持される(結合は行わない、順序を保持する)
- [x] `is_paragraph(node)`が`<p>`要素を判定する
- [x] `convert_paragraph(node) -> (ParagraphBlock, tuple[Diagnostic, ...])`が`<p>`の子要素を`convert_inline_nodes`で変換する
- [x] 空の`<p>`は空の`inlines`を持つ`ParagraphBlock`を返す(diagnosticは不要、空段落自体は不正ではないため)
- [x] `<p>`以外の要素を渡すと`ValueError`を送出する
- [x] `make check`が成功する

## 非対象

- 太字/斜体/code/line break等の具体的なinline要素認識(TASK-G006)
- リスト/定義リスト/引用/preformatted等の他ブロック変換(TASK-G007以降)
- 文書全体の組み立て(トップレベルノードをBlockへ振り分ける処理、TASK-G010/G012)

## 実施結果

- `src/wikiepwing/normalize/paragraphs.py`に`convert_inline_nodes`/`is_paragraph`/`convert_paragraph`を実装した。
- `tests/test_normalize_paragraphs.py`に8件のテストを追加。
- `uv run pytest tests/test_normalize_paragraphs.py`: 8 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート531件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G005チェック)、`LOG.md`(新規エントリ)を更新した。
- 未知inline要素の透過再帰は、G006がdispatchへ具体的なtagハンドラを追加できるよう設計した拡張ポイント。
- 次タスク: TASK-G006 Strong/emphasis/code/line break。
