# CURRENT_TASK.md

## Task ID

TASK-L004

## 目的

`ARCHITECTURE.md` 16.2("標準レイアウト"のカテゴリ付録)を検証するend-to-endテストを追加する。調査の結果、カテゴリ機能自体はTASK-E008(ingestのcategories取り込み)・normalize/orchestrate.pyの`_read_categories`・TASK-H007(`mini_layout.py`の"カテゴリ"付録レンダリング)によってすでに実装済みだったが、raw ingest→normalize→Mini renderの一連の流れを通してカテゴリが失われずに伝播することを確認する専用テストが一つも無いことに気づいた(各層は個別にテストされているが、"category appendix"という機能としての結合テストが無かった)。本タスクはこのテストギャップを埋める。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-L004(依存: E008,H007)を読んだ
- [x] `mini_layout.py`がすでに`article.categories`を"カテゴリ"見出し付きで付録レンダリングしていることを確認した(TASK-H007で実装済み)
- [x] `ingest/record_parser.py`・`normalize/orchestrate.py`の`_read_categories`がすでにraw Enterprise JSONの`categories`フィールドを`Article.categories`まで伝播させていることを確認した(TASK-E008前後で実装済み)
- [x] `_read_categories`・カテゴリのend-to-end伝播を検証する専用テストが存在しないことに気づいた(既存のnormalizeend-to-endテストはarticle件数等のみ検証し、categoriesの中身は見ていない)

## 変更予定ファイル

- `tests/test_normalize_orchestrate.py`(raw fixture→normalize→`Article.categories`のend-to-endテストを追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_orchestrate.py
make check
git diff --check
```

## 完了条件

- [x] `tests/fixtures/enterprise/normal_articles.ndjson`の既知の記事(例: Emacs、page_id 900001、categories `["Category:Emacs"]`)について、raw ingest→normalize後の`model.sqlite3`に格納された`Article.categories`が正しいことを確認する
- [x] `make check`が成功する

## 非対象

- カテゴリ検索語(TASK-L005)
- レンダリング自体の新規実装(TASK-H007ですでに実装済み、既存テストで十分にカバーされている)

## 実施結果

- 調査の結果、カテゴリ機能自体(ingestでのcategories取り込み、`_read_categories`、`mini_layout.py`の"カテゴリ"付録レンダリング)はすでに実装済みだったが、raw ingest→normalizeの全体を通してカテゴリが失われずに伝播することを確認するテストが存在しないギャップに気づいた。
- `tests/test_normalize_orchestrate.py`に`test_categories_survive_raw_ingest_through_normalize`を追加した。既知のfixture記事(Emacs、page_id 900001)がnormalize後の`model.sqlite3`から`article_json_zstd`を実際に解凍・デコードした結果、`categories == ("Category:Emacs",)`であることを確認する。
- `make check`(format-check/lint/mypy/pytest 935件)と`git diff --check`が成功した。
