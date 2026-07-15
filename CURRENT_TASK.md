# CURRENT_TASK.md

## Task ID

TASK-Q006

## 目的

TASK-P002/P003で確立した方針(受け入れテストのみ、実際のconfig配線は別タスク)と同じ形で、Full profile(`config/profiles/full.toml`)を使った実際のend-to-end build(ingest→normalize→generate→verify)が完走することを確認する受け入れテストを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q006(依存: O012,Q005,L005)を読んだ
- [x] `tests/test_lite_profile_build.py`(TASK-P003)の実装を再確認した
- [x] `config/profiles/full.toml`(TASK-P001)の内容を再確認した

## 変更予定ファイル

- `tests/test_full_profile_build.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_full_profile_build.py
make check
git diff --check
```

## 完了条件

- [x] `config/profiles/full.toml`をoverrideとして使い、100記事fixtureに対するingest→normalize→generate→verifyの全stageが`complete`で完走する
- [x] 生成された`entries.jsonl`が`verify_entries_jsonl`で有効と判定される
- [x] `make check`が成功する

## 非対象

- `images.enabled`以外のconfig値(`search.*`/`distribution.*`等)を実際にnormalize/render pipelineへ配線すること
- Reference comparison engine(TASK-Q007)

## 実施結果

- `tests/test_full_profile_build.py`(新規)に`test_full_profile_build_over_hundred_article_fixture`を実装した。TASK-P003と同じ構成で、`config/profiles/full.toml`をoverrideとして使い、`config.profile == "full"`を確認したうえで全stageが完走し、有効な`entries.jsonl`(100件)が生成されることを確認した。
- `make check`(format-check/lint/mypy/pytest 1268件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- TASK-P002/P003と同じ理由で、`images.enabled`以外のconfig値の実際のnormalize/render pipelineへの配線は対象外。
