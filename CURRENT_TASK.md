# CURRENT_TASK.md

## Task ID

TASK-Q007

## 目的

`COMPATIBILITY.md` 5(固定query比較: Result presence/Overlap@N/Target coverage)・13(Compatibility report schemaの`queries`フィールド)を実装する。TASK-C007(reference report)・TASK-H011(EPWING verifier baseline)が既に提供する構造化データを踏まえ、reference側とcandidate側(自分のbuild)の同一固定query setに対する検索結果を比較し、target coverage・overlap@Nを算出する`compare_query_results`を実装する。実際にcandidate側の検索を実行するharness(EB search adapterを自分のbuildに対して走らせる部分)は、実build/Docker実行を要するため対象外とし、比較計算のみを実装する(reference側searchのpersistence: TASK-C006/`reference/searches.py`と同じ責務分離)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-Q007(依存: C007,H011)を読んだ
- [x] `COMPATIBILITY.md` 5(固定query比較の3つのmetrics: Result presence/Overlap@N/Target coverage、5.3の初期threshold)・13(Compatibility report schema)を再確認した
- [x] `reference/queries.py`の`FixedQuery`(`key`/`text`/`expected_presence`、"正解heading"のような追加フィールドはない)を確認し、target coverageの操作的定義を「`expected_presence=True`のqueryはhitが1件以上、`expected_presence=False`のqueryはhitが0件」(5.3の「missing query returns false exact hit: 0」と整合)とした
- [x] `reference/searches.py`の`SearchHit`(`heading`等、entry_locatorはbackend固有のためcandidate側と直接比較不可)を確認し、Overlap@Nの比較キーは`heading`テキストを採用する方針にした

## 変更予定ファイル

- `src/wikiepwing/compatibility/__init__.py`(新規)
- `src/wikiepwing/compatibility/comparison.py`(新規: `QueryHitSet`, `QueryComparison`, `ComparisonSummary`, `compare_query_results`)
- `tests/test_compatibility_comparison.py`(新規)
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

- [x] `expected_presence=True`のqueryでcandidate側にhitが1件以上あれば`presence_matches_expectation=True`
- [x] `expected_presence=False`のqueryでcandidate側にhitが0件であれば`presence_matches_expectation=True`(1件でもあれば偽陽性としてFalse)
- [x] `overlap_at_n`が`|candidate_headings ∩ reference_headings| / |reference_headings|`で計算される。reference側headingsが空の場合は`None`
- [x] `ComparisonSummary.target_coverage`が`presence_matches_expectation`がTrueのqueryの割合
- [x] `ComparisonSummary.false_positive_count`が`expected_presence=False`かつhitがあったqueryの件数
- [x] reference側に存在するがcandidate側に対応するquery_keyがない場合は`ValueError`を送出する(部分的な比較を隠さない)
- [x] `make check`が成功する

## 非対象

- 実際にcandidate側の検索を実行するharness(自分のbuildに対するEB search adapter実行、実build/Docker実行が必要)
- Compatibility thresholds(TASK-Q008、閾値判定・レポート全体のstatus判定)

## 実施結果

- `src/wikiepwing/compatibility/`(新規パッケージ)の`comparison.py`に`QueryHitSet`・`QueryComparison`・`ComparisonSummary`・`compare_query_results`を実装した。target coverageは「`expected_presence`と実際のhit有無が一致するqueryの割合」、overlap@Nは`heading`テキストによる集合演算(entry_locatorはbackend固有のため使わない)とした。
- `tests/test_compatibility_comparison.py`(新規10件)で、presence一致/不一致・偽陽性検出・target coverage計算・overlap@N計算(交差なし/一部/reference側空)・overlap_at_n_meanの平均・candidate側query_key欠落時のエラー・空入力を確認した。
- `make check`(format-check/lint/mypy/pytest 1278件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- 実際にcandidate側の検索を実行するharness(実build/Docker実行が必要なEB search adapter実行)は対象外とした。
