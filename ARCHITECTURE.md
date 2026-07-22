# ARCHITECTURE.md

## 1. 文書の目的

この文書は、Wikipedia EPWING Builder v2の構造、境界、データ契約、実行モデル、失敗処理、再現性、セキュリティを定義します。

実装詳細がこの文書と矛盾する場合、実装を正当化するのではなく、次のどちらかを行います。

1. 実装を設計へ合わせる
2. 意図的な設計変更として`DECISIONS.md`へADRを追加し、この文書を更新する

---

## 2. プロジェクト定義

### 2.1 目的

2026年時点の日本語Wikipediaを、個人利用を主眼とした高機能EPWING/JIS X 4081互換辞書へ変換します。

目標機能:

- 記事本文
- 見出し語検索
- リダイレクト・別名検索
- 前方・後方・複合検索の実用的な索引
- 記事内見出し
- 内部リンク
- 表
- Infobox
- 数式
- 代表画像
- カテゴリ・メタデータ
- 外字フォールバック
- Mini / Lite / Fullプロファイル
- ebzip圧縮
- 再現可能なDockerビルド
- 中断・再開
- 検証レポート
- Boookends 2023版との機能比較

### 2.2 Boookendsとの関係

Boookends 2023年版は、次の用途だけに使用します。

- サブブック構造の観察
- 検索機能の観察
- 記事レイアウトの比較
- 画像・表・外字の扱いの比較
- Mini / Lite / Fullの差分把握
- ゴールデン記事の比較基準

目標は機能的互換性です。次は目標外です。

- バイナリ一致
- 未公開生成スクリプトの復元
- ブランド・名称・ロゴの流用
- 2023年版ファイルの改変配布
- 作者固有の実装を推測して模倣すること

### 2.3 成功状態

プロジェクトが成功した状態は次です。

1. 固定した入力Snapshotから、再実行可能なDockerビルドで辞書を生成できる
2. Mini / Lite / Fullの3成果物を生成できる
3. 主要記事が読みやすく、内部リンク・見出し語・redirect検索が機能する
4. 変換失敗や欠落が機械可読なレポートへ出る
5. 代表的なEPWINGビューア2種類以上とEmacs Lookup系で確認できる
6. 同一入力・設定・コードから論理内容ハッシュが一致する
7. 参照版との差が説明可能である

---

## 3. 最上位設計原則

### 3.1 ネットワーク取得と変換を分離する

`source acquire`だけがネットワークへ接続します。取得完了後、変換パイプラインはオフラインで動作します。

理由:

- 再現性
- API障害やtoken期限からの分離
- リトライ範囲の限定
- 同一入力によるデバッグ
- 途中からの再開

### 3.2 レンダリング済みHTMLを標準入力とする

標準入力はWikimedia Enterprise通常Snapshotの`article_body.html`です。

理由:

- MediaWiki本体がテンプレート展開した結果を利用できる
- 複雑なLua/Template展開を自前実装しなくてよい
- 表、Infobox、脚注、数式、内部リンクをDOMとして扱える
- Wikitextの時代差によるパーサー破損を減らせる

ただし標準SnapshotのHTML項目はoptionalであるため、欠落時の診断とWikitextフォールバックを持ちます。

### 3.3 Structured Contentsに依存しない

2026年7月時点のStructured Contents Snapshotは日本語Wikipediaを対象としていません。したがって、テーブルやInfoboxの抽出をStructured Contentsへ依存させません。

将来jawikiが対応しても、追加adapterとして扱い、既存HTML経路を壊しません。

### 3.4 中間モデルを正本とする

HTMLから直接FreePWING記法へ変換しません。

```text
Source snapshot
  -> RawArticle
  -> NormalizedArticle
  -> RenderedEntry
  -> EpwingBookModel
  -> FreePWING input
  -> EPWING files
```

各矢印は独立したステージです。

### 3.5 機能不足は劣化表示し、データ損失を記録する

未対応DOMを見つけた場合:

1. 可能な限りテキストを抽出
2. `UnsupportedBlock`または`UnsupportedInline`へ保存
3. diagnosticを記録
4. 記事全体の生成は継続

記事全体を落とすのは、構造破損や出力制約により安全に処理できない場合だけです。

### 3.6 巨大処理を不変ステージへ分割する

ステージ完了成果物は原則として再書き換えません。次のステージが別ファイル・別DBを生成します。

利点:

- 再開
- 差分比較
- 破損範囲の限定
- キャッシュ判定
- 弱い実装エージェントでも責務を理解しやすい

---

## 4. 外部事実と制約

### 4.1 Wikimedia Enterprise通常Snapshot

通常Snapshotは、プロジェクト・namespace単位のtar.gzで、NDJSONを含みます。記事項目には次が含まれ得ます。

- `identifier`: page ID
- `name`: 記事名
- `url`
- `namespace.identifier`
- `version.identifier`: revision ID
- `date_modified`
- `article_body.html`
- `article_body.wikitext`
- `redirects`
- `categories`
- `templates`
- `license`
- `image`: 主画像

Snapshotには少量の重複・削除済み記事が混入する可能性があるため、同一page IDでは最大の`version.identifier`を採用し、削除・visibility情報を扱います。

### 4.2 Wikimedia公式ダンプ

補助入力として次を利用できます。

- `pages-articles-multistream.xml.bz2`
- `pages-articles-multistream-index.txt.bz2`
- `redirect.sql.gz`
- `page.sql.gz`
- `page_props.sql.gz`
- `categorylinks.sql.gz`
- checksums

