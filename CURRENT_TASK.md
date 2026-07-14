# CURRENT_TASK.md

## Task ID

TASK-J002

## 目的

`ARCHITECTURE.md` 14 / `PLAN.md`のNFKC/case/space variantsを実装する。設計を詰める過程で気づいた点: NFKC正規化とcase-foldの2軸は、TASK-J001の`normalize_index_key`が**クエリ側にも同じ関数を適用する前提**(TASK-J007のbackend search mappingで保証される)であれば、既存の1つの`normalized_key`だけで自動的に吸収される――全角`Ｅｍａｃｓ`で検索しても半角`Emacs`で検索しても、双方が`normalize_index_key`を通れば同じ`"emacs"`になるため、別々のSearchTermを追加登録する必要が無い。一方で**空白**は事情が異なる: `normalize_index_key`は空白の「連続run」を1個のスペースへ畳み込むだけで、空白を完全に除去はしない。したがって"New York"(スペース1個)と"NewYork"(スペース無し)は正規化しても別の文字列のままであり、ユーザーがスペース無しで検索した場合にヒットさせるには、**スペース除去済みの別バリアントを明示的にSearchTermとして追加登録する**必要がある。本タスクはこの空白除去バリアント生成を実装する(NFKC/case軸は追加実装不要であることをテストで明示する)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-J002(依存: J001)を読んだ
- [x] `ARCHITECTURE.md` 14.1-14.3・`DATA_CONTRACTS.md` 8を再確認した
- [x] TASK-J001の`normalize_index_key`がNFKC+case-fold+空白run畳み込みを行うことを確認した
- [x] NFKC/case軸は共有の正規化関数で双方向に吸収されるが、空白の完全除去だけは別途バリアント生成が必要であることに気づいた

## 変更予定ファイル

- `src/wikiepwing/search/space_variant.py`(新規: `space_removed_variant()`)
- `src/wikiepwing/search/search_term.py`(`title_terms_for_article`が空白除去バリアントも生成するよう拡張)
- `tests/test_search_space_variant.py`(新規)
- `tests/test_search_term.py`(空白除去バリアント生成の回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_search_space_variant.py tests/test_search_term.py tests/test_search_normalize_key.py
make check
git diff --check
```

## 完了条件

- [x] `space_removed_variant(normalized_key)`が、空白を含む場合は空白除去済み文字列を返し、含まない場合は`None`を返す(重複SearchTerm防止)
- [x] `title_terms_for_article`が、titleおよびredirectエイリアスそれぞれについて、空白除去バリアントが元と異なる場合のみ`kind="alias"`のSearchTermを追加生成する
- [x] NFKC/case軸(全角⇔半角、大文字⇔小文字)は`normalize_index_key`だけで双方向に吸収されることをテストで明示する(新規SearchTerm生成が不要であることの根拠)
- [x] `make check`が成功する

## 非対象

- kana variant(TASK-J003)・punctuation variant(TASK-J004)
- alias priority統一(TASK-J005)・collision repository(TASK-J006)・backend search mapping(TASK-J007、クエリ側にも`normalize_index_key`を適用する実配線はここで行う)

## 実施結果

- `src/wikiepwing/search/space_variant.py`に`space_removed_variant()`を実装した(空白を全て除去した文字列を返し、変化が無ければ`None`)。
- `search_term.py`の`title_terms_for_article`を拡張し、titleおよび各redirectエイリアスについて、空白除去バリアントが元と異なる場合に`kind="alias"`・`source="nfkc_case_space_variant"`のSearchTermを追加生成するようにした。
- 既存の`test_title_terms_include_redirect_aliases`が、新しく挿入される空白除去バリアントによりkeysの並びが変わったため、redirect種別のみを抽出して比較する形に修正した。
- `tests/test_search_space_variant.py`(新規4件)・`tests/test_search_term.py`への追加3件(複数単語title/単一単語title/複数単語alias)・`tests/test_search_normalize_key.py`への追加2件(全角⇔半角、大文字⇔小文字が`normalize_index_key`だけで収束することの明示)を実装した。
- `make check`(format-check/lint/mypy/pytest 803件)と`git diff --check`が成功した。
