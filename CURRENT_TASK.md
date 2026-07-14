# CURRENT_TASK.md

## Task ID

TASK-M006

## 目的

`DATA_CONTRACTS.md` 10(Gaiji registry contract: "AssignmentはUnicode sort order + width classなどの決定論的規則を使用。処理順依存にしません。")を実装する。TASK-M004の`gaiji`テーブルの`assigned_code`列(NOT NULL UNIQUE)へ入れる値を、登録済みsequence群から決定論的に計算する`assign_gaiji_codes()`を実装する。実際のFreePWING/EB向けファイル形式(`halfchars.txt`/`fullchars.txt`、実際のgaiji code表現)への変換はTASK-M007(依存: M006,H009)の対象であり、本タスクは抽象的な決定論的割当のみを扱う。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M006(依存: M005)を読んだ
- [x] `DATA_CONTRACTS.md` 10(Assignment規則)を再確認した
- [x] `tests/fixtures/handcrafted/halfchars.txt`/`fullchars.txt`/`generate_gaiji.pl`(実際のFreePWING gaiji fixture)を確認し、half/wideが別々のファイル(=別々のcode空間)で管理されることを確認した(本タスクでもnarrow/wideを別々に採番する根拠)
- [x] 実際のEB/FreePWING側のgaiji code表現形式(`halfchars.txt`の行形式等)への変換はTASK-M007の範囲であることを確認した(本タスクはその手前の抽象的な決定論的割当のみ)

## 変更予定ファイル

- `src/wikiepwing/gaiji/code_assignment.py`(新規: `assign_gaiji_codes()`）
- `tests/test_gaiji_code_assignment.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_code_assignment.py
make check
git diff --check
```

## 完了条件

- [x] `assign_gaiji_codes(entries)`が、width_class("narrow"/"wide")ごとに独立した採番空間を持つ
- [x] 各width_class内でsequenceのUnicodeソート順に基づいて決定論的にcodeを割り当てる(入力の並び順に依存しない)
- [x] 同じ入力集合に対して常に同じ割当結果を返す(冪等性)
- [x] 不正なwidth_class・重複sequenceに対してエラーを送出する
- [x] `make check`が成功する

## 非対象

- 実際のFreePWING/EB向けファイル形式への変換(TASK-M007)
- gaiji.sqlite3への実際の書き込み配線(将来のタスク)

## 実施結果

- `src/wikiepwing/gaiji/code_assignment.py`に`GaijiCodeAssignmentError`・`assign_gaiji_codes()`を実装した。width_class("narrow"/"wide")ごとに独立した採番空間を持ち、各グループ内でsequenceのUnicodeソート順(Pythonのデフォルト文字列比較)に基づいて`f"{width_class}-{index:04d}"`形式のcodeを1始まりで割り当てる。
- `tests/fixtures/handcrafted/halfchars.txt`/`fullchars.txt`(実際のFreePWING gaiji fixture)を確認し、narrow/wideが別々のファイル(=別々のcode空間)で管理される実際の慣習を根拠とした。
- `tests/test_gaiji_code_assignment.py`(新規8件)で、width_class毎の連番割当・独立したcode空間・Unicodeソート順による決定論的割当・入力順序に依存しない冪等性・空入力・不正width_class・重複sequence・4桁ゼロパディングを確認した。
- `make check`(format-check/lint/mypy/pytest 996件)と`git diff --check`が成功した。
