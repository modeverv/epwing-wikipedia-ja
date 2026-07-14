# CURRENT_TASK.md

## Task ID

TASK-I005

## 目的

`ARCHITECTURE.md` 7.2(Orchestratorの責務"manifest比較"・"resume判定")を実装する。既存の3つのorchestrateモジュール(ingest/normalize/generate)は、直前のmanifestの`status`が`running`かどうかだけを見て再実行を拒否/許可しているが、`status: complete`な直前実行を**再利用してstageを丸ごとskipする**判定ロジックがまだ存在しない。TASK-I002(fingerprint)・TASK-I003(lock)・TASK-I004(atomic write)がすべて揃ったので、直前のmanifest・現在のstage_version・現在のinput fingerprintsを比較し、「再利用可能か・再実行が必要か」を返す純粋関数を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-I005(依存: I002-I004)を読んだ
- [x] `ARCHITECTURE.md` 7.2/7.3のOrchestrator責務・Stage Protocolを確認した
- [x] `DATA_CONTRACTS.md` 3(Stage manifest contract)のstatus enum・inputs/stage_version欄を確認した
- [x] 既存3 orchestrateモジュールの`read_manifest_status`実装(runningのみ判定)を確認した

## 変更予定ファイル

- `src/wikiepwing/pipeline/resume.py`(新規: `decide_resume()`, `ResumeDecision`)
- `tests/test_pipeline_resume.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_pipeline_resume.py
make check
git diff --check
```

## 完了条件

- [x] `decide_resume(previous_manifest, stage_version, current_inputs)`が、manifestが存在しない/`status`が`complete`でない/`stage_version`が異なる/`inputs`が異なる、のいずれかの場合は再実行判定(`should_skip=False`)を返す
- [x] 上記いずれにも該当しない(直前実行が`complete`かつstage_version一致・inputs完全一致)場合は`should_skip=True`を返す
- [x] 判定結果に人間可読な理由(`reason`)を含む
- [x] `make check`が成功する

## 非対象

- 既存orchestrateモジュール(ingest/normalize/generate)への`decide_resume`の実配線(呼び出し側統合はTASK-I006の`--from-stage`/`--force-stage`と合わせて次タスクで実施)
- outputsファイルの実在性・sha256一致チェック(将来必要なら別途)

## 実施結果

- `src/wikiepwing/pipeline/resume.py`に`ResumeDecision`/`decide_resume()`を実装した。manifest欠落・status不一致・stage_version不一致・inputs不一致を順にチェックし、すべて一致する場合のみ`should_skip=True`を返す。
- `tests/test_pipeline_resume.py`(新規7件)で、manifest無し・failed/running status・stage_version不一致・inputs不一致(欠落/追加/変更)・完全一致の各分岐を確認した。
- `uv run ruff format`でフォーマットを修正した後、`make check`(format-check/lint/mypy/pytest 763件)と`git diff --check`が成功した。
- TASKS.mdのTASK-I005を`[x]`にし、LOG.mdに実施記録を追記した。既存orchestrateモジュールへの実配線はTASK-I006へ委ねた。
