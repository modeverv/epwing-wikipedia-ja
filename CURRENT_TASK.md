# CURRENT_TASK.md

## Task ID

TASK-Q005

## 目的

`CONFIG_REFERENCE.md`の`[search]` `max_terms_per_article`(「keyword/cross termsの爆発防止。title/redirectは別budget扱い可能」)・`max_key_bytes`・`PLAN.md`の「stop words」を実装する。TASK-Q001-Q004が生成する`keyword`/`cross_component`種別のSearchTermに対してのみ`max_terms_per_article`の上限を適用し(title/redirect/alias/category/readingは別budgetとして常に通す)、`max_key_bytes`を超えるkeyのtermと、stop word集合に含まれるtermを除外する`apply_search_budgets`を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q005(依存: Q001-Q004)を読んだ
- [x] `CONFIG_REFERENCE.md`の`max_terms_per_article`(「title/redirectは別budget扱い可能」)・`max_key_bytes`を再確認した
- [x] `PLAN.md`の「stop words」(具体的な単語リストはどのドキュメントにも記載がない)を確認し、stop word集合は呼び出し側が注入するパラメータとして実装し、具体的な単語リスト自体はこのタスクの対象外とする方針にした
- [x] `sort_search_terms`(priority降順+安定tie-break)を先に適用してから budget truncationすることで、budget超過時に優先度の高いtermが優先的に残るようにする設計にした

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`(`apply_search_budgets`追加)
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

- [x] `kind`が`keyword`/`cross_component`のtermのみ`max_terms_per_article`の対象になる(title/redirect/alias/category/readingは常に通る)
- [x] budget超過時、priorityの高いtermが優先的に残る(`sort_search_terms`の順序を尊重)
- [x] `max_key_bytes`(UTF-8バイト長)を超えるtermは種別を問わず除外される
- [x] `stop_words`(正規化済みキーの集合)に含まれる`keyword`/`cross_component`のtermは除外される
- [x] `make check`が成功する

## 非対象

- Full profile(TASK-Q006)
- 具体的なstop word一覧の選定(呼び出し側が注入するパラメータとして扱う)

## 実施結果

- `search_term.py`に`apply_search_budgets`(`_BUDGETED_KINDS = {"keyword", "cross_component"}`)を実装した。`sort_search_terms`で優先度降順に並べたうえで、`max_key_bytes`超過・stop word一致(budgeted kindのみ)・`max_terms_per_article`超過(budgeted kindのみ)を順にフィルタする。
- `tests/test_search_term.py`(新規7件)で、keyword/cross_componentのbudget上限・title/redirectの除外・budget超過時の高優先度term保持・key長超過の除外・stop wordの除外(budgeted kindのみ)・空入力を確認した。
- `make check`(format-check/lint/mypy/pytest 1267件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- 具体的なstop word一覧の選定は対象外とした(呼び出し側が注入するパラメータとして実装、デフォルトは空集合)。
