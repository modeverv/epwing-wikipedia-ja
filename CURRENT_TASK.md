# CURRENT_TASK.md

## Task ID

TASK-P005

## 目的

TASK-H013の`docker/toolchain/mini-end-to-end-smoke.sh`(実toolchain image内でfpwmake/eb-searchまで通す100記事gate)と同じ形の、Lite profile(`config/profiles/lite.toml`)向けDocker smoke testを追加する。TASK-P004でwikiepwing-toolchain:devイメージを実際にrebuild・検証した際にTASK-O007の`convert_to_bmp`のSVGバグを発見・修正済みであり、そのイメージを引き続き使ってこのタスクを検証する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-P005(依存: P004)を読んだ
- [x] `docker/toolchain/mini-end-to-end-smoke.sh`(TASK-H013)の実装を確認した
- [x] `RenderedEntry.graphics`が現時点で常に空(実際のFreePWING graphics統合はEPIC O012で対象外とした)であるため、Lite profileのDocker smoke testはMini版とほぼ同じ形(fpwmake/eb-searchでの検索確認)になる。実画像埋め込みの差異は検証できないことを明記する
- [x] Dockerが実際に利用可能で、`wikiepwing-toolchain:dev`イメージが直前のbugfix検証でrebuild済みであることを確認した

## 変更予定ファイル

- `docker/toolchain/lite-100-article-smoke.sh`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
sh docker/toolchain/lite-100-article-smoke.sh wikiepwing-toolchain:dev
make check
git diff --check
```

## 完了条件

- [x] `docker/toolchain/lite-100-article-smoke.sh`が`config/profiles/lite.toml`を使ってPython pipeline(register→ingest→normalize→generate→verify)を実行する
- [x] 実toolchain image内で`fpwmake`によるhonmon構築、`ebinfo`、`wikiepwing-eb-search`による複数titleの検索確認まで実際に完走する
- [x] `make check`が成功する

## 非対象

- 実際の画像embedding(`RenderedEntry.graphics`は依然空のため、Lite/Mini間でこのsmoke testに実質的な差はない)
- TASK-P006/P007(10,000記事規模のビルド)

## 実施結果

- `docker/toolchain/lite-100-article-smoke.sh`(新規)を、TASK-H013の`mini-end-to-end-smoke.sh`と同じ構成で作成した(`config/profiles/lite.toml`をoverrideとして使い、`NormalizeOptions`に`images_enabled=config.section("images")["enabled"]`を渡す)。
- `wikiepwing-toolchain:dev`イメージを実際にrebuildし(この過程でTASK-O007の`convert_to_bmp`のSVGバグを発見・修正、別コミット済み)、本スクリプトを実際に実行した。Python pipeline(register→ingest→normalize→generate→verify)・`fpwmake`によるhonmon構築・`ebinfo`・`wikiepwing-eb-search`での複数title("Emacs"/"Linux"/"Vim alias"/"GNU Project")検索確認まで全て実際に完走することを確認した。
- `RenderedEntry.graphics`が現時点で常に空(実際のFreePWING graphics統合はEPIC O012で対象外とした)であるため、このsmoke testはMini版と実質的に同じ内容になる(画像embeddingの差異は検証できない)ことを明記した。
- `make check`(1236件、変更なし)と`git diff --check`が成功した。
