# CURRENT_TASK.md

## Task ID

TASK-I007

## 目的

`PLAN.md` Phase 9の出口条件("completed stage再利用"・"corrupt output再利用拒否"・"interrupted stageだけ再実行")とテスト観点("normalize途中kill"・"output hash mismatch")を実装・検証する。TASK-I005/I006の`decide_resume`は`status`/`stage_version`/`inputs`のみを比較しており、**manifestが`complete`と主張していても実際の出力ファイルが消失・破損している場合に誤って再利用してしまう**ギャップに気づいた。本タスクで(1)`decide_resume`に出力ファイルの実在性・sha256一致チェックを追加し、(2)実プロセスをkillしてstageの中断・強制再実行・冪等性を確認する統合テストを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-I007(依存: I006)を読んだ
- [x] `PLAN.md` Phase 9の出口条件・テスト観点を確認した
- [x] `decide_resume`(TASK-I005)が出力ファイルの実在性・内容を検証していないことに気づいた

## 変更予定ファイル

- `src/wikiepwing/pipeline/resume.py`(`decide_resume`に`current_output_fingerprint`引数を追加)
- `src/wikiepwing/ingest/orchestrate.py`・`src/wikiepwing/normalize/orchestrate.py`・`src/wikiepwing/render/generate.py`(実際の出力fingerprintを`decide_resume`へ渡すよう配線)
- `tests/test_pipeline_resume.py`(出力fingerprint比較の回帰テスト追加)
- `tests/test_normalize_orchestrate.py`(kill/restart統合テスト、corrupt output再実行テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_pipeline_resume.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py
make check
git diff --check
```

## 完了条件

- [x] `decide_resume`が、直前manifestの`outputs`に記録されたsha256/size_bytesと現在の出力ファイルの実際の値が一致しない場合(またはファイルが消失している場合)、`should_skip=False`を返す
- [x] 3 orchestrateモジュールが実際の出力fingerprintを計算して`decide_resume`へ渡すよう配線される
- [x] 実プロセスを`SIGKILL`でkillした後、manifestが`running`のまま残り、`force=True`での再実行が成功し、結果が冪等であることを統合テストで確認する
- [x] `make check`が成功する

## 非対象

- ingest/generateの実プロセスkillテスト(normalizeの1本で代表させる。パターンは同一)
- 複数worker間の分散lock(TASK-I003のprocess-local `fcntl.flock`のみを対象とする既存範囲を維持)

## 実施結果

- `src/wikiepwing/pipeline/resume.py`の`decide_resume`に`current_output_fingerprint: tuple[int, str] | None`引数を追加した。直前manifestの`outputs`が非空の場合、渡されたfingerprintが一致しない(またはNone=ファイル消失)なら`should_skip=False`を返す(fail-closed)。`outputs`が空/未記録の場合はこのチェックをスキップする。
- `ingest/orchestrate.py`・`normalize/orchestrate.py`・`render/generate.py`それぞれに`_current_output_fingerprint(path)`ヘルパーを追加し、実際の出力ファイルのfingerprintを`decide_resume`へ渡すよう配線した。
- 実装中に気づいたバグ: 出力が壊れている(corrupt)と判定されて再実行が必要になっても、`initialize_model_database`/`initialize_raw_database`が壊れたsqliteファイルへ直接接続しようとして`sqlite3.DatabaseError`で失敗していた。`run_normalize`/`run_ingest`にtry/except+ファイル削除+再初期化のフォールバックを追加して修正した。
- `tests/test_pipeline_resume.py`に出力fingerprint比較の4テスト(missing/corrupt/matching/no-outputs-recorded)を追加した。
- `tests/test_normalize_orchestrate.py`に(1)出力ファイルが壊れている場合に再実行され正しく再構築されることを確認するテスト、(2)`multiprocessing`(fork context)で`run_normalize`をbatch_size=1・記事ごとに0.2秒sleepするon_progressで起動し、0.4秒後に`SIGKILL`した後、manifestが`running`のまま残ること・`force=False`では拒否されること・`force=True`での再実行が成功し10記事全件が正しく格納されることを確認する統合テストを追加した(3回連続実行して安定性を確認済み)。
- `make check`(format-check/lint/mypy/pytest 786件)と`git diff --check`が成功した。
