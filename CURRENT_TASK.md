# CURRENT_TASK.md

## Task ID

TASK-E008

## 目的

TASK-E003〜E007を結合し、`source.lock.json`のchunkをstreaming読取→parse→validate→重複解決→repository書込まで行う`wikiepwing ingest`コマンドを実装する。progress・診断・stage manifestを出力する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E008を読んだ(依存: E003-E007、いずれも完了済み)
- [x] `DATA_CONTRACTS.md` 3節(stage manifest contract)を確認した
- [x] `AGENTS.md` 2.6(ステージ全体を壊す失敗は即座に停止、記事単位は診断化)を確認した
- [x] TASK-D004(`SourceLock`/`parse_source_lock`)、TASK-D006(`verify_fingerprint`)、TASK-E001〜E007を確認した

## 変更予定ファイル

- `src/wikiepwing/ingest/orchestrate.py`
- `src/wikiepwing/cli.py`
- `tests/test_ingest_orchestrate.py`
- `tests/test_cli.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_ingest_orchestrate.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `source.lock.json`をparseし、各chunk fileを`verify_fingerprint`で検証してから(全体stage止め判断)streaming読取する
- [x] chunkごとにNDJSON行をparse(E004)→重複解決(E006、DB既存stateと比較)→安全性検証(E005)→repository書込(E007)する
- [x] `DATA_CONTRACTS.md` 3節のmanifest契約(schema_version/stage/status/run_id/started_at/completed_at/inputs/outputs/metrics)に沿ったmanifestを書き出す
- [x] metrics(records_read/written/rejected/warnings/errors/fatals)を集計する
- [x] batch_size件ごとにtransactionをcommitする(bounded memory、中断時の損失を限定)
- [x] `wikiepwing ingest`コマンドがconfig/source.lock.jsonから実行できる
- [x] TASK-D010の10正常記事+8 edge caseをend-to-endで実際に取り込み、期待通りの結果(重複解決・rejectを含む)になることを確認する
- [x] `make check`が成功する

## 非対象

- 中断後の再開判定・partial cleanup(TASK-E010)
- raw DB全体の整合性検証コマンド(TASK-E009)
- stage manifestの汎用化・全stage共通化(EPIC I)。本タスクではingest stage専用の実装に留め、`logical_hash`/image digest等の未整備fieldはnull/省略とする

## 実施結果

- `src/wikiepwing/ingest/orchestrate.py`に`run_ingest`、`IngestMetrics`、`IngestManifest`、`IngestResult`、`IngestError`を実装した。
- 各chunk fileは処理前に`verify_fingerprint`でsource.lock.jsonの記録値と照合し、不一致はDB書込前にstage全体を止める(`IngestError`、AGENTS 2.6準拠)。
- chunkごとにNDJSON行をstreaming読取(E003)→parse(E004、失敗時はerror診断化してskip)→重複解決(E006、DB既存stateと比較)→安全性検証(E005)→repository書込(E007)の順で処理する。
- `batch_size`件ごとに`repository.batch()`でtransactionをcommitし、`on_progress`callbackでprogressを通知する。
- `DATA_CONTRACTS.md` 3節の契約に沿ったmanifest(schema_version/stage/stage_version/status/run_id/started_at/completed_at/inputs/outputs/metrics/software)をatomic書込した。`logical_hash`/image digestはEpic S未整備のためnullとした。
- `wikiepwing ingest --lock-path`コマンドを追加した。`--namespace`/`--run-id`/`--raw-database`/`--manifest-path`/`--batch-size`/`--git-commit`のoverrideを実装した。
- TASK-D010の10正常記事+8 edge case(11行)をend-to-endで取り込み、期待通りの結果(written=17イベント/16行、rejected=2、duplicate=3、error=3)になることを確認した。
- `tests/test_ingest_orchestrate.py`に4件、`tests/test_cli.py`に2件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート356件、`git diff --check`が成功した。

**判断・注意点**

- `source_sequence`はchunkごとに0から再開する(chunk跨ぎの一意性は保証しない)。診断・重複記録にどのchunkかを明示するfieldは現schemaに無いため、複数chunkで同じpage_idが競合する場合の完全な追跡性は将来の課題として残した。
- stage manifestの`logical_hash`・`app_image_digest`・`toolchain_image_digest`はEpic S(BUILD-INFO)が整備されるまでnullとし、`stage_version`は固定値1とした。将来TASK-I001でstage manifestを全stage共通化する際に本実装を土台にする。
