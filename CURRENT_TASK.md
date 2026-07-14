# CURRENT_TASK.md

## Task ID

TASK-H010

## 目的

`ARCHITECTURE.md` 17.1(`EpwingBackend` Protocol)・17.2(FreePWING adapterの責務)に基づき、`wikiepwing generate` CLIコマンドを実装する。model.sqlite3の`normalize_status != 'rejected'`な記事を読み、`RenderedEntry`(TASK-H007)へ変換し、`write_entries_jsonl`(TASK-H009)でFreePWINGビルド入力(entries.jsonl)へ書き出す。`ingest`/`normalize`と同じmanifest lifecycleパターンに従う。

実際の`fpwmake`実行によるEPWINGバイナリ生成(catalog/subbook設定の動的生成、実運用gaiji文字集合の管理を含む)は、これらの生成ロジック自体がまだ未実装(Epic後半、gaiji font pipeline等)であるため、本タスクでは対象外とする。TASK-H009で構築済みの`docker/toolchain/freepwing_build_entries.pl`は本コマンドが生成する`entries.jsonl`をそのまま読めるため、既存のfixture向けMakefile/catalogs.txt等を使い続ければ手動でのtoolchain実行は可能だが、これを自動化する部分は将来のtaskへ委ねる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H010(依存: H009)を読んだ
- [x] `ARCHITECTURE.md` 17.1(`EpwingBackend` Protocol)・17.2(FreePWING adapterの責務: "FreePWING source file生成"/"catalog/subbook設定"/"index登録"等、後者2つは本タスク非対象)を確認した
- [x] `migrations/model/001_initial.sql`の`articles`テーブル(`article_json_zstd`/`normalize_status`)を確認した
- [x] `model/canonical.py`(`decode_article`)・`ingest/zstd_codec.py`(`decompress`)・`render/mini_layout.py`(`render_article_to_entry`)・`render/freepwing_source.py`(`write_entries_jsonl`)を再利用する
- [x] `ingest/orchestrate.py`/`normalize/orchestrate.py`のmanifest lifecycleパターン(running/complete/failed、`--force`)を踏襲する

## 変更予定ファイル

- `src/wikiepwing/render/generate.py`
- `src/wikiepwing/cli.py`(`generate`サブコマンド追加)
- `tests/test_render_generate.py`
- `tests/test_cli.py`(generateサブコマンドの確認を追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_generate.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `run_generate`がmodel.sqlite3の`normalize_status != 'rejected'`な記事を読み、`RenderedEntry`へ変換し、`entries.jsonl`へ書き出す
- [x] `rejected`な記事は除外される
- [x] manifestのrunning/complete/failed lifecycleと`--force`挙動が既存パターンと同様に動作する
- [x] `wikiepwing generate`サブコマンドが動作する
- [x] `make check`が成功する

## 非対象

- 実際の`fpwmake`実行によるEPWINGバイナリ生成の自動化
- catalog/subbook設定の動的生成(TASK-H009までのfixtureベースの手動運用のまま)
- 実運用gaiji文字集合・font pipelineの管理
- EPWING verifier baseline(TASK-H011)

## 実施結果

- `src/wikiepwing/render/generate.py`に`run_generate`/`GenerateMetrics`/`GenerateManifest`/`GenerateResult`/`read_manifest_status`を実装した。
- `src/wikiepwing/cli.py`に`generate`サブコマンドを追加した。
- `tests/test_render_generate.py`(4件)を追加、`tests/test_cli.py`にgenerateサブコマンドのend-to-endテスト(2件)を追加。
- `uv run pytest tests/test_render_generate.py tests/test_cli.py`: 22 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート695件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H010チェック)、`LOG.md`(新規エントリ)を更新した。
- 実際の`fpwmake`実行・catalog/subbook動的生成・実運用gaiji管理は非対象(前提subsystem未実装)。
- 次タスク: TASK-H011 EPWING verifier baseline。
