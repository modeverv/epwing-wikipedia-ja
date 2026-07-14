# CURRENT_TASK.md

## Task ID

TASK-G002

## 目的

`ARCHITECTURE.md` 12.2のpass構成における`N10 Root selection`(HTML parse後・unsafe node除去前)を実装する。Wikimedia Enterprise/MediaWikiのレンダリング済みHTMLでは本文が`<div class="mw-parser-output">`でラップされるのが一般的な慣行であるため、これを優先的に検出し、無い場合は`<body>`、それも無い場合はdocument直下をcontent rootとして選択する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G002(依存: G001、実装note無し)を読んだ
- [x] `ARCHITECTURE.md` 12.2(pass構成: N00 Parse HTML → N10 Root selection → N20 Remove unsafe/non-content nodes → ...)を確認した。G002はcontainer選択のみを担当し、node除去自体はG003の責務であることを確認した
- [x] `tests/fixtures/enterprise/*.ndjson`の`article_body.html`が`<html><body><p>...</p></body></html>`という素朴な合成fixtureであり、`mw-parser-output`等の実際のWikipediaラッパーを含まないことを確認した
- [x] `ARCHITECTURE.md`/`DATA_CONTRACTS.md`/`PLAN.md`のいずれにも具体的なselector/wrapper要素名の明文化が無いことを確認した。`mw-parser-output`はMediaWiki/Wikimedia Enterpriseのレンダリング済みHTMLで本文をラップする一般的な規約であり、この慣行に基づくdocumented assumptionとして実装する

## 変更予定ファイル

- `src/wikiepwing/normalize/root_selection.py`
- `tests/test_normalize_root_selection.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_root_selection.py
make check
git diff --check
```

## 完了条件

- [x] `select_root_content(document: ElementNode) -> tuple[Node, ...]`が`class`属性に`mw-parser-output`トークンを含む最初の`div`要素の子要素を返す
- [x] `mw-parser-output`が無い場合、最初の`<body>`要素の子要素を返す
- [x] どちらも無い場合、document直下(parse_htmlの`#document`ルート)の子要素をそのまま返す
- [x] `mw-parser-output`が`<body>`の内側にネストしていても正しく検出される
- [x] `make check`が成功する

## 非対象

- Unsafe/UI node除去(TASK-G003)
- Block/Inlineへの実際の変換(TASK-G004以降)

## 実施結果

- `src/wikiepwing/normalize/root_selection.py`に`select_root_content`を実装した。
- `tests/test_normalize_root_selection.py`に5件のテストを追加。
- `uv run pytest tests/test_normalize_root_selection.py`: 5 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート507件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G002チェック)、`LOG.md`(新規エントリ)を更新した。
- `mw-parser-output`セレクタの採用はdocumented assumption(実データでの検証は将来のタスク)。
- 次タスク: TASK-G003 Unsafe/UI node removal。
