# CURRENT_TASK.md

## Task ID

TASK-I001

## 目的

`DATA_CONTRACTS.md` 3節(Stage manifest contract)を形式化した共有モジュールを実装する。`ingest/orchestrate.py`・`normalize/orchestrate.py`・`render/generate.py`がそれぞれ独立に実装していた「manifestの読み込み・status抽出・atomic書き込み」ロジック(ほぼ同一の重複コード)を`src/wikiepwing/pipeline/stage_manifest.py`へ集約し、`DATA_CONTRACTS.md` 3節のenvelope形状(schema_version/stage/stage_version/status/run_id/started_at/completed_at/inputs/outputs/metrics/software、status enum: running/complete/failed/interrupted/invalid)を検証する`validate_stage_manifest_payload`を追加する。既存3モジュールの公開API(`read_manifest_status`とその例外型)は後方互換を保つ。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-I001(依存: E008,G012,H010)とI002-I007(Fingerprint計算/Stage lock/Atomic output/Resume判定/`--from-stage`/`--force-stage`/kill-restart統合テスト、いずれも本タスクの後続)を読んだ
- [x] `DATA_CONTRACTS.md` 3節(Stage manifest contract、path/JSON例/status enum)を確認した
- [x] `ingest/orchestrate.py`・`normalize/orchestrate.py`・`render/generate.py`の`read_manifest_status`/`_write_manifest`実装(ほぼ同一)を確認した
- [x] 既存テスト(`test_ingest_orchestrate.py`等)が`read_manifest_status`の例外型(`IngestError`等)とメッセージ文言に依存していることを確認し、後方互換を保つ設計とした

## 変更予定ファイル

- `src/wikiepwing/pipeline/__init__.py`
- `src/wikiepwing/pipeline/stage_manifest.py`
- `src/wikiepwing/ingest/orchestrate.py`(共有実装を利用するようリファクタ)
- `src/wikiepwing/normalize/orchestrate.py`(同上)
- `src/wikiepwing/render/generate.py`(同上)
- `tests/test_pipeline_stage_manifest.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_pipeline_stage_manifest.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py
make check
git diff --check
```

## 完了条件

- [x] `validate_stage_manifest_payload`が`DATA_CONTRACTS.md` 3節のenvelope必須field・status enumを検証する
- [x] `read_manifest_status`/atomic書き込みの共有実装が3モジュールから利用され、重複コードが削減される
- [x] 既存の`read_manifest_status`呼び出し元テスト(例外型・メッセージ文言含む)がすべて変更無しで成功する
- [x] `make check`が成功する

## 非対象

- Fingerprint計算(TASK-I002)
- Stage lock(TASK-I003)
- Atomic stage output(TASK-I004、manifestのatomic書き込み自体は既存実装を踏襲するのみ)
- Resume判定・`--from-stage`/`--force-stage`(TASK-I005-I006)

## 実施結果

- `src/wikiepwing/pipeline/__init__.py`(新規パッケージ)、`src/wikiepwing/pipeline/stage_manifest.py`に`validate_stage_manifest_payload`/`read_manifest_payload`/`extract_status`/`write_stage_manifest_payload`を実装した。
- `ingest/orchestrate.py`・`normalize/orchestrate.py`・`render/generate.py`をリファクタし、共有実装を利用するようにした(公開API・例外型は変更無し)。
- `tests/test_pipeline_stage_manifest.py`に25件のテストを追加。
- `uv run pytest tests/test_pipeline_stage_manifest.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py`: 45 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート739件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(I001チェック)、`LOG.md`(新規エントリ)を更新した。
- リファクタ中に発見したバグを修正した: `read_manifest_payload`にフル検証を組み込むと既存テストの最小限manifestが壊れるため、読み取り時は緩い検証に留め、フル検証は書き込み時のみに適用するよう設計変更した。
- 次タスク: TASK-I002 Fingerprint calculation。
