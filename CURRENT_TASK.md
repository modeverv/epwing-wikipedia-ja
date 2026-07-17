# CURRENT_TASK.md

## Task ID

TASK-T013

## 目的

ユーザーが全件規模の`entries-mini.jsonl`(約150万記事)でビルドを試したところ`invalid character: \x8f`で失敗した。外字(gaiji)パイプラインの現状を調査した結果、本格対応(normalize/generateへの外字置換統合、CLIコマンド新設)は相応の規模の作業になることを説明し、ユーザーから「簡易的な回避策を先に試したい」との依頼を受けた。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `src/wikiepwing/gaiji/`配下のライブラリ関数(representability/classifier/code_assignment/glyph_renderer/freepwing_gaiji/database)が、`normalize`/`generate`のどこからも呼ばれておらず、CLIコマンドとしても存在しないことをgrepで確認した(RELEASE_CHECKLIST.mdの「✅完了」表記はライブラリ関数レベルの意味であり、パイプライン統合はされていない)
- [x] `invalid character: \x8f`の原因が、PerlのEncodeモジュールの`euc-jp`がJIS X 0212(SS3、`\x8f`プレフィックス)の文字もエンコードしてしまう一方、FreePWINGのFPWParserはJIS X 0208の2バイトコードしか理解できないためであると特定した
- [x] ユーザーへ本格対応の規模を説明し、「簡易的な回避策を先に試したい」という回答を得た

## 変更予定ファイル

- `docker/toolchain/freepwing_build_entries.pl`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
# JIS X 0212専用文字を含む新規フィクスチャでの再現確認(手動)
git diff --check
```

## 完了条件

- [x] `to_euc_jp`が、EUC-JPエンコード結果の先頭バイトが`0x8f`になる文字を全角下駄記号(〓、JIS X 0208内)に置換し、`invalid character`エラーを起こさなくなる
- [x] 既存の`freepwing-build-entries-smoke.sh`が引き続き成功する
- [x] JIS X 0212専用の実在漢字を含む新規フィクスチャでビルドが成功することを確認した
- [x] `git diff --check`が成功する

## 非対象

- 本格的な外字(gaiji)パイプライン統合(normalize/generateでの検出・コード割り当て・グリフ描画・CLIコマンド新設) -- ユーザーが依頼すれば別タスクとして実施
- 下駄記号に置換された文字が実際のEPWINGビューアでどう表示されるかの目視確認(バイナリ内部のバイト列レベルの検証はFreePWINGの内部文字テーブル正規化により単純なgrepでは確認できなかった)

## 実施結果

原因: PerlのEncodeモジュールの`euc-jp`は、JIS X 0212(補助漢字面)の文字もSS3(`\x8f`)プレフィックス付きでエンコードしてしまうが、FreePWINGのFPWParserはJIS X 0208の2バイトコードしか理解せず`\x8f`を見ると即エラーになる。実データの本文には、珍しくはない通常の漢字でJIS X 0212にしか収録されていないものが含まれるため、全件規模で初めて顕在化した(既存のフィクスチャは意図的にJIS X 0208内の文字だけを使っていたため再現しなかった)。

`docker/toolchain/freepwing_build_entries.pl`の`to_euc_jp`を文字単位のループに変更し、各文字をEUC-JPエンコードした結果の先頭バイトが`0x8f`になるものだけを全角下駄記号(〓、U+3013、素のJIS X 0208で表現可能)に置換するようにした。これは本格的なgaiji置換の代替であり、該当文字の情報は失われる簡易回避策であることを明記した。

既存の`freepwing-build-entries-smoke.sh`(通常のASCII/JIS X0208日本語コンテンツ)が引き続き成功することを確認した。加えて、JIS X 0212専用の実在漢字「凜」を含む新規フィクスチャを作成してビルドし、`invalid character`エラーが再発せず最後まで`.epwing.zip`が生成されることを確認した。

シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。

なお、本格的な外字パイプライン統合(normalize/generateでの外字コード割り当て・専用グリフ描画・EPWING外字フォントとしての登録)は今回実施していない。ユーザーが依頼すれば別タスクとして着手する。RELEASE_CHECKLIST.mdの「gaiji fallback ✅ 完了」の記載も、ライブラリ関数レベルの完了であってパイプライン統合はされていない実態を反映するよう修正が必要(今回未実施)。