必須ではありませんが、次の用途で有効です。

- Snapshot欠落検証
- redirectの比較
- 記事数比較
- Wikitextフォールバック
- Snapshot APIを使えないときのMini生成

### 4.3 EPWING/FreePWING

EPWING固有の制約は、推測でコードへ埋め込まず、toolchain probeで確認します。

確認対象:

- 対応検索種別
- 文字コード・外字
- 一記事あたりの実用上限
- 画像形式・サイズ
- サブブック数
- index key長
- 内部参照
- `ebzip`対象ファイル

probe結果は`toolchain-capabilities.json`として固定します。

---

## 5. システム全体像

```text
┌─────────────────────────────────────────────────────────────┐
│ CLI / Orchestrator                                          │
│ doctor, acquire, inspect, ingest, normalize, render, build  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────┐
│ Source Acquisition            │
│ Enterprise / XML / Reference  │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│ Immutable Source Bundle       │
│ tar.gz, checksums, lock file  │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│ Raw Ingest                    │
│ dedup, validate, compress     │
│ raw.sqlite3                   │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│ HTML Normalization            │
│ DOM cleanup, semantic blocks  │
│ model.sqlite3                 │
└───────┬───────────────┬───────┘
        │               │
        ▼               ▼
┌───────────────┐  ┌───────────────────┐
│ Media Pipeline│  │ Search Pipeline   │
│ images/math   │  │ titles/aliases    │
└───────┬───────┘  └─────────┬─────────┘
        └────────────┬────────┘
                     ▼
┌───────────────────────────────┐
│ Rendered Entry Store          │
│ rendered.sqlite3              │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│ EPWING Backend Adapter        │
│ FreePWING source generation   │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│ Package / Verify / Compare    │
│ ebzip, zip, reports, hashes   │
└───────────────────────────────┘
```

---

## 6. リポジトリ構造

```text
wikipedia-epwing-v2/
├── AGENTS.md
├── ARCHITECTURE.md
├── PLAN.md
├── TASKS.md
├── TESTING.md
├── COMPATIBILITY.md
├── CONFIG_REFERENCE.md
├── DECISIONS.md
├── CURRENT_TASK.md
├── LOG.md
├── MEMORY.md
├── README.md
├── Makefile
├── compose.yaml
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── config/
│   ├── default.toml
│   ├── projects/
│   │   ├── jawiki.toml
│   │   └── enwiki.toml
│   ├── profiles/
│   │   ├── mini.toml
│   │   ├── lite.toml
│   │   └── full.toml
│   ├── dom-rules/
│   │   ├── common.toml
│   │   └── jawiki.toml
│   └── gaiji/
│       └── substitutions.toml
├── docker/
│   ├── app.Dockerfile
│   ├── toolchain.Dockerfile
│   ├── entrypoint.sh
│   └── toolchain/
│       ├── build-freepwing.sh
│       ├── build-eb.sh
│       └── probe.sh
├── migrations/
│   ├── raw/
│   ├── model/
│   ├── rendered/
│   └── reference/
├── patches/
│   ├── freepwing/
│   └── eb/
├── scripts/
│   ├── build-fixture.sh
│   ├── build-full.sh
│   ├── inspect-artifact.sh
│   └── compare-viewers.md
├── src/wikiepwing/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── errors.py
│   ├── logging.py
│   ├── hashing.py
│   ├── paths.py
│   ├── pipeline/
│   │   ├── orchestrator.py
│   │   ├── stage.py
│   │   ├── manifest.py
│   │   ├── locks.py
│   │   └── progress.py
│   ├── source/
│   │   ├── base.py
│   │   ├── enterprise.py
│   │   ├── xml_dump.py
│   │   ├── downloader.py
│   │   ├── auth.py
│   │   ├── checksums.py
│   │   └── lockfile.py
│   ├── ingest/
│   │   ├── ndjson.py
│   │   ├── xml.py
│   │   ├── deduplicate.py
│   │   ├── validate.py
│   │   └── repository.py
│   ├── model/
│   │   ├── article.py
│   │   ├── blocks.py
│   │   ├── inline.py
│   │   ├── media.py
│   │   ├── diagnostics.py
│   │   └── codec.py
│   ├── normalize/
│   │   ├── html_parser.py
│   │   ├── dom_cleanup.py
│   │   ├── sections.py
│   │   ├── paragraphs.py
│   │   ├── links.py
│   │   ├── lists.py
│   │   ├── tables.py
│   │   ├── infoboxes.py
│   │   ├── references.py
│   │   ├── math.py
│   │   ├── media.py
│   │   └── unknown.py
│   ├── text/
│   │   ├── unicode.py
│   │   ├── japanese.py
│   │   ├── whitespace.py
│   │   ├── title.py
│   │   └── gaiji.py
│   ├── search/
│   │   ├── headword.py
│   │   ├── redirect.py
│   │   ├── alias.py
│   │   ├── keyword.py
│   │   ├── cross.py
│   │   └── collisions.py
│   ├── media/
│   │   ├── downloader.py
│   │   ├── policy.py
│   │   ├── metadata.py
│   │   ├── image_convert.py
│   │   ├── svg_sanitize.py
│   │   ├── math_render.py
│   │   └── cache.py
│   ├── render/
│   │   ├── entry.py
│   │   ├── layout.py
│   │   ├── table.py
│   │   ├── infobox.py
│   │   ├── reference.py
│   │   └── profile.py
│   ├── epwing/
│   │   ├── backend.py
│   │   ├── freepwing.py
│   │   ├── source_writer.py
│   │   ├── catalog.py
│   │   ├── indexes.py
│   │   ├── graphics.py
│   │   ├── gaiji.py
│   │   ├── package.py
│   │   └── probe.py
│   ├── reference/
│   │   ├── scanner.py
│   │   ├── searches.py
│   │   ├── entries.py
│   │   ├── report.py
│   │   └── repository.py
│   ├── verify/
│   │   ├── source.py
│   │   ├── database.py
│   │   ├── model.py
│   │   ├── epwing.py
│   │   ├── content.py
│   │   ├── compatibility.py
│   │   └── report.py
│   └── report/
│       ├── json_report.py
│       ├── html_report.py
│       └── metrics.py
├── tests/
│   ├── fixtures/
│   │   ├── enterprise/
│   │   ├── html/
│   │   ├── xml/
│   │   ├── images/
│   │   └── epwing/
│   ├── golden/
│   ├── unit/
│   ├── integration/
│   ├── end_to_end/
│   ├── toolchain/
│   └── compatibility/
├── output/
├── reports/
└── work/
```

