# CURRENT_TASK.md

## Task ID

TASK-T006

## 目的

`TASKS.md`のTASK-T006(v1.0 release checklist、依存: S005,T001-T005すべて完了済み)を実施する。PLAN.md 31(v1.0 Definition of Done)の各項目を、このセッションで実際に検証済みの内容(EPIC R/S、TASK-T001〜T005)とコードの実際の状態(grepで確認)に照らして正直に評価し、`RELEASE_CHECKLIST.md`としてまとめる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-T006(依存: S005,T001-T005、すべて完了済み)を読んだ
- [x] `PLAN.md` 31(Build/Content/Quality/Reproducibility/Documentationの5カテゴリ)を項目ごとに評価する方針にした
- [x] `BUILD-INFO.json`生成関数(`build_build_info`/`write_build_info`)がCLIのどこからも呼ばれていないこと、`app_image_digest`/`toolchain_image_digest`が常に`None`であることをgrepで確認した(Reproducibilityカテゴリの評価に反映)
- [x] `distribution.include_attribution_appendix`が設定検証のみで実装が無いこと(TASK-T005で確認済み)をDocumentation/Reproducibilityカテゴリの評価に反映する

## 変更予定ファイル

- `RELEASE_CHECKLIST.md`(新規)
- `README.md`(読む順に追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

なし(ドキュメントのみ。必要に応じて既存実装の有無をgrepで確認する)

## 完了条件

- [x] `RELEASE_CHECKLIST.md`にPLAN.md 31の5カテゴリすべての項目を記載した
- [x] 各項目について「done」「partial」「not done」を実データ検証結果・コード確認に基づいて判定した
- [x] 未実装・未検証の項目(BUILD-INFO.jsonの生成未配線、Docker digestの未計算、attribution appendixの未実装、全件規模でのEPWINGバイナリビルド未実施等)を隠さず明記した
- [x] `README.md`から`RELEASE_CHECKLIST.md`への導線を追加した

## 非対象

- 未実装項目の実装自体(本タスクは評価・記録のみ)

## 実施結果

`RELEASE_CHECKLIST.md`(新規)を作成し、PLAN.md 31の5カテゴリ(Build/Content/Quality/Reproducibility/Documentation)すべての項目を✅done/🟡partial/❌not doneで評価した。

強く検証済みの項目(source lock、resume、Mini/Lite/Full生成、logical hashesなど)はEPIC R/Sでの実データ全件規模・複数環境での検証結果を根拠とした。部分的な項目(画像/数式の全件検証、EPWINGバイナリの全件ビルド、reference/compatibility比較の全件実測)はスコープが縮小されている理由(rate limit、実行時間等)を明記した。

コード確認により新たに発見した3件の未実装ギャップを明記した:
1. 検索語budget(TASK-Q005の`apply_search_budgets`)が`normalize`/`generate`のどこからも呼ばれていない(grepで確認) — Mini/Lite/Fullの`search`設定が実質的にentries.jsonlへ反映されない
2. `BUILD-INFO.json`生成関数(TASK-S001)がCLIのどこからも呼ばれていない
3. Docker image digest(`app_image_digest`/`toolchain_image_digest`)を計算・記録するコードが存在しない(常に`None`)

これらはTASK-T005で発見したattribution appendix未実装と合わせて、v1.0リリース前に対応が必要なギャップとして「まとめ」セクションに整理した。`README.md`の読む順と想定リポジトリ構成に追加した。コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。
