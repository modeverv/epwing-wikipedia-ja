# CURRENT_TASK.md

## Task ID

TASK-T017

## 目的

`wikiepwing ingest` の記事処理前後にある重い無表示処理へ進捗表示を追加し、処理中か終了不能かを利用者が判別できるようにする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] 実データの過去manifestと現在の実装を調査した

## 変更予定ファイル

- `src/wikiepwing/source/checksums.py`
- `src/wikiepwing/ingest/database.py`
- `src/wikiepwing/ingest/orchestrate.py`
- `src/wikiepwing/cli.py`
- 対応するテスト
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest -q tests/test_checksums.py tests/test_ingest_database.py tests/test_ingest_orchestrate.py tests/test_cli.py
make format-check
make lint
make typecheck
make test
git diff --check
```

## 完了条件

- [x] 入力チャンク検証の進捗が表示される
- [x] 既存DBの整合性検証中であることと継続中の進捗が表示される
- [x] 出力DB fingerprint計算のバイト進捗が表示される
- [x] 進捗コールバックを使わない既存呼び出しとの互換性を維持する
- [x] 対応テストと標準検証が成功する
- [x] 対象変更だけをコミットする

## 非対象

- ingest再実行時のmanifest探索・スキップ仕様の変更
- ingestの処理速度改善
- 外字関連の未コミット変更

## 実施結果

入力チャンク検証、既存出力DBのresume判定用fingerprint、SQLite `integrity_check`、終了時DB fingerprintへ進捗コールバックを追加した。CLIはバイト処理を256 MiBごと、整合性検証を開始・1,000万VMステップごと・完了時に標準エラーへ表示する。小さい処理でも各フェーズの完了表示は省略しない。

局所テスト73件、標準テスト1,437件、format-check、lint、mypy、`git diff --check`がすべて成功した。
