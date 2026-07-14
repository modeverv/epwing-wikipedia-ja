# CURRENT_TASK.md

## Task ID

TASK-H009

## 目的

`ARCHITECTURE.md` 17.2(FreePWING adapterの責務: "FreePWING source file生成")を実装する。任意件数の`RenderedEntry`(alias数・internal target数も可変)をFreePWINGの`FPWUtils::FPWParser` Perl APIへ渡し、`fpwmake`が消費するsource(`work/text`/`work/heading`/`work/word2`等)を生成する仕組みを作る。既存の`tests/fixtures/handcrafted/build_fixture.pl`はentry数3・alias数2に固定されたsmoke test専用スクリプトであり、本タスクではこれを一般化する。Python側はentryを中間形式(JSON Lines)へ書き出すのみとし、実際のFPWParser呼び出しはPerlスクリプト(Docker toolchain image内で実行)が担う(`ARCHITECTURE.md` 17.2の非責務"HTML解析"等はPythonに残す設計と整合)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H009(依存: B009,H007-H008)を読んだ
- [x] `ARCHITECTURE.md` 17.1(`EpwingBackend` Protocol)・17.2(FreePWING adapterの責務/非責務)を確認した
- [x] `tests/fixtures/handcrafted/build_fixture.pl`・`entries.tsv`・`Makefile`・`docker/toolchain/handcrafted-three-entry-smoke.sh`を読み、実際のFPWParser呼び出しパターン(`initialize_fpwparser`/`text`/`heading`/`word2`/`add_tag`/`add_text`/`add_reference_start-end`/`finalize_fpwparser`)を確認した
- [x] `wikiepwing-toolchain:dev` Dockerイメージがローカルに存在し、`perl -MJSON::PP`が利用可能であることを確認した(実機検証環境あり)

## 変更予定ファイル

- `src/wikiepwing/render/freepwing_source.py`(RenderedEntry列 → JSON Lines書き出し)
- `docker/toolchain/freepwing_build_entries.pl`(汎用Perl driver、entry数・alias数・target数を任意にする)
- `tests/test_render_freepwing_source.py`(Python側の単体テスト)
- `docker/toolchain/freepwing-build-entries-smoke.sh`(実Dockerでの end-to-end smoke test、可変件数のentryで検証)
- `tests/test_freepwing_build_entries_smoke.py`(smoke scriptの存在・Makefile配線確認、実行はmanual markerで別途)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_freepwing_source.py tests/test_freepwing_build_entries_smoke.py
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
make check
git diff --check
```

## 完了条件

- [x] `write_entries_jsonl(entries, destination)`が`RenderedEntry`列をtag/title/aliases/body/targetsのJSON Linesへ書き出す
- [x] `docker/toolchain/freepwing_build_entries.pl`が任意件数・可変alias数・可変target数のentryを処理し、`fpwmake`で`honmon`/`work/cgr`等を生成できる(実Dockerで検証)
- [x] 同一entry内の重複headwordは吸収し、entry間の重複headwordはエラーとする
- [x] 未知のlink targetを参照するとエラーとする
- [x] `make check`が成功する

## 非対象

- graphic/gaijiの実際の登録内容の一般化(既存のhandcrafted fixtureのcgraphs.txt等をそのまま利用、TASK-H009では拡張しない)
- EPWING generate command全体の配線(TASK-H010)
- catalog/subbook設定の動的生成(既存のcatalogs.txt固定運用のまま)

## 実施結果

- `src/wikiepwing/render/freepwing_source.py`に`write_entries_jsonl`を実装した。
- `docker/toolchain/freepwing_build_entries.pl`(汎用Perl driver)、`docker/toolchain/freepwing-build-entries-smoke.sh`(実Docker end-to-end smoke test)を実装した。`Makefile`に`test-freepwing-build-entries`ターゲットを追加した。
- `tests/test_render_freepwing_source.py`(5件)、`tests/test_freepwing_build_entries_smoke.py`(5件)を追加。
- `uv run pytest tests/test_render_freepwing_source.py tests/test_freepwing_build_entries_smoke.py`: 10 passed。
- `sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev`: 実機で成功(`wikiepwing-eb-search`によるtitle/alias headwordの実検索・解決を確認)。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート689件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H009チェック)、`LOG.md`(新規エントリ)を更新した。
- 実装中に発見したUTF-8→EUC-JP変換漏れのバグを修正した(Perlスクリプト内で`Encode::encode('euc-jp', ...)`を明示適用)。
- 次タスク: TASK-H010 EPWING generate command。
