# CURRENT_TASK.md

## Task ID

TASK-D009

## 目的

`source.lock.json`を読み、記録済みfingerprintとの再検証(file)、tar構造の列挙(tar)、NDJSON内容の bounded sample(NDJSON)を行うinspectコマンドを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D009を読んだ
- [x] `ARCHITECTURE.md` 7.1(`wikiepwing source inspect`)を確認した
- [x] `PLAN.md` Phase 3出口条件(「source lockから再検証可能」)を確認した
- [x] TASK-D004(`parse_source_lock`)、TASK-D006(`compute_fingerprint`)、TASK-D007/D008で生成される`source.lock.json`の実構造を確認した

## 変更予定ファイル

- `src/wikiepwing/source/inspect.py`
- `src/wikiepwing/cli.py`
- `tests/test_source_inspect.py`
- `tests/test_cli.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_source_inspect.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `source.lock.json`をparseし、記録されたfilesそれぞれの実際のsize/SHA-256を再計算して一致を判定する
- [x] symlink登録(`register-local-source --no-copy`)されたfileも解決済みの実体を再検証できる
- [x] fingerprintが一致したfileのみtar構造(member名・size)を列挙する
- [x] NDJSON member(`.ndjson`で終わる名前)を検出し、bounded byte数・件数でJSON行をsample・parseする
- [x] 不正なtar・不正なNDJSON行を明確なエラーとして報告する
- [x] `wikiepwing inspect-source --lock-path`がオフラインで動作し、不一致があれば非ゼロ終了コードを返す
- [x] `make check`が成功する

## 非対象

- 実際のraw ingest処理(EPIC E)
- fixture NDJSONの作成(TASK-D010)
- HTML/Wikitextの検証(EPIC E/Gの対象)

## 実施結果

- `src/wikiepwing/source/inspect.py`に`inspect_source`、`SourceInspection`、`FileInspection`、`TarMember`、`NdjsonSample`、`InspectError`を実装した。
- lockの各fileについて`compute_fingerprint`で実際のsize/SHA-256を再計算し、記録値と比較する。symlink登録(`register-local-source --no-copy`)されたfileは解決済みの実体を対象にする。
- fingerprintが一致したfileのみ`tarfile`でtar構造を列挙し、`.ndjson`で終わるmemberを検出してbounded byte数・件数でJSON行をsample・parseする(`readline(N+1)`で1行あたりのメモリを上限管理)。
- 不正なtar・不正なNDJSON行・不在file・lock自体の破損を明確な`InspectError`として拒否する。
- `src/wikiepwing/cli.py`に`wikiepwing inspect-source --lock-path --sample-lines`コマンドを追加した。JSON結果を出力し、不一致があれば終了コード1を返す。完全にオフラインで動作する。
- `tests/test_source_inspect.py`に14件、`tests/test_cli.py`に2件(`--help`とregister→inspectのend-to-end)のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート254件、`git diff --check`が成功した。
- 実credentialsで`acquire`→`inspect-source`をend-to-endで実行し(project=aawiki)、`ok: true`、tar member `chunk_0.ndjson`、NDJSON sample1件を正しく取得できることを実データで確認した。sample内容から実際のWME記事レコード全フィールド(`article_body.html`、`license`、`redirects`、`version`等)が判明し、将来のEPIC E(Raw ingest)実装の参考情報として有用だった。

**判断・注意点**

- `tarfile.getmembers()`はtar形式の性質上、archive全体を順次スキャンする(central directoryが無いため)。bytes-in-memoryは境界内(streaming)だが、大きなchunk(実測300MB超)ではtar構造列挙に時間がかかる。これは「開発者による手動inspect」用途として許容範囲と判断した。
- HTML/Wikitextの内容検証自体は対象外とし、単にNDJSON行がJSON objectとしてparseできることのみ確認する。
