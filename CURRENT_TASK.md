# CURRENT_TASK.md

## Task ID

TASK-T012

## 目的

ユーザーが実際に`make build-epwing`(ENTRIES=entries-mini.jsonlのような相対パス)を実行したところ、`cp: -r not specified; omitting directory '/input/entries.jsonl'`で失敗した。原因を特定し修正する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] エラーメッセージから、`docker run -v`のホスト側パスが相対パスの場合に名前付きボリュームとして解釈され、存在しないボリュームは空ディレクトリとしてマウントされてしまうというDockerの挙動が原因と特定した

## 変更予定ファイル

- `docker/toolchain/build-epwing.sh`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
# 実際にバグを再現・修正確認
sh docker/toolchain/build-epwing.sh wikiepwing-toolchain:dev <相対パスのentries.jsonl> output/verify-test.epwing.zip "" "" "検証用百科事典"
docker run --rm -v <extracted>:/book:ro --entrypoint /opt/eb/bin/wikiepwing-eb-search wikiepwing-toolchain:dev /book word "Emacs" 5
git diff --check
```

## 完了条件

- [x] `entries`/`graphics_dir`/`gaiji_dir`が相対パスで渡されても`docker run -v`に絶対パスとして渡される
- [x] 相対パスでの実行で実際にビルドが成功し、`ebinfo`・`wikiepwing-eb-search`での検索が成功することを確認した
- [x] `git diff --check`が成功する

## 非対象

- ユーザーの実データ(`entries-mini.jsonl`、約150万記事)を全件規模でビルドすること(ユーザー側で実施予定)
- 検証中に見つかった別問題(`invalid character: \x8f`、gaiji未指定時のエンコーディングエラー)の修正(今回のバグとは無関係な別事象のため、ユーザーへの報告に留める)

## 実施結果

原因: `docker run -v`は、ホスト側パスが`/`・`./`・ドライブレターで始まらない場合(単なる相対ファイル名など)、bind mountではなく名前付きボリュームとして解釈する。存在しない名前のボリュームは自動的に空のディレクトリとして作成されるため、`/input/entries.jsonl`が実際にはファイルではなく空ディレクトリになり、`cp`(非再帰)が失敗していた。

`docker/toolchain/build-epwing.sh`で、`entries`/`graphics_dir`/`gaiji_dir`の存在チェック直後・`docker run -v`に渡す前に絶対パスへ解決するコードを追加した。

`tests/fixtures/enterprise/hundred_articles.ndjson`から実際にPythonパイプライン(register-local-source→ingest→normalize→generate)で生成した100記事分のentries.jsonlを相対パスで指定してビルドし、EPWINGパッケージが正しく生成され、`ebinfo`でタイトル表示・`wikiepwing-eb-search`で"Emacs"の検索が実際にヒットすることを確認した(ユーザーが遭遇したのと同じ相対パスの使い方で再現・検証)。

なお、ユーザー環境の実際の`entries-mini.jsonl`(約150万記事)の先頭50件で試したところ、このバグとは別に`invalid character: \x8f`という`freepwing_build_entries.pl`のエンコーディングエラーが発生した。gaijiディレクトリを指定していない状態でJIS X 0208外の文字を含む実データを処理しようとしたために起きたと見られ、今回のバグとは無関係。ユーザーへ別途報告する。

シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。
