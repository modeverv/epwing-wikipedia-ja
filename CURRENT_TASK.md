# CURRENT_TASK.md

## Task ID

TASK-T040

## 目的

Wikipedia Enterprise Snapshot チャンク取得 (`acquire`) およびソースダンプ登録・正規化 (`register-local-source`, `ingest`, `normalize`) コマンドの `Makefile` ターゲットを追加し、`README.md` を更新する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した

## 変更予定ファイル

- `Makefile`
- `README.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
make check
```

## 完了条件

- [x] `Makefile` に `acquire`, `register-local-source`, `ingest`, `normalize` ターゲットが追加されていること
- [x] `README.md` が更新され、入力データ取得・正規化から EPWING ビルドまでの全コマンド一覧が明記されていること
- [x] リント・フォーマット・テストスイート（`make check`）がすべて成功すること

## 結果

- `Makefile` に `acquire`（Wikipedia Snapshot チャンクの取得・ダウンロード・固定）、`register-local-source`（ローカルダンプ登録）、`ingest`（Raw DB取り込み）、`normalize`（正規化・モデルDB構築）を追加。
- `README.md` の運用タスク表・コマンド例をフルパイプライン対応へ更新。
- 全 1,484 件のテストおよび `make check` を通過。

## 非対象

- 他の無関係なサブコマンドの廃止
