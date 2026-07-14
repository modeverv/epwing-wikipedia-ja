# CURRENT_TASK.md

## Task ID

TASK-K010

## 目的

`PLAN.md` Phase 11の出口条件("simple cells lossless"、"wide table readable vertical layout"、"malformed fallback"、"oversized diagnostic")を実際のend-to-endパイプラインで検証するgolden setを作る。実装中に気づいた重大なギャップ: TASK-K001-K009で構築した`build_table_block`/`build_infobox_block`は、`normalize/convert_block.py`の`convert_block()`ディスパッチャからまだ一度も呼ばれておらず、`<table>`要素は依然として`_convert_unsupported`(fallback)へ落ちていた。本タスクでまずこの配線を行い(循環import回避のため`build_table_block`/`build_infobox_block`は関数内local importで取り込む)、その上でTASK-G013と同じ形式(HTML fixture + 期待JSON)のgolden setを追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K010(依存: K006,K009)を読んだ
- [x] `PLAN.md` Phase 11の出口条件・fixture一覧(2x2 simple, multi-header, rowspan, colspan, wide 12 columns, nested table, malformed table, very large table)を確認した
- [x] `convert_block.py`の`convert_block()`が`<table>`を`_convert_unsupported`へ落としていたことに気づいた(K001-K009が配線されていなかった)
- [x] `table_block.py`/`infobox_block.py`が`convert_document`(`convert_block.py`内で定義)を使っており、`convert_block.py`から直接importすると循環importになることを確認した(関数内local importで回避する)
- [x] TASK-G013の golden set構造(`tests/golden/normalize/*.html`+`*.json`、`test_golden_normalize.py`)を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/convert_block.py`(`<table>`をinfobox/table判定して`build_infobox_block`/`build_table_block`へディスパッチするよう配線)
- `tests/golden/normalize/`(table/infobox向けのHTML+JSON fixtureを追加)
- `tests/test_golden_normalize.py`(fixture数の期待値を更新)
- `tests/test_normalize_convert_block.py`(table配線の回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_golden_normalize.py tests/test_normalize_convert_block.py
make check
git diff --check
```

## 完了条件

- [x] `convert_block()`が`<table>`要素をinfobox/tableとして正しくディスパッチし、`_convert_unsupported`へ落ちなくなる
- [x] simple/wide/complexの各complexityのテーブル、infobox、malformed(不正span)なテーブル、ネストしたテーブルを含むgolden fixtureを追加する
- [x] `make check`が成功する

## 非対象

- 画像の実ダウンロード(別epic)
- 数式・参照(別epic)

## 実施結果

- 実装中に発見した重大なギャップ: `convert_block.py`の`convert_block()`は、TASK-K001-K009で構築した`build_table_block`/`build_infobox_block`を一度も呼んでおらず、`<table>`要素は依然として`_convert_unsupported`(fallback)へ落ちていた。`is_infobox`/`is_table`をモジュール先頭でimportし、`build_infobox_block`/`build_table_block`(`convert_document`を呼び返すため循環importになる)は関数内local importで取り込むことで配線した。
- `tests/test_normalize_convert_block.py`・`tests/test_normalize_pipeline.py`の既存テストが`<table>`を「未知要素のfallback例」として使っていたため、`<div>`/`<figure>`に差し替え、新たに`<table>`/infoboxが正しくTableBlock/InfoboxBlockへディスパッチされることを確認する専用テスト2件を追加した。
- `tests/golden/normalize/`にTASK-G013と同形式のfixture6件(11_table_simple, 12_table_wide, 13_table_rowspan, 14_table_malformed_span, 15_infobox, 16_table_nested)を追加した。期待JSONは実際のパイプライン(`normalize_html`)を実行して機械生成し、目視で妥当性を確認した。`14_table_malformed_span`のみ`TABLE_INVALID_SPAN`診断を期待するよう`test_golden_normalize.py`を拡張した(他は従来通りdiagnostics無しを要求)。
- 標準スイート912件(golden fixture 6件・その他新規/変更テストを含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。実DB経由のend-to-endテスト(`test_mini_end_to_end_build.py`等)も影響を受けず成功した。
