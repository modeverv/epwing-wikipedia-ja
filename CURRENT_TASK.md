# CURRENT_TASK.md

## Task ID

TASK-R001

## 目的

`PLAN.md` Phase 20(10,000記事耐久試験)の「page ID rangeだけでなく、次を含むstratified sample」を実装する。AskUserQuestionでの承認に基づき、実際にWikimedia Enterprise APIから実データ(jawiki namespace 0の最初の1 chunk、約2.7万記事)を取得し、それを対象にlong article/table-heavy/image-heavy/math-heavy/history-literature/technical/disambiguation/list article/rare Unicodeの各層を検出して、10,000記事のstratified sampleとそのreportを生成する`sampling`モジュールを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R001(依存: P007,Q009)を読んだ
- [x] `PLAN.md`の「Phase 20 — 10,000記事耐久試験」(stratified sampleの層一覧)を再確認した
- [x] AskUserQuestionで実データ取得(1 chunk、約381MB)の承認を得て、実際に`.env`の認証情報でWikimedia Enterprise APIを認証し、jawiki namespace 0の最初のchunk(27,859記事、約2GB展開後)をローカルscratchpadへダウンロード・検証済み(git管理外、コミットしない)
- [x] `wikiepwing.ingest.record_parser.parse_record`(既存のNDJSON→`RawArticle`パーサ)を再利用し、独自のNDJSONパースを再実装しない方針にした
- [x] 実データ(著作権・ライセンス配慮が必要な実Wikipedia本文)はgitへコミットしない。テストは合成の小さいfixtureのみを使う

## 変更予定ファイル

- `src/wikiepwing/sampling/__init__.py`(新規)
- `src/wikiepwing/sampling/stratify.py`(新規: `ArticleSignals`, `compute_signals`, `StratifiedSample`, `select_stratified_sample`, `iter_raw_articles`, `build_stratified_sample_ndjson`, `write_sample_report`)
- `tests/test_sampling_stratify.py`(新規、合成fixtureのみ)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_sampling_stratify.py
make check
git diff --check
# 実データに対する検証(git管理外のscratchpadで実行)
uv run python3 -c "..."  # build_stratified_sample_ndjsonを実際のchunkに対して実行
```

## 完了条件

- [x] `compute_signals`が`RawArticle`からlong_article/table_heavy/image_heavy/math_heavy/disambiguation/list_article/history_or_literature/technical/rare_unicodeの各層を検出する(該当なしは`baseline`)
- [x] `select_stratified_sample`が各非baseline層について`min_per_stratum`件を優先的に選び、残りをbaselineで`target_total`まで埋める、streaming可能な1パスアルゴリズムである
- [x] `build_stratified_sample_ndjson`が実際のNDJSONファイルから選択された記事の生の行を新しいNDJSONファイルへ書き出す
- [x] `write_sample_report`が`schema_version`/`total_scanned`/`total_selected`/層ごとの発見数・選択数を含むJSONレポートを書き出す
- [x] 実際にダウンロード済みの実データ(jawiki namespace 0 chunk 0、27,859記事)に対して実行し、stratified sampleとreportが生成できることを確認した(git管理外)。実際の選択数は8,055件(target_total=10,000に対し、1 chunkのみではbaseline候補が尽きたため未達。詳細は実施結果参照)
- [x] `make check`が成功する

## 非対象

- Full-build preflight gate(TASK-R002)
- 実データ・生成したsample NDJSON・reportをgitへコミットすること(著作権・サイズの理由で対象外、コードとテストのみコミットする)

## 実施結果

- `src/wikiepwing/sampling/stratify.py`(新規)に`compute_signals`(9つの非baseline層+baseline)・`select_stratified_sample`(1パスstreamingアルゴリズム)・`iter_raw_articles`・`build_stratified_sample_ndjson`・`write_sample_report`を実装した。既存の`ingest.record_parser.parse_record`を再利用し、NDJSONパースを再実装しなかった。
- `tests/test_sampling_stratify.py`(新規20件、すべて合成fixture)で、各層の検出・複数層への同時該当・budget充足順序・target_total遵守・重複除去・NDJSON書き出し・reportフィールドを確認した。
- `make check`(format-check/lint/mypy/pytest 1310件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- **実データでの検証**: AskUserQuestionでの承認に基づき、`.env`の実認証情報でWikimedia Enterprise APIへ実際に認証し(login経由)、jawiki namespace 0の最初の1 chunk(約381MB圧縮、展開後約2GB、27,859記事の実記事)を取得した(git管理外のscratchpadへ、コミットしていない)。取得したchunkに対して`build_stratified_sample_ndjson(target_total=10_000, min_per_stratum=500)`を実行し、約2分22秒で完走した: `total_scanned=27859`, `total_selected=8055`(target 10,000に対し未達。この1 chunkには「どの層にも該当しないbaseline記事」が4,929件しかなく、それを全て使い切っても8,055件までしか埋まらなかったため。9つの非baseline層それぞれ`min_per_stratum=500`件ずつ、重複除去後の合計選択数は約3,126件)。各層の実際の発見数: table_heavy=14797, image_heavy=7623, disambiguation=3908, long_article=3103, history_or_literature=1613, technical=663, math_heavy=464, rare_unicode=43, list_article=79。
- 実データ・生成したsample NDJSON(約473MB)・reportはgitへコミットしていない(著作権・サイズの理由)。実行後、抽出した中間ファイル(展開済み2GB NDJSON)は削除し、ダウンロード済みsource.lock.json+chunkはscratchpad上に残した。
