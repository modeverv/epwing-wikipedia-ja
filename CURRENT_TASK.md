# CURRENT_TASK.md

## Task ID

TASK-H011

## 目的

`ARCHITECTURE.md` 7.1に記載の`wikiepwing verify`コマンドの基礎を実装する。TASK-H010の`generate`が生成する`entries.jsonl`を対象に、`docker/toolchain/freepwing_build_entries.pl`(TASK-H009)がPerl側で行っているのと同じ不変条件(重複tag/重複headword/未知link target/空title)を、Dockerを使わずPython側で先に検査できる軽量verifierを実装する。実際のEPWINGバイナリ(honmon等)を対象とした検証(EB Libraryでの実lookup等)はEpic後半(H013 Mini end-to-end build等)に委ねる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H011(依存: H010)を読んだ
- [x] `ARCHITECTURE.md` 7.1(`wikiepwing verify`)を確認した
- [x] `docker/toolchain/freepwing_build_entries.pl`(TASK-H009)が検証している不変条件(invalid tag/duplicate tag/empty title/unknown link target/duplicate headword)を確認し、同等のチェックをPython側でも先に行う設計とした
- [x] `src/wikiepwing/render/freepwing_source.py`(`write_entries_jsonl`)が書き出す`entries.jsonl`の形式(tag/title/aliases/body/targets)を確認した
- [x] `ingest/verify.py`(`verify_raw_database`)のVerificationResult/payload()パターンを参考にする

## 変更予定ファイル

- `src/wikiepwing/render/verify.py`
- `src/wikiepwing/cli.py`(`verify`サブコマンド追加)
- `tests/test_render_verify.py`
- `tests/test_cli.py`(verifyサブコマンドの確認を追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_verify.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `verify_entries_jsonl(path) -> VerificationResult`が空tag/空title/重複tag/重複headword(別entry間)/未知link targetを検出する
- [x] 問題が無ければ`ok=True`を返す
- [x] `wikiepwing verify --entries <path>`サブコマンドがJSON reportを出力し、`ok`に応じて終了コードを返す
- [x] `make check`が成功する

## 非対象

- 実際に構築されたEPWINGバイナリ(honmon等)へのEB Library経由の検証(TASK-H013等)
- 100-article fixture(TASK-H012)

## 実施結果

- `src/wikiepwing/render/verify.py`に`verify_entries_jsonl`/`VerificationResult`/`VerificationIssue`/`EntriesVerificationError`を実装した。
- `src/wikiepwing/cli.py`に`verify`サブコマンドを追加した。
- `tests/test_render_verify.py`(10件)、`tests/test_cli.py`への追加(3件)を実装。
- `uv run pytest tests/test_render_verify.py tests/test_cli.py`: 30 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート707件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H011チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-H012 100-article fixture。
