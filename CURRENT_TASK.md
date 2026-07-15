# CURRENT_TASK.md

## Task ID

TASK-Q008

## 目的

`COMPATIBILITY.md` 5.3(Initial thresholds)・13(Compatibility report schemaの`thresholds`/`status`フィールド)を実装する。TASK-Q007の`ComparisonSummary`に対して、設定可能なthreshold(target coverage下限・許容false positive数)を適用し、`"pass"`/`"fail"`のstatusを判定する`evaluate_thresholds`を追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q008(依存: Q007)を読んだ
- [x] `COMPATIBILITY.md` 5.3(exact title 100%/redirect 99%以上/fixed common queries 95%以上/missing query false hit 0)・13(`thresholds`/`status`)を再確認した
- [x] `reference/queries.py`の`FixedQuery`にquery class(exact title/redirect/common等)を区別するフィールドがなく、TASK-Q007が単一の集約`target_coverage`のみを算出する設計だったことを踏まえ、本タスクもclass別ではなく単一のtarget coverage閾値+false positive上限に対する汎用的な閾値評価として実装する(class別内訳が必要になった場合はfixture schema拡張を伴う別タスクの対象と判断)

## 変更予定ファイル

- `src/wikiepwing/compatibility/comparison.py`(`ThresholdConfig`, `ThresholdEvaluation`, `evaluate_thresholds`, `DEFAULT_THRESHOLDS`追加)
- `tests/test_compatibility_comparison.py`(追記)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_compatibility_comparison.py
make check
git diff --check
```

## 完了条件

- [x] `target_coverage`が`min_target_coverage`以上であれば`target_coverage_ok=True`
- [x] `false_positive_count`が`max_false_positives`以下であれば`false_positives_ok=True`
- [x] 両方満たす場合のみ`status="pass"`、いずれか満たさない場合は`status="fail"`
- [x] `DEFAULT_THRESHOLDS`が`COMPATIBILITY.md` 5.3の「fixed common queries target coverage: 95%以上」・「missing query returns false exact hit: 0」を反映する
- [x] `make check`が成功する

## 非対象

- query class別(exact title/redirect/common)の個別閾値評価(fixture schemaにclass情報がないため)
- Compatibility HTML report(TASK-Q009)

## 実施結果

- `compatibility/comparison.py`に`ThresholdConfig`・`DEFAULT_THRESHOLDS`(`min_target_coverage=0.95`, `max_false_positives=0`)・`ThresholdEvaluation`・`evaluate_thresholds`を実装した。
- `tests/test_compatibility_comparison.py`(新規5件)で、閾値内でのpass・target coverage不足でのfail・false positiveでのfail・デフォルト閾値の使用・デフォルト値がCOMPATIBILITY.mdと一致することを確認した。
- `make check`(format-check/lint/mypy/pytest 1283件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- query class別(exact title/redirect/common)の個別閾値評価は対象外とした(fixture schemaにclass情報がないため)。