`output/`, `reports/`, `work/`の巨大内容はGit管理しません。

---

## 7. 実行コンポーネント

### 7.1 CLI

単一エントリポイントは`wikiepwing`です。

```text
wikiepwing doctor
wikiepwing source acquire
wikiepwing source inspect
wikiepwing reference scan
wikiepwing ingest
wikiepwing normalize
wikiepwing media
wikiepwing render
wikiepwing epwing generate
wikiepwing verify
wikiepwing compare-reference
wikiepwing package
wikiepwing build
wikiepwing report
wikiepwing clean
```

CLIは薄く保ちます。ビジネスロジックをClick/Typer command関数へ直接書きません。

### 7.2 Orchestrator

Orchestratorは次だけを担当します。

- stage依存関係解決
- manifest比較
- lock取得
- stage開始・終了記録
- 失敗状態記録
- resume判定
- progress集約

記事変換ロジックを持ちません。

### 7.3 Stageインターフェース

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass(frozen=True)
class StageResult:
    output_paths: tuple[Path, ...]
    record_count: int
    diagnostic_count: int
    logical_hash: str

class Stage(Protocol):
    name: str
    version: int

    def input_fingerprints(self, ctx: "BuildContext") -> dict[str, str]: ...
    def run(self, ctx: "BuildContext") -> StageResult: ...
    def verify(self, ctx: "BuildContext", result: StageResult) -> None: ...
```

Stage versionを変更すると、そのstage以降のキャッシュを無効にします。

---

## 8. データディレクトリと成果物

コンテナ内部の標準パス:

```text
/data/sources       取得済みSnapshot・dump
/data/reference     手元Boookends 2023版（read-only）
/data/work          stage DB・一時成果物
/data/cache         画像・数式・HTTP content cache
/data/output        最終EPWING・ZIP
/data/reports       JSON/HTML/CSVレポート
/data/logs          build log
/app                ソースコード（read-only運用可能）
```

runごとの構造:

```text
/data/work/runs/<run_id>/
├── run.json
├── manifests/
│   ├── 00-doctor.json
│   ├── 10-ingest.json
│   ├── 20-normalize.json
│   └── ...
├── raw.sqlite3
├── model.sqlite3
├── rendered.sqlite3
├── index.sqlite3
├── epwing-source/
└── tmp/
```

run_id例:

```text
jawiki-20260701-full-git-a1b2c3d4
```

run_idへ秘密情報やホスト絶対パスを含めません。

---

## 9. Source Bundle設計

### 9.1 Snapshot availability gate

実装は`jawiki_namespace_0`の存在やHTML fieldの充足を固定知識として決め打ちしません。acquire時にmetadata endpointを問い合わせ、次を検証します。

- requested project/namespaceのSnapshotが列挙される
- download endpointが利用可能
-取得したsample recordに期待schemaがある
- HTML充足率が設定thresholdを満たす

標準Snapshotが取得不能、またはHTML充足率が不足する場合:

- `enterprise` modeは明示的に失敗する
- `xml` fallbackでMini相当を作ることは許可する
- Lite/Fullを自動的に品質低下させて生成しない
- alternative rendererを追加するまではblock状態をreportする

### 9.2 Source lock

`source.lock.json`は取得入力を固定します。

```json
{
  "schema_version": 1,
  "project": "jawiki",
  "namespace": 0,
  "provider": "wikimedia-enterprise-snapshot",
  "snapshot_identifier": "jawiki_namespace_0",
  "snapshot_version": "2026-07-01",
  "date_modified": "2026-07-01T12:00:00Z",
  "downloaded_at": "2026-07-13T10:00:00Z",
  "files": [
    {
      "path": "jawiki_namespace_0.tar.gz",
      "size_bytes": 0,
      "sha256": "..."
    }
  ],
  "supplements": [],
  "tool": {
    "name": "wikiepwing",
    "version": "0.1.0"
  }
}
```

`latest`という文字列を後続manifestへ残しません。必ず具体的versionへ解決します。

### 9.3 認証

認証環境変数例:

```text
WME_USERNAME
WME_PASSWORD
WME_ACCESS_TOKEN
WME_REFRESH_TOKEN
```

優先順位:

1. 有効なaccess token
2. refresh tokenからaccess token更新
3. username/passwordでlogin

tokenは永続DBへ保存しません。必要ならroot以外のみ読める一時ファイルを使い、終了時に削除します。

### 9.4 ダウンロード

要件:

- HEADでサイズ取得
- HTTP Range対応時にresume
- `.partial`へ保存
- 完了後にSHA-256計算
- atomic rename
- 5xxとtimeoutだけbounded retry
- 401/403は即時失敗
- disk free事前確認
- `source.lock.json`は全ファイル検証後にのみ作成

---

## 10. Raw ingest設計

### 10.1 入力

- tar.gz内NDJSON
- 1行1記事
- UTF-8

### 10.2 ストリーミング

tar.gzを全展開せず、tar streamからNDJSONを読みます。

禁止:

- 全NDJSONをメモリへ読む
- 全展開してから読むことを必須にする
- 記事ごとの小ファイルを数百万個作る

### 10.3 RawArticle

```python
@dataclass(frozen=True)
class RawArticle:
    page_id: int
    revision_id: int
    title: str
    namespace_id: int
    url: str
    date_modified: datetime
    html: str | None
    wikitext: str | None
    redirects: tuple[str, ...]
    categories: tuple[str, ...]
    templates: tuple[str, ...]
    licenses: tuple["LicenseRecord", ...]
    main_image: "SourceImage" | None
    source_sequence: int
    source_hash: str
