# CURRENT_TASK.md

## Task ID

TASK-E009

## 目的

取込済み`raw.sqlite3`の整合性を検証するverifierを実装する。integrity_check・foreign key・各tableの件数・html/wikitext blobのsample展開を確認する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E009を読んだ(依存: E008完了済み)
- [x] `DATA_CONTRACTS.md` 4節(raw.sqlite3 schema)を再確認した
- [x] TASK-E002(`zstd_codec.decompress`)、TASK-E007(`RawRepository`が書くtable一覧)を確認した

## 変更予定ファイル

- `src/wikiepwing/ingest/verify.py`
- `src/wikiepwing/cli.py`
- `tests/test_ingest_verify.py`
- `tests/test_cli.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_ingest_verify.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `PRAGMA integrity_check`/`PRAGMA foreign_key_check`を実行し結果を記録する
- [x] articles(accepted/rejected別)/redirects/categories/templates/licenses/article_licenses/main_images/ingest_duplicates/diagnosticsの件数を集計する
- [x] html_zstd/wikitext_zstdを持つ行から決定的にsampleを選び、実際に`decompress`して破損を検出する
- [x] 上記すべてが正常な場合のみ`ok=True`を返す
- [x] `wikiepwing verify-raw --raw-database`コマンドがオフラインで動作し、`ok=False`なら非ゼロ終了コードを返す
- [x] TASK-E008で取込んだTASK-D010 fixture由来のDBに対し実際に検証し、期待通りの件数・sample展開成功を確認する
- [x] `make check`が成功する

## 非対象

- 中断recovery判定(TASK-E010)
- model/rendered/index DBの検証(将来epic)

## 実施結果

- `src/wikiepwing/ingest/verify.py`に`RawVerificationCounts`、`RawVerificationResult`、`verify_raw_database`を実装した。
- `PRAGMA integrity_check`/`PRAGMA foreign_key_check`、articles(accepted/rejected別)/redirects/categories/templates/licenses/article_licenses/main_images/ingest_duplicates/diagnosticsの件数集計、`ROW_NUMBER() OVER`による決定的な等間隔sample抽出とhtml/wikitext blobの`decompress`検証を実装した。
- `wikiepwing verify-raw --raw-database --sample-size`コマンドを追加した。不整合があれば非ゼロ終了コードを返す。
- TASK-D010の10正常記事をTASK-E008で取り込んだDBに対し実際に検証し、`ok=True`・件数一致・sample展開成功を確認した。さらにhtml_zstdを意図的に壊した行を作り、`decompress`失敗が正しく検出されることを確認した。
- `tests/test_ingest_verify.py`に5件、`tests/test_cli.py`に2件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート362件、`git diff --check`が成功した。

**判断・注意点**

- sampleは真の乱数ではなく`page_id`順の等間隔抽出とし、決定的な再現性を優先した。
- model/rendered/index DBの検証は将来のepicで同様のパターンを再利用する想定とした。
