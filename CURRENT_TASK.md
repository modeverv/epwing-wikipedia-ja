# CURRENT_TASK.md

## Task ID

TASK-T014

## 目的

ユーザーが`make build-epwing`実行中に「進捗も何も出ない、遅すぎる」と報告(質問で対象を確認したところ`make build-epwing`と回答)。`freepwing_build_entries.pl`のentries.jsonlパース・FPWParser登録の2ループに進捗出力を追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `make build`という(存在しない)ターゲットとの混同の可能性があったため、AskUserQuestionで実際に指している対象を確認し、`make build-epwing`であるとの回答を得た
- [x] `freepwing_build_entries.pl`に2つの大きなループ(entries.jsonlのパース、FPWParserへの登録)があり、どちらも進捗出力が皆無であることを確認した(TASK-T013で追加した1文字ずつのEUC-JP変換が特にパースループを重くしている)
- [x] `fpwsort`/`fpwindex`等それ以降の工程はFreePWING/EB付属のコンパイル済みバイナリで、ソースを持たないため進捗追加は対象外と判断した

## 変更予定ファイル

- `docker/toolchain/freepwing_build_entries.pl`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
# 45,000件の合成entries.jsonlで進捗出力を確認(手動)
git diff --check
```

## 完了条件

- [x] パースループ・FPWParser登録ループの両方が`N/total`件ごと(20,000件間隔)+完了時に必ず1回、標準エラー出力に進捗を出す
- [x] 既存の`freepwing-build-entries-smoke.sh`が引き続き成功する
- [x] 45,000件規模の合成フィクスチャで実際に途中経過の出力を確認した
- [x] `git diff --check`が成功する

## 非対象

- `fpwsort`/`fpwindex`/`fpwcontrol`/`fpwlink`/`ebzip`等、FreePWING/EB付属のコンパイル済みバイナリ側への進捗追加(ソースを持たないため対象外)

## 実施結果

`docker/toolchain/freepwing_build_entries.pl`に`$| = 1`(autoflush)・`$PROGRESS_EVERY = 20_000`を追加し、entries.jsonlパースループの開始前に総行数を数える軽量な事前パスを追加した。パースループは`parse N/total`を、FPWParser登録ループは`index N/total`を、それぞれN件ごと+ループ終了後に必ず1回、標準エラー出力するようにした。

既存の`freepwing-build-entries-smoke.sh`(3エントリ)が引き続き成功し、`parse 3/3`・`index 3/3`が出力されることを確認した。加えて45,000件の合成entries.jsonlを実際に`build-epwing.sh`経由でビルドし、`parse 20000/45000`→`parse 40000/45000`→`parse 45000/45000`→`index ...`という進捗が実際に出力され、ビルドも最後まで成功することを確認した。

`fpwsort`/`fpwindex`/`fpwcontrol`/`fpwlink`/`ebzip`等、その後の工程はFreePWING/EB付属のコンパイル済みバイナリであり、ソースを持たず進捗出力を追加できないため今回は対象外とし、ユーザーへその旨を伝える。

シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。
