# CURRENT_TASK.md

## Task ID

TASK-T011

## 目的

ユーザー依頼により追加。TASK-T010で並列化・limitモードを追加した`image-fetch`が、実行中の進捗を一切出力せず「動いているのか分からない」という状態だった(acquireで過去に遭遇したのと同じ問題)。`fetch_media`にURL1件完了ごとの進捗コールバックを追加し、CLIで標準エラー出力に表示するようにする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `acquire`(TASK-T008)で確立した「`on_progress`コールバックをCLIがstderrにprintする」パターンを踏襲する方針にした
- [x] 並列実行時(`max_workers > 1`)は`executor.map`のままだと先頭のURLが遅いと後続の速い完了が報告されないため、`concurrent.futures.as_completed`に切り替える必要があることを確認した

## 変更予定ファイル

- `src/wikiepwing/media/orchestrate.py`(`FetchProgress`追加、`fetch_media`に`on_progress`引数追加、並列実行を`as_completed`ベースに変更)
- `src/wikiepwing/cli.py`(`image-fetch`で進捗をstderrに出力)
- `tests/test_media_orchestrate.py`(回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run mypy src
uv run ruff format .
uv run ruff check .
uv run pytest tests/test_media_orchestrate.py -q
make check
git diff --check
```

## 完了条件

- [x] `fetch_media`が`on_progress`(completed/total/succeeded/failed)を受け付け、URL1件完了ごとに呼ばれる
- [x] 並列実行時は実際にダウンロードが完了した順にコールバックが呼ばれるが、返り値の`tuple`はplan順のまま変わらない
- [x] `image-fetch`実行時にstderrへ進捗が出力される
- [x] 回帰テストを追加し、`make check`が成功する

## 非対象

- ダウンロード速度(bytes/sec)や残り時間の推定表示

## 実施結果

`src/wikiepwing/media/orchestrate.py`に`FetchProgress`(completed, total, succeeded, failed)を追加し、`fetch_media`に`on_progress`引数を追加した。逐次実行時(`max_workers == 1`)はURLを1件処理するたびに呼び出す。並列実行時(`max_workers > 1`)は`executor.map`をやめて`concurrent.futures.as_completed`ベースの実装に変更し、futureが実際に完了した順(plan順ではない)でコールバックを呼ぶようにした。返り値の`tuple`は従来通りplan順(ユニークURL抽出順)を維持している。

`src/wikiepwing/cli.py`の`image-fetch`コマンドで`on_progress`をstderrへの`print`に接続した(`fetch N/M succeeded=X failed=Y`形式)。

`tests/test_media_orchestrate.py`に3件のテスト(逐次実行時の進捗順序、並列実行時の進捗イベント数、失敗のカウント)を追加した。

`make check`(1410 passed、+3件)、`uv run mypy src`(138ファイル、エラーなし)、`git diff --check`が成功することを確認した。既存のacquire/normalize/generateと同じ「stderrへの進捗print」パターンに合わせている。
