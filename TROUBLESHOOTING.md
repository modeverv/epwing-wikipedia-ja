# TROUBLESHOOTING.md

EPIC R(TASK-R001〜R009)・EPIC S(TASK-S001〜S005)で日本語Wikipedia全件(約150万記事)規模のビルドを実際に実行した際に遭遇した問題と、その診断・対処方法をまとめます。「1. 既に修正済みの問題」は現在のコードでは再発しません(参考・原因理解用)。「2. 運用上の注意点」はコード修正では解消できない、実行環境・外部サービス側の制約です。

---

## 1. 既に修正済みの問題(参考)

古いバージョンのコードや、フォークして独自変更を加えた場合の切り分けに使ってください。

### `ingest`が特定のchunkでUNIQUE制約違反(`redirects`/`categories`等)で失敗する

- **症状**: `sqlite3.IntegrityError: UNIQUE constraint failed: redirects.target_page_id, redirects.normalized_redirect_title`
- **原因**: 実データには、末尾空白や全角/半角差など、正規化後に同一キーへ衝突する重複したredirect/category/template/license名が存在する。
- **対処**: `src/wikiepwing/ingest/repository.py`の`_replace_children`が`_dedupe_by_key`で先勝ちdedupeするよう修正済み(TASK-R003)。

### `ingest`が特定のchunkでNDJSON行サイズ超過エラーになる

- **症状**: `wikiepwing.ingest.tar_reader.TarStreamError: NDJSON line exceeded 8388608 bytes`
- **原因**: `iter_ndjson_lines`が常に`tar_reader.DEFAULT_MAX_LINE_BYTES`(8MiB)を使っており、設定可能な`ingest.max_html_bytes`/`max_wikitext_bytes`(既定64MiB)以下の記事でも失敗していた。
- **対処**: `src/wikiepwing/ingest/orchestrate.py`の`_max_ndjson_line_bytes`が`max_html_bytes+max_wikitext_bytes+overhead`から動的に上限を計算するよう修正済み(TASK-R003)。

### `normalize`が特定の記事でCHECK制約違反(`media_references`)で失敗する

- **症状**: `sqlite3.IntegrityError: CHECK constraint failed: length(media_id) BETWEEN 1 AND 8192`
- **原因**: 実データのHTMLは、SVGプレースホルダー画像用に`<img src="data:image/svg+xml;base64,...">`(数KB〜十数KB)を使うことがあり、これがそのまま`media_id`/`source_url`として保存されようとしていた。
- **対処**: `src/wikiepwing/normalize/media_node.py`の`parse_image_node`が`data:` URIをスキップするよう修正済み(TASK-R004)。

### `verify`が有効な`entries.jsonl`をJSONパースエラーとして拒否する

- **症状**: `wikiepwing.render.verify.EntriesVerificationError: <path>:<line>: invalid JSON: Unterminated string...`
- **原因**: `_read_records`が`text.splitlines()`を使っており、JSON文字列内に現れる正当なUnicode改行文字(U+2029 PARAGRAPH SEPARATOR等、実データの本文に実在する)を行区切りと誤認識し、1つの正常なJSONLレコードを複数の不正な断片に分割していた。
- **対処**: `src/wikiepwing/render/verify.py`が`\n`のみで分割するよう修正済み(TASK-R005)。

### `image-fetch`が全件`https://`スキーム必須エラーで失敗する

- **症状**: 全リクエストが`media URL must use https://`で失敗する
- **原因**: 実データの`<img src>`の大多数はプロトコル相対URL(`//upload.wikimedia.org/...`)で、`https://`が省略されている。
- **対処**: `src/wikiepwing/media/downloader.py`の`_resolve_protocol_relative`がリクエスト直前に`https:`を補完するよう修正済み(TASK-R007)。

### `image-fetch`が全件HTTP 403で失敗する

