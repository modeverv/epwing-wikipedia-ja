# CURRENT_TASK.md

## Task ID

TASK-R004

## 目的

`TASKS.md`のTASK-R004(Full jawiki normalize、依存: R003完了済み)を実施する。TASK-R003で生成した`raw.sqlite3`(全81チャンク、accepted_articles=1,508,200)を`wikiepwing normalize`で`model.sqlite3`へ正規化する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R004(依存: R003、完了済み)を読んだ
- [x] TASK-R003で生成した`raw.sqlite3`(スクラッチパッド内、約27GB、`verify-raw`で`integrity_check=ok`確認済み)を入力に使う
- [x] 150万件規模の実データ変換はBashツールの10分タイムアウトを超える可能性が高いため、nohup+disownでバックグラウンド起動し、`Monitor`(persistent)で進捗を監視する

## 変更予定ファイル

- 実行中に実データで発見したバグの修正:
  - `src/wikiepwing/normalize/media_node.py`(`parse_image_node`が`<img src>`の`data:` URI(実データではSVGプレースホルダー画像で最大約10KB超)をそのまま`MediaReference`化しており、`model.sqlite3`の`media_references.media_id/source_url`のCHECK制約(8192バイト)違反でnormalize全体が失敗していたバグを修正。`data:`スキームのsrcは参照すべき外部リソースではないため`None`を返しスキップするようにした)
  - `tests/test_normalize_media_node.py`(回帰テスト追加)
- 実行結果として: スクラッチパッド内に`model.sqlite3`と関連レポートを生成する
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python -m wikiepwing.cli normalize \
  --config "$SCRATCH/full-ingest-override.toml" \
  --raw-database "$SCRATCH/data/work/raw.sqlite3" \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r004
```

## 完了条件

- [x] `model.sqlite3`が生成され、`raw.sqlite3`のaccepted articles全件が正規化される
- [x] normalizeステージのmanifestが`completed`状態で書かれる
- [x] 実行中に実データ固有のクラッシュ・バグが見つかった場合は原因を特定し、コード修正・テスト追加・commitしてから再実行する(TASK-R003で確立したパターンを踏襲)

## 非対象

- Mini/Lite/Full生成(TASK-R005以降)
- 実データを`git`にコミットすること

## 実施結果

実データ(`raw.sqlite3`、accepted_articles=1,508,200)に対して`wikiepwing normalize`を実行し、1件の実データ限定バグを発見・修正した: `parse_image_node`が`<img src>`の`data:` URI(実データではSVGプレースホルダー画像で最大約10KB超)をそのまま`MediaReference`化しており、`model.sqlite3`の`media_references`テーブルのCHECK制約(8192バイト)違反でnormalize全体が約2500件目(page_id 4406)で失敗した。`data:`スキームのsrcをスキップするよう`media_node.py`を修正し、回帰テストを追加した(TASK-R003と同じ「実データでバグ発見→修正・テスト・commit→再実行」パターン)。

修正適用後の再実行(`run-id=full-r004-retry`)で全1,508,200記事が正規化され、normalizeステージmanifestが`status=complete`(articles_read=1,508,200, articles_written=1,508,200, articles_rejected=0, errors=0, fatals=0, warnings=8,923,739)。`model.sqlite3`内の`diagnostics`テーブルを確認したところ、警告の大半(8,923,739件全て)は既存の`DOM_UNKNOWN_ELEMENT`(TASK-G010の「未知DOM要素のフォールバック」機構、既存実装済み・意図した警告レベルの動作)であり、新規バグではないことを確認した。`model.sqlite3`(約12.3GB)はスクラッチパッドのみに保持し、gitにはコミットしない。
