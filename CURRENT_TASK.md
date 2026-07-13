# CURRENT_TASK.md

## Task ID

TASK-C007

## 目的

`reference.sqlite3`のinventory識別子、固定query結果、entry標本、diagnosticを決定的なJSON/HTML reportへまとめ、機械取得不能な表示品質を実行可能なmanual checklistへ分離する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-C007を読んだ
- [x] C006の実参照DBが7 entries、1 recoverable read failure、integrity okであることを確認した
- [x] `ARCHITECTURE.md` 19.3-19.5と`COMPATIBILITY.md` 6.3/7を確認した

## 変更予定ファイル

- `src/wikiepwing/reference/report.py`
- `src/wikiepwing/cli.py`
- `tests/test_reference_report.py`
- `tests/test_cli.py`
- `TASKS.md`
- `PLAN.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_reference_report.py tests/test_cli.py
make toolchain-image
WIKIEPWING_REFERENCE_PATH=/Users/seijiro/work/004_dic/Wikip_ja20230120 \
  docker compose -f compose.yaml -f compose.reference.yaml run --rm reference-inspector \
  wikiepwing reference-report --database /data/work/reference.sqlite3
make check
```

## 完了条件

- [x] reportがschema version、book/subbook、query/result counts、entry標本、diagnosticを含む
- [x] JSON/HTML/Markdownを出力先内のtemporary fileからatomic replaceする
- [x] HTML中の外部由来文字列をescapeし、inline scriptや外部resourceを含めない
- [x] manual checklistがviewer/version/OS/hashと記事別表示・link・media・gaiji確認欄を持つ
- [x] 実DBから3成果物を生成し、再生成SHA-256が一致する
- [x] Phase 2出口条件を実測で確認する
- [x] offline局所テストと`make check`が成功する

## 非対象

- manual checklistの人間による記入
- EBWin/EBPocket/Emacs LookupのUI自動操作
- Source acquisition（TASK-D001以降）

## 実施結果

- 実DBの1 subbook、18 queries、820 results、7 entry samples、8 diagnosticsをschema-versioned JSONへ出力した。
- 同じ内容を外部resourceやscriptを持たないescape済みHTMLへ出力した。
- viewer/version、OS、artifact hash、検索、7記事×10表示項目、警告確認を持つmanual checklistを生成した。
- 再生成前後のSHA-256はJSON `3aeb3143366a8588e1526930dc5c25cbf22cb6cd5a73f492c712b48e0c5d7a63`、HTML `5cb27f8cdb3b9b8acdb8f718f76f92df8969b43cd305c366b43fae4fb2bcbe48`、checklist `d7ebaa5167a3348335815311ef86031bbeed6a849b3d496085f3b087d3c519df`で一致した。
- 参照`CATALOGS` SHA-256はC002時点と同じ`5751a37c296a20c80efe69230e36511c35dcb05cb91e14f2067d9f524fb710a6`だった。
- format-check、ruff、mypy strict、標準テスト102件、`git diff --check`が成功した。
- 次の工程へ進む前に`reports/reference-manual-checklist.md`の人間によるviewer確認が必要。
