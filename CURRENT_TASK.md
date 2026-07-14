# CURRENT_TASK.md

## Task ID

TASK-J007

## 目的

`ARCHITECTURE.md` 17.2(FreePWING adapter)と`ARCHITECTURE.md` 14(Search architecture)を接続する。既存の`mini_layout.render_article_to_entry`は`article.title` + 全aliasという素朴なheadword生成しか行っておらず、TASK-H008/J001-J006で構築したSearchTerm基盤(title/redirect/space/kana/punctuation variant、priority、衝突解決)を一切使っていなかった。本タスクで、ビルド対象の全記事にまたがってSearchTermを生成し、TASK-J006の`resolve_single_candidate_per_key`でグローバルに衝突解決した上で、記事ごとのheadwordリストへ再構成し、実際のFreePWING出力(`entries.jsonl`)へ反映する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-J007(依存: B009,J006)を読んだ。B009は完了済み。
- [x] `mini_layout.render_article_to_entry`が`title_terms_for_article`を使っておらず、単純に`article.title`+全aliasをheadwordにしていることに気づいた
- [x] `render/verify.py`のDUPLICATE_HEADWORDチェック(異なるentry間で同一headword文字列を許さない)が、実質的に単一候補per keyの制約であることを確認した(TASK-J006の`resolve_single_candidate_per_key`がそのまま適用できる)

## 変更予定ファイル

- `src/wikiepwing/search/backend_mapping.py`(新規: `headwords_for_articles()`)
- `src/wikiepwing/render/mini_layout.py`(`render_article_to_entry`に`headwords`オーバーライド引数を追加)
- `src/wikiepwing/render/generate.py`(`_render_all`を2パス化し、全記事のheadwordsをグローバルに解決してから各entryへ反映)
- `tests/test_search_backend_mapping.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_search_backend_mapping.py tests/test_render_generate.py tests/test_render_mini_layout.py tests/test_mini_end_to_end_build.py
make check
git diff --check
```

## 完了条件

- [x] `headwords_for_articles(articles)`が、全記事のSearchTermをまとめて衝突解決し、記事ごとにpriority順のheadwordタプルを返す
- [x] 衝突で自記事のSearchTermが全て他記事に奪われても、自身のtitleは必ずheadwordsに残る
- [x] `render_article_to_entry`が`headwords`引数を受け取れる(省略時は既存の素朴な生成にフォールバックし、単体記事テストとの後方互換を保つ)
- [x] `render/generate.py`の`_render_all`が、全記事を先にデコードしてから`headwords_for_articles`を1回だけ呼び、各entryへ適用する
- [x] `make check`が成功する

## 非対象

- `rendered.sqlite3`本体の永続化層(`search_terms`テーブル、TASK-J006で対象外とした通り)
- reading/category/keyword/cross_component SearchTermの生成(まだ実装されていない)

## 実施結果

- `src/wikiepwing/search/backend_mapping.py`に`headwords_for_articles()`を実装した。全記事の`title_terms_for_article`をまとめて`resolve_single_candidate_per_key`(TASK-J006)へ通し、勝者を`target_page_id`で再グルーピング、priority降順で並べてheadwordタプルを返す。衝突で自記事のSearchTermが全滅しても、自身の`article.title`は必ず先頭に残るようにした。
- `render/mini_layout.py`の`render_article_to_entry`に`headwords: tuple[str, ...] | None = None`引数を追加した(省略時は従来通り`article.title`+全alias)。
- `render/generate.py`の`_render_all`を2パス化した: 先にDBから全articleをデコードし、`headwords_for_articles`を1回だけ呼んでから各entryへ適用する(記事間のSearchTerm衝突をグローバルに解決するため)。
- `tests/test_search_backend_mapping.py`(新規4件: 単一記事のtitle+redirect、無関係な2記事、variant衝突時の勝者決定、自記事titleが必ず残ること)を実装した。既存の`test_render_generate.py`・`test_render_mini_layout.py`・`test_mini_end_to_end_build.py`は変更無しで成功した。
- `make check`(format-check/lint/mypy/pytest 835件)と`git diff --check`が成功した。
