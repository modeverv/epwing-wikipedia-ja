# CURRENT_TASK.md

## Task ID

TASK-P003

## 目的

TASK-P002と同じ方針(受け入れテストのみ、実際のconfig配線はTASK-P004)で、Lite profile(`config/profiles/lite.toml`)を使った実際のend-to-end build(ingest→normalize→generate→verify)が完走することを確認する受け入れテストを実装する。TASK-N007(数式failure fallback)・TASK-O012(画像plan/fetch/convert)・TASK-P001(Profile schema)が揃ったことで、Lite profileが謳う機能(代表画像・math bitmap・Infobox/table整形・references保持)を支える基盤コンポーネントが出揃った、というのがこのタスクの依存関係の意味だと判断した。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-P003(依存: N007,O012,P001)を読んだ
- [x] TASK-P002で確立した「受け入れテストのみ、config wiring自体はTASK-P004」という方針をLite profileにも適用する
- [x] `config/profiles/lite.toml`(TASK-P001)の内容を再確認した

## 変更予定ファイル

- `tests/test_lite_profile_build.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_lite_profile_build.py
make check
git diff --check
```

## 完了条件

- [x] `config/profiles/lite.toml`をoverrideとして使い、100記事fixtureに対するingest→normalize→generate→verifyの全stageが`complete`で完走する
- [x] 生成された`entries.jsonl`が`verify_entries_jsonl`で有効と判定される
- [x] `make check`が成功する

## 非対象

- `images.enabled`/`math.render_graphics`等のconfig値を実際にnormalize/render pipelineへ配線すること(TASK-P004の対象)
- Full profileの同等テスト(別タスク)

## 実施結果

- `tests/test_lite_profile_build.py`(新規)に`test_lite_profile_build_over_hundred_article_fixture`を実装した。TASK-P002と同じ構成で、`config/profiles/lite.toml`をoverrideとして使い、`config.profile == "lite"`を確認したうえで全stageが完走し、有効な`entries.jsonl`(100件)が生成されることを確認した。
- `make check`(format-check/lint/mypy/pytest 1232件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- TASK-P002と同じ理由で、config値の実際のnormalize/render pipelineへの配線は対象外(TASK-P004)。
