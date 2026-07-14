# CURRENT_TASK.md

## Task ID

TASK-D007

## 目的

metadata解決→chunk download→verify→source.lock.json書込を1つのacquireオーケストレーションとCLIコマンドへ組み上げる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D007を読んだ
- [x] `ARCHITECTURE.md` 9.4(ダウンロード要件、source.lock.jsonは全ファイル検証後にのみ作成)を確認した
- [x] `DATA_CONTRACTS.md` 2節(source lock契約、`.tar.gz`拡張子へ訂正済み)を確認した
- [x] TASK-D002(`EnterpriseAuthClient`)、TASK-D003(`SnapshotMetadataClient`/`ResolvedSnapshot`)、TASK-D004(`SourceLock`/`build_source_lock`/`canonical_json`)、TASK-D005(`ResumableChunkDownloader`)、TASK-D006(`compute_fingerprint`/`verify_fingerprint`)を確認した
- [x] `config/default.toml`の`source`/`source.enterprise`セクションと`paths.sources`を確認した
- [x] `tests/test_cli.py`の既存コマンドの`--help`テストパターンを確認した

## 変更予定ファイル

- `src/wikiepwing/source/acquire.py`
- `src/wikiepwing/cli.py`
- `tests/test_acquire.py`
- `tests/test_cli.py`
- `DATA_CONTRACTS.md`(拡張子訂正、完了)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_acquire.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `acquire_snapshot`がauth解決→metadata解決→chunkごとdownload→verify→`SourceLock`構築→atomic書込を順に行う
- [x] 既にdestinationが存在するchunkは再downloadせず、fingerprintを再計算して使う(中断再開時の無駄な再取得を避ける)
- [x] download直後にverify_fingerprintで再検証し、破損を検出したら失敗させる
- [x] `sources_root`が絶対pathでない場合・snapshot directoryやchunk destinationがsymlinkの場合を拒否する
- [x] `wikiepwing acquire` CLIコマンドが`config`/環境変数からsecrets・endpoint・timeout・retryを組み立てて実行できる
- [x] git commitは`git rev-parse HEAD`で自動解決し、失敗時は`--git-commit`を明示要求する
- [x] `make check`が成功する

## 非対象

- 実際にjawiki全81 chunk(約30 GB)を本セッションでacquireすること(コードとfakeによるテストに限定)
- disk空き容量事前確認(`doctor`コマンド側)
- ローカル既存sourceの登録(TASK-D008)

## 実施結果

- `src/wikiepwing/source/acquire.py`に`acquire_snapshot`(auth解決→metadata解決→chunkごとdownload→verify→`SourceLock`構築→atomic書込)、`AcquireResult`、`AuthResolver`/`MetadataResolver`/`ChunkDownloader` Protocolを実装した。
- destinationが既に存在するchunkは再downloadせず`compute_fingerprint`で再計算し、新規downloadしたchunkは`verify_fingerprint`で再検証してから`SourceLockFile`へ積む。
- `snapshot_directory`・chunk destinationのsymlinkを拒否し、`sources_root`が絶対pathでない場合を拒否する。
- `src/wikiepwing/cli.py`に`wikiepwing acquire`コマンドを追加した。`--namespace`/`--snapshot-version`/`--git-commit`のCLI override、`config/default.toml`の`source`/`source.enterprise`セクションからのendpoint/timeout/retry組み立て、`load_enterprise_secrets(os.environ)`によるsecrets読取を実装した。
- `git_commit`は`git rev-parse HEAD`で自動解決し、失敗時は`--git-commit`を明示要求するエラーで終了するようにした。
- `tests/test_acquire.py`に7件(単一/複数chunk、再download skip、破損検知、sources_root/symlink検証)、`tests/test_cli.py`に`acquire --help`テストを追加した。
- format-check、ruff lint、mypy strict、標準スイート224件、`git diff --check`が成功した。
- 実credentialsで`wikiepwing acquire`コマンド全体を実行し(project=aawiki、namespace=0、`--config`で一時TOMLへ差し替え)、実際に認証→metadata解決→chunk download→verify→`source.lock.json`書込までend-to-endで成功することを確認した。生成された`source.lock.json`は`DATA_CONTRACTS.md`契約通りの構造で、SHA-256は以前の手動疎通確認と一致した。

**判断・注意点**

- disk空き容量事前確認はdoctorコマンド側の対象として残した。
- ローカル既存source登録(コピー無しのpredownloaded file利用)はTASK-D008の対象とした。
- 実データ検証に使った一時スクリプトはリポジトリ外のスクラッチパッドに置き、コミットしていない。credentialsは一切ログ・文書へ出力していない。
