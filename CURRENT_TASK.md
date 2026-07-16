# CURRENT_TASK.md

## Task ID

TASK-R005

## 目的

`TASKS.md`のTASK-R005(Full Mini generate、依存: R004完了済み, P002 Mini profile完了済み)を実施する。TASK-R004で生成した`model.sqlite3`(全1,508,200記事)から、Miniプロファイル設定で`wikiepwing generate`を実行し`entries.jsonl`を生成する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R005(依存: R004,P002、両方完了済み)を読んだ
- [x] `config/profiles/mini.toml`(画像無効・数式graphics無効・table fallback・検索語を絞る設定)を`--config`で重ねる
- [x] 150万件規模のgenerateはBashツールの10分タイムアウトを超える可能性が高いため、nohup+disownでバックグラウンド起動し、`Monitor`(persistent、10分間隔)で進捗を監視する

## 変更予定ファイル

- 実行中に実データで発見したバグの修正:
  - `src/wikiepwing/render/verify.py`(`_read_records`が`text.splitlines()`を使っており、JSON文字列内に現れる正当なUnicode改行文字(U+2029 PARAGRAPH SEPARATORなど、実データの本文に実在する)を行区切りとして誤って分割し、1つの正常なJSONLレコードを複数の不正な断片に壊していたバグを修正。JSONLの本来の区切り文字である`\n`のみで分割するよう`text.split("\n")`に変更)
  - `tests/test_render_verify.py`(回帰テスト追加)
- 実行結果として: スクラッチパッド内に`entries-mini.jsonl`と関連レポートを生成する
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python -m wikiepwing.cli generate \
  --config "$SCRATCH/full-ingest-override.toml" \
  --config config/profiles/mini.toml \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --entries-output "$SCRATCH/data/output/entries-mini.jsonl" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r005-mini
```

## 完了条件

- [x] `entries-mini.jsonl`が生成され、`model.sqlite3`の非rejected記事全件が変換される
- [x] generateステージのmanifestが`completed`状態で書かれる
- [x] 実行中に実データ固有のクラッシュ・バグが見つかった場合は原因を特定し、コード修正・テスト追加・commitしてから再実行する(TASK-R003/R004で確立したパターンを踏襲)

## 非対象

- Mini検証・レポート(TASK-R006)
- Lite/Full生成(TASK-R007以降)
- 実データを`git`にコミットすること

## 実施結果

`model.sqlite3`(1,508,200記事)に対してMiniプロファイル設定で`wikiepwing generate`を実行し、`entries-mini.jsonl`(約12.9GB)を生成した。generateステージmanifestは`status=complete`(articles_read=1,508,200, entries_written=1,508,200, articles_skipped=0)。

生成後の`wikiepwing verify`実行時に実データ限定バグを発見・修正した: `_read_records`が`text.splitlines()`を使っており、JSON文字列内に現れる正当なUnicode改行文字(U+2029 PARAGRAPH SEPARATORなど)を行区切りとして誤認識し、1つの正常なJSONLレコード(page_id 61417、line 33734)を複数の不正な断片に分割してJSONパースエラーになっていた。JSONLの区切り文字である`\n`のみで分割するよう修正し、回帰テストを追加した。

修正後の`verify`再実行で全1,508,200件のJSONパースに成功し(`entry_count=1508200`)、5件の`DUPLICATE_HEADWORD`(異なるpage_id間で同一見出し語)を検出した(`ok=false`)。これは`verify`が意図通り検出すべき実データの品質課題であり、この検出結果の調査・報告はTASK-R006(Full Mini verify/report)の対象とする。`entries-mini.jsonl`はスクラッチパッドのみに保持し、gitにはコミットしない。
