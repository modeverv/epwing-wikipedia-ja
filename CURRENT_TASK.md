# CURRENT_TASK.md

## Task ID

TASK-H007

## 目的

`ARCHITECTURE.md` 16.2(標準レイアウト)を実装する。Articleを`RenderedEntry`(TASK-H006)へ変換する。タイトル・別名・更新日・導入文・見出し番号付き本文(1./1.1形式)・カテゴリ・出典情報を、EPWING画面幅を考慮した単純なplain textへ変換する。Table render policy(16.3、Epic K)・Entry size budget超過時の分割(16.4)は本タスクでは対象外とし、現状Table/InfoboxBlockを生成する変換器が無いため(Epic K/L未実装)実質的に発生しない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H007(依存: H006,G012)を読んだ
- [x] `ARCHITECTURE.md` 16.2(標準レイアウトのテキスト例)・16.3(Table render policy、対象外)・16.4(Entry size budget、対象外)を確認した
- [x] `render/entry_id.py`(`compute_entry_id`)・`render/rendered_entry.py`(`RenderedEntry`)・`render/render_node.py`(`TextRenderNode`)を確認した
- [x] `model/article.py`(`Article`)・`model/blocks.py`の全variantを確認した

## 変更予定ファイル

- `src/wikiepwing/render/mini_layout.py`
- `tests/test_render_mini_layout.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_mini_layout.py
make check
git diff --check
```

## 完了条件

- [x] `render_article_to_entry(article) -> RenderedEntry`がtitle/別名/更新日/導入文/本文/カテゴリ/出典情報を含むplain textを生成する
- [x] 見出しが1./1.1形式で正しく番号付けされる(兄弟見出しの連番、深いネストの復帰を含む)
- [x] paragraph/list/definition list/quote/preformatted/horizontal rule/unsupportedのfallback_textが本文へ反映される
- [x] `entry_id`が`compute_entry_id(article.page_id)`と一致する
- [x] `headwords`が記事titleと全aliasを含む
- [x] `estimated_size`が生成したtextのUTF-8バイト数と一致する
- [x] `diagnostics`が`article.diagnostics`をそのまま引き継ぐ
- [x] `make check`が成功する

## 非対象

- Table render policy(TASK-H007の範囲外、Epic K)
- Entry size budget超過時の分割(16.4、後続task)
- internal_targets/graphicsの実際の解決(link resolution・image epicは別途)

## 実施結果

- `src/wikiepwing/render/mini_layout.py`に`render_article_to_entry`(`_HeadingNumberer`等の内部ヘルパーを含む)を実装した。
- `tests/test_render_mini_layout.py`に12件のテストを追加。
- `uv run pytest tests/test_render_mini_layout.py`: 12 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート672件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H007チェック)、`LOG.md`(新規エントリ)を更新した。
- Table render policy/Entry size budget超過時の分割は非対象。
- 次タスク: TASK-H008 SearchTerm model and title terms。
