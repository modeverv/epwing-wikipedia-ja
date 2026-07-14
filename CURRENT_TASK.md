# CURRENT_TASK.md

## Task ID

TASK-D006

## 目的

fileのstreaming SHA-256計算とsize検証を1つの再利用可能なmoduleへ集約する。TASK-D005のdownloaderが個別に持っていた同等ロジックをこのmoduleへ委譲し、将来のTASK-D007(acquireコマンド)やverify系処理からも同じ実装を使えるようにする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D006を読んだ
- [x] `ARCHITECTURE.md`のsourceパッケージ構成(`source/checksums.py`)を確認した
- [x] `DATA_CONTRACTS.md` 2節のsource lock契約(`sha256`は64桁小文字hex、`size_bytes`)を確認した
- [x] TASK-D005の`ResumableChunkDownloader`内部の`_sha256_file`実装を確認した(本タスクで置き換える)

## 変更予定ファイル

- `src/wikiepwing/source/checksums.py`
- `src/wikiepwing/source/downloader.py`(内部実装を`checksums`委譲へ置換)
- `tests/test_checksums.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_checksums.py tests/test_chunk_downloader.py
make check
git diff --check
```

## 完了条件

- [x] `compute_fingerprint`がfileを一定サイズのbufferでstreaming読取し、size_bytesとSHA-256を返す(全体を一度にメモリへ読まない)
- [x] `verify_fingerprint`が期待size/hashと実際の値を比較し、不一致を明確に区別して報告する
- [x] symlinkのfileを拒否する
- [x] 不正な期待SHA-256形式(64桁小文字hex以外)・負のsize_bytesを拒否する
- [x] `ResumableChunkDownloader`が独自実装ではなくこのmoduleを使う
- [x] `make check`が成功する

## 非対象

- source.lock.jsonへの実際の検証呼び出し(TASK-D007)
- 参照辞書やmodel DBなど他DBのintegrity check(既存の`PRAGMA integrity_check`系とは別)

## 実施結果

- `src/wikiepwing/source/checksums.py`に`FileFingerprint`、`compute_fingerprint`(一定bufferでのstreaming読取、size_bytes/SHA-256を返す)、`verify_fingerprint`(期待値との比較、size/hashを区別してエラー報告)を実装した。
- symlink拒否、read不能fileの明確なエラー、`read_chunk_bytes`非正値拒否、期待SHA-256の64桁小文字hex形式検証、負のsize拒否を実装した。
- `src/wikiepwing/source/downloader.py`の`ResumableChunkDownloader.download`から独自の`_sha256_file`実装を削除し、`compute_fingerprint`を使うよう置き換えた(重複実装の解消)。
- `tests/test_checksums.py`に12件のオフラインテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート216件、`git diff --check`が成功した。

**判断・注意点**

- source.lock.jsonへの実際の検証呼び出しはTASK-D007(acquireコマンド)の対象とした。
