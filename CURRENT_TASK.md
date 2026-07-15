# CURRENT_TASK.md

## Task ID

TASK-P006

## 目的

`tests/fixtures/enterprise/generate_hundred_articles.py`(TASK-H012)と同じ決定論的な生成パターンを10,000記事規模へ拡張した`generate_ten_thousand_articles.py`を実装し、`ten_thousand_articles.ndjson`を生成する。TASK-P007(10,000-article Lite run)がこの fixture を使う前提。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-P006(依存: P005)を読んだ
- [x] `tests/fixtures/enterprise/generate_hundred_articles.py`(TASK-H012)の実装(20 topicsの繰り返し+世代サフィックス、決定論的なlink/alias/category/image割り当て)を確認した
- [x] 既存fixtureのpage_id範囲(`normal_articles.ndjson`: 900001-900010, `edge_case_articles.ndjson`: 910001-910008付近, `hundred_articles.ndjson`: 920001-920100)を確認し、衝突しない`930001`を新fixtureの開始page_idとした

## 変更予定ファイル

- `tests/fixtures/enterprise/generate_ten_thousand_articles.py`(新規)
- `tests/fixtures/enterprise/ten_thousand_articles.ndjson`(新規、生成物)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
python3 tests/fixtures/enterprise/generate_ten_thousand_articles.py
make check
git diff --check
```

## 完了条件

- [x] `generate_ten_thousand_articles.py`が10,000件のユニークなpage_id/title/URLを持つ決定論的なNDJSONを生成する
- [x] スクリプトを再実行してもbyte-identicalな出力になる
- [x] 既存fixtureのpage_id範囲と衝突しない
- [x] `make check`が成功する

## 非対象

- TASK-P007(この fixture を使った実際の10,000-article Lite run)

## 実施結果

- `tests/fixtures/enterprise/generate_ten_thousand_articles.py`(新規)を`generate_hundred_articles.py`と同じ決定論的パターンで実装した(`FIRST_PAGE_ID=930001`、`ARTICLE_COUNT=10000`、既存fixtureのpage_id範囲と衝突しない)。
- 生成した`ten_thousand_articles.ndjson`(10,000行、14.7MB)は、page_id/titleとも10,000件全てユニークで、スクリプトを2回実行してbyte-identical(同一md5)であることを確認した。
- `make check`(1236件、変更なし)と`git diff --check`が成功した。
