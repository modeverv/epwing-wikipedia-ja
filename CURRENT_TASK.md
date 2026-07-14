# CURRENT_TASK.md

## Task ID

TASK-E005

## 目的

parseされた`RawArticle`に対し、field length・URL形式・namespace一致・HTML/wikitext sizeを検証し、記事単位で受理/拒否と構造化診断を返す安全性検証を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E005を読んだ(依存: E004完了済み)
- [x] `AGENTS.md` 2.6(記事単位の回復可能な失敗は構造化診断として保存、ステージ全体を壊す失敗のみ停止)を確認した
- [x] `CONFIG_REFERENCE.md` 8節・`config/default.toml`の`[ingest]`(`max_title_bytes`/`max_url_bytes`/`max_html_bytes`/`max_wikitext_bytes`)を確認した
- [x] `DATA_CONTRACTS.md`の`diagnostics`table列(code/severity/stage/page_id/title/message/details_json)を確認した
- [x] TASK-E004の`RawArticle`を確認した

## 変更予定ファイル

- `src/wikiepwing/ingest/validate.py`
- `tests/test_ingest_validate.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_ingest_validate.py
make check
git diff --check
```

## 完了条件

- [x] `ValidationLimits.from_config`が`config/default.toml`の`[ingest]`値を読み取れる
- [x] title/urlのbyte長超過、html/wikitextのbyte長超過、宣言namespaceと期待値の不一致、非https URLを検出し診断化する
- [x] 診断は`code`/`severity`/`message`/`details`を持ち、`DATA_CONTRACTS.md`の`diagnostics`table列へ素直に対応付けられる
- [x] error以上の診断が1件でもあれば`accepted=False`、無ければ`accepted=True`を返す
- [x] TASK-D010のtitle長すぎ/invalid URL edge caseが正しく拒否され、正常な10記事は全件受理されることを確認する
- [x] `make check`が成功する

## 非対象

- 重複解決(TASK-E006)
- DBへの実書込・diagnosticsテーブルへの永続化(TASK-E007)

## 実施結果

- `src/wikiepwing/ingest/validate.py`に`ValidationLimits`(`from_config`で`[ingest]`section読取)、`Diagnostic`、`ValidationResult`、`validate_article`を実装した。
- title/url/html/wikitextのbyte長超過(`REC_TITLE_TOO_LONG`/`REC_URL_TOO_LONG`/`REC_HTML_TOO_LARGE`/`REC_WIKITEXT_TOO_LARGE`)、非httpsまたは不正なURL(`REC_INVALID_URL`)、宣言namespaceと期待値の不一致(`REC_UNEXPECTED_NAMESPACE`)を検出し、`error`重大度の診断が1件でもあれば`accepted=False`とする。
- 診断は`code`/`severity`/`message`/`details`(dict)を持ち、`DATA_CONTRACTS.md`の`diagnostics`table列(code/severity/message/details_json + page_id等はdetails内)へ素直に対応付けられる形にした。
- TASK-D010のtitle長すぎ/invalid URL edge caseが正しく拒否され、正常な10記事は全件受理されることを確認した。large article edge caseはdefault設定(64 MiB上限)では受理され、tightな上限では拒否されることを確認した。
- **fixture修正**: TASK-D010で作成した`title_too_long` edge caseが実際には3549 bytesしかなく、`config/default.toml`の実際の既定`max_title_bytes=4096`を超えていなかったため、5250 bytesへ拡張し実際にdefault設定下で拒否されることを確認した。
- `tests/test_ingest_validate.py`に15件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート332件、`git diff --check`が成功した。

**判断・注意点**

- `config/default.toml`の`ingest.strict_required_fields`はE004(NDJSON record parser)の必須field強制と関連する設定だが、現時点ではどこにも配線されていない。必須field欠落時に記事単位skipへ倒す(diagnostic化)か、記事全体を即fatalにするかの選択はTASK-E007/E008で検討する。
