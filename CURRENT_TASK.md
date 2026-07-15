# CURRENT_TASK.md

## Task ID

TASK-Q003

## 目的

`ARCHITECTURE.md` 13(alias source「lead sentenceのbold alias」)・14.3(Full profileの索引「lead bold term」)・`DATA_CONTRACTS.md`のpriority提案(`200 lead term`)を実装する。記事本文の先頭(見出し前)の`ParagraphBlock`(lead paragraph)内で太字(`StrongInline`)になっているspanを、`kind="alias"`・`priority=200`・`source="lead"`の`SearchTerm`として抽出する`lead_alias_terms_for_article`を追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q003(依存: G012,J007)を読んだ
- [x] `ARCHITECTURE.md` 13(「lead sentenceのbold alias（後期実装）」)・14.3・`DATA_CONTRACTS.md`のpriority提案(`200 lead term`)を再確認した
- [x] Wikipedia記事の典型パターン(先頭段落で記事タイトルとその別名が太字で示される、例:「**GNU Emacs**（しばしば**Emacs**と略される）は...」)を踏まえ、lead paragraphは「最初の見出しより前に出現する最初のParagraphBlock」と定義した
- [x] タイトル自身と正規化キーが一致するbold spanは、既に`title_terms_for_article`が`priority=1000`でカバーしているため、重複除去の対象にした

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`(`lead_alias_terms_for_article`追加)
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

- [x] 最初の見出しより前にある最初の`ParagraphBlock`中の`StrongInline`テキストを`kind="alias"`・`priority=200`・`source="lead"`の`SearchTerm`として抽出する
- [x] 見出しより後に現れる`ParagraphBlock`のbold spanは対象外
- [x] 記事タイトルと同じ正規化キーのbold spanは除外する(title_termsで既にカバー済みのため)
- [x] 同一記事内で同じ正規化キーのbold spanが複数回出現しても重複したSearchTermを生成しない
- [x] lead paragraphが存在しない、またはbold spanがない記事は空タプルを返す
- [x] `make check`が成功する

## 非対象

- Cross component extraction(TASK-Q004)
- 実際の`rendered.sqlite3`永続化層への配線

## 実施結果

- `search_term.py`に`lead_alias_terms_for_article`(`_LEAD_ALIAS_PRIORITY=200`)・`_first_lead_paragraph`(最初の見出しより前の最初の`ParagraphBlock`を返す)・`_strong_texts`(`StrongInline`のテキストを再帰的に収集)を実装した。タイトル自身と正規化キーが一致するbold spanは除外する。
- `tests/test_search_term.py`(新規7件)で、bold spanの抽出・見出し後のparagraph除外・タイトル自身の除外・重複除去・bold spanなし/paragraphなし/blocksなしでの空タプルを確認した。
- `make check`(format-check/lint/mypy/pytest 1255件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
