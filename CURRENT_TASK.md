# CURRENT_TASK.md

## Task ID

TASK-I006

## 目的

`PLAN.md` Phase 9(`--from-stage`/`--force-stage`)と`ARCHITECTURE.md` 7.1(CLIコマンド一覧の`wikiepwing build`)を実装する。TASK-I005で実装した`decide_resume`はまだどのorchestratorからも呼ばれておらず、`--from-stage`/`--force-stage`はそもそも複数stageを繋ぐコマンドが無ければ意味を持たない。本タスクで(1)`run_ingest`/`run_normalize`/`run_generate`自身に`decide_resume`を配線し、直前実行が`complete`かつstage_version/inputs一致なら実処理をskipして直前manifestをそのまま返すようにし、(2)`wikiepwing build`コマンドを新設してingest→normalize→generateを順に実行し、`--from-stage`で開始stageを選び、`--force-stage`で指定した1 stageだけ強制再実行する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-I006(依存: I005)を読んだ
- [x] `PLAN.md` Phase 9(`--resume`/`--from-stage`/`--force-stage`)を確認した
- [x] `ARCHITECTURE.md` 7.1のCLIコマンド一覧に`wikiepwing build`が存在することを確認した(未実装だった)
- [x] 既存3 orchestrateモジュールの`run_*`関数のmanifest lifecycle実装を確認した

## 変更予定ファイル

- `src/wikiepwing/pipeline/build.py`(新規: `STAGE_ORDER`, `stages_from()`, `is_forced_stage()`)
- `src/wikiepwing/pipeline/stage_manifest.py`(`parse_manifest_timestamp()`追加)
- `src/wikiepwing/ingest/orchestrate.py`(`decide_resume`配線、`_resume_result`)
- `src/wikiepwing/normalize/orchestrate.py`(同上)
- `src/wikiepwing/render/generate.py`(同上)
- `src/wikiepwing/cli.py`(`build`サブコマンド追加)
- `tests/test_pipeline_build.py`(新規)
- `tests/test_ingest_orchestrate.py`・`tests/test_normalize_orchestrate.py`・`tests/test_render_generate.py`(resume/force回帰テスト追加)
- `tests/test_cli.py`(`build`コマンドのend-to-end/resume/`--from-stage`テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_pipeline_build.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `run_ingest`/`run_normalize`/`run_generate`が、直前manifestが`complete`かつstage_version/inputs一致の場合に実処理をskipし、直前manifestをそのまま返す(`force=True`で常に強制再実行)
- [x] `wikiepwing build`が`--lock-path`からingest→normalize→generateを順に実行し、各段のmanifest pathを表示する
- [x] `--from-stage <stage>`で、指定stageより前のstageを一切実行しない
- [x] `--force-stage <stage>`で、指定した1 stageだけ強制再実行する(他stageは通常のresume判定に従う)
- [x] `make check`が成功する

## 非対象

- media/render(画像・数式等)stageの追加(EPIC O/N等、将来のstage追加時に`STAGE_ORDER`を拡張する)
- outputsファイルの実在性・sha256一致チェック(TASK-I005と同様、manifestの`inputs`/`stage_version`/`status`比較のみ)
- kill/restart統合テスト(TASK-I007)

## 実施結果

(未記入)
