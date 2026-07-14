# CURRENT_TASK.md

## Task ID

TASK-K005

## 目的

`PLAN.md` Phase 11("wide renderer"、出口条件"wide table readable vertical layout")と`ARCHITECTURE.md` 16.3("wide": 1行をrecordとして縦表示)を実装する。TASK-K004で`complexity=="wide"`/`"complex"`は暫定的にcaption+行数プレースホルダで劣化表示していたが、本タスクで実際の縦record表示に置き換える。先頭行が全てヘッダーセルの場合はそれをフィールドラベルとして使い、各データ行を「ラベル: 値」の並びとして出力する。"complex"(結合セルあり)専用のレンダラtaskがTASKS.mdに存在しないため、16.3の"complex"("row/sectionごとのkey-value化")が"wide"の縦record表示と同じ方針であることを根拠に、本タスクのレンダラを両方のcomplexityに適用する(結合セルはDOM順にそのまま各フィールドとして展開し、グリッド上の正確な位置合わせは行わない)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K005(依存: K003,H007)を読んだ
- [x] `PLAN.md` Phase 11の出口条件("wide table readable vertical layout")・`ARCHITECTURE.md` 16.3を再確認した
- [x] TASK-K004で追加した`_render_table`の暫定プレースホルダ(wide/complex)を確認した
- [x] "complex"専用のレンダラtaskがTASKS.mdに存在しないことを再確認した(TASK-K004のLOGで気づき、本タスクで対応方針を決定する)

## 変更予定ファイル

- `src/wikiepwing/render/mini_layout.py`(`_render_table`を拡張し、wide/complexを縦record表示にする)
- `tests/test_render_mini_layout.py`(wide/complexの縦record表示テストを追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_mini_layout.py
make check
git diff --check
```

## 完了条件

- [x] `complexity`が`wide`または`complex`の`TableBlock`が、各データ行を「ラベル: 値」の並びとして縦に表示する
- [x] 先頭行が全てヘッダーセルの場合、そのセルの文字列をフィールドラベルとして使う
- [x] ヘッダー行が無い場合は「列N」という汎用ラベルにフォールバックする
- [x] レコード間に空行を入れて視覚的に区切る
- [x] `make check`が成功する

## 非対象

- oversized(行上限による分割、TASK-K006)
- 結合セルの正確なグリッド位置に基づくラベル対応付け(現実装はDOM順の素朴な展開に留める)

## 実施結果

- `render/mini_layout.py`に`_render_table_as_records()`を実装し、`_render_table`の`complexity in ("wide", "complex")`分岐から呼び出すようにした。先頭行が全てヘッダーセルなら、その文字列を以降の各行のフィールドラベルとして使い、「ラベル: 値」を1行ずつ、レコード間に空行を挟んで出力する。ヘッダー行が無い場合は「列N」にフォールバックする。
- "complex"専用のレンダラtaskがTASKS.mdに存在しないため、16.3の"complex"("row/sectionごとのkey-value化")が"wide"の縦record表示と同じ方針であるという判断で、本タスクのレンダラを両方のcomplexityに適用した。結合セルはDOM順にそのまま展開し、グリッド上の正確な位置合わせは行わない(将来必要になれば別途対応)。
- `tests/test_render_mini_layout.py`の既存プレースホルダテストを、ヘッダー行有り/無しの縦record表示テストと"complex"の縦record表示テストに置き換えた(新規3件)。
- `make check`(format-check/lint/mypy/pytest 880件)と`git diff --check`が成功した。
