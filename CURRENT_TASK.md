# CURRENT_TASK.md

## Task ID

TASK-T003

## 目的

`TASKS.md`のTASK-T003(Troubleshooting、依存: R009完了済み)を実施する。PLAN.md 31(v1.0 Definition of Done)のDocumentation項目「troubleshooting」を満たす。EPIC R/Sで実データ全件規模のビルド中に実際に遭遇した症状・原因・対処を`TROUBLESHOOTING.md`としてまとめ、将来の運用者が同じ問題に再度時間を使わずに済むようにする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-T003(依存: R009、完了済み)を読んだ
- [x] PLAN.md 31の「troubleshooting」以外に詳細な出口条件記述が無いことを確認した
- [x] EPIC R(TASK-R003〜R007)・EPIC S(TASK-S005)で実際に発見・対処した実データ限定の問題(すべて既にコード修正済み)と、コード修正では解消できない運用上の注意点(Wikimedia側のrate limit挙動、Docker Desktopのメモリサイジング、ディスク容量、認証情報設定)を区別してまとめる方針にした

## 変更予定ファイル

- `TROUBLESHOOTING.md`(新規)
- `README.md`(読む順に追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

なし(ドキュメントのみ、既存のLOG.md/CURRENT_TASK.mdの実施結果から実データを引用する)

## 完了条件

- [x] `TROUBLESHOOTING.md`にEPIC R/Sで発見・修正済みの実データ限定バグ(症状→原因→対処、現在のコードでは解消済み)をまとめた
- [x] `TROUBLESHOOTING.md`にコード修正では解消できない運用上の注意点(rate limit、Dockerメモリ、ディスク容量、認証情報)をまとめた
- [x] `TROUBLESHOOTING.md`に診断手順(doctor/verify/verify-raw/manifest確認)への導線を含めた
- [x] `README.md`から`TROUBLESHOOTING.md`への導線を追加した

## 非対象

- Viewer verification guide(TASK-T004)
- Licensing/attribution guide(TASK-T005)

## 実施結果

`TROUBLESHOOTING.md`(新規)を作成した。「1. 既に修正済みの問題」でEPIC R(TASK-R003〜R007)で発見・修正した7件の実データ限定バグ(redirects等の重複キー、NDJSON行サイズ制限、data: URI画像、Unicode改行文字によるJSONL分割、プロトコル相対URL、User-Agent、429リトライ)を症状→原因→対処の形式でまとめた。「2. コード修正では解消できない運用上の注意点」でrate limit/Docker OOM(TASK-S005)/ディスク容量/認証情報/DUPLICATE_HEADWORD(TASK-R006)/古いCommons URL/ImageMagick未インストールをまとめた。「3. 診断手順」でdoctor/manifest確認/verify-raw/verify/image-fetchレポート集計への導線を示した。

すべての項目は実際にEPIC R/Sで遭遇し、LOG.md/CURRENT_TASK.mdに記録済みの実データに基づいて書いた(推測での記述はしていない)。`README.md`の読む順と想定リポジトリ構成に`TROUBLESHOOTING.md`を追加した。コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。
