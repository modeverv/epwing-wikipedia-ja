# CURRENT_TASK.md

## Task ID

TASK-P007

## 目的

TASK-P006で生成した`ten_thousand_articles.ndjson`を使い、Lite profile(`config/profiles/lite.toml`)でのend-to-end build(register→ingest→normalize→generate→verify)を10,000記事規模で実行し、完走することを確認する。TASK-P002/P003の100記事規模の受け入れテストと同じ形を、ADR-015の次段階(10,000記事gate)として10,000記事規模へ拡張する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-P007(依存: P006)を読んだ
- [x] `tests/test_lite_profile_build.py`(TASK-P003、100記事規模)の実装を再確認した
- [x] `tests/fixtures/enterprise/ten_thousand_articles.ndjson`(TASK-P006)が実際に生成済みであることを確認した

## 変更予定ファイル

- `tests/test_lite_profile_10000_build.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_lite_profile_10000_build.py
make check
git diff --check
```

## 完了条件

- [x] `config/profiles/lite.toml`をoverrideとして使い、10,000記事fixtureに対するingest→normalize→generate→verifyの全stageが`complete`で完走する
- [x] 生成された`entries.jsonl`が`verify_entries_jsonl`で有効と判定される(10,000件)
- [x] `make check`が成功する(このテストの実行時間が許容範囲内であることを確認する)

## 非対象

- 実toolchain(fpwmake/eb-search)での10,000-entry honmon構築(Docker smoke testとして別途実施する場合は非常に時間がかかるため、今回はPython pipelineレベルのend-to-endに限定する)

## 実施結果

- `tests/test_lite_profile_10000_build.py`(新規)に`test_lite_profile_build_over_ten_thousand_article_fixture`を実装した。TASK-P003と同じ構成で、TASK-P006の`ten_thousand_articles.ndjson`を使い、`config/profiles/lite.toml`をoverrideとして10,000記事規模でend-to-end buildが完走することを確認した。
- 実行時間は約3.4秒(`make check`全体でも約13.5秒)であり、CIの実行時間に問題のない範囲であることを確認した。
- `make check`(format-check/lint/mypy/pytest 1237件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- 実toolchain(fpwmake/eb-search)での10,000-entry honmon構築は対象外とした(Python pipelineレベルのend-to-endに限定)。
