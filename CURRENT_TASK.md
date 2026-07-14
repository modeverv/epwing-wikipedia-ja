# CURRENT_TASK.md

## Task ID

TASK-J004

## 目的

`ARCHITECTURE.md` 14 / `PLAN.md`のpunctuation variantsを実装する。TASK-J002(space variant)・TASK-J003(kana variant)と同じパターンで、`normalize_index_key`(NFKC+case-fold+空白畳み込み)だけでは吸収できない軸を追加のSearchTermとして補う。対象は句読点・記号(中黒「・」、波ダッシュ、括弧、ハイフン、句点等)で、ユーザーがこれらの記号を省略して検索することが多いため、記号を全て除去したバリアントキーを追加登録する。個別の記号を都度列挙するのではなく、Unicodeの`unicodedata.category`が"P"(Punctuation)で始まる文字を機械的に除去する客観的な定義を採用する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-J004(依存: J001)を読んだ
- [x] TASK-J002(space_variant)・TASK-J003(kana_variant)の実装パターンを確認した
- [x] `DATA_CONTRACTS.md` 8のpriority proposalに"punctuation variant"専用の階層が無いことを確認した(space/kana variantと同様、priorityは暫定のローカル定数とする)

## 変更予定ファイル

- `src/wikiepwing/search/punctuation_variant.py`(新規: `punctuation_removed_variant()`)
- `src/wikiepwing/search/search_term.py`(`_variant_terms`がpunctuation variantも生成するよう拡張)
- `tests/test_search_punctuation_variant.py`(新規)
- `tests/test_search_term.py`(punctuation variant生成の回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_search_punctuation_variant.py tests/test_search_term.py
make check
git diff --check
```

## 完了条件

- [x] `punctuation_removed_variant(normalized_key)`が、Unicode category "P"始まりの文字を全て除去した文字列を返し、除去対象が無い/結果が空文字列になる場合は`None`を返す
- [x] `title_terms_for_article`が、titleおよびredirectエイリアスそれぞれについて、punctuation variantが元と異なる場合のみ`kind="alias"`・`source="punctuation_variant"`のSearchTermを追加生成する
- [x] `make check`が成功する

## 非対象

- alias priority統一(TASK-J005)・collision repository(TASK-J006)・backend search mapping(TASK-J007)
- 他バリアント(space/kana)との組み合わせ生成

## 実施結果

- `src/wikiepwing/search/punctuation_variant.py`に`punctuation_removed_variant()`を実装した。`unicodedata.category(c)`が"P"で始まる文字(中黒・括弧・句読点・ASCII記号など)を全て除去し、変化が無い/結果が空文字列になる場合は`None`を返す。
- `search_term.py`の`_variant_terms`を、`(生成関数, priority, source)`のタプル列`_VARIANT_GENERATORS`をループする形にリファクタリングし、space/kana/punctuationの3種類のバリアントを統一的に生成するようにした(`punctuation_variant`のpriority=40)。
- `tests/test_search_punctuation_variant.py`(新規7件: 中黒・ASCII記号・括弧・日本語句読点・記号無し・記号のみ・長音記号は対象外)と`tests/test_search_term.py`への追加2件を実装した。
- `make check`(format-check/lint/mypy/pytest 821件)と`git diff --check`が成功した。
