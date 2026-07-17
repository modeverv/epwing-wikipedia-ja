# CURRENT_TASK.md

## Task ID

TASK-T016

## 目的

ユーザー依頼。TASK-T014で追加した進捗出力(2万件ごと)を10件ごとに変更してほしい、また`make`を実行するたびに最新のプログラムが反映されているか確認したい、という依頼。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `docker/toolchain.Dockerfile`を`grep`し、`freepwing_build_entries.pl`が一切`COPY`されていないことを確認した
- [x] `build-epwing.sh`が実行時にホスト上のファイルを一時ディレクトリへコピーしてbind mountしていることを確認し、常に最新版が使われることを確認した

## 変更予定ファイル

- `docker/toolchain/freepwing_build_entries.pl`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
git diff --check
```

## 完了条件

- [x] `$PROGRESS_EVERY`が10に変更されている
- [x] 既存の`freepwing-build-entries-smoke.sh`が引き続き成功する
- [x] `git diff --check`が成功する
- [x] 「makeのたびに最新版が反映されるか」の質問にユーザーへ回答した

## 非対象

- なし(小さな変更+質問への回答)

## 実施結果

`docker/toolchain/freepwing_build_entries.pl`の`$PROGRESS_EVERY`を`20_000`から`10`に変更した。既存の`freepwing-build-entries-smoke.sh`が引き続き成功することを確認した。

「makeのたびに最新版が反映されるか」については、`docker/toolchain.Dockerfile`が`freepwing_build_entries.pl`を一切`COPY`していないこと、`build-epwing.sh`が実行時にホスト上の現在のファイルを一時ディレクトリへコピーしてbind mountする実装になっていることを確認し、Dockerイメージの再ビルドに関わらず常にホスト上の最新ファイルが使われる旨をユーザーへ回答した。

`git diff --check`が成功することを確認した。シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。
