# CURRENT_TASK.md

## Task ID

TASK-Q001

## 目的

`ARCHITECTURE.md` 14.3(Full profileの索引に含まれる「heading keyword」)・`DATA_CONTRACTS.md`のpriority提案(`400 heading keyword`)を実装する。`Article.blocks`中の`HeadingBlock`ごとに、その見出しテキストを`kind="keyword"`の`SearchTerm`として抽出する`heading_keyword_terms_for_article`を、`title_terms_for_article`/`category_terms_for_article`と同じ形で`search_term.py`に追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q001(依存: J007)を読んだ
- [x] `ARCHITECTURE.md` 14.1/14.3・`DATA_CONTRACTS.md`のpriority提案(`400 heading keyword`)を再確認した
- [x] `search_term.py`の既存パターン(`title_terms_for_article`/`category_terms_for_article`、`SearchTerm`のdataclass、`sort_search_terms`)を確認した
- [x] `category_terms_for_article`と同様、one-to-many(1つの見出しキーワードが複数記事の見出しに一致しうる)ため、`title_terms_for_article`には統合せず独立した関数として実装する方針にした

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`(`heading_keyword_terms_for_article`追加)
- `tests/test_search_term.py`(追記)
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

- [x] `Article.blocks`中の各`HeadingBlock`から見出しテキストを抽出し、`kind="keyword"`・`priority=400`・`source="heading"`の`SearchTerm`を生成する
- [x] 見出しがネストしたinline(strong/emphasis等)を含む場合もテキストを正しく平坦化する
- [x] 同一記事内で同じ正規化キーの見出しが複数回出現しても重複したSearchTermを生成しない
- [x] 空文字列になる見出し(inlineなし等)は無視する
- [x] 見出しが1つもない記事は空タプルを返す
- [x] `make check`が成功する

## 非対象

- Infobox keyword extraction(TASK-Q002)
- 実際の`rendered.sqlite3`永続化層への配線(`category_terms_for_article`と同様、現時点では独立したgenerator関数として提供するのみ)

## 実施結果

- `search_term.py`に`heading_keyword_terms_for_article`(`_HEADING_KEYWORD_PRIORITY=400`)と、inline木を平坦化する`_flatten_inline_text`を実装した。`category_terms_for_article`と同様、one-to-manyのため`title_terms_for_article`には統合しない独立した関数とした。同一記事内での正規化キー重複は除去する。
- `tests/test_search_term.py`(新規6件)で、見出しからのterm抽出・ネストしたinlineの平坦化・同一記事内での重複除去・空見出しの無視・見出しなし記事での空タプル・正規化キーの確認をした。
- `make check`(format-check/lint/mypy/pytest 1243件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- `category_terms_for_article`と同様、実際の`rendered.sqlite3`永続化層への配線は対象外(独立したgenerator関数として提供するのみ)。
