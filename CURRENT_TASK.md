# CURRENT_TASK.md

## Task ID

TASK-H006

## 目的

`ARCHITECTURE.md` 16(RenderedEntry)を実装する。`entry_id`/`page_id`/`title`/`headwords`/`body`/`internal_targets`/`graphics`/`estimated_size`/`diagnostics`を持つ`RenderedEntry` dataclassを定義する。`body: tuple[RenderNode, ...]`の`RenderNode`型は`ARCHITECTURE.md`に詳細な仕様が無いため、Mini layout renderer(TASK-H007)が拡張できる最小限のテキスト/改行のみの表現(`TextRenderNode`/`LineBreakRenderNode`)を暫定定義する。ArticleからRenderedEntryへの実際の変換ロジックはTASK-H007の範囲であり、本タスクは型定義のみを対象とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H006(依存: H005)とH007(Mini layout renderer、依存: H006,G012)を読んだ
- [x] `ARCHITECTURE.md` 16(RenderedEntry dataclass定義)・16.1(entry ID)・16.2(標準レイアウトのテキスト例)を確認した
- [x] `render/entry_id.py`(H005)の`compute_entry_id`を確認した
- [x] `model/diagnostics.py`の`Diagnostic`を再利用する

## 変更予定ファイル

- `src/wikiepwing/render/render_node.py`
- `src/wikiepwing/render/rendered_entry.py`
- `tests/test_render_render_node.py`
- `tests/test_render_rendered_entry.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_render_node.py tests/test_render_rendered_entry.py
make check
git diff --check
```

## 完了条件

- [x] `TextRenderNode`(`text: str`)/`LineBreakRenderNode`(フィールド無し)と`RenderNode`(union)を実装する
- [x] `RenderedEntry`(`ARCHITECTURE.md` 16の全field)を実装し、`entry_id`/`title`が非空文字列、`page_id`が正の整数、`estimated_size`が非負整数であることを検証する
- [x] `make check`が成功する

## 非対象

- ArticleからRenderedEntryへの実際の変換(TASK-H007 Mini layout renderer)
- Table/Infobox等を表現するRenderNode variant(必要になれば別タスクで拡張)

## 実施結果

- `src/wikiepwing/render/render_node.py`に`TextRenderNode`/`LineBreakRenderNode`/`RenderNode`を実装した。
- `src/wikiepwing/render/rendered_entry.py`に`RenderedEntry`/`RenderedEntryError`を実装した。
- `tests/test_render_render_node.py`(2件)、`tests/test_render_rendered_entry.py`(6件)を追加。
- `uv run pytest tests/test_render_render_node.py tests/test_render_rendered_entry.py`: 8 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート660件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H006チェック)、`LOG.md`(新規エントリ)を更新した。
- `RenderNode`の形状はARCHITECTURE.mdに明文化が無いdocumented assumption(text/line breakのみの最小限)。
- 次タスク: TASK-H007 Mini layout renderer。
