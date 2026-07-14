# CURRENT_TASK.md

## Task ID

TASK-I002

## 目的

`ARCHITECTURE.md` 7.3(`Stage.input_fingerprints(ctx) -> dict[str, str]`)と`DATA_CONTRACTS.md` 3節のmanifest`inputs`欄(`{"source_lock": "sha256:...", "config": "sha256:..."}`形式)を実装する。既存の`normalize/orchestrate.py`・`render/generate.py`が`inputs`へ入力ファイルの**path文字列**をそのまま入れていた(実際のcontent fingerprintではなかった)ことに気づき、`compute_input_fingerprint`を実装してraw.sqlite3/model.sqlite3の実際のcontent hashへ置き換える。これによりTASK-I005(Resume判定)が入力の実際の変更を検出できるようになる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-I002(依存: I001)を読んだ
- [x] `ARCHITECTURE.md` 7.3(Stage Protocol、`input_fingerprints`)・`DATA_CONTRACTS.md` 3節(`inputs`欄の`sha256:...`形式)を確認した
- [x] `normalize/orchestrate.py`・`render/generate.py`の既存`inputs`欄が入力DBの**path文字列**を入れているだけで実際のcontent fingerprintでは無いことに気づいた(既存テストはinputs欄の値を検証していないため後方互換上の問題は無い)
- [x] `source/checksums.py`の`compute_fingerprint`(`FileFingerprint(size_bytes, sha256)`)を再利用する

## 変更予定ファイル

- `src/wikiepwing/pipeline/fingerprint.py`
- `src/wikiepwing/ingest/orchestrate.py`(`inputs`のsha256プレフィックス統一)
- `src/wikiepwing/normalize/orchestrate.py`(`inputs`をraw.sqlite3の実fingerprintへ変更)
- `src/wikiepwing/render/generate.py`(`inputs`をmodel.sqlite3の実fingerprintへ変更)
- `tests/test_pipeline_fingerprint.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_pipeline_fingerprint.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py
make check
git diff --check
```

## 完了条件

- [x] `compute_input_fingerprint(path) -> str`が`sha256:<hex>`形式の文字列を返す
- [x] `normalize`/`generate`のmanifestの`inputs`欄が、入力DBファイルの実際のcontent fingerprintを含む(path文字列だけではない)
- [x] 入力DBの内容が変われば同じpathでもfingerprintが変わることをテストで確認する
- [x] `make check`が成功する

## 非対象

- Stage lock(TASK-I003)
- Atomic stage output(TASK-I004)
- Resume判定・`--from-stage`/`--force-stage`(TASK-I005-I006)
- configファイル自体のfingerprint化(configのファイルpathがrun_ingest等に渡されていないため、本タスクの範囲では対応しない)

## 実施結果

- `src/wikiepwing/pipeline/fingerprint.py`に`compute_input_fingerprint`を実装した。
- `normalize/orchestrate.py`・`render/generate.py`の`inputs`欄を実content fingerprintへ修正し、`ingest/orchestrate.py`の`inputs`欄を`sha256:`プレフィックス形式へ統一した。
- `tests/test_pipeline_fingerprint.py`に4件のテストを追加。
- `uv run pytest tests/test_pipeline_fingerprint.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py`: 24 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート743件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(I002チェック)、`LOG.md`(新規エントリ)を更新した。
- 既存の`normalize`/`generate`の`inputs`欄がpath文字列のみでcontent fingerprintでは無かったバグに気づき修正した。
- 次タスク: TASK-I003 Stage lock。
