# CURRENT_TASK.md

## Task ID

TASK-T008

## 目的

ユーザー依頼により追加。ユーザーが実際に`acquire`をネイティブホストで実行した際、コマンドが進捗を一切出力しないため「動いているのか固まっているのか分からない」という問題に遭遇した。`acquire_snapshot`/`ResumableChunkDownloader.download`に進捗コールバックを追加し、`wikiepwing acquire`実行中にチャンク単位(何番目のチャンクが完了したか)・チャンク内バイト単位(現在のチャンクを何MB/何MBダウンロード済みか)の進捗を標準エラー出力に表示するようにする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `src/wikiepwing/ingest/orchestrate.py`等、既存の`on_progress`コールバックパターン(cli.pyがstderrにprintする)を確認し、同じ設計を踏襲する方針にした
- [x] `src/wikiepwing/source/acquire.py`の`acquire_snapshot`(チャンクのループ)と`src/wikiepwing/source/downloader.py`の`ResumableChunkDownloader.download`(1チャンクのストリーミング読み込みループ)の両方に進捗フックが必要であることを確認した(全81チャンク×チャンクあたり数百MBのため、チャンク単位だけでは数分間隔の無出力が残る)

## 変更予定ファイル

- `src/wikiepwing/source/downloader.py`(`ChunkDownloadProgress`、`ResumableChunkDownloader`に`progress_interval_bytes`・`on_progress`追加)
- `src/wikiepwing/source/acquire.py`(`AcquireProgress`、`AcquireChunkProgress`、`acquire_snapshot`に`on_progress`・`on_chunk_progress`追加)
- `src/wikiepwing/cli.py`(`acquire`コマンドで進捗をstderrに出力、`_format_mib`ヘルパー追加)
- `tests/test_acquire.py`(回帰テスト追加)
- `tests/test_chunk_downloader.py`(回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_acquire.py tests/test_chunk_downloader.py
make check
git diff --check
```

## 完了条件

- [x] `ResumableChunkDownloader.download`が`on_progress`(バイト単位、`progress_interval_bytes`ごとに間引き、最後に必ず1回)を受け付ける
- [x] `acquire_snapshot`が`on_progress`(チャンク完了ごと)・`on_chunk_progress`(チャンク内バイト単位、ダウンロード中のみ)を受け付ける
- [x] `wikiepwing acquire`実行時にstderrへ進捗が出力される
- [x] 既存の`_FakeDownloader`(test_acquire.py)が新しい`on_progress`引数を受け付けるよう更新した
- [x] 回帰テストを追加し、`make check`が成功する

## 非対象

- `ingest`/`normalize`/`generate`など他コマンドの進捗表示の変更(既に実装済み)
- ダウンロード速度(bytes/sec)や残り時間の推定表示(今回はバイト数のみ)

## 実施結果

`src/wikiepwing/source/downloader.py`に`ChunkDownloadProgress`(bytes_downloaded, total_bytes)を追加し、`ResumableChunkDownloader.__init__`に`progress_interval_bytes`(既定8MiB)、`download`に`on_progress`引数を追加した。ストリーミング読み込みループ内で`progress_interval_bytes`ごとに間引いて呼び出し、ループ終了後に端数が残っていれば最後に必ず1回呼ぶ(小さいチャンクでも必ず最低1回は報告される)。

`src/wikiepwing/source/acquire.py`に`AcquireProgress`(チャンク完了ごと: chunks_completed/chunks_total/chunk_identifier/size_bytes/already_present)と`AcquireChunkProgress`(ダウンロード中のチャンクのバイト単位進捗)を追加し、`acquire_snapshot`に`on_progress`/`on_chunk_progress`引数を追加した。`ChunkDownloader` Protocolも`on_progress`引数を受け付けるよう更新した。

`src/wikiepwing/cli.py`の`acquire`コマンドで両コールバックをstderrへの`print`に接続した(`chunk N/M <identifier>: downloaded (330.5 MB)`、`chunk N/M <identifier>: 120.0 MB / 330.5 MB`という形式)。`_format_mib`ヘルパーを追加した。

`tests/test_acquire.py`の既存`_FakeDownloader.download`が新しい`on_progress`引数(型付き)を受け付けるよう更新し(呼び出されたら1件のprogress eventを発行するようにした)、新規に3件のテスト(チャンクごとに1イベント・順序通り、already_presentのマーキング、チャンク内バイト進捗)を追加した。`tests/test_chunk_downloader.py`に3件のテスト(間引かれた複数イベント、間隔未満でも最後に必ず1件、`progress_interval_bytes`の非正数値の拒否)を追加した。

`make check`(1401 passed, +6件)、`uv run mypy src`(138ファイル、エラーなし)、`git diff --check`が成功することを確認した。既存のingest/normalize/generateと同じ「stderrへの進捗print」パターンに合わせたため、他コマンドとの一貫性を保っている。
