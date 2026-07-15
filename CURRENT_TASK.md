# CURRENT_TASK.md

## Task ID

TASK-Q004

## 目的

`ARCHITECTURE.md` 14.1/14.3(索引kind「cross_component」、Liteの「limited cross component」)・`DATA_CONTRACTS.md`のpriority提案(`100 cross component`)・`PLAN.md`の「クロス検索」節(候補source「redirect/alias components」)を実装する。titleおよびredirect aliasのうち複数単語(空白区切り)からなるものについて、各単語成分を個別の`kind="cross_component"`の`SearchTerm`として抽出する`cross_component_terms_for_article`を追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q004(依存: J007)を読んだ
- [x] `ARCHITECTURE.md` 14.1(SearchTerm.kindに`cross_component`)・14.3(Liteの「limited cross component」)・`DATA_CONTRACTS.md`のpriority提案(`100 cross component`)・`PLAN.md`の「クロス検索」節(候補source「redirect/alias components」)・`TESTING.md`の「cross component」headword categoryを確認した
- [x] 「cross component」の定義が"何を分解するか"詳細に明記されていないため、`PLAN.md`が挙げる「redirect/alias components」を一次情報源とし、title/redirect aliasを空白区切りで単語成分へ分解し、各成分を個別のsearch termにする、という解釈を採用した(例: "GNU Emacs" -> "GNU"・"Emacs")

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`(`cross_component_terms_for_article`追加)
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

- [x] titleが複数単語(空白区切り)の場合、各単語を`kind="cross_component"`・`priority=100`・`source="cross_component"`の`SearchTerm`として抽出する
- [x] redirect aliasも同様に各単語成分を抽出する
- [x] 単一単語のtitle/aliasからは何も抽出しない(分解する意味がないため)
- [x] 同一記事内で同じ正規化キーの成分が複数回出現しても重複したSearchTermを生成しない
- [x] `make check`が成功する

## 非対象

- Search budgets and stop rules(TASK-Q005、成分数の上限・stop word除去等)
- 実際の`rendered.sqlite3`永続化層への配線

## 実施結果

- `search_term.py`に`cross_component_terms_for_article`(`_CROSS_COMPONENT_PRIORITY=100`)を実装した。titleと各redirect aliasを空白で分割し、単語数が2以上の場合のみ各単語成分を抽出する。
- `tests/test_search_term.py`(新規5件)で、複数単語titleの分解・単一単語titleでの空・redirect alias成分の抽出・非redirect aliasの除外・重複除去を確認した。
- `make check`(format-check/lint/mypy/pytest 1260件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- 「cross component」の厳密な定義がARCHITECTURE.mdに詳細記載されていなかったため、`PLAN.md`の「クロス検索」節が挙げる「redirect/alias components」を一次情報源として採用した(空白区切りの単語成分分解という解釈)。
