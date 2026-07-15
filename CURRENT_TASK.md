# CURRENT_TASK.md

## Task ID

TASK-Q002

## 目的

`ARCHITECTURE.md` 14.3(Full profileの索引「infobox selected values」)・`DATA_CONTRACTS.md`のpriority提案(`300 infobox keyword`)を実装する。TASK-Q001の`heading_keyword_terms_for_article`と同じ形で、`InfoboxBlock`の各フィールドの値(name/labelではなくvalue)を平坦化して`kind="keyword"`の`SearchTerm`として抽出する`infobox_keyword_terms_for_article`を追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q002(依存: K009,J007)を読んだ
- [x] `ARCHITECTURE.md` 14.3・`DATA_CONTRACTS.md`のpriority提案(`300 infobox keyword`)を再確認した
- [x] `model/blocks.py`の`InfoboxField.value`(`tuple[Block, ...]`、TASK-K009の`build_infobox_block`が`convert_document`で構築)を確認し、`ParagraphBlock`以外のBlock型が来る可能性があるため、`mini_layout.py`と同様のduck-typed再帰flattenを実装する方針にした
- [x] TASK-Q001の`heading_keyword_terms_for_article`と同じ重複除去・one-to-many分離の設計を踏襲する

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`(`infobox_keyword_terms_for_article`, `_flatten_block_text`追加)
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

- [x] `InfoboxBlock`の各フィールドの`value`(`ParagraphBlock`等)を平坦化して`kind="keyword"`・`priority=300`・`source="infobox"`の`SearchTerm`を生成する
- [x] フィールド名(name/label)自体はkeywordとして抽出しない(value側のみ)
- [x] 同一記事内で同じ正規化キーが複数回出現しても重複したSearchTermを生成しない
- [x] 空文字列になるフィールド値は無視する
- [x] Infoboxが1つもない記事は空タプルを返す
- [x] `make check`が成功する

## 非対象

- Lead alias extraction(TASK-Q003)
- 実際の`rendered.sqlite3`永続化層への配線

## 実施結果

- `search_term.py`に`infobox_keyword_terms_for_article`(`_INFOBOX_KEYWORD_PRIORITY=300`)と、`InfoboxField.value`(`tuple[Block,...]`)をduck-typedに再帰flattenする`_flatten_block_text`を実装した。フィールド名(label)は抽出せず、value側のみを対象にした。
- `tests/test_search_term.py`(新規5件)で、フィールド値からのterm抽出・フィールド名の除外・重複除去・空値の無視・infoboxなし記事での空タプルを確認した。
- `make check`(format-check/lint/mypy/pytest 1248件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
