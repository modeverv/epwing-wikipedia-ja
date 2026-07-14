# CURRENT_TASK.md

## Task ID

TASK-L005

## 目的

`ARCHITECTURE.md` 14.3(Full profileの"category")と`DATA_CONTRACTS.md` 8のpriority proposal("500 category")を実装する。各記事のカテゴリからSearchTermを生成する。設計上重要な点: カテゴリは本質的に「1カテゴリ名 → 複数記事」の一対多関係であり、これまでのtitle/redirect/variant SearchTerm(1キー→1記事、衝突時はTASK-J006で単一勝者に解決)とは性質が異なる。単一headword→単一entryしか表現できない現在のFreePWING backend(`headwords_for_articles`が`resolve_single_candidate_per_key`で単一候補へ解決する設計)へcategory termsをそのまま混ぜると、同じカテゴリの記事群が誤って1つに潰されてしまう。そのため、本タスクのcategory term生成は`title_terms_for_article`とは独立した関数とし、`headwords_for_articles`の単一候補解決パスには**通さない**設計にする(将来、複数候補を保持できる`rendered.sqlite3`の`search_terms`テーブル実装時に接続する)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-L005(依存: L004,J007)を読んだ
- [x] `ARCHITECTURE.md` 14.3・`DATA_CONTRACTS.md` 8(500 category)を再確認した
- [x] TASK-J006の`resolve_single_candidate_per_key`・TASK-J007の`headwords_for_articles`を再確認し、カテゴリという一対多の性質がこれらと相容れないことに気づいた
- [x] `DATA_CONTRACTS.md` 7の`search_terms`テーブル(正規化キーへのUNIQUE制約無し、複数候補を保持できる設計)が、カテゴリのような一対多検索に本来適した永続化層であることを再確認した(TASK-J006で気づき済み、まだ未実装)

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`(`category_terms_for_article()`を追加、`title_terms_for_article`とは独立)
- `tests/test_search_term.py`(category term生成の回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

## 完了条件

- [x] `category_terms_for_article(article)`が、`article.categories`の各カテゴリについて`kind="category"`・priority=500のSearchTermを生成する
- [x] カテゴリが無い記事は空タプルを返す
- [x] `title_terms_for_article`の出力には含まれない(独立した関数のまま)
- [x] `make check`が成功する

## 非対象

- `headwords_for_articles`/`resolve_single_candidate_per_key`への実配線(一対多の性質上、単一候補解決とは相容れないため対象外)
- `rendered.sqlite3`の`search_terms`テーブル永続化層(別タスク)

## 実施結果

- `src/wikiepwing/search/search_term.py`に`category_terms_for_article()`を実装した。`article.categories`の各カテゴリについて`kind="category"`・priority=500(`_CATEGORY_PRIORITY`)・`source="category"`のSearchTermを1件ずつ生成する。`title_terms_for_article`とは独立した関数のまま維持した(一対多の性質上、`headwords_for_articles`の単一候補解決へ混ぜるべきでない理由をモジュールdocstringに明記)。
- `tests/test_search_term.py`への追加4件(複数カテゴリからの複数term生成・normalize_index_keyの適用確認・カテゴリ無し記事での空タプル・title_terms_for_articleに含まれないことの確認)を実装した。
- `make check`(format-check/lint/mypy/pytest 939件)と`git diff --check`が成功した。