```

### 10.4 raw.sqlite3

主要テーブル:

```sql
CREATE TABLE articles (
    page_id INTEGER PRIMARY KEY,
    revision_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    namespace_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    date_modified TEXT NOT NULL,
    html_zstd BLOB,
    wikitext_zstd BLOB,
    source_hash TEXT NOT NULL,
    source_sequence INTEGER NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    ingest_status TEXT NOT NULL,
    CHECK (ingest_status IN ('accepted', 'rejected', 'deleted'))
) STRICT;

CREATE TABLE redirects (
    target_page_id INTEGER NOT NULL,
    redirect_title TEXT NOT NULL,
    normalized_redirect_title TEXT NOT NULL,
    PRIMARY KEY (target_page_id, normalized_redirect_title),
    FOREIGN KEY (target_page_id) REFERENCES articles(page_id)
) WITHOUT ROWID;

CREATE TABLE categories (...);
CREATE TABLE templates (...);
CREATE TABLE licenses (...);
CREATE TABLE diagnostics (...);
CREATE TABLE metadata (...);
```

詳細schemaは実装時にmigrationへ分割します。

### 10.5 重複処理

同じpage_idが複数回現れた場合:

1. revision IDが大きい方を採用
2. 同じrevision IDでhashが同じなら重複として無視
3. 同じrevision IDでhashが異なるならfatal diagnostic候補
4. 古いレコードは`ingest_duplicates`へ記録

titleだけで同一記事判定しません。

### 10.6 入力上限

設定可能な安全上限:

- title: 4 KiB
- URL: 16 KiB
- HTML: 64 MiB/article
- Wikitext: 64 MiB/article
- redirects: 100,000/article
- categories: 100,000/article
- JSON nesting: parserが対応する現実的上限

上限超過は記事を落とすのではなく、field単位truncate可能性を設計判断として記録します。HTML本体上限超過は原則rejectし、ページIDとサイズを報告します。

---

## 11. Normalized Article Model

### 11.1 Article

```python
@dataclass(frozen=True)
class Article:
    page_id: int
    revision_id: int
    title: str
    normalized_title: str
    source_url: str
    source_date_modified: datetime
    abstract: str | None
    blocks: tuple["Block", ...]
    aliases: tuple["Alias", ...]
    categories: tuple[str, ...]
    media: tuple["MediaReference", ...]
    diagnostics: tuple["Diagnostic", ...]
    source_license_ids: tuple[str, ...]
```

### 11.2 Block union

```text
ParagraphBlock
HeadingBlock
UnorderedListBlock
OrderedListBlock
DefinitionListBlock
QuoteBlock
PreformattedBlock
CodeBlock
TableBlock
InfoboxBlock
ImageBlock
MathBlock
ReferencesBlock
NoticeBlock
HorizontalRuleBlock
UnsupportedBlock
```

### 11.3 Inline union

```text
TextInline
StrongInline
EmphasisInline
InternalLinkInline
ExternalLinkInline
CodeInline
MathInline
LineBreakInline
RubyInline
UnsupportedInline
```

### 11.4 Link

```python
@dataclass(frozen=True)
class InternalLinkInline:
    label: tuple["Inline", ...]
    target_title: str
    target_normalized_title: str
    target_fragment: str | None
    target_page_id: int | None
    resolution: Literal["resolved", "missing", "externalized"]
```

HTMLのURLをそのままEPWING内部リンクへしません。title/page IDへ解決します。

### 11.5 Table

```python
@dataclass(frozen=True)
class TableCell:
    blocks: tuple["Block", ...]
    row_span: int
    col_span: int
    is_header: bool

@dataclass(frozen=True)
class TableBlock:
    caption: tuple["Inline", ...]
    rows: tuple[tuple[TableCell, ...], ...]
    source_class_names: tuple[str, ...]
    complexity: Literal["simple", "wide", "complex", "unsupported"]
```

### 11.6 Infobox

InfoboxはTableBlockの単なる別名にしません。記事冒頭メタデータとして別型にします。

```python
@dataclass(frozen=True)
class InfoboxField:
    name: str
    value: tuple["Block", ...]

