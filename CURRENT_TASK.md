# CURRENT_TASK.md

## Task ID

TASK-T004

## 目的

`TASKS.md`のTASK-T004(Viewer verification guide、依存: Q009,R009完了済み)を実施する。COMPATIBILITY.md 7(Viewer compatibility)の記録項目・Pass ruleに基づき、実際にEPWINGビューア(EBWin系、EBPocket系、Emacs Lookup/lookup.el系)で成果物を確認する手順を`VIEWER_VERIFICATION.md`としてまとめる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-T004(依存: Q009,R009、両方完了済み)を読んだ
- [x] `COMPATIBILITY.md` 7(必須候補、記録項目、Pass rule)を再確認した
- [x] 実際にEBWin/EBPocket/lookup.elを使った確認は本タスクでは実施しない(このヘッドレス環境にはこれらのビューアが無く、また全件規模のEPWINGバイナリ自体がまだビルドされていないため)。本タスクは「どう確認するか」の手順書作成に限定する
- [x] `docker/toolchain`のFreePWINGビルドツールチェーンが3記事手作り・100記事フィクスチャで既に検証済み(TASK-H013等)であることを確認し、全件規模のEPWINGバイナリビルドはまだ未実施であることをTROUBLESHOOTING.md/BUILD.mdの記述と整合させた

## 変更予定ファイル

- `VIEWER_VERIFICATION.md`(新規)
- `README.md`(読む順に追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

なし(ドキュメントのみ)

## 完了条件

- [x] `VIEWER_VERIFICATION.md`に対象ビューア(EBWin系、EBPocket系、Emacs Lookup/lookup.el系)ごとの入手・セットアップ方法を記載した
- [x] `VIEWER_VERIFICATION.md`にEPWINGバイナリの入手方法(現状は`docker/toolchain`での小規模フィクスチャビルドのみ)を明記した
- [x] `VIEWER_VERIFICATION.md`にCOMPATIBILITY.md 7.2の記録項目に沿ったチェックリスト・記録テンプレートを含めた
- [x] `VIEWER_VERIFICATION.md`にMini/LiteのPass rule(COMPATIBILITY.md 7.3)を明記した
- [x] `README.md`から`VIEWER_VERIFICATION.md`への導線を追加した

## 非対象

- 実際にビューアで確認作業を行うこと(ビューアが無い環境のため手順書作成のみ)
- Licensing/attribution guide(TASK-T005)

## 実施結果

`VIEWER_VERIFICATION.md`(新規)を作成した。EPWINGバイナリのビルド手順(ツールチェーンイメージのビルド、既に検証済みの小規模スモークテスト`handcrafted-three-entry-smoke.sh`/`mini-end-to-end-smoke.sh`/`lite-100-article-smoke.sh`、全件規模での実行手順)、対象ビューア(EBWin系/EBPocket系/Emacs Lookup・lookup.el系)の概要、COMPATIBILITY.md 7.2の記録項目とPass rule(7.3)、記録テンプレート例の4セクションで構成した。

本書執筆時点で全件規模のEPWINGバイナリビルド・実ビューアでの確認はまだ実施していないこと(3記事手作り・100記事フィクスチャでのみ検証済み)を明記した。この環境には実際のビューア(EBWin/EBPocket/lookup.el)が無く、また全件規模のhonmonもまだビルドしていないため、本タスクは手順書作成に限定し、実際の確認作業は行っていない。`docker/toolchain/mini-end-to-end-smoke.sh`のコメントと`freepwing_build_entries.pl`/`eb-search.c`/`eb-entry.c`の実装を確認し、記述が実際のツールチェーンと整合することを確認した。

`README.md`の読む順と想定リポジトリ構成に`VIEWER_VERIFICATION.md`を追加した。コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。
