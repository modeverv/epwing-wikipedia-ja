# CURRENT_TASK.md

## Task ID

TASK-R002

## 目的

`PLAN.md` 30(「Full build前ゲート一覧」)を実装する。既存の`doctor.py`(`CheckResult`/`CheckStatus`/`DoctorReport`)の枠組みを再利用し、環境面の既存doctor check(disk容量・path書き込み可能性等)に加えて、full build固有のgate項目(source lockが具体的なバージョンに解決されていること、profileが固定値であること、および呼び出し側が実行した各種test suite/smoke testの結果)を組み合わせた`run_full_build_preflight`を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R002(依存: R001,I007)を読んだ
- [x] `PLAN.md` 30(Full build前ゲート一覧の13項目)を再確認した
- [x] `doctor.py`の`run_doctor`(環境面のCheckResultを既に多く提供している: architecture/python/locale/timezone/container/configuration/path/free_disk/tool)を確認し、これを土台として再利用する方針にした
- [x] `PLAN.md` 30の項目のうち、「Phase 0〜20完了」「toolchain smoke green」「reference scan complete」「100記事Mini/Lite green」「10,000記事Lite green」「resume test green」「gaiji test green」「image security test green」「no network after acquire verified」は、実際にそれらのtest/smoke scriptを実行した結果を呼び出し側が知っている(このプロセス自身が判定できるものではない)ため、`test_suite_results: Mapping[str, bool]`として呼び出し側から注入する設計にした。オブジェクティブに検証可能な項目(`source lock concrete`・`profile settings fixed`・doctor既存check経由の`Docker disk capacity`/`logs/reports persistent`)はこの関数自身が直接検証する

## 変更予定ファイル

- `src/wikiepwing/doctor.py`(`CheckCategory`に`"release-gate"`追加)
- `src/wikiepwing/preflight.py`(新規: `FULL_BUILD_GATE_ITEMS`, `run_full_build_preflight`)
- `tests/test_preflight.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_preflight.py
make check
git diff --check
```

## 完了条件

- [x] `run_full_build_preflight`が既存の`DoctorReport`のcheckに加え、`source_lock.snapshot_version`が`"latest"`という文字列そのものでないことを検証するcheckを追加する
- [x] `config.profile`が`"mini"`/`"lite"`/`"full"`のいずれかであることを検証するcheckを追加する(config読み込み自体が既に強制しているため、ここでは防御的な再確認)
- [x] 呼び出し側が渡した`test_suite_results`の各項目(`toolchain_smoke`/`reference_scan`/`hundred_article_mini`/`hundred_article_lite`/`ten_thousand_article_lite`/`resume_test`/`gaiji_test`/`image_security_test`/`no_network_after_acquire`)がそれぞれ`CheckResult`として結果に反映される
- [x] `test_suite_results`に必須項目が欠けている場合は`fail`のCheckResultになる(黙って無視しない)
- [x] 全てのrequired checkがpassした場合のみ`DoctorReport.ok`が`True`になる
- [x] `make check`が成功する

## 非対象

- Full jawiki ingest(TASK-R003)
- 実際にtoolchain smoke test等を実行してtest_suite_resultsを収集する自動化(呼び出し側の責務)

## 実施結果

- `doctor.py`の`CheckCategory`に`"release-gate"`を追加した。
- `src/wikiepwing/preflight.py`(新規)に`FULL_BUILD_GATE_ITEMS`(9項目)・`run_full_build_preflight`を実装した。既存の`DoctorReport`のcheckに、`source_lock_concrete`(`build_source_lock`が既に`snapshot_version="latest"`を拒否するため実質的に防御的な再確認)・`profile_fixed`(config読み込みが既に強制)・9つのtest suite結果checkを追加する。
- `tests/test_preflight.py`(新規7件)で、全passでのok・既存doctor checkの保持・非concreteなsource lockでのfail・test_suite_results欠落時のfail-closed・個別test失敗でのgate fail・全gate itemの反映・profile_fixed checkのpassを確認した。
- `make check`(format-check/lint/mypy/pytest 1317件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- 「Phase 0〜20完了」「toolchain smoke green」等の実際にtest/smokeを実行したかどうかの判定は、このプロセス自身では検証できないため呼び出し側が注入する設計にした。
