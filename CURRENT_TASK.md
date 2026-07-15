# CURRENT_TASK.md

## Task ID

TASK-O004

## 目的

`ARCHITECTURE.md` 15.4のダウンロード安全性要件のうち、ネットワーク層に関わる部分(HTTPSのみ・host allowlist・redirect回数制限・timeout・content-length上限)を実装する。TASK-O001-O003で選択された`MediaReference.source_url`を実際に取得するsecure downloaderを`src/wikiepwing/media/`(gaiji同様の独立パッケージ)配下に新設する。「実デコード後pixel上限」「MIMEとmagic byte検証」「SVG sanitize」はバイト列を実際にデコードする必要があるためTASK-O005-O006の対象とし、本タスクでは扱わない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O004(依存: A004)を読んだ
- [x] `ARCHITECTURE.md` 15.4(ダウンロード安全性の全項目)を再確認した
- [x] `A004`(構造化ログ、secret redaction)を確認した
- [x] 既存の`source/downloader.py`(Snapshot chunk用: HTTPS強制、redirectをmanualに1回だけ追いhopごとにAuthorizationを転送しない、`urllib.request`ベース)のパターンを参考にした。ただしこちらは同一APIへの決め打ちのredirectを1回だけ扱う設計であるのに対し、O004は任意の(allowlistされた)外部ホストへの複数回redirectを制限付きで追う必要があるため、別モジュールとして実装する

## 変更予定ファイル

- `src/wikiepwing/media/__init__.py`(新規)
- `src/wikiepwing/media/downloader.py`(新規: `MediaDownloadError`, `MediaDownloadResult`, `SecureMediaDownloader`)
- `tests/test_media_downloader.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_downloader.py
make check
git diff --check
```

## 完了条件

- [x] `https://`以外のURL(`http://`等)は取得前に拒否する
- [x] ホストが`allowed_hosts`に含まれない場合は取得前に拒否する
- [x] redirectは`max_redirects`回まで追い、各hopでHTTPS/host allowlistを再検証する。超過時はエラー
- [x] `Content-Length`ヘッダが`max_content_length_bytes`を超える場合は本文を読まずに拒否する
- [x] ヘッダが嘘をついている場合に備え、実際に読み取ったバイト数が上限を超えたら読み取りを中断してエラーにする(defense in depth)
- [x] timeoutが呼び出しに反映される
- [x] `make check`が成功する

## 非対象

- MIME/magic byte検証・実デコード後pixel上限(TASK-O005)
- SVG sanitize(TASK-O006)
- raster変換・content-addressed cache・dedup(TASK-O007-O009)

## 実施結果

- `src/wikiepwing/media/`(新規パッケージ)に`downloader.py`を実装した。`SecureMediaDownloader.download(url)`は各redirect hopでHTTPS/host allowlistを再検証しながら`max_redirects`回まで追い、`Content-Length`ヘッダによる事前拒否と実読み取りバイト数による事後拒否(defense in depth)の両方でcontent-length上限を守る。ネットワーク層は`MediaTransport` Protocolで抽象化し、テストは`urllib`を使わないfake transportで行う(既定実装は`urllib.request`ベース、`source/downloader.py`のno-redirect openerパターンを踏襲)。
- `tests/test_media_downloader.py`(新規16件)で、HTTPS強制・host allowlist・redirect追跡と各hopでの再検証・redirect超過・Location欠落・想定外status・content-length上限(header/実読み取り両方)・responseが常にcloseされること・コンストラクタのバリデーションを確認した。
- `make check`(format-check/lint/mypy/pytest 1136件)と`git diff --check`が成功した。
- MIME/magic byte検証・実デコード後pixel上限・SVG sanitizeは対象外(TASK-O005/O006)。
