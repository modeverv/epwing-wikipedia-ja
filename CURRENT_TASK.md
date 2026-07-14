# CURRENT_TASK.md

## Task ID

TASK-H008

## 目的

`ARCHITECTURE.md` 14.1(SearchTerm)を実装し、Articleから"title terms"(記事title本体、および`TASK-H004`のredirect由来alias)を`SearchTerm`列へ変換する関数を実装する。reading/category/keyword/cross_component等の他kindは対象外(将来のtask)とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H008(依存: H004,H006)を読んだ
- [x] `ARCHITECTURE.md` 14.1(SearchTerm dataclass)・14.2(衝突規則、参考情報)・14.3(プロファイル別索引、参考情報)を確認した
- [x] `ingest/repository.py`の`normalize_title`を再利用する

## 変更予定ファイル

- `src/wikiepwing/search/__init__.py`
- `src/wikiepwing/search/search_term.py`
- `tests/test_search_term.py`
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

- [x] `SearchTerm`(`ARCHITECTURE.md` 14.1の全field)を実装し、`key`/`normalized_key`/`source`が非空文字列、`target_page_id`が正の整数、`kind`が既定の7値のいずれかであることを検証する
- [x] `title_terms_for_article(article) -> tuple[SearchTerm, ...]`が記事title自身を`kind="title"`のSearchTermへ変換する
- [x] `article.aliases`のうち`source="redirect"`のものを`kind="redirect"`のSearchTermへ変換する
- [x] title側の`priority`がredirect側より高い(数値が小さい)
- [x] `make check`が成功する

## 非対象

- reading/category/keyword/cross_component kindの生成(将来のtask)
- 衝突規則(14.2)・プロファイル別索引(14.3)の実装(Epic後半)

## 実施結果

- `src/wikiepwing/search/__init__.py`(新規パッケージ)、`src/wikiepwing/search/search_term.py`に`SearchTerm`/`SearchTermError`/`title_terms_for_article`を実装した。
- `tests/test_search_term.py`に7件のテストを追加。
- `uv run pytest tests/test_search_term.py`: 7 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート679件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H008チェック)、`LOG.md`(新規エントリ)を更新した。
- priority値(title=0, redirect=10)はdocumented assumption。
- 次タスク: TASK-H009 FreePWING source writer。
