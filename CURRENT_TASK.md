# CURRENT_TASK.md

## Task ID

TASK-S004

## 目的

`TASKS.md`のTASK-S004(Same-host rebuild comparison、依存: R006,S001-S003完了済み)を実施する。PLAN.md 28(Phase 24 再現性試験)の出口条件「entry logical hash一致」を検証するため、同一ホスト・同一入力(TASK-R003で取得済みのsource.lock.json、全81チャンク)から独立に2回目のingest→normalize→generateを実行し、`build_logical_hash.compute_logical_build_hash`で1回目(TASK-R003〜R005/R008/R009)の`entries.jsonl`と論理ハッシュが一致するか比較する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S004(依存: R006,S001-S003、すべて完了済み)を読んだ
- [x] `src/wikiepwing/build_logical_hash.py`(TASK-S002)の`compute_logical_build_hash`/`collect_build_streams`を比較に使う設計にした(新規コード不要)
- [x] 1回目のビルド成果物(`raw.sqlite3`, `model.sqlite3`, `entries-mini/lite/full.jsonl`)はスクラッチパッドに保持済みで、比較対象として再利用する
- [x] 2回目のビルドは同じ`source.lock.json`(全81チャンク、jawiki_namespace_0, snapshot 35061ecbd3bc55c31cffd4b46838673d)から独立にingest→normalize→generateを実行する(ingest/normalizeともに数時間規模)

## 変更予定ファイル

- なし(コード変更を伴わない実行タスク。スクラッチパッド内に2回目の`raw2.sqlite3`/`model2.sqlite3`/`entries-rebuild2.jsonl`を生成する)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
# 2回目のingest
uv run python -m wikiepwing.cli ingest \
  --config "$SCRATCH/full-ingest-override.toml" \
  --raw-database "$SCRATCH/data/work/raw2.sqlite3" \
  --manifest-path "$SCRATCH/data/work/runs/rebuild2/manifests/30-ingest.json" \
  --lock-path "$SCRATCH/data/sources/jawiki/35061ecbd3bc55c31cffd4b46838673d/source.lock.json" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id rebuild2-ingest

# 2回目のnormalize
uv run python -m wikiepwing.cli normalize \
  --config "$SCRATCH/full-ingest-override.toml" \
  --raw-database "$SCRATCH/data/work/raw2.sqlite3" \
  --model-database "$SCRATCH/data/work/model2.sqlite3" \
  --manifest-path "$SCRATCH/data/work/runs/rebuild2/manifests/40-normalize.json" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id rebuild2-normalize

# 2回目のgenerate(mini)
uv run python -m wikiepwing.cli generate \
  --config "$SCRATCH/full-ingest-override.toml" \
  --config config/profiles/mini.toml \
  --model-database "$SCRATCH/data/work/model2.sqlite3" \
  --entries-output "$SCRATCH/data/output/entries-rebuild2.jsonl" \
  --manifest-path "$SCRATCH/data/work/runs/rebuild2/manifests/50-generate.json" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id rebuild2-generate

# 論理ハッシュ比較
uv run python3 -c "from wikiepwing.build_logical_hash import compute_logical_build_hash as h; print(h(entries_jsonl=...))"
```

## 完了条件

- [x] 2回目のingest/normalize/generateがすべて`status=complete`で完了する
- [x] 1回目と2回目の`entries.jsonl`(同一プロファイル)の`compute_logical_build_hash`が一致する
- [x] 一致しない場合は差異の原因を調査・報告する(PLAN.md出口条件「binary差異説明」)(今回は完全一致のため差異なし)
- [x] 実行中に実データ固有のクラッシュ・バグが見つかった場合は原因を特定し、コード修正・テスト追加・commitしてから再実行する(TASK-R003〜R009で確立したパターンを踏襲。今回はクラッシュ・バグなし)

## 非対象

- Cross-host comparison(TASK-S005、別ホストでの再現。今回はsame-hostのみ)
- clean image build / Docker上での再現性(実行環境の制約上、ホストPython実行のみ)
- 実データを`git`にコミットすること

## 実施結果

同一ホスト・同一入力(`source.lock.json`、全81チャンク)から独立に2回目のingest→normalize→generateを実行し、1回目(TASK-R003〜R005)の成果物と比較した。すべての段階でbyte-for-byte完全一致を確認した:

- `raw2.sqlite3`のsha256(`cd6d0cdb4bb4fcaa244c95f3bbab921f2912fd7a317b50d61fcbfbd2b7d1aaeb`)が1回目の`raw.sqlite3`と完全一致(records_read=1,547,381, records_written=1,547,292, errors=78はすべて同一)
- `model2.sqlite3`のsha256(`fd76e4a67c2aa9025f85c8e44de5388934e4e34e28668eccfaad5cd8fbcd3499`)が1回目の`model.sqlite3`と完全一致(articles_read/written=1,508,200, warnings=8,923,739はすべて同一)
- `entries-rebuild2.jsonl`(Miniプロファイル)のsha256(`1b6310d24f3485b1c2436cc2b0b3a7b3d75c006275f59e3f7474fb6078c58ac7`)が1回目の`entries-mini.jsonl`と完全一致
- `build_logical_hash.compute_logical_build_hash`による論理ハッシュも両ビルドで完全一致(`765528ac4926c5a37d6b527c1f140ca7b9a408be7bcaa8a774d2e9d947141c57`)

PLAN.md 28(Phase 24 再現性試験)の出口条件「entry logical hash一致」を実データ全件規模(150万記事超)で確認した。差異が無かったため「binary差異説明」は不要。実行中に実データ固有のクラッシュ・バグは発生しなかった(TASK-R003〜R009で発見・修正済みのバグはすべて再現せず、修正が正しく機能していることも同時に確認できた)。

2回目のビルド成果物(`raw2.sqlite3`, `model2.sqlite3`, `entries-rebuild2.jsonl`)はスクラッチパッドのみに保持し、gitにはコミットしない。
