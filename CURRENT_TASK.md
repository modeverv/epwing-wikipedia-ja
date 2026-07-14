# CURRENT_TASK.md

## Task ID

TASK-J005

## 目的

`DATA_CONTRACTS.md` 8(SearchTerm contract)のpriority proposal(1000 exact title 〜 100 cross component の10段階スケール)と衝突時の安定sort規則(`normalized_key`, `target_entry_id`, `source`)を実装する。TASK-H008/J002-J004で導入した優先度定数(`_TITLE_PRIORITY=0`等、数値が小さいほど優先という暫定のローカルスケール)を、DATA_CONTRACTS.mdの正式スケール(数値が大きいほど優先)へ置き換える。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-J005(依存: J002-J004)を読んだ
- [x] `DATA_CONTRACTS.md` 8のpriority proposal・"同priorityは`normalized_key`, `target_entry_id`, `source`で安定sort"を再確認した
- [x] 既存`search_term.py`の暫定優先度定数(0/10/20/30/40、小さいほど優先)を確認した

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`(優先度定数をDATA_CONTRACTS.mdスケールへ置き換え、`sort_search_terms()`を追加)
- `tests/test_search_term.py`(優先度の大小関係のテストを新スケールに合わせて修正、安定sortのテストを追加)
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

- [x] title=1000, redirect=900, kana variant=600(DATA_CONTRACTS.mdの明示値)、space/punctuation variantは"800 normalized title variant"として扱う
- [x] `sort_search_terms(terms)`が、priority降順、同priority内は`normalized_key`, `target_page_id`, `source`で安定sortする
- [x] `make check`が成功する

## 非対象

- alias/category/keyword/cross_componentの生成(まだどのコードも生成していない、将来のEPIC J/K/L)
- collision repository/report(TASK-J006、dropped候補のレポート)

## 実施結果

- `search_term.py`の優先度定数をDATA_CONTRACTS.mdのスケール(数値が大きいほど優先)へ置き換えた: title=1000、redirect=900、space/punctuation variant=800(normalized title variant)、kana variant=600。
- `sort_search_terms(terms)`を実装した。priority降順、同priority内は`normalized_key`→`target_page_id`→`source`の昇順で安定sortする。
- 優先度スケールの向きが変わったことで既存の`test_title_priority_is_higher_than_redirect_priority`のassertion(`<`)を`>`へ修正した(数値が大きい方が優先という新スケールと整合)。
- `tests/test_search_term.py`に、優先度スケールの検証テストと`sort_search_terms`のpriority降順/tie-break動作を確認するテスト3件を追加した。
- `make check`(format-check/lint/mypy/pytest 824件)と`git diff --check`が成功した。
