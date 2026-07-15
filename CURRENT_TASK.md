# CURRENT_TASK.md

## Task ID

TASK-Q009

## 目的

`COMPATIBILITY.md` 13(Compatibility report schema)を実装する。TASK-Q007の`ComparisonSummary`・TASK-Q008の`ThresholdEvaluation`から、schema 13と一致するJSON payloadを構築し、`reference/report.py`(TASK-C007)と同じ原子的書き込みパターンでJSON+HTMLレポートを出力する`write_compatibility_report`を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q009(依存: Q008)を読んだ
- [x] `COMPATIBILITY.md` 13(Compatibility report schema)を再確認した
- [x] `reference/report.py`の`write_reference_report`(JSON/HTML/atomic write、`_write_temporary`+`os.replace`パターン)を参考にした
- [x] schema 13の`articles`/`viewers`セクション(記事比較・viewer手動確認)は本タスクのengineが計算しない値であるため、実データのない`0`のような偽の値を書かず、payloadから省略する方針にした(`redirect_coverage`も同様、query class別データがないため省略)

## 変更予定ファイル

- `src/wikiepwing/compatibility/report.py`(新規: `build_compatibility_report`, `write_compatibility_report`)
- `tests/test_compatibility_report.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_compatibility_report.py
make check
git diff --check
```

## 完了条件

- [x] `build_compatibility_report`が`schema_version`/`reference`/`candidate`/`queries`(`total`/`target_coverage`/`overlap_at_10`)/`thresholds`/`status`を含むJSON-serializableなdictを返す
- [x] `write_compatibility_report`がJSON(`compatibility-report.json`)とHTML(`compatibility-report.html`)を原子的に書き込む
- [x] HTML出力にstatus・target coverage・false positive countが人間可読な形で含まれる
- [x] `make check`が成功する

## 非対象

- article比較・viewer手動確認セクション(実データを計算するengineがまだ存在しないため、payloadから省略)
- query class別(exact title/redirect)の内訳

## 実施結果

- `compatibility/report.py`に`build_compatibility_report`(schema 13の`reference`/`candidate`/`queries`/`thresholds`/`status`を構築)・`write_compatibility_report`(`atomic_write_text`でJSON+HTMLを原子的に書き込み)を実装した。`articles`/`viewers`セクション・`redirect_coverage`は実データがないため意図的に省略した。
- `tests/test_compatibility_report.py`(新規8件)で、schema fieldの一致・JSON serializable・JSON/HTML書き込み・pass/fail両方のHTML反映・ディレクトリ自動作成・overlap Noneの扱い(payload/HTML両方)を確認した。
- `make check`(format-check/lint/mypy/pytest 1290件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
