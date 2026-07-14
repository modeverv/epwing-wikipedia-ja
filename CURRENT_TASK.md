# CURRENT_TASK.md

## Task ID

TASK-K003

## 目的

`ARCHITECTURE.md` 11.5の`TableBlock.complexity`(`Literal["simple", "wide", "complex", "unsupported"]`)を決定する分類器を実装する。16.3(Table render policy)はsimple="小列数・短いcell・grid-like text"、wide="1行をrecordとして縦表示"、complex="row/sectionごとのkey-value化"と方針だけを述べ、具体的な閾値は規定していない。TASK-K002の`NormalizedTable`(グリッド位置・列数)を入力に、次の判断基準を採用する: (1) 行が無い(空テーブル)場合は`unsupported`、(2) いずれかのセルがrowspan/colspanで結合されている場合は`complex`(16.3の「row/sectionごとのkey-value化」に対応する構造的複雑さ)、(3) 結合が無く列数が閾値を超える場合は`wide`、(4) それ以外は`simple`。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K003(依存: K002)を読んだ
- [x] `ARCHITECTURE.md` 16.3(Table render policy)を再確認した(具体的な閾値は規定されていないため、本タスクでの判断根拠をdocstringに明記する)
- [x] TASK-K002の`NormalizedTable`/`PositionedCell`を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/table_complexity.py`(新規: `classify_table_complexity()`)
- `tests/test_normalize_table_complexity.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_table_complexity.py
make check
git diff --check
```

## 完了条件

- [x] 空テーブル(行数0)は`unsupported`
- [x] rowspan/colspanで結合されたセルが1つでもあれば`complex`
- [x] 結合が無く列数が閾値(デフォルト6)を超える場合は`wide`
- [x] それ以外(結合無し・列数が閾値以下)は`simple`
- [x] `make check`が成功する

## 非対象

- 実際のレンダラ(TASK-K004 simple/K005 wide、複雑度に応じた具体的なテキスト整形)
- oversized(行上限による分割、TASK-K006)

## 実施結果

- `src/wikiepwing/normalize/table_complexity.py`に`classify_table_complexity()`を実装した。判定順序: 行が無ければ`unsupported`→結合セル(rowspan/colspan>1)が1つでもあれば`complex`→列数が閾値(デフォルト6、`max_simple_columns`で変更可能)を超えれば`wide`→それ以外は`simple`。
- `tests/test_normalize_table_complexity.py`(新規8件)で、空テーブル・結合無し小規模テーブル・閾値ちょうど・閾値超過・カスタム閾値・rowspan単独での複雑判定・colspan単独での複雑判定・complexがwideより優先されることを確認した。
- `make check`(format-check/lint/mypy/pytest 866件)と`git diff --check`が成功した。