@dataclass(frozen=True)
class InfoboxBlock:
    title: str | None
    fields: tuple[InfoboxField, ...]
    images: tuple[str, ...]
```

### 11.7 Diagnostic

```python
@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Literal["info", "warning", "error", "fatal"]
    stage: str
    page_id: int | None
    title: str | None
    message: str
    source_path: str | None
    source_excerpt: str | None
    details: dict[str, object]
```

Diagnostic codeは安定APIです。

例:

```text
SRC_HTML_MISSING
SRC_DUPLICATE_PAGE
DOM_UNKNOWN_ELEMENT
DOM_INVALID_NESTING
TABLE_TOO_COMPLEX
INFOBOX_EMPTY
LINK_TARGET_MISSING
MEDIA_DOWNLOAD_FAILED
MEDIA_LICENSE_MISSING
MATH_RENDER_FAILED
CHAR_GAIJI_REQUIRED
CHAR_UNREPRESENTABLE
EPWING_ENTRY_TOO_LARGE
EPWING_INDEX_COLLISION
VERIFY_CATALOG_INVALID
```

---

## 12. HTML Normalization

### 12.1 DOM parser

- `lxml`を第一候補とする
- recovery modeの使用有無を設定化する
- script/style/template-like executable contentを除去する
- 外部entity解決を無効にする
- ネットワークアクセスを無効にする

### 12.2 Pass構成

Normalizationは順序付きpassとして実装します。

```text
N00 Parse HTML
N10 Root selection
N20 Remove unsafe/non-content nodes
N30 Normalize headings and section anchors
N40 Classify infobox/navbox/metadata tables
N50 Convert paragraphs and inline markup
N60 Convert lists
N70 Convert tables
N80 Convert images and figures
N90 Convert math
N100 Convert references
N110 Resolve internal links
N120 Normalize whitespace
N130 Validate model
N140 Store diagnostics
```

各passは入力ArticleDraftを受け、新ArticleDraftとdiagnosticsを返します。global mutable stateを避けます。

### 12.3 除外候補

デフォルトで本文から除外するもの:

- 編集リンク
- navigation UI
- coordinates UIの重複表示
- hidden metadata
- maintenance category表示
- navbox
- authority control box
- portal box
- language switch UI
- script/style

ただし情報を落とす可能性があるclassは、fixtureで確認してからruleへ追加します。

### 12.4 DOM rule設定

CSS selector/class名の判断をコードへ散在させません。

```toml
[[remove]]
selector = ".mw-editsection"
reason = "editing UI"

[[classify]]
selector = "table.infobox"
as = "infobox"

[[classify]]
selector = "table.wikitable"
as = "table"
```

rule versionをmanifestへ記録します。

### 12.5 内部リンク解決

対象URL例:

```text
/wiki/Emacs
https://ja.wikipedia.org/wiki/Emacs
./Emacs
```

処理:

1. URL decode
2. fragment分離
3. project base URL確認
4. namespace/title抽出
5. normalized title生成
6. raw DBでpage ID解決
7. redirect targetの扱いを設定に従う
8. EPWING entry IDへ後段で変換

外部サイトへのリンクはplain URLまたは注記として残します。

---

## 13. Text normalizationと日本語索引

### 13.1 保存用本文

本文は過剰にNFKCしません。視覚・意味が変わる可能性があるためです。

処理対象:

- Unicode validation
- CRLF -> LF
- 不正制御文字除去
- ゼロ幅文字の方針適用
- 連続空白の文脈別整理

### 13.2 索引用文字列

索引用に別の正規化関数を持ちます。

```text
Unicode NFKC
全角/半角統一
ASCII case fold
空白統一
一部句読点除去
長音・中点のvariant生成（設定）
ひらがな/カタカナvariant生成（設定）
```

本文文字列と索引keyを混同しません。

### 13.3 alias source

alias候補:

- redirects
- 記事title
- normalized title variant
- HTML中のdisplay title
- lead sentenceのbold alias（後期実装）
- Wikidata alias（将来optional）

aliasにはsourceとconfidenceを付けます。

---

## 14. Search architecture

### 14.1 SearchTerm

```python
@dataclass(frozen=True)
class SearchTerm:
    key: str
    normalized_key: str
    target_page_id: int
    kind: Literal[
        "title",
        "redirect",
        "alias",
        "reading",
        "category",
        "keyword",
        "cross_component",
    ]
    priority: int
    source: str
```

### 14.2 衝突規則

同一keyが複数記事へ向く場合:

- silently overwriteしない
- 全候補を保持可能なbackend方式を優先
- backend制約で単一候補しか持てない場合はpriorityと安定sortで選ぶ
- dropped候補をレポートする

### 14.3 プロファイル別索引

Mini:

- title
- normalized title
- redirect

Lite:

- Mini
- alias
- kana variant
- limited cross component

Full:

- Lite
- category
- heading keyword
- infobox selected values
- lead bold term
- configured keyword

括弧付き同名記事（例: `日本 (アルバム)`）は、完全一致検索でも候補を失わないよう
括弧前の基底タイトル（`日本`）を追加のaliasとして持つ。検索キーと表示見出しは
分離し、表示見出しには導入部で記事名に明示的に付随する仮名読みだけを
`記事名〔よみ〕`形式で付与する。読みを推測してはならず、抽出できない場合は元の
記事名をそのまま表示する。

本文全単語の全文索引は初期スコープ外です。

---

## 15. Media architecture

### 15.1 画像は別stage

Normalizationは画像参照だけを保存します。ダウンロードしません。

### 15.2 MediaReference

```python
@dataclass(frozen=True)
class MediaReference:
    media_id: str
    source_url: str
    source_name: str | None
    alt_text: str | None
    caption: str | None
    role: Literal["main", "infobox", "lead", "body", "icon", "unknown"]
    source_width: int | None
    source_height: int | None
