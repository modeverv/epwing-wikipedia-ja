# CURRENT_TASK.md

## Task ID

TASK-T015

## 目的

ユーザーから`freepwing_build_entries.pl`が「めちゃくちゃ遅い」、進捗表示や並列化で何とかならないか問い合わせがあった。原因を調査し、リスクの低い範囲で高速化する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] TASK-T013で追加した`to_euc_jp`の1文字ずつの`encode()`呼び出しループが、全件規模で数億〜十億回規模のPerl関数呼び出しになっており、支配的なコストであると特定した
- [x] JIS X 0212のSS3シーケンス(`\x8f`+2バイト)が他の正当なEUC-JPシーケンスの末尾バイトとして出現し得ないため、文字列全体を1回encodeしてから正規表現で一括置換する実装に変えても等価であることを理論的に確認した
- [x] FPWParser登録ループ(`word2->add_entry`の`entry_position()`)が処理順依存の内部状態を持つため、安全に並列化できないと判断した(今回は対象外)

## 変更予定ファイル

- `docker/toolchain/freepwing_build_entries.pl`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
# 新旧実装のバイト単位一致確認・実行時間比較(手動)
git diff --check
```

## 完了条件

- [x] 新実装が旧実装(1文字ずつのループ)とバイト単位で完全に等価であることを、エッジケースを含めて確認した
- [x] 実際に計測して高速化効果を確認した
- [x] 既存の`freepwing-build-entries-smoke.sh`が引き続き成功する
- [x] `git diff --check`が成功する

## 非対象

- パースループ自体の複数プロセス並列化(実装・出力順序保証のリスクがあるため対象外)
- FPWParser登録ループの並列化(`entry_position()`の処理順依存のため対象外)
- `fpwsort`/`fpwindex`等コンパイル済みバイナリの高速化(ソースを持たないため対象外)

## 実施結果

`to_euc_jp`を、文字列全体を1回`encode('euc-jp', $value)`した後、結果のバイト列に対して`s/\x8f../$GETA_MARK_EUC_JP/gs`で正規表現一括置換する実装に変更した(従来は`split //`で1文字ずつループし`encode()`を呼んでいた)。

JIS X 0212のSS3シーケンス(`\x8f` + 2バイト、両方とも`0xA1`-`0xFE`)は、他の正当なEUC-JPシーケンス(JIS X0208の2バイト目・SS2かなの2バイト目、いずれも`0xA1`以上)の末尾バイトとして`\x8f`(0x8Fは0xA1未満)が出現することがないため、新実装は旧実装とバイト単位で完全に等価。様々なエッジケース(JIS X0212専用文字の連続、通常文字との混在、下駄記号が入力に既に含まれる場合等)を通したPerlスクリプトで一致を確認した。

10万件・本文400〜800文字程度の合成entries.jsonl(約131MB)で実際にDocker内で計測: 旧実装134.08秒→新実装68.16秒(約2倍の高速化)。全件規模(約150万記事)では単純計算で約34分→約17分程度の短縮が見込まれる。

FPWParserへの登録ループ(`word2->add_entry`が`entry_position()`という処理順依存の内部カウンタを使う)は状態を持つため安全に並列化できないと判断し、今回は対象外とした。パースループ自体のプロセス並列化も、実装・出力順序保証のリスクを考慮し今回は見送った(ユーザーが依頼すれば別途検討)。

既存の`freepwing-build-entries-smoke.sh`が引き続き成功することを確認した。シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。
