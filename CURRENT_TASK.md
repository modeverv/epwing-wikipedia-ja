# CURRENT_TASK.md

## Task ID

TASK-T007

## 目的

ユーザー依頼により追加。`RELEASE_CHECKLIST.md`(TASK-T006)で発見した「`entries.jsonl`から日本語Wikipedia全件規模でEPWING本体(HONMON)をビルドする本番用スクリプトが存在しない」というギャップに対応する。既存の`freepwing_build_entries.pl`(TASK-H009、汎用実装済み)・`write_graphics_build_files`(TASK-O011)・`write_gaiji_build_files`(EPIC M)を組み合わせ、任意件数の`entries.jsonl`・任意個数の画像/gaijiからEPWINGパッケージ(`.epwing.zip`)を組み立てる`docker/toolchain/build-epwing.sh`と、それを呼ぶ`make build-epwing`ターゲットを追加する。README.mdの「想定コマンド」を実態に合わせて更新する。実際のビルド実行(全件規模)はユーザー側が行うため、本タスクでは小規模な動作確認のみ行う。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `docker/toolchain/mini-end-to-end-smoke.sh`/`handcrafted-three-entry-smoke.sh`/`package-smoke.sh`の実装を読み、fpwmakeの呼び出しパターン(Makefile変数、`fpwmake`→`fpwmake catalogs`、ebzip、zip)を理解した
- [x] `docker/toolchain/freepwing_build_entries.pl`が既に汎用実装(任意件数のentries、任意個数のaliases/targets)であることを確認した
- [x] `src/wikiepwing/media/freepwing_graphics.py`の`write_graphics_build_files`、`src/wikiepwing/gaiji/freepwing_gaiji.py`の`write_gaiji_build_files`が既に`cgraphs.txt`/`halfchars.txt`/`fullchars.txt`形式で出力することを確認した(新規実装不要、既存出力をそのまま使う)
- [x] `catalogs.txt`(EPWINGカタログメタデータ)を生成するPythonコードが存在しないことを確認し、シェルスクリプト内でタイトル/サブブック名をパラメータ化して生成する設計にした
- [x] `docker/toolchain/fpwutils.mk`(fpwmakeのMakefile本体)を確認し、`CGRAPHS`/`HALFCHARS`/`FULLCHARS`が未設定/空でも動作すること(画像・gaiji無しのMini相当ビルドに対応)を確認した

## 変更予定ファイル

- `docker/toolchain/build-epwing.sh`(新規)
- `Makefile`(`build-epwing`ターゲット追加)
- `README.md`(「想定コマンド」を実態に更新)
- `TASKS.md`(TASK-T007追加)
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
# 小規模動作確認(100記事フィクスチャのentries.jsonlを使用、画像・gaiji無し)
sh docker/toolchain/build-epwing.sh wikiepwing-toolchain:dev <entries.jsonl> /tmp/test.epwing.zip "" "" "テスト百科事典"
# 生成されたZIPをwikiepwing-eb-searchで検索できることを確認
```

## 完了条件

- [x] `docker/toolchain/build-epwing.sh`が任意の`entries.jsonl`(+任意でgraphics/gaijiディレクトリ)から`.epwing.zip`を生成できる
- [x] `make build-epwing`ターゲットが上記スクリプトを呼び出せる
- [x] 小規模テスト(100記事フィクスチャ由来のentries.jsonl、画像・gaiji無し)でビルドが成功し、`wikiepwing-eb-search`で実際に検索できることを確認した
- [x] `README.md`の「想定コマンド」セクションを実態のCLIコマンド・ビルド手順に更新した

## 非対象

- 全件規模(約150万記事)での実際のビルド実行(ユーザー側が実施)
- 画像・gaiji付きの本番規模テスト(小規模動作確認のみ、時間的制約のため画像・gaiji無しの最小ケースに限定)
- BUILD-INFO.json/Docker digest/attribution appendixの配線(RELEASE_CHECKLIST.mdに記録済みの別ギャップ、本タスクの範囲外)

## 実施結果

`docker/toolchain/build-epwing.sh`(新規)を作成した。既存の`freepwing_build_entries.pl`(entries.jsonl解析)、`write_graphics_build_files`/`write_gaiji_build_files`が出力する`cgraphs.txt`/`halfchars.txt`/`fullchars.txt`形式をそのまま入力として受け付け、`catalogs.txt`(EPWINGカタログメタデータ、タイトル/サブブック名をパラメータ化)をスクリプト内で生成し、`fpwmake`→`fpwmake catalogs`→`ebzip`→`zip`で最終的な`.epwing.zip`を組み立てる。画像・gaijiディレクトリは省略可能(Mini相当のビルドに対応、空の`cgraphs.txt`/`halfchars.txt`/`fullchars.txt`をコンテナ内で使う)。

`Makefile`に`build-epwing`ターゲットと関連変数(`ENTRIES`, `GRAPHICS_DIR`, `GAIJI_DIR`, `TITLE`, `SUBBOOK_DIR`, `EPWING_OUTPUT`)を追加した。

小規模動作確認として、`tests/fixtures/enterprise/hundred_articles.ndjson`(既存の100記事フィクスチャ)を実際に`register-local-source`→`ingest`→`normalize`→`generate`→`verify`のPythonパイプラインに通してentries.jsonlを生成し(画像・gaiji無し)、新しい`build-epwing.sh`でEPWINGパッケージを実際にビルドした。ビルドは成功し(`ebinfo`が正しいタイトル「テスト百科事典」を表示)、生成されたZIPを展開して`wikiepwing-eb-search`で"Emacs"を検索したところ、実際に複数の検索結果(R行)が返り、正しく検索可能なEPWING辞書であることを確認した。テスト用の一時ファイルはすべて削除済み。

`README.md`の「想定コマンド」「CLIの最終形」セクションを、実際に動作する`wikiepwing`サブコマンド(acquire/ingest/normalize/generate/verify/image-plan/image-fetch/image-convert/disk-usage/clean/update)と、新設した`make build-epwing`による実際のEPWINGビルド手順に更新した。README.mdの読む順に[BUILD.md](BUILD.md)への参照を強調した。

`make check`(既存のPythonテストスイート、コード変更なしのため影響なし)と`git diff --check`が成功することを確認した。
