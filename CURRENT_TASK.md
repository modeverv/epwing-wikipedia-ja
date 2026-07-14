# CURRENT_TASK.md

## Task ID

TASK-J003

## 目的

`ARCHITECTURE.md` 14.3(Lite profileの"kana variant")と`DATA_CONTRACTS.md` 8のpriority proposal("600 kana variant")を実装する。ひらがな/カタカナのどちらで書かれたタイトル・エイリアスでも、もう一方の表記で検索した際にヒットするよう、ひらがな⇔カタカナを機械的に入れ替えた変換キーを追加のSearchTermとして登録する。半角カタカナはTASK-J001の`normalize_index_key`のNFKC正規化で既に全角カタカナへ畳み込まれるため、本タスクでは全角カタカナ⇔ひらがなの単純往復変換だけを扱えばよい。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-J003(依存: J001)を読んだ
- [x] `ARCHITECTURE.md` 14.3・`DATA_CONTRACTS.md` 8(600 kana variant)を確認した
- [x] `normalize_index_key`のNFKCが半角カタカナを全角カタカナへ畳み込むことを確認した(半角カタカナは本タスクの対象外で良い根拠)

## 変更予定ファイル

- `src/wikiepwing/search/kana_variant.py`(新規: `kana_variant()`)
- `src/wikiepwing/search/search_term.py`(`title_terms_for_article`がkana variantも生成するよう拡張)
- `tests/test_search_kana_variant.py`(新規)
- `tests/test_search_term.py`(kana variant生成の回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_search_kana_variant.py tests/test_search_term.py
make check
git diff --check
```

## 完了条件

- [x] `kana_variant(normalized_key)`が、ひらがなをカタカナへ・カタカナをひらがなへ機械的に変換した文字列を返し、かな文字が一切無ければ`None`を返す
- [x] `title_terms_for_article`が、titleおよびredirectエイリアスそれぞれについて、kana variantが元と異なる場合のみ`kind="alias"`・`source="kana_variant"`のSearchTermを追加生成する
- [x] `make check`が成功する

## 非対象

- punctuation variant(TASK-J004)
- alias priority統一(TASK-J005)・collision repository(TASK-J006)・backend search mapping(TASK-J007)
- kana variantとspace variantの組み合わせ(複合バリアント)生成

## 実施結果

- `src/wikiepwing/search/kana_variant.py`に`kana_variant()`を実装した。ひらがな(U+3041-3096)⇔カタカナ(U+30A1-30F6)を1文字ずつ機械的に入れ替え(オフセット0x60)、他の文字はそのまま保持する。変化が無ければ`None`。
- `search_term.py`の`_space_variant_terms`を`_variant_terms`に統合し、space variantとkana variantの両方を生成するよう拡張した(`_KANA_VARIANT_PRIORITY = 30`)。
- `tests/test_search_kana_variant.py`(新規6件: ひらがな→カタカナ、カタカナ→ひらがな、混在、漢字/ASCII不変、漢字+かな混在、長音記号)と`tests/test_search_term.py`への追加3件を実装した。
- `make check`(format-check/lint/mypy/pytest 812件)と`git diff --check`が成功した。
