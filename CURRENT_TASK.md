# CURRENT_TASK.md

## Task ID

TASK-E004

## 目的

1つのNDJSON行(Wikimedia Enterprise記事record)を型付き`RawArticle`へparseする。TASK-D009/D010で確認済みの実フィールド構造に基づき、required/optional fieldを区別する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E004を読んだ(依存: E003完了済み)
- [x] `ARCHITECTURE.md` 10.3(`RawArticle`)を確認した
- [x] TASK-D009の実データ確認(`categories`/`templates`/`wikitext`は記事によって省略されうる、`redirects`は存在時に配列)を再確認した
- [x] TASK-D010の`tests/fixtures/enterprise/*.ndjson`(10正常記事+8 edge case)を確認した

## 変更予定ファイル

- `src/wikiepwing/ingest/record_parser.py`
- `tests/test_record_parser.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_record_parser.py
make check
git diff --check
```

## 完了条件

- [x] `RawArticle`(`ARCHITECTURE.md` 10.3準拠)、`LicenseRecord`、`SourceImage`を実装する
- [x] required field(`identifier`/`version.identifier`/`name`/`namespace.identifier`/`url`/`date_modified`)欠落・型不一致を明確に拒否する
- [x] optional field(`article_body.html`/`article_body.wikitext`/`redirects`/`categories`/`templates`/`license`/`image`)の省略を許容し、既定値(None/空tuple)を使う
- [x] `source_hash`を生NDJSON行のSHA-256として計算し、同一行は同一hash、異なる行は異なるhashになる
- [x] TASK-D010の10正常記事と8 edge caseすべてを実際にparseし、期待通りの結果になることを確認する
- [x] `make check`が成功する

## 非対象

- title長・URL形式・HTML/wikitextサイズ等の安全性検証(TASK-E005)
- 重複解決ロジック(TASK-E006)
- DBへの書込(TASK-E007)

## 実施結果

- `src/wikiepwing/ingest/record_parser.py`に`RawArticle`(`ARCHITECTURE.md` 10.3準拠)、`LicenseRecord`、`SourceImage`、`parse_record`、`RecordParseError`を実装した。
- required field: `identifier`/`version.identifier`/`name`/`namespace.identifier`/`url`/`date_modified`/`article_body`(objectとして)を検証し、欠落・型不一致を明確に拒否した。
- optional field: `article_body.html`/`article_body.wikitext`/`redirects`/`categories`/`templates`/`license`/`image`は省略を許容し、既定値(None/空tuple)を使う。TASK-D009の実データで`categories`/`templates`/`wikitext`が記事によって省略されることを確認済みのため、この設計にした。
- `source_hash`は生NDJSON行のSHA-256とし、同一行→同一hash、異なる行→異なるhashを保証した(TASK-D010のedge caseで確認)。
- TASK-D010の10正常記事+8 edge caseすべてを実際にparseし、期待通りの結果(html/wikitext省略、同page ID別revision、重複hash、conflicting hash、長いtitle、invalid URL、空license、large articleいずれも正しく処理)を確認した。
- `tests/test_record_parser.py`に19件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート317件、`git diff --check`が成功した。

**判断・注意点**

- `image`フィールドの実際の形状はTASK-D009で確認したaawiki Main Pageの実サンプルに存在しなかったため未確認であり、`content_url`または`url`キーのどちらかをbest-effortで受け入れる設計にした(一次資料未確認の仮定として明記)。実jawiki記事で画像付きサンプルを確認できた際に見直す。
- title長・URL形式・HTML/wikitextサイズ等の安全性検証は行わない(パースは成功させ、TASK-E005で拒否判断する)。
