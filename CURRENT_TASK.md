# CURRENT_TASK.md

## Task ID

TASK-P002

## 目的

TASK-P001で作成した`config/profiles/mini.toml`を使い、Mini profileでの実際のend-to-end build(ingest→normalize→generate→verify)が完走することを確認する受け入れテストを実装する。AskUserQuestionで確認した方針に従い、`[images]`/`[math]`/`[tables]`/`[search]`/`[references]`のconfig値を実際にnormalize/renderパイプラインへ配線する作業(`images.enabled=false`で画像を抑制する等)はTASK-P004(Profile-driven renderer)の対象とし、本タスクでは「Mini profile configで実際にbuildが完走し、有効なentries.jsonlが生成される」ことを確認する受け入れテストに限定する。TASK-H013(100記事のmini-scale build gate、ただしdefault/lite相当のconfigを使用)と同じ形の統合テストを、Mini profile configを使う形で追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-P002(依存: H013,J007,K010,L004,M009)を読んだ
- [x] `tests/test_mini_end_to_end_build.py`(TASK-H013、`load_config(DEFAULT_CONFIG)`のみを使う100記事gate)の実装を確認した
- [x] normalize/renderパイプラインの現状(`NormalizeOptions`は`[normalize]`セクションのみを消費し、`[images]`/`[math]`/`[tables]`/`[search]`/`[references]`は現時点でどこからも読まれていない)を確認した
- [x] AskUserQuestionで「受け入れテストのみ、config wiring自体はTASK-P004」の方針を確認した

## 変更予定ファイル

- `tests/test_mini_profile_build.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_mini_profile_build.py
make check
git diff --check
```

## 完了条件

- [x] `config/profiles/mini.toml`をoverrideとして使い、100記事fixtureに対するingest→normalize→generate→verifyの全stageが`complete`で完走する
- [x] 生成された`entries.jsonl`が`verify_entries_jsonl`で有効と判定される
- [x] `make check`が成功する

## 非対象

- `images.enabled`/`math.render_graphics`/`tables.enabled`等のconfig値を実際にnormalize/render pipelineへ配線し、Mini profile固有の出力差異(画像なし、mathのtext fallback等)を実現すること(TASK-P004の対象)
- Lite/Full profileの同等テスト(TASK-P003以降)

## 実施結果

- `tests/test_mini_profile_build.py`(新規)に`test_mini_profile_build_over_hundred_article_fixture`を実装した。TASK-H013の100記事gateと同じ構成(register→ingest→normalize→generate→verify)で、`load_config`に`config/profiles/mini.toml`をoverrideとして渡し、`config.profile == "mini"`を確認したうえで全stageが完走し、有効な`entries.jsonl`(100件)が生成されることを確認した。
- `make check`(format-check/lint/mypy/pytest 1231件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- AskUserQuestionで確認した通り、`images.enabled`/`math.render_graphics`等のconfig値を実際にnormalize/render pipelineへ配線する作業は対象外とした(TASK-P004の対象)。現時点ではMini profile configを使っても出力はdefault/lite相当と同じだが、それはこのタスクの範囲外の既知のギャップとして記録した。
