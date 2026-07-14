# CURRENT_TASK.md

## Task ID

TASK-H013

## 目的

`DECISIONS.md` ADR-015("3、10、100、10,000記事の段階Gateを通過するまで全件を禁止する")の100記事Gateとして、`TASK-H012`の100記事fixtureを使い、`register-local-source`→`ingest`→`normalize`→`generate`→`verify`の全パイプラインをend-to-endで実行し、正しく完走することを検証する。加えて、`TASK-H009`で構築済みの実toolchain(`freepwing_build_entries.pl`)を使い、生成された100記事の`entries.jsonl`から実際にEPWING辞書(honmon)を構築し、`wikiepwing-eb-search`で複数記事のtitleとaliasが正しく解決できることを実機検証する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H013(依存: H011-H012)を読んだ
- [x] `DECISIONS.md` ADR-015(段階Gate)を確認した
- [x] `docker/toolchain/freepwing-build-entries-smoke.sh`(TASK-H009)のDocker実行パターンを踏襲する
- [x] `tests/fixtures/enterprise/hundred_articles.ndjson`(TASK-H012)を使う

## 変更予定ファイル

- `tests/test_mini_end_to_end_build.py`(Python側pipeline全体のend-to-endテスト、Docker不要)
- `docker/toolchain/mini-end-to-end-smoke.sh`(実toolchainでのhonmon構築+`wikiepwing-eb-search`検証)
- `Makefile`(`test-mini-end-to-end`ターゲット追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_mini_end_to_end_build.py
sh docker/toolchain/mini-end-to-end-smoke.sh wikiepwing-toolchain:dev
make check
git diff --check
```

## 完了条件

- [x] `register_local_source`→`run_ingest`→`run_normalize`→`run_generate`→`verify_entries_jsonl`が100記事fixtureに対してエラー無く完走し、全manifestが`complete`になる
- [x] `entries.jsonl`が100件のentryを含み、`verify_entries_jsonl`が`ok=True`を返す
- [x] 実Docker toolchainで100記事から実際に`honmon`を構築し、`wikiepwing-eb-search`で複数の異なるtitle/aliasが正しいheadingへ解決できることを実機で確認する
- [x] `make check`が成功する

## 非対象

- 10,000記事規模のGate(将来のtask)
- Epic K/L/N/O等の未実装機能(Table/Infobox/Image/Math/References/internal link変換)の統合

## 実施結果

- `tests/test_mini_end_to_end_build.py`(Python側end-to-end、Docker不要)、`docker/toolchain/mini-end-to-end-smoke.sh`(実toolchainでの検証)を実装した。`Makefile`に`test-mini-end-to-end`ターゲットを追加した。
- `uv run pytest tests/test_mini_end_to_end_build.py`: 1 passed。
- `sh docker/toolchain/mini-end-to-end-smoke.sh wikiepwing-toolchain:dev`: 実機で成功(100記事からhonmonを構築、"Emacs"/"Linux"/"GNU Project"/"Vim alias"の4クエリすべてで正しいhitを確認)。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート714件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H013チェック)、`LOG.md`(新規エントリ)を更新した。
- `<a>`要素の実HTML変換が未実装のため、fixture内の内部linkは本文中plain textとして扱われ`internal_targets`は実質空になることを既知の制約として記録した。
- Epic H(Links and Mini rendering)完了。次はEpic I(Pipeline resume)。
