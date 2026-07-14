# CURRENT_TASK.md

## Task ID

TASK-D008

## 目的

ユーザーが既に取得済みのfileを、再downloadせずに(copyまたはsymlinkで)source.lock.jsonへ登録できるようにする(`local-enterprise` provider相当)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D008を読んだ
- [x] `CONFIG_REFERENCE.md` 6節(`source.provider`の`local-enterprise`: predownloaded tar.gz)を確認した
- [x] `PLAN.md`のlocal source registration/local file mode記述を確認した
- [x] TASK-D004(`SourceLock`/`build_source_lock`/`canonical_json`)、TASK-D006(`compute_fingerprint`)、TASK-D007の`AcquireResult`を確認した

## 変更予定ファイル

- `src/wikiepwing/source/register.py`
- `src/wikiepwing/cli.py`
- `tests/test_register.py`
- `tests/test_cli.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_register.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `register_local_source`が既存fileをcopy(既定)またはsymlink(`copy=False`)でsources_root配下へ登録する
- [x] 登録済み(destinationが既に存在する)fileは再copy/再symlinkしない
- [x] 各fileのfingerprintを計算し、呼び出し側が期待SHA-256を渡した場合は不一致を拒否する
- [x] predownloaded fileが存在しない・通常fileでない場合を拒否する
- [x] `sources_root`/snapshot directory/destinationのsymlink・絶対path要件を`acquire_snapshot`と整合させる
- [x] `wikiepwing register-local-source` CLIコマンドがオフラインで動作する(ネットワーク・credentials不要)
- [x] `make check`が成功する

## 非対象

- Wikimedia Enterprise APIへの問い合わせ(このタスクは完全オフライン)
- `source.provider`設定値の検証・切替ロジック自体(既存の`config.py`スキーマ範囲外)
- Source inspect command(TASK-D009)

## 実施結果

- `src/wikiepwing/source/register.py`に`register_local_source`、`LocalSourceFile`、`RegisterError`を実装した。
- destinationが既に存在する(file/symlinkいずれも)場合は再copy/再symlinkせず、その場でfingerprintを再計算するだけにした(acquireの冪等skipと同じ発想)。
- `copy=True`(既定)は一時fileへ書込→fsync→`os.replace`でatomic copy、`copy=False`は解決済み絶対pathへの`symlink_to`を使う。
- 呼び出し側が`expected_sha256`を渡した場合は不一致を明確なエラーで拒否する。predownloaded fileの不在・非通常file、`sources_root`非絶対path、snapshot directoryのsymlinkを拒否する。
- Wikimedia Enterprise metadataレスポンスが存在しないため、`metadata_response_sha256`は登録入力(project/namespace/snapshot_identifier/snapshot_version/date_modified/chunk_identifiers)を正準JSON化したものへのSHA-256として合成した(同じ入力からは決定的に同じ値になることをテストで確認)。
- `SourceLock`の書込を`lockfile.write_source_lock`として`acquire.py`から`lockfile.py`へ切り出し、`acquire.py`・`register.py`双方から再利用するようにした(重複実装の解消)。
- `src/wikiepwing/cli.py`に`wikiepwing register-local-source`コマンドを追加した。`--file PATH:CHUNK_IDENTIFIER[:SHA256]`(複数指定可)、`--copy`/`--no-copy`、`--date-modified`(RFC3339)、`--git-commit`を実装した。完全にオフラインで動作する。
- `tests/test_register.py`に12件、`tests/test_cli.py`に2件(`--help`とend-to-end登録)のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート238件、`git diff --check`が成功した。

**判断・注意点**

- `metadata_response_sha256`をローカル登録用に合成する設計は一次資料が無いための小さな仮定であり、明示的に記録した(WMEの実応答ハッシュとは異なる性質だが、フィールドの目的(このlockを生成した入力の再現可能な指紋)は保っている)。
- `source.provider`設定値自体の検証・切替は対象外とした(既存`config.py`のスキーマ範囲外)。
