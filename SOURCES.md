# SOURCES.md

## 1. 調査基準日

2026-07-13

この文書は外部仕様に関する判断根拠を記録します。実装時にはURLの現行内容を再確認してください。

---

## 2. Wikimedia Enterprise

### Documentation portal

`https://enterprise.wikimedia.com/docs/`

確認事項:

- free account作成
- JWT認証
- project一覧
- standard Snapshot
- On-demand

### Snapshot API

`https://enterprise.wikimedia.com/docs/snapshot/`

2026-07-13確認内容:

- project/namespace全体をtar.gzで取得
- archive内はNDJSON
- free accountでは月次Snapshotが案内されている
- Snapshot/Structured Contentsには少量の重複・削除済み記事が含まれる場合がある
- 重複時は最大`version.identifier`を採用する案内

### Data dictionary

`https://enterprise.wikimedia.com/docs/data-dictionary/`

通常記事responseで利用する候補:

- `name`
- `identifier`
- `version.identifier`
- `url`
- `namespace.identifier`
- `article_body.html`
- `article_body.wikitext`
- `license`
- `redirects`
- `categories`
- `templates`
- `image`

`article_body.html`はcontent extraction向けのparsed HTMLとして説明されている。

### Structured Contents limitation

Snapshot documentationの2026-07-13表示では、Structured Contents Betaの対応プロジェクト一覧にjawikiが含まれていない。

したがって、v2はStructured Contentsをjawiki必須経路にしない。

### 実アカウントでの疎通確認(2026-07-14)

ユーザーが作成したWikimedia Enterpriseアカウントのusername/passwordで、TASK-D002/D003の実装コードから実APIへ疎通確認した。credentials自体はログや本文書へ一切記録していない。

**認証API(`https://auth.enterprise.wikimedia.com/v1`)**

- `POST /login` に`{"username": "...", "password": "..."}`(JSON body)で、成功時`access_token`を含むJSONを返す。実測でtoken長は1067文字。
- credentials不足時は`{"status":400,"message":"missing username or password"}`、不正credentials時は`{"status":401,"message":"Incorrect username or password."}`(いずれもcredentials自体は含まない)。
- `src/wikiepwing/source/auth.py`の`/login`エンドポイントとフィールド名(`username`/`password`/`access_token`)の仮定は実データと一致した。

**Snapshot metadata API(`https://api.enterprise.wikimedia.com/v2`)**

- `GET /snapshots` に`Authorization: Bearer <access_token>`で、全project×namespaceのSnapshot metadataをJSON配列で返す(2026-07-14実測で3,262件、応答約1.16 MB)。project/namespaceによるserver側絞り込みは無く、client側filterが必要。
- 各entryの実フィールド構成(`src/wikiepwing/source/enterprise.py`実装時の当初仮定と異なった点を含む):
  - `identifier`: 例 `"jawiki_namespace_0"`
  - `is_part_of.identifier`: project識別子(**`project`ではなく`is_part_of`**)
  - `namespace.identifier`: namespace番号
  - `in_language.identifier`: 言語コード(未使用、今後の参考として記録)
  - `version`: revision内容hash文字列(日付ではない)。例 `"35061ecbd3bc55c31cffd4b46838673d"`
  - `date_modified`: RFC3339、ナノ秒精度の小数点以下桁を持つ場合がある(例 `"2026-07-01T00:50:43.412259882Z"`)。Python 3.12の`datetime.fromisoformat`はマイクロ秒精度へ丸めて解析可能。
  - `size`: `{"value": <float>, "unit_text": <string>}`のオブジェクト(**単純なbyte数の整数ではない**)。近似値であり、正確なbyte数はダウンロード時に別途確認が必要。
  - `chunks`: 文字列配列。**jawiki namespace 0は2026-07-14時点で81個のchunk(`jawiki_namespace_0_chunk_0`〜`_80`)に分割**されている。単一tar.gzという当初の`ARCHITECTURE.md`例示は簡略化であり、実際のdownloaderはchunk単位の取得を前提に設計する必要がある(TASK-D005への申し送り)。
- jawiki namespace 0のSnapshotは実際に列挙され、`is_part_of.identifier == "jawiki"`かつ`namespace.identifier == 0`のentryが1件存在することを確認した(2026-07-14時点でサイズ約30,896 MB)。

**Chunk download API(`https://api.enterprise.wikimedia.com/v2/snapshots/{chunk_identifier}/download`、2026-07-14実測、TASK-D005着手前の疎通確認)**

- `GET .../{chunk_identifier}/download`(Bearer認証)はHTTP 307で署名付きS3 URL(`https://wme-eks-data-pr.s3.amazonaws.com/snapshots/{chunk_identifier}_group_1.tar.gz?X-Amz-...`)へredirectする。
- 署名は`X-Amz-Expires=60`(60秒)で失効する。大きなfileのdownloaderは途中で署名を再取得できる設計が必要。
- redirect先のS3 URLへ`Authorization`headerを転送すると`400 InvalidArgument: Only one auth mechanism allowed`になる。素朴なurllibの自動redirect追従はこのheaderを保持したまま転送するため使えず、redirectを手動処理し、S3への実request自体は素のGET(`Authorization`無し、必要なら`Range`のみ)で送る必要がある。
- **2026-07-14時点で、`aawiki_namespace_0_chunk_0`(約1 KB相当の最小規模)を含め、確認した全chunkでS3側が`404 NoSuchKey`を返した。** 署名検証自体は通っている(`AccessDenied`/`SignatureDoesNotMatch`ではない)ため、request形式の誤りではなく対象objectがbucketに実在しないことを示す。アカウントのプラン起因(metadata閲覧のみでSnapshot本体のdownload権限が無い等)の可能性がある。ユーザーがWikimedia Enterpriseのアカウントプランを確認中。TASK-D005再開時に本状況を再確認すること。

---

## 3. Wikimedia official dumps

### jawiki latest index

`https://dumps.wikimedia.org/jawiki/latest/`

2026-07-06付近の例として確認できるもの:

- `jawiki-latest-pages-articles.xml.bz2`
- `jawiki-latest-pages-articles-multistream.xml.bz2`
- multistream index
- redirect SQL
- page SQL
- checksums

通常XML dumpは補助・検証・fallback用。

### General dump documentation

`https://meta.wikimedia.org/wiki/Data_dumps`

`https://meta.wikimedia.org/wiki/Data_dumps/Dump_format`

---

## 4. FreePWING / EB

### FreePWING-related archive

`https://openlab.ring.gr.jp/edict/fpw/`

FreePWING/辞書変換ツールの歴史的配布元・索引として調査対象。

古いsource URLが消失する可能性があるため、実装時は:

- mirror確認
- source archive SHA-256固定
- project内patch管理
- Docker image build test

を行う。

---

## 5. 参照辞書

手元のBoookends 2023日本語Wikipedia EPWING版をread-onlyで使用する。

記録すべき情報:

- local pathはsource controlへ書かない
- directory fingerprint
- file hashes
- profile Full/Lite/Mini
- reference scan date
- viewer/tool versions

参照物の内容・ファイルをプロジェクト成果物へ複製しない。