- **症状**: 全リクエストが`unexpected HTTP status: 403`で失敗する
- **原因**: WikimediaのCDN(upload.wikimedia.org)はUser-Agentポリシー(https://meta.wikimedia.org/wiki/User-Agent_policy)を強制しており、Pythonの`urllib`既定のUser-Agent(`Python-urllib/3.x`)を拒否する。
- **対処**: `_UrllibTransport`がプロジェクトを識別する説明的なUser-Agentを送るよう修正済み(TASK-R007)。

### `image-fetch`が大量にHTTP 429で失敗する

- **症状**: `unexpected HTTP status: 429`が多数発生する
- **原因**: `image-fetch`は逐次リクエストで、クライアント側のペーシングが無いため、Wikimedia側のrate limitに頻繁に引っかかる。
- **対処**: `SecureMediaDownloader.download`が`Retry-After`ヘッダ(あれば優先)または指数バックオフで最大`max_rate_limit_retries`(既定5)回リトライするよう修正済み(TASK-R007)。それでも解消しない場合は下記「2.1 rate limit」を参照。

---

## 2. コード修正では解消できない運用上の注意点

### 2.1 `image-fetch`の速度とrate limit

`image-fetch`は逐次ダウンロード(並列化なし)です。jawiki全件では約250万件のユニーク画像URLがあり(TASK-R007実測)、1リクエストあたり約0.4秒とすると全件で4〜12日規模になります。リトライ・バックオフを実装済みですが(2.1参照の修正済み項目)、根本的な対策はスコープの縮小(検証目的なら`plan_media`の結果を間引いてサンプルのみ`fetch_media`/`convert_media`に渡す)か、時間を確保して実行することです。

### 2.2 Docker実行時のメモリ不足(OOM)

`generate`は全記事(jawiki全件で約150万件)をメモリに保持してから見出し語衝突をグローバルに解決するため、ネイティブホストでは30〜40GB規模のメモリを使用します。Docker Desktopの既定メモリ割り当て(macOSで約8GB)では、コンテナが**エラーメッセージを出さずに**無応答終了します(manifestが`status=running`のまま、`entries_written=0`で止まる)。

- **症状**: `generate`コンテナが数分で終了するが、ログが空でmanifestの`completed_at`が`null`のまま
- **対処**: Docker Desktopの設定(Settings → Resources → Memory)でメモリ割り当てを増やし(TASK-S005では約85GBに設定)、Docker Desktopを再起動してから再実行する。

### 2.3 ディスク容量

jawiki全件では、Snapshot(約29GB)・`raw.sqlite3`(約27GB)・`model.sqlite3`(約12GB)・`entries.jsonl`(プロファイルごとに約13GB)を合わせて、1回のビルドで100GB超を消費します。`wikiepwing disk-usage`で現在の使用量を確認し、`wikiepwing clean --keep-runs N`で古い`paths.work/runs`を整理できます(`paths.output`は対象外)。

### 2.4 認証情報

`WME_USERNAME`/`WME_PASSWORD`(または`WME_ACCESS_TOKEN`/`WME_REFRESH_TOKEN`)が環境変数に設定されていないと、`acquire`/`update`が`AuthError: no enterprise credentials available`で失敗します。`.env`ファイルは自動読み込みされないため、`set -a; source .env; set +a`のように明示的にシェルへ読み込んでください。

### 2.5 `verify`が`DUPLICATE_HEADWORD`を報告する

- **症状**: `verify`が`ok=false`で、同一見出し語が2つの異なる`page_id`に使われていると報告する
- **原因**: バグではなく、Wikimedia Enterprise Snapshot自体の特性です。記事の削除・再作成によって同一タイトルに新しい`page_id`が割り当てられ、Snapshotの取得期間内に新旧両方のpage_idの状態が含まれることがあります(TASK-R006で実データ150万件中5件を確認、いずれも`title`/`source_url`が完全一致するが`page_id`/`revision_id`/`source_sequence`が異なるペアだった)。
- **対処**: 実際のEPWINGビルド時の見出し語衝突解消は、既存のFreePWINGツールチェーン(`docker/toolchain/freepwing_build_entries.pl`)側の処理に委ねます。

### 2.6 `image-fetch`が一部URLで400/404を返す

- **症状**: 特定のCommons画像URLが`unexpected HTTP status: 400`または`404`を返す
- **原因**: バグではなく、レンダリング済みHTMLが古いサムネイルURL(パラメータやファイル名の形式が変わった、あるいはCommons側でファイルが削除・改名された)を参照している実データの特性です(`curl`で同じURLを直接叩いても同じ400/404が返ることを確認済み)。
- **対処**: `image-fetch`は1URLの失敗で全体を止めず、`FetchOutcome.ok=False`として記録し続行します。失敗率が極端に高い場合のみ、`--report`のJSONでエラー内訳(`unexpected HTTP status`のコード別集計)を確認してください。

### 2.7 ImageMagickが見つからない

- **症状**: `image-convert`関連のテストがskipされる、または`RasterConversionError`
- **原因**: ImageMagick(`magick`コマンド)が未インストール。
- **対処**: `brew install imagemagick`(macOS)等でインストールしてください。

---

## 3. 診断手順

1. `wikiepwing doctor`(または`--json`)で環境・パス・ツール導線を確認する。
2. 各ステージのmanifest(`paths.work/runs/<run-id>/manifests/*.json`)の`status`を確認する。`running`のまま止まっている場合はクラッシュ(OOM等)を疑う。
3. `wikiepwing verify-raw --raw-database <raw.sqlite3>`で取り込み後の整合性(integrity, foreign keys, counts, samples)を確認する。
4. `wikiepwing verify --entries <entries.jsonl>`で生成後の整合性(空tag/title、重複、未解決リンク)を確認する。
5. `image-fetch`の`--report`に書かれるJSONの`error`フィールドをコードで集計し、失敗理由の内訳(rate limit/host allowlist/古いURL等)を切り分ける。

詳細な設定・実行手順は[BUILD.md](BUILD.md)、設定ファイルの構成は[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)を参照してください。
