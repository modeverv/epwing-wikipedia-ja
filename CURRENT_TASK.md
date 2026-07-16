# CURRENT_TASK.md

## Task ID

TASK-R009

## 目的

`TASKS.md`のTASK-R009(Full profile generate/verify、依存: R008,Q006完了済み)を実施する。TASK-R004の`model.sqlite3`(全1,508,200記事)からFullプロファイル設定で`wikiepwing generate`を実行し、`verify`する。EPIC R(Full-scale builds)最後のタスク。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R009(依存: R008,Q006、両方完了済み)を読んだ
- [x] TASK-R008で判明した通り、`render/generate.py`はプロファイル設定を参照しないため、`entries-full.jsonl`もTASK-R005/R008と同一内容になる見込みであることを踏まえて実行する

## 変更予定ファイル

- なし(コード変更を伴わない実行タスク)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python -m wikiepwing.cli generate \
  --config "$SCRATCH/full-ingest-override.toml" \
  --config config/profiles/full.toml \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --entries-output "$SCRATCH/data/output/entries-full.jsonl" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r009-full

uv run python -m wikiepwing.cli verify --entries "$SCRATCH/data/output/entries-full.jsonl"
```

## 完了条件

- [x] `entries-full.jsonl`が生成され、generateステージのmanifestが`completed`状態で書かれる
- [x] `verify`が全件のJSONパースに成功する
- [x] TASK-R008の仮説(Full/Lite/Miniで内容が同一)を実際に確認する

## 非対象

- EPIC S(S004/S005、依存: R006。今回のEPIC Rの結果を踏まえて次に着手)
- 実データを`git`にコミットすること

## 実施結果

`model.sqlite3`(1,508,200記事)に対してFullプロファイル設定で`wikiepwing generate`を実行し、`entries-full.jsonl`を生成した。generateステージmanifestは`status=complete`(articles_read=1,508,200, entries_written=1,508,200, articles_skipped=0)。

TASK-R008で立てた仮説通り、`entries-full.jsonl`のsha256は`entries-mini.jsonl`/`entries-lite.jsonl`と完全に一致した(`1b6310d24f3485b1c2436cc2b0b3a7b3d75c006275f59e3f7474fb6078c58ac7`、byte-for-byte同一)。これはTASK-R008で確認した通り、`render/generate.py`がプロファイル設定を一切参照しない現行実装の設計に基づく期待通りの結果であり、バグではない。

`verify`結果もTASK-R006/R008と同一の5件の`DUPLICATE_HEADWORD`(内容が同一のため当然)で、既に正当な実データ特性と判定済み。

これでEPIC R(Full-scale builds、TASK-R001〜R009)がすべて完了した。実行中に発見・修正した実データ限定バグは合計7件(TASK-R003で2件: redirects等の重複キー、NDJSON行サイズ制限。TASK-R004で1件: data: URI画像。TASK-R005で1件: Unicode改行文字によるJSONL分割。TASK-R007で3件: プロトコル相対URL、User-Agent、429リトライ)。`entries-full.jsonl`はスクラッチパッドのみに保持し、gitにはコミットしない。
