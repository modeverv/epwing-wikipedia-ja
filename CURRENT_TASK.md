# CURRENT_TASK.md

## Task ID

TASK-E003

## 目的

acquireされたchunkの`.tar.gz`から、全展開せずにNDJSON行をstreamingで読み出すreaderを実装する。member検証(symlink/device/複数member/不正名を拒否)を行う。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E003を読んだ(依存: D010完了済み)
- [x] `ARCHITECTURE.md` 10.1-10.2(tar.gz内NDJSON、streaming、全展開禁止)を確認した
- [x] TASK-D009の実データ確認(chunkのtar.gzは1 memberの`chunk_N.ndjson`のみ)を確認した
- [x] TASK-D010の`tests/fixtures/enterprise/*.ndjson`を確認した

## 変更予定ファイル

- `src/wikiepwing/ingest/tar_reader.py`
- `tests/test_tar_reader.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_tar_reader.py
make check
git diff --check
```

## 完了条件

- [x] tar.gzをstreaming mode(`r|gz`)で開き、全展開せずNDJSON行をgeneratorとして1行ずつ返す
- [x] ちょうど1つの`.ndjson`で終わる通常fileのみを許可し、それ以外(symlink/device/複数member/不正名/0件)を拒否する
- [x] 1行あたりのbyte数上限を持ち、超過行を拒否する(bounded memory)
- [x] 不正なtar・不正なgzip streamを明確なエラーとして拒否する
- [x] `tests/fixtures/enterprise/normal_articles.ndjson`相当の内容を実際にtar.gz化してend-to-endで読めることを確認する
- [x] `make check`が成功する

## 非対象

- NDJSON行のJSON parsing・RawArticleへのfield抽出(TASK-E004)
- schema検証・重複解決(TASK-E005、E006)

## 実施結果

- `src/wikiepwing/ingest/tar_reader.py`に`iter_ndjson_lines`、`TarStreamError`を実装した。`tarfile.open(..., mode="r|gz")`の純粋streamingモードで開き、全展開せずgeneratorとして1行ずつ返す。
- 唯一のmemberが`*.ndjson`という名前の通常fileであることを検証し、symlink・directory・path traversal名・想定外の2つ目のmemberを拒否した。streaming modeでは先読みができないため、「member数の検証」はgeneratorが完全に消費された後に完了する設計にした(tarfileの`next()`が未読分を自動skipする性質を利用)。
- 1行あたりのbyte数上限(既定8 MiB)を持ち、超過行・非positiveな上限指定を拒否した。
- `tests/fixtures/enterprise/normal_articles.ndjson`(TASK-D010)を実際にtar.gz化し、end-to-endで10行すべて正しく読めることを確認した。
- `tests/test_tar_reader.py`に12件のテスト(通常読取、空行skip、末尾改行無し、行超過、空archive、複数member、不正member名、path traversal、symlink、directory、不正gzip、非positive上限)を追加した。
- format-check、ruff lint、mypy strict、標準スイート298件、`git diff --check`が成功した。

**判断・注意点**

- 実データ(TASK-D005/D009で確認済み)ではchunk archiveは常に1 memberのみだったため、複数member・0 memberをどちらも異常として拒否する設計にした。将来実際のjawiki chunkで複数member構成が見つかった場合はこの前提を見直す。
