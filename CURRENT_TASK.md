# CURRENT_TASK.md

## Task ID

TASK-D005

## 目的

Snapshot chunkのresumable downloaderを実装する。HEAD相当のContent-Range/Content-Length確認、Range再開、`.partial`ファイルへの書込とatomic rename、5xx/timeout/接続断へのbounded retry、401/403の即時失敗を持つ。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D005を読んだ
- [x] `ARCHITECTURE.md` 9.4(ダウンロード要件)を確認した
- [x] `SOURCES.md`のChunk download API訂正版(2026-07-14実測: `GET /v2/snapshots/{snapshot_identifier}/chunks/{identifier}/download`が307でS3署名付きURLへredirectし、Rangeが機能することを確認済み)を確認した
- [x] `DECISIONS.md` ADR-016(chunk単位download)を確認した
- [x] TASK-D004の`SourceLockFile`(`relative_path`/`chunk_identifier`/`size_bytes`/`sha256`)を確認した

## 変更予定ファイル

- `src/wikiepwing/source/downloader.py`
- `tests/test_chunk_downloader.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_chunk_downloader.py
make check
git diff --check
```

## 完了条件

- [x] `GET /v2/snapshots/{snapshot_identifier}/chunks/{identifier}/download`への2段階(API redirect→S3 Range GET)を実装し、S3への転送で`Authorization`headerを送らない
- [x] 401/403は即座に失敗として扱う(リトライしない)
- [x] 5xx/timeout/接続断はbounded retryする
- [x] 既存の`.partial`ファイルがあればその末尾からRangeで再開する
- [x] `Content-Range`/`Content-Length`から期待total sizeを検証し、不一致・不正形式を拒否する
- [x] 完了後はSHA-256を計算し、`.partial`から最終destinationへatomic rename(`os.replace`)する
- [x] destination・partial pathのsymlinkを拒否する
- [x] `make check`が成功する

## 非対象

- `source.lock.json`への書込(TASK-D007)
- 実際にjawiki全81 chunk・約30 GBを本セッションでダウンロードすること(コード実装とテストに限定)
- checksum/fingerprintの別モジュール化(TASK-D006)
- disk空き容量の事前確認(`doctor`/acquireコマンド側)

## 実施結果

- `src/wikiepwing/source/downloader.py`に`ResumableChunkDownloader`(resume/retry/atomic renameのオーケストレーション)、`ChunkTransport` Protocol、`HttpChunkTransport`(API redirect→S3への手動2段階request)、`ChunkDownloadResult`を実装した。
- `HttpChunkTransport`は正しいendpoint`GET /v2/snapshots/{snapshot_identifier}/chunks/{identifier}/download`を叩き、307/301/302/303/308 redirectを自前の`HTTPErrorProcessor`override(自動redirect追従を無効化)で捕捉し、redirect先のS3 URLへは`Authorization`headerを送らずに素のGET(`Range`のみ)を送る。
- `ResumableChunkDownloader.download`は既存の`.partial`ファイルの末尾からRangeで再開し、`Content-Range`(206)/`Content-Length`(200)から期待total sizeを検証、`.partial`をappendモードで書込み、完了後にSHA-256を計算して`os.replace`でatomic renameする。
- 401/403は`ChunkDownloadAuthError`として即座に失敗(リトライしない)、5xx/timeout/接続断/不正なContent-Range/status不一致は`ChunkDownloadError`としてbounded retry(`max_retries`、デフォルト5)する。destinationと`.partial`のsymlinkを拒否する。
- `tests/test_chunk_downloader.py`に25件のオフラインテスト(通常完了、再開、途中断からの再試行、retry上限超過、認証エラー即時失敗、不正なstatus/header、symlink拒否、`HttpChunkTransport`の2段階redirect・Authorization非転送・401/5xx/timeout)を追加した。
- 実credentialsで実際にend-to-endダウンロードを検証した: `aawiki_namespace_0_chunk_0`(1,252 bytes)を完全ダウンロードし、gzip展開して中身が`chunk_0.ndjson`であることを確認した。さらに実ファイルを途中で切り詰めた状態から実APIに対して再開させ、新規フルダウンロードと完全に同一のbytesが得られることを確認した(resumeが実データで実証された)。
- format-check、ruff lint、mypy strict、標準スイート205件、`git diff --check`が成功した。

**判断・注意点**

- 前回セッションで発見した404は、アカウント権限ではなくendpoint pathの誤り(chunkをsnapshotと同列に扱っていた)が原因だった。ユーザーが提示した公式APIリファレンスで訂正した。
- disk空き容量の事前確認と`source.lock.json`への書込・生成はacquireコマンド(TASK-D007)側の責務として残した。
- 実データ検証に使った一時スクリプトはリポジトリ外のスクラッチパッドに置き、コミットしていない。credentialsは一切ログ・文書へ出力していない。
