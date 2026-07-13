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
