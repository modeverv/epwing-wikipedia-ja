# CURRENT_TASK.md

## Task ID

TASK-D010

## 目的

TASK-D009で実データにより確定したWikimedia Enterprise記事NDJSONの実フィールド構造(`identifier`/`version.identifier`/`name`/`namespace.identifier`/`is_part_of`/`in_language`/`article_body.html`/`article_body.wikitext`/`license`/`redirects`/`categories`/`templates`)に基づき、EPIC E(Raw ingest)が使う10記事の正常fixtureと、`PLAN.md` Phase 4記載のedge case fixtureを作成する。credentials・実個人情報は一切含めない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D010を読んだ
- [x] `PLAN.md` Phase 4の「開発用データ」節(10記事NDJSON fixture/edge case fixture/malformed fixture)とfixture edge case一覧を確認した
- [x] `ARCHITECTURE.md` 10.3(`RawArticle`)とdata dictionary候補フィールドを確認した
- [x] TASK-D009で実際に取得した実記事レコード(`article_body.html`/`license`/`redirects`/`version`等)の実構造を確認した

## 変更予定ファイル

- `tests/fixtures/enterprise/normal_articles.ndjson`
- `tests/fixtures/enterprise/edge_case_articles.ndjson`
- `tests/fixtures/enterprise/edge_case_index.json`
- `tests/test_enterprise_fixtures.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_enterprise_fixtures.py
make check
git diff --check
```

## 完了条件

- [x] `normal_articles.ndjson`が10行、各行が実フィールド構造を持つ有効なJSON objectである
- [x] edge case fixtureが`PLAN.md`記載の全項目(HTMLなし+Wikitextあり、同page ID revision違い、同revision同hash重複、同revision異hash、title長すぎ、invalid URL、empty license、large article)を含む
- [x] `edge_case_index.json`が各edge caseのシナリオ名と対応行番号を記録する
- [x] fixtureにtoken・実credentials・実個人情報を含まない
- [x] テストが各fixtureの行数・JSON妥当性・各edge caseの実在を検証する
- [x] `make check`が成功する

## 非対象

- 実際のNDJSON parser・重複解決ロジックの実装(EPIC E)
- malformed(JSON構文自体が壊れている)fixtureの作成(将来のE004/E005タスクで必要に応じて追加)
- 実jawiki記事本文の再現(手作りの安全な代替内容を使う)

## 実施結果

- `tests/fixtures/enterprise/normal_articles.ndjson`にTASK-D009で確認した実フィールド構造(`identifier`/`name`/`url`/`namespace.identifier`/`in_language`/`is_part_of`/`date_modified`/`version.identifier`/`article_body.html`+`wikitext`/`license`/`redirects`/`categories`/`templates`)を持つ10記事(Emacs、Linux等、既存fixtureと一貫したテーマ)を作成した。
- `tests/fixtures/enterprise/edge_case_articles.ndjson`(11行)に`PLAN.md`記載の全8種のedge case(HTMLなし+Wikitextあり、同page ID別revision、同revision同hash重複、同revision異hash、title長すぎ、invalid URL、empty license、large article)を作成した。
- `tests/fixtures/enterprise/edge_case_index.json`で各シナリオ名と対応行番号(0-indexed)を記録した。
- `tests/test_enterprise_fixtures.py`に12件のテスト(行数、必須フィールド、secrets不在、各edge caseの実在)を追加した。
- fixture作成中、Bashツールのコード実行系(`uv run`)が一時的に利用不能になったため、`jq`/`sed`(read-only系)でJSON妥当性と各edge caseの内容を1行ずつ手動検証してから、復旧後に`uv run pytest`で最終確認した。
- format-check、ruff lint、mypy strict、標準スイート266件、`git diff --check`が成功した。

**判断・注意点**

- 実jawiki記事本文を再現するのではなく、既存のhandcrafted fixture(Emacs/Linux/Wikipedia系)と一貫したテーマの安全な合成内容を使った。credentials・実個人情報は一切含まれない(テストで`WME_*`/`Bearer `マーカーの不在も確認)。
- malformed(JSON構文自体が壊れている)fixtureは対象外とし、将来のE004/E005タスクで必要に応じて追加する。