```

### 15.3 選択ポリシー

優先順位:

1. 主画像
2. Infobox主要画像
3. lead figure
4. 本文先頭の意味ある画像
5. 追加本文画像

除外候補:

- 16pxなどのicon
- edit/help icon
- decorative flag（設定で許可可能）
- tracking image
- blank placeholder
- duplicate hash

### 15.4 ダウンロード安全性

- HTTPSのみ
- host allowlist
- redirect回数制限
- timeout
- content-length上限
- 実デコード後pixel上限
- MIMEとmagic byte検証
- SVG sanitize
- external entity禁止
- ImageMagick delegate制限

### 15.5 Cache key

```text
sha256(canonical_url + requested_width + converter_version + policy_version)
```

source responseのETag/Last-Modifiedもmetadataへ保存します。

### 15.6 画像ライセンス

通常Snapshotのtop-level licenseは記事本文ライセンスであり、個別画像ライセンスの完全な代替と見なしません。

画像再配布を行うFull成果物では、Commons/Fileページ由来の帰属情報取得を別機能として実装します。

ライセンス情報がない画像は:

- personal buildではwarning付きで含めるか設定可能
- distributable buildでは除外するのが既定

### 15.7 数式

HTML中のMathML/TeX/画像表現から、次の優先順位で扱います。

1. テキスト代替を保存
2. TeX sourceがあればcache keyに使用
3. SVG/PNGへ安全にレンダリング
4. EPWING graphicへ変換
5. 失敗時はTeX/plain textへフォールバック

---

## 16. RenderedEntry

```python
@dataclass(frozen=True)
class RenderedEntry:
    entry_id: str
    page_id: int
    title: str
    heading: str | None
    headwords: tuple[str, ...]
    body: tuple["RenderNode", ...]
    internal_targets: tuple[str, ...]
    graphics: tuple[str, ...]
    estimated_size: int
    diagnostics: tuple[Diagnostic, ...]
```

`title`は記事の正規タイトルおよび検索語生成の入力、`heading`はEPWING検索結果に
表示する見出しである。両者を混同せず、読み表示の追加で検索キーを変化させない。

### 16.1 entry ID

安定ID:

```text
p<page_id>
```

例: `p12345`

タイトル変更で内部参照が壊れないよう、page IDを基準にします。

### 16.2 標準レイアウト

```text
[記事タイトル]
別名: ...
更新: YYYY-MM-DD

[Infoboxの主要項目]

導入文

1. 見出し
本文

1.1 小見出し
本文

関連項目
カテゴリ
出典情報
```

EPWING画面幅を考え、深い入れ子や広い表を縦方向へ変換します。

### 16.3 Table render policy

simple:

- 小列数
- 短いcell
- grid-like text

wide:

- 1行をrecordとして縦表示

complex:

- row/sectionごとのkey-value化
- captionと注記を保持

oversized:

- configured row上限で分割
- 続きentryを作るか、要約とtruncate diagnostic

### 16.4 Entry size budget

backend実測上限より安全率を引いた値をbudgetにします。

超過時の順序:

1. nav/referenceの重複を削る
2. oversized tableを分割
3. reference一覧を別entryへ分割
4. 本文sectionを続きentryへ分割
5. それでも不可ならfatal article diagnostic

本文を無言で切り捨てません。

---

## 17. EPWING backend

### 17.1 interface

```python
class EpwingBackend(Protocol):
    def capabilities(self) -> "BackendCapabilities": ...
    def begin_book(self, metadata: "BookMetadata") -> None: ...
    def add_entry(self, entry: RenderedEntry) -> None: ...
    def add_search_term(self, term: SearchTerm) -> None: ...
    def add_graphic(self, graphic: "GraphicAsset") -> None: ...
    def finalize(self) -> "BackendOutput": ...
