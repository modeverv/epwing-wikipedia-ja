# CURRENT_TASK.md

## Task ID

TASK-D002

## 目的

Wikimedia Enterprise認証クライアントを実装する。access token優先、refresh tokenでの更新、username/passwordでのloginという固定優先順位で1つの利用可能なaccess tokenを解決し、timeoutを守り、tokenをどこにも永続化しない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-D002を読んだ
- [x] `ARCHITECTURE.md` 9.3の認証優先順位とtoken非永続化方針を確認した
- [x] `ARCHITECTURE.md`のsourceパッケージ構成(`source/auth.py`)を確認した
- [x] `config/default.toml`の`source.enterprise.auth_base`/`request_timeout_seconds`を確認した
- [x] TASK-D001の`EnterpriseSecrets`を確認した

## 変更予定ファイル

- `src/wikiepwing/source/__init__.py`
- `src/wikiepwing/source/auth.py`
- `tests/test_auth.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_auth.py
make check
git diff --check
```

## 完了条件

- [x] `EnterpriseSecrets`から優先順位(access token → refresh token → username/password)で1つのaccess tokenを解決する
- [x] access tokenが与えられている場合はHTTP呼び出しを行わない
- [x] refresh/login呼び出しにtimeoutを強制し、非正のtimeoutを拒否する
- [x] HTTPレスポンスのbyte数を上限で制限し、不正JSON・`access_token`欠落を拒否する
- [x] 401/403は即座に失敗として扱う(リトライしない)
- [x] 認証情報がまったく無い場合は明確なエラーを送出する
- [x] token・password・username自体をファイルへ書かない、モジュールがファイルシステムへ触れない
- [x] `make check`が成功する

## 非対象

- Snapshot metadata取得(TASK-D003)
- 5xx/timeoutのbounded retry(acquireコマンド側、TASK-D007以降)
- 実ネットワークに対するWikimedia Enterprise API呼び出しの手動確認

## 実施結果

- `src/wikiepwing/source/auth.py`に`EnterpriseAuthClient`(優先順位解決)、`AuthTransport` Protocol、`HttpAuthTransport`(bounded urllib実装)、`ResolvedAccessToken`を実装した。
- access tokenが存在する場合はtransportを一切呼ばない。refresh tokenはlogin(username/password)より優先する。
- HTTPレスポンスは64 KiB上限で読み、上限超過・不正JSON・`access_token`欠落・空文字tokenを`AuthError`として拒否した。
- 401/403はリトライなしで即座に`AuthError`、5xx/timeout/URLErrorも同様に即座に失敗させた(bounded retryはacquireコマンド側の対象)。
- `auth_base`はhttps以外を拒否し、非正のtimeoutは`EnterpriseAuthClient`・`HttpAuthTransport`双方で拒否した。
- モジュールはファイルシステムへ一切触れず、tokenは戻り値のdataclassとしてのみ保持する。
- `tests/test_auth.py`に17件のオフラインテスト(優先順位、空token拒否、HTTPS必須、401/5xx/timeout/oversized/malformed JSON/access_token欠落)を追加した。
- format-check、ruff lint、mypy strict、標準スイート130件、`git diff --check`が成功した。

**判断・注意点**

- 実際のWikimedia Enterprise auth APIのendpoint path(`/login`、`/token-refresh`)はSOURCES.mdに一次資料の確認記録がなく、`config/default.toml`の`auth_base`と一般的なWME API形状からの仮定である。実クレデンシャルでの疎通確認はTASK-D003以降、または`reports/reference-manual-checklist.md`と同様に人間による実施が必要。
- 5xx/timeoutのbounded retryはこのクライアントの責務外とし、呼び出し側(将来のacquireコマンド)に委ねた。
