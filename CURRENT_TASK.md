# CURRENT_TASK.md

## Task ID

TASK-D003

## 目的

Wikimedia Enterprise Snapshot metadataクライアントを実装する。project/namespaceでSnapshotを列挙・絞り込みし、`latest`のような曖昧な文字列を残さず1つの具体的versionへ解決する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D003を読んだ
- [x] `ARCHITECTURE.md` 9.1(Snapshot availability gate)と9.2(source lock契約)を確認した
- [x] `DATA_CONTRACTS.md` 2節のsource lock契約(`metadata_response_sha256`、`snapshot_version`が具体的である必要)を確認した
- [x] `config/default.toml`の`source.namespace`/`source.snapshot`/`source.enterprise.api_base`を確認した
- [x] TASK-D002の`EnterpriseAuthClient`/`ResolvedAccessToken`を確認した

## 変更予定ファイル

- `src/wikiepwing/source/enterprise.py`
- `tests/test_enterprise_metadata.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_enterprise_metadata.py
make check
git diff --check
```

## 完了条件

- [x] project/namespaceでSnapshot一覧を絞り込む
- [x] `requested_version == "latest"`は列挙結果の中から最新の具体的versionへ解決し、`"latest"`という文字列を戻り値へ残さない
- [x] 明示的versionが要求された場合は一致するものだけを返し、無ければ明確に失敗する
- [x] メタデータ応答のbyte数を上限で制限する
- [x] メタデータ応答のSHA-256を計算し`metadata_response_sha256`として返す
- [x] 401/403は即座に失敗として扱う(リトライしない)
- [x] 該当project/namespaceのSnapshotが1件も無い場合は明確に失敗する(Mini/Liteを自動で品質低下させない)
- [x] `make check`が成功する

## 非対象

- 実際のダウンロード(TASK-D005)
- source.lock.json全体の生成(TASK-D004、TASK-D007)
- 5xx/timeoutのbounded retry(acquireコマンド側)
- 実アカウントでの疎通確認(ユーザーがアカウント作成中のため保留)

## 実施結果

- `src/wikiepwing/source/enterprise.py`に`SnapshotMetadataClient`、`SnapshotMetadataTransport` Protocol、`HttpSnapshotMetadataTransport`(bounded urllib実装)、`SnapshotCandidate`/`ResolvedSnapshot`を実装した。
- project/namespaceで一致するSnapshotのみへ絞り込み、1件も無ければ明確に失敗する(Mini/Liteを自動で品質低下させない)。
- `requested_version == "latest"`は列挙結果から`(date_modified, version_identifier)`最大のものへ解決し、戻り値の`version_identifier`に`"latest"`という文字列を残さない。サーバ側が`version: "latest"`を返した場合も明示的に拒否する。
- 明示的versionを要求した場合は完全一致のみを返し、0件または重複は失敗させる。
- メタデータ応答は4 MiB上限で読み、上限超過・不正JSON・非配列・空配列・必須フィールド欠落・timezone欠落の`date_modified`を`SnapshotMetadataError`として拒否した。
- `metadata_response_sha256`として生レスポンスのSHA-256を返し、`DATA_CONTRACTS.md`のsource lock契約と整合させた。
- `HttpSnapshotMetadataTransport`はhttps以外のbase URLと空`access_token`を拒否し、401/403/5xx/timeout/URLErrorを即座に失敗させた(リトライなし)。
- `tests/test_enterprise_metadata.py`に23件のオフラインテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート153件、`git diff --check`が成功した。

**判断・注意点**

- Snapshot metadata一覧APIの実endpoint(`GET {api_base}/snapshots`)とレスポンス形状(`identifier`/`project.identifier`/`namespace.identifier`/`version`/`date_modified`/`size`)は、`ARCHITECTURE.md`が言及する`namespace.identifier`/`version.identifier`のnestedオブジェクト形式から類推した仮定であり、一次資料での確認記録が`SOURCES.md`にない。実アカウントでの疎通確認まで暫定とする。
- ユーザーはWikimedia Enterpriseアカウントを作成しusername/passwordを`.env`へ設定済みだが、本タスクは引き続きモック/テストダブルのみで実装し、実API呼び出しの疎通確認は行っていない。
- 5xx/timeoutのbounded retryはこのクライアントの責務外とし、将来のacquireコマンド(TASK-D007)に委ねた。
