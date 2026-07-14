# CURRENT_TASK.md

## Task ID

TASK-G013

## 目的

`PLAN.md` Phase 6出口条件"10記事golden一致"を実装する。`ARCHITECTURE.md`のディレクトリ構成で予告されている`tests/golden/`配下に、Phase 6の初期対応範囲(headings/paragraphs/bold-italic/ordered-unordered list/definition list/pre-code/line break/simple quote/horizontal rule/HTML entities/section anchors)を1つずつ代表する10個のHTML入力+期待Block JSON出力のペアを配置し、`normalize_html`の出力が固定的に一致し続けることをregression testとして保証する。internal/external link(Epic H範囲、未実装)は対象外とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G013(依存: G012)を読んだ
- [x] `PLAN.md` Phase 6(初期対応一覧・出口条件"10記事golden一致")を確認した
- [x] `ARCHITECTURE.md`のディレクトリ構成(`tests/golden/`)を確認した
- [x] `normalize/pipeline.py`の`normalize_html`と`model/blocks.py`の`block_payload`を再利用する

## 変更予定ファイル

- `tests/golden/normalize/*.html`(10ファイル)
- `tests/golden/normalize/*.json`(10ファイル、対応する期待Block JSON配列)
- `tests/test_golden_normalize.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_golden_normalize.py
make check
git diff --check
```

## 完了条件

- [x] 10個のgolden fixture(heading/paragraph/bold-italic/ordered list/unordered list(nested)/definition list/preformatted-code/line break/blockquote/horizontal rule+HTML entities+section anchor)を用意する
- [x] 各fixtureについて`normalize_html`の出力(`block_payload`でJSON化したもの)が保存済みの期待JSONと完全一致する
- [x] `make check`が成功する

## 非対象

- internal/external linkを含むgolden fixture(Epic H未実装のため)
- Table/Infobox/Image/Math/Referencesを含むgolden fixture(Epic K/L/N/O未実装のため)

## 実施結果

- `tests/golden/normalize/`に10組のHTML/JSON goldenペアを作成した。
- `tests/test_golden_normalize.py`に11件のテスト(存在確認+10 fixtureの完全一致検証)を追加。
- `uv run pytest tests/test_golden_normalize.py`: 11 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート620件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G013チェック)、`LOG.md`(新規エントリ)を更新した。
- Epic G(HTML normalization baseline)完了。次はEpic H(Links and Mini rendering)。
