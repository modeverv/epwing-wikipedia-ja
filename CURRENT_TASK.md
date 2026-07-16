# CURRENT_TASK.md

## Task ID

TASK-R003

## 目的

`TASKS.md`のTASK-R003(Full jawiki ingest、依存: R002完了済み)を実施する。TASK-R002のAskUserQuestionでユーザーが承認した実データでのフルスケールビルド方針に基づき、実際に取得済みの全81チャンク(約29GB、`jawiki_namespace_0`, snapshot version `35061ecbd3bc55c31cffd4b46838673d`)を`wikiepwing ingest`で`raw.sqlite3`へ取り込む。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R003(依存: R002、完了済み)を読んだ
- [x] バックグラウンドで進行していた全81チャンクのSnapshot取得(`wikiepwing acquire`)が正常終了したことを確認した(`source.lock.json`に`files`が81件、`project=jawiki`, `namespace=0`, `snapshot_version=35061ecbd3bc55c31cffd4b46838673d`)
- [x] スクラッチパッドのディスク空き容量(1.7Ti)が29GB規模の`raw.sqlite3`生成に十分であることを確認した
- [x] これは実データ(日本語Wikipedia全記事相当)に対する長時間実行コマンドであり、Bashツールの10分タイムアウトを超える可能性があるため、`acquire`の時と同様にnohup+disownでバックグラウンド起動し、`Monitor`(persistent)で進捗を監視する

## 変更予定ファイル

- 実行中に実データで発見したバグの修正(1件目):
  - `src/wikiepwing/ingest/repository.py`(`_replace_children`が同一正規化キーへ衝突するredirects/categories/templates/licensesを重複挿入しUNIQUE制約違反になっていたバグを修正。`_dedupe_by_key`ヘルパーで先勝ちdedupe)
  - `tests/test_repository.py`(回帰テスト追加)
- 実行中に実データで発見したバグの修正(2件目):
  - `src/wikiepwing/ingest/orchestrate.py`(`iter_ndjson_lines`が常に`tar_reader.DEFAULT_MAX_LINE_BYTES`(8MiB)を使っており、`ingest.max_html_bytes`/`max_wikitext_bytes`(既定64MiB)以下でも8MiBを超えるNDJSON行で`TarStreamError`となりチャンク全体が失敗していたバグを修正。`_max_ndjson_line_bytes`で`max_html_bytes+max_wikitext_bytes+overhead`から動的に上限を計算し、`validate_article`の設定可能なreject判定に委ねるようにした)
  - `tests/test_ingest_orchestrate.py`(回帰テスト追加)
- 実行結果として: スクラッチパッド内に`raw.sqlite3`と関連レポートを生成する(git管理外)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python -m wikiepwing.cli ingest \
  --config "$SCRATCH/full-ingest-override.toml" \
  --lock-path "$SCRATCH/data/sources/jawiki/35061ecbd3bc55c31cffd4b46838673d/source.lock.json" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r003
```

## 完了条件

- [x] `raw.sqlite3`が生成され、81チャンク全件が取り込まれる
- [x] ingestステージのmanifestが`completed`状態で書かれる
- [x] `verify-raw`で整合性(integrity, foreign keys, counts, samples)が確認できる

## 非対象

- normalize以降(TASK-R004)
- 実データを`git`にコミットすること(スクラッチパッドのみに保持し、リポジトリには一切含めない)

## 実施結果

実データ(日本語Wikipedia全記事、`jawiki_namespace_0`, snapshot version `35061ecbd3bc55c31cffd4b46838673d`, 81チャンク約29GB)に対して`wikiepwing ingest`を実行し、2件の実データ限定バグを発見・修正した。

1件目: `_replace_children`が同一正規化キー(trailing whitespace/全角半角差など)へ衝突するredirects/categories/templates/licensesを無条件に挿入しており、`redirects`等のUNIQUE制約違反でchunk 0付近(4000件目)で失敗した。`_dedupe_by_key`ヘルパーで先勝ちdedupeするよう修正し、回帰テストを追加した。

2件目: `iter_ndjson_lines`が常に`tar_reader.DEFAULT_MAX_LINE_BYTES`(8MiB)を使っており、設定可能な`ingest.max_html_bytes`/`max_wikitext_bytes`(既定64MiB)以下の記事でも8MiBを超えるNDJSON行でチャンク全体が失敗した(chunk 46、約120万件目)。`_max_ndjson_line_bytes`で`max_html_bytes+max_wikitext_bytes+overhead`から動的に上限を計算し、`validate_article`の設定可能なreject判定に委ねるよう修正し、回帰テストを追加した。

両修正を適用した3回目の実行(`run-id=full-r003-retry2`)で全81チャンク・1,547,381レコード(読み込み)、1,547,292件書き込み、rejected 0、エラー78件(重複解決系diagnostics)で`status=complete`のingestステージmanifestを取得した(`raw.sqlite3`約27GB、スクラッチパッドのみに保持、gitにはコミットしない)。`verify-raw`(sample-size=50、実際は100件チェック)で`integrity_check=ok`、`foreign_key_errors=0`、`sample_failures=[]`、`accepted_articles=1,508,200`を確認した。

コード変更(`repository.py`, `orchestrate.py`, 回帰テスト2件追加)は`uv run ruff format .`/`uv run ruff check .`、`make check`(1380 passed, 6 skipped)、`git diff --check`が成功したことを確認済みで、TASK-R003実施前に個別commitした。
