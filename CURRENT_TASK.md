# CURRENT_TASK.md

## Task ID

TASK-J001

## 目的

`ARCHITECTURE.md` 14(Search architecture)と`DATA_CONTRACTS.md` 8(SearchTerm contract、例: `"key": "Ｅｍａｃｓ"` -> `"normalized_key": "emacs"`)が要求する索引キー正規化を、単一の正本関数として明文化する。現状`search_term.py`は`ingest.repository.normalize_title`(NFKC + strip のみ、大文字小文字を畳み込まない)を流用しており、`Ｅｍａｃｓ`は`Emacs`にはなるが`emacs`にはならず、DATA_CONTRACTS.mdの例と食い違う。EPIC J以降(NFKC/case/space variants、kana variants、punctuation variants)が積み上がる土台として、検索索引専用の正規化契約を`search`パッケージ内に切り出す。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-J001(依存: H008)を読んだ
- [x] `ARCHITECTURE.md` 14.1-14.3(SearchTerm/衝突規則/プロファイル別索引)を確認した
- [x] `DATA_CONTRACTS.md` 8(SearchTerm contract、priority proposal)を確認した
- [x] 既存`search/search_term.py`が`ingest.repository.normalize_title`(NFKC+strip、case-fold無し)を流用しており、DATA_CONTRACTS.mdの例(`Ｅｍａｃｓ` -> `emacs`)を満たさないことに気づいた

## 変更予定ファイル

- `src/wikiepwing/search/normalize_key.py`(新規: `normalize_index_key()`)
- `src/wikiepwing/search/search_term.py`(`normalize_title`の代わりに`normalize_index_key`を使うよう変更)
- `tests/test_search_normalize_key.py`(新規)
- `tests/test_search_term.py`(既存テストが新しい正規化結果と整合するか確認・必要なら更新)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_search_normalize_key.py tests/test_search_term.py
make check
git diff --check
```

## 完了条件

- [x] `normalize_index_key(text)`が、NFKC正規化・Unicode case-fold・空白の畳み込みとtrimを行う
- [x] `normalize_index_key("Ｅｍａｃｓ") == "emacs"`(DATA_CONTRACTS.md 8の例と一致)
- [x] `search_term.title_terms_for_article`が`normalize_index_key`を使うよう切り替わる
- [x] `make check`が成功する

## 非対象

- kana variant・punctuation variant・alias priority統一・collision repository(TASK-J002-J006)
- `ingest.repository.normalize_title`自体の変更(ingest側の重複解決に使われており、別の関心事のため据え置く)

## 実施結果

- `src/wikiepwing/search/normalize_key.py`に`normalize_index_key()`/`NormalizeKeyError`を実装した。NFKC正規化→Unicode case-fold(`str.casefold()`)→空白ランの単一スペースへの畳み込み→trimを行い、結果が空文字列なら`NormalizeKeyError`を送出する。
- `search_term.py`の`title_terms_for_article`を、`ingest.repository.normalize_title`ではなく新しい`normalize_index_key`を使うよう変更した。
- `tests/test_search_normalize_key.py`(新規8件)で、全角→半角小文字化(DATA_CONTRACTS.mdの例)・大文字小文字畳み込み・前後/内部空白・全角空白・日本語保持・空文字列/空白のみでのエラーを確認した。既存`tests/test_search_term.py`は変更なしで7件成功した。
- `make check`(format-check/lint/mypy/pytest 794件)と`git diff --check`が成功した。