```

### 17.2 FreePWING adapter

責務:

- FreePWING source file生成
- catalog/subbook設定
- index登録
- graphic/gaiji登録
- command invocation
- stderr解析
- output構造確認
- EUC-JP変換後かつFreePWING `BaseWord`正規化後の同一検索キー・同一本文位置の重複除去

非責務:

- HTML解析
- table flatten
- alias抽出
- 日本語正規化
- image download

### 17.3 toolchain image

`toolchain.Dockerfile`で固定:

- Debian base digest
- build dependencies
- FreePWING source URL + SHA-256
- EB Library source URL + SHA-256
- patch files
- fonts package version
- image conversion tools

build後にcompilerや不要パッケージを削減してもよいですが、最初はデバッグ可能性を優先します。

### 17.4 toolchain probe

probeは手作り辞書で次を測定します。

- Japanese text
- internal link
- exact/prefix/suffix/keyword系検索
- bitmap graphic
- narrow/wide gaiji
- large entry
- long key
- many aliases
- ebzip roundtrip

probe結果が期待と違う場合、Wikipedia pipelineへ進みません。

---

## 18. 外字設計

### 18.1 文字分類

出力時に各Unicode scalarを分類します。

```text
A. backend標準文字として表現可能
B. 設定済み文字列へ置換可能
C. gaiji bitmapとして表現
D. 表現不能
```

### 18.2 置換例

- non-breaking space -> normal space
- typographic quote -> configured quote
- variation selector -> base glyph + diagnostic
- combining sequence -> NFC化後に再判定

意味を変える置換は行いません。

### 18.3 Gaiji registry

```text
Unicode sequence
normalized sequence
width class
font source identifier
bitmap hash
assigned gaiji code
usage count
```

同じ文字列は一度だけbitmap生成します。

### 18.4 フォント

Docker内の再配布可能なNoto CJK系などを利用し、package versionとhashをmanifestへ記録します。フォントファイルそのものを成果物へ含めません。成果物には生成済みbitmapだけを含めます。

### 18.5 失敗

D分類の文字はreplacement markerだけで済ませず、コードポイント表記をfallbackにします。

例:

```text
[U+1Fxxx]
```

件数・頻出順・記事例をreportへ出します。

---

## 19. Reference dictionary inspector

### 19.1 目的

Boookends 2023版を読み取り、比較可能な観測値を作ります。

### 19.2 読み取りのみ

参照辞書はread-only mountします。変更・再圧縮・再配布しません。

### 19.3 収集項目

- CATALOGS
- subbook名
- directory/file構造
- file size
- EB/EPWING識別情報
- 利用可能検索種別
- title検索件数
- fixed query結果
- fixed articleの本文抜粋hash
- internal link数
- image/gaiji利用数（取得可能範囲）

### 19.4 reference.sqlite3

```text
reference_books
reference_subbooks
reference_queries
reference_query_results
reference_entries
reference_metrics
reference_diagnostics
```

### 19.5 比較不能項目

ビューアやtoolchainから機械取得できない項目は、manual checklistへ回します。無理にHTML scrapingやOCRで取得しません。

---

## 20. Pipeline stages

ステージ番号は予約範囲を持たせます。

```text
00 doctor
05 toolchain-probe
10 reference-scan
20 source-acquire
25 source-verify
30 ingest
35 raw-verify
40 normalize
45 model-verify
50 search-extract
55 media-plan
60 media-fetch
65 media-convert
70 render
75 gaiji-build
80 epwing-source
85 epwing-generate
90 package
95 verify
97 compare-reference
99 report
```

### 20.1 Manifest

各stage manifest:

```json
{
  "schema_version": 1,
  "stage": "normalize",
  "stage_version": 3,
  "status": "complete",
  "run_id": "...",
  "started_at": "...",
  "completed_at": "...",
  "inputs": {
    "raw_db": "sha256:...",
    "config": "sha256:...",
    "dom_rules": "sha256:..."
  },
  "outputs": [
    {
      "path": "model.sqlite3",
      "size_bytes": 0,
      "sha256": "...",
      "logical_hash": "..."
    }
  ],
  "metrics": {
    "records_read": 0,
    "records_written": 0,
    "warnings": 0,
    "errors": 0
  }
}
```

### 20.2 Cache validity

再利用条件:

- stage version一致
- input fingerprint一致
- relevant config hash一致
- output file存在
- output hash一致
- manifest status complete
- verify成功

mtimeだけで再利用判定しません。

### 20.3 Lock

同じrun/stageを複数processが同時実行しないようlock fileを使います。古いlockはPIDと開始時刻を確認して明示的に解除します。

---

## 21. Profiles

### 21.1 Mini

目的: 小容量・高速・本文検索中心。

- 本文
- 見出し
- title
- redirect
- internal links
- Infoboxは主要textのみ
- tableはplain vertical text
- imageなし
- mathはtext fallback
- referencesは短縮

### 21.2 Lite

目的: 日常利用で高い実用性。

- Miniすべて
- 代表画像最大2〜3
- Infobox整形
- table整形
- math bitmap
- alias/kana variant
- limited cross/keyword
- references保持

### 21.3 Full

目的: 参照版に近い高機能。

- Liteすべて
- 画像最大8程度（設定）
- category index
- heading/infobox keyword
- richer alias
- attribution appendix
- large table分割
- detailed references
- compatibility metrics

同じコードパスを使い、profile設定で差を作ります。`if profile == "full"`を各所へ散在させません。

---

## 22. Resource management

### 22.1 CPU

- parse/normalizeはprocess pool候補
- SQLite writerは単一writer + queueを基本
- image convertは別worker limit
- worker数はconfigとcgroup CPUから決定

### 22.2 Memory

- 記事単位処理
- batch size上限
- BLOBをまとめて保持しない
- queue depth制限
- memory telemetry optional

### 22.3 Disk

事前見積もり:

```text
source tar.gz
raw.sqlite3
model.sqlite3
rendered.sqlite3
image cache
math cache
epwing source
epwing uncompressed
ebzip output
zip output
safety margin
```

4TB環境では容量よりもDocker Desktop disk image上限とI/O配置が問題になるため、named volumeとDocker storage設定をdoctorで確認します。

### 22.4 Progress

表示項目:

- stage
- records done/total
- records/sec
- bytes read/written
- warning/error count
- current shard/page ID
- elapsed

時間予測は不安定なので必須にしません。

---

## 23. Error model

### 23.1 Fatal

- checksum mismatch
- source lock不整合
- DB corruption
- schema mismatch
- disk full
- FreePWING executable missing
- catalog generation failure
- output verify failure
- 同revision IDで異なる内容hash

### 23.2 Recoverable article error

- unsupported element
- malformed table
- missing link target
- missing image
- failed formula
- unrepresentable char

### 23.3 Retryable

- HTTP timeout
- 5xx
- transient DNS
- rate limit with retry-after

### 23.4 Exit codes

```text
0 success
2 configuration error
3 source acquisition error
4 source validation error
5 stage data error
6 toolchain error
7 verification failure
8 compatibility threshold failure
9 interrupted
```

---

## 24. Verification architecture

### 24.1 Source verification

- lock fileとactual file hash
- tar member数
- NDJSON parse sample
- project/namespace一致
- expected schema fields

### 24.2 DB verification

- `PRAGMA integrity_check`
- foreign key check
- expected table count
- duplicate constraints
- status totals

### 24.3 Model verification

- block nesting
- unique page IDs
- title not empty
- internal links validity
- diagnostics consistency
- serialization roundtrip

### 24.4 EPWING verification

- directory structure
- catalog parse
- subbook count/name
- entry count
- search query sample
- internal reference sample
- graphic sample
- gaiji sample
- ebzip decompression/read test

### 24.5 Compatibility verification

`COMPATIBILITY.md`のthresholdを評価します。

---

## 25. Reporting

### 25.1 JSON report

機械処理用の正本です。

必須:

- source lock
- git commit
- image digest
- config hashes
- toolchain versions
- stage durations
- counts
- diagnostics histogram
- top unsupported DOM/classes
- char/gaiji statistics
- image statistics
- search term statistics
- output hashes
- verification results
- compatibility results

### 25.2 HTML report

人間向け:

- summary
- failure highlights
- representative article links
- charts/table
- profile sizes
- reference comparison

### 25.3 CSV

大量diagnosticの詳細をCSV/JSONLで出せるようにします。

---

## 26. Reproducibility

### 26.1 完全一致と論理一致

ZIP timestampやfilesystem orderingによりbinary hashが変わる可能性があります。

二種類を記録します。

- physical SHA-256: 実ファイルhash
- logical hash: entry/index/graphicのcanonical stream hash

### 26.2 決定論

- DB queryにはORDER BY
- worker処理結果をpage ID順にmerge
- archive timestamp固定
- locale固定
- timezone UTC
- random seed固定またはrandom不使用
- dependency lock
- Docker base digest固定

### 26.3 Provenance

生成物に`BUILD-INFO.json`を添付します。

---

## 27. Security architecture

### 27.1 Container user

- non-root
- `/data`必要箇所だけwrite
- `/app` read-only可能
- no-new-privileges
- capability drop

### 27.2 HTML/XML

- XXE禁止
- entity expansion禁止
- script実行禁止
- network fetch禁止
- parser limits

### 27.3 Images

- allowlist domain
- sanitize SVG
- decompression bomb detection
- pixel limit
- process timeout
- temp directory isolation

### 27.4 subprocess

- shell=False
- fixed executable path
- untrusted valueをoption名に使わない
- timeout
- stdout/stderr capture limit

---

## 28. Licensing and attribution

### 28.1 本文

- 記事ライセンス配列を保存
- source URL、記事名、revision ID、更新日を保持
- BUILD-INFOにWikimedia projectとsnapshot版を記載

### 28.2 画像

- source file page
- author
- license identifier
- license URL
- source URL
- transformed size/hash

取得できない項目はmissingとして記録し、distributable profileの方針に従います。

### 28.3 コード

プログラムライセンスは別途選択し、Wikipedia contentのライセンスを上書きしません。

---

## 29. 拡張点

将来追加可能:

- enwiki
- Simple English
- Wiktionary
- Structured Contents adapter
- Wikidata aliases
- incremental update
- alternative backend
- ZIM/SQLite/HTML出力
- separate full-text index

初期実装では拡張点のinterfaceだけを用意し、未使用機能を先回り実装しません。

---

## 30. 主要ADR要約

- ADR-001: HTML Snapshotを標準入力
- ADR-002: Structured Contents非依存
- ADR-003: 中間semantic model
- ADR-004: stage別SQLite
- ADR-005: ORM不使用
- ADR-006: FreePWING隔離
- ADR-007: UTF-8内部表現と出力時gaiji
- ADR-008: named volume
- ADR-009: reference compatibilityは測定
- ADR-010: profilesは設定駆動

詳細は`DECISIONS.md`。

---

## 31. 実装開始前の設計ゲート

次を確認するまでコードを大量に書きません。

- [ ] toolchainの取得元とhash方針が決まった
- [ ] Wikimedia Enterprise account/tokenの注入方法が決まった
- [ ] 手元Boookends 2023版をread-only mountできる
- [ ] Mini/Lite/Fullの定義に合意している
- [ ] raw/model/rendered DBの責務が理解されている
- [ ] fixtureの入手・匿名化・コミット方針が決まった
- [ ] 公開配布か個人利用かをconfigで分ける方針がある

---

## 32. 参考仕様URL

実装時に最新版を再確認します。

- Wikimedia Enterprise docs: `https://enterprise.wikimedia.com/docs/`
- Snapshot API: `https://enterprise.wikimedia.com/docs/snapshot/`
- Data dictionary: `https://enterprise.wikimedia.com/docs/data-dictionary/`
- Wikimedia dumps: `https://dumps.wikimedia.org/jawiki/latest/`
- Wikimedia dump documentation: `https://meta.wikimedia.org/wiki/Data_dumps`
- FreePWING archive/index: `https://openlab.ring.gr.jp/edict/fpw/`
