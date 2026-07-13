# TESTING.md

## 1. 目的

この文書は、Wikipedia EPWING Builder v2が「生成できた」だけではなく、内容・検索・文字・画像・再現性まで検証できるようにするテスト戦略を定義します。

テストの優先順位:

1. データ損失を検知する
2. ステージ境界を検証する
3. 失敗が再現できる
4. 小規模fixtureで高速に回る
5. フルビルド前に性能劣化を検知する
6. ビューア依存挙動を手動チェックへ分離する

---

## 2. テスト層

### 2.1 Unit

対象:

- config merge
- title normalization
- URL parsing
- Unicode classification
- DOM node conversion
- table span normalization
- search term generation
- cache key
- manifest validation

条件:

- networkなし
- filesystemはtmp_path
- 1テスト原則1責務
- deterministic

### 2.2 Snapshot/Golden

対象:

- HTML -> Article model
- Article -> RenderedEntry
- table/infobox layout
- diagnostics
- source/report JSON

canonical JSONをgoldenにします。binary EPWING全体をgoldenにしません。

### 2.3 Integration

対象:

- tar stream -> raw.sqlite3
- raw.sqlite3 -> model.sqlite3
- model -> rendered.sqlite3
- rendered -> FreePWING source
- toolchain invocation
- package/verify

### 2.4 End-to-end

対象:

- 3記事手作り
- 10記事NDJSON
- 100記事fixture
- 10,000記事sample

### 2.5 Compatibility

対象:

- Boookends 2023固定query
- article feature comparison
- EPWING viewer matrix

### 2.6 Security

対象:

- malicious HTML
- XXE
- path traversal
- SVG script/external refs
- decompression bomb
- huge image dimensions
- shell injection title
- token logging

### 2.7 Performance

対象:

- records/sec
- peak RSS
- DB size/article
- cache hit ratio
- per-article slowest percentile
- index term growth

---

## 3. Pytest marker

```text
unit
integration
end_to_end
toolchain
network
slow
compatibility
security
performance
manual
```

標準CI相当:

```bash
pytest -m "not network and not slow and not manual"
```

Docker toolchain:

```bash
pytest -m toolchain
```

明示的ネットワーク:

```bash
pytest -m network --run-network
```

---

## 4. Fixture階層

```text
tests/fixtures/
├── enterprise/
│   ├── 10-articles.ndjson
│   ├── duplicate-revisions.ndjson
│   ├── malformed.ndjson
│   └── missing-fields.ndjson
├── html/
│   ├── basic-article.html
│   ├── headings.html
│   ├── lists.html
│   ├── links.html
│   ├── table-simple.html
│   ├── table-wide.html
│   ├── table-spans.html
│   ├── infobox-person.html
│   ├── infobox-software.html
│   ├── references.html
│   ├── math.html
│   ├── images.html
│   ├── unicode.html
│   └── malicious.html
├── images/
│   ├── valid.png
│   ├── valid.jpg
│   ├── safe.svg
│   ├── script.svg
│   ├── external-ref.svg
│   ├── fake-png.txt
│   └── huge-dimensions.png.fixture
├── xml/
│   └── fallback-small.xml.bz2
└── epwing/
    └── handcrafted-source/
```

実Wikipedia記事をfixtureに含める場合:

- 取得元URL
- page ID
- revision ID
- license
- 取得日
- fixture生成方法

を`fixtures/METADATA.json`へ記録します。

---

## 5. ゴールデン記事セット

### 5.1 構造別

- ordinary prose article
- table-heavy
- infobox-heavy
- math-heavy
- image-heavy
- reference-heavy
- disambiguation
- list article
- short stub
- very long article
- rare Unicode
- nested list
- code/preformatted

### 5.2 日本語実用記事候補

- 日本
- 東京都
- 姫路市
- Emacs
- Linux
- 源氏物語
- 微分積分学
- 量子力学
- 第二次世界大戦
- 曖昧さ回避記事

記事本文の具体的文言は更新されるため、live contentを直接期待値にしません。固定revision fixtureを使います。

---

## 6. Source acquisition tests

### 必須ケース

1. valid metadata
2. 401
3. 403
4. 429 + Retry-After
5. 500 -> bounded retry
6. timeout
7. Range supported resume
8. Range unsupported restart
9. size mismatch
10. partial file
11. final atomic rename
12. disk insufficient
13. token redaction
14. `latest` resolution
15. local registration

### 成功判定

- incomplete downloadでsource lockを作らない
- `.partial`がfinal扱いされない
- lock内file hashとactual一致
- auth headerがexception/logへ含まれない

---

## 7. Ingest tests

### Schema field cases

- required present
- optional absent
- unknown extra field
- wrong type
- empty HTML
- empty Wikitext
- empty redirects/categories/licenses

extra fieldは将来互換のため原則許容し、利用しないfield名をdebug count可能にします。required type不正はrejectします。

### Duplicate matrix

| Existing | New | Expected |
|---|---|---|
| rev 10 hash A | rev 11 hash B | rev 11採用 |
| rev 11 hash A | rev 10 hash B | rev 11維持 |
| rev 11 hash A | rev 11 hash A | duplicate ignore |
| rev 11 hash A | rev 11 hash B | fatal conflict |

### DB checks

- integrity_check `ok`
- foreign_key_check empty
- page_id unique
- redirect target exists
- compressed BLOB roundtrip
- rejected count equals diagnostics

---

## 8. HTML normalization tests

### Node mapping table

| HTML | Model |
|---|---|
| `h2..h6` | HeadingBlock |
| `p` | ParagraphBlock |
| `strong/b` | StrongInline |
| `em/i` | EmphasisInline |
| `a` internal | InternalLinkInline |
| `a` external | ExternalLinkInline |
| `ul/ol` | ListBlock |
| `dl` | DefinitionListBlock |
| `pre` | PreformattedBlock |
| `blockquote` | QuoteBlock |
| `table.infobox` | InfoboxBlock |
| other meaningful table | TableBlock |
| `figure/img` | MediaReference/ImageBlock |
| math node | MathInline/MathBlock |
| unknown block | UnsupportedBlock + diagnostic |

### Invariants

- visible text order is stable
- script/style text does not leak
- hidden editing UI removed
- whitespace does not join words accidentally
- link label preserved
- unknown meaningful text preserved
- model validation passes

### Malformed HTML

- unclosed tags
- nested anchors
- invalid table
- invalid UTF-8 replacement at source parser boundary
- huge nesting

parser recovery behaviorをgolden化します。

---

## 9. Link tests

- `/wiki/Emacs`
- absolute same-project URL
- percent-encoded Japanese title
- fragment only
- title + fragment
- red link class
- missing page
- external HTTPS
- `mailto:`（既定では除外/テキスト化）
- unsafe scheme `javascript:` reject
- title containing `%2F`

### Metrics

fixture内の意図的missing以外はresolve率100%。全件ではresolve率をreportし、低下をregression thresholdにします。

---

## 10. Table tests

### Logical preservation

simple tableで、caption/header/cell visible textがすべてmodelへ存在すること。

### Span

rowspan/colspanをlogical gridへ展開する場合は、元セルと展開セルを区別できるmetadataを持つか、render ruleをテストします。

### Complexity

classifier入力と期待:

- 3列 x 5行 -> simple
- 12列 x 20行 -> wide
- nested table -> complex
- 10,000行 -> oversized

閾値はconfigにし、classifier unit testを持ちます。

### Renderer

- simple: header and rows
- wide: record-oriented
- complex: readable fallback
- oversized: split/truncate diagnostic

---

## 11. Infobox tests

fixture types:

- person
- geographic location
- software
- organization
- scientific entity

checks:

- label/value pairing
- empty rows removed
- style rows removed
- nested links preserved
- main image ref retained
- field count limit
- duplicate title removed
- lead text not swallowed

---

## 12. Search tests

### Headword categories

- title
- normalized title
- redirect
- alias
- reading variant
- category
- keyword
- cross component

### Properties

- same input -> same term order
- no empty key
- key length budget
- target page exists
- collision recorded
- priority deterministic

### Fixed query test

各profileについてquery -> expected target setを定義します。順位がbackend依存の場合は上位N内包含で判定します。

---

## 13. Unicode/Gaiji tests

### Character classes

- standard ASCII
- kana
- common kanji
- JIS outside candidate
- CJK extension
- combining sequence
- variation selector
- emoji
- mathematical symbol
- private use
- control char

### Invariants

- silent dropなし
- substitutionはmappingに存在
- gaiji registry unique
- same sequence same code
- bitmap hash stable
- fallback includes code point
- usage count correct

### Visual manual set

HTML reportへgaiji contact sheetを出し、ビューアで目視します。

---

## 14. Image security tests

### URL

- allowed upload.wikimedia.org
- HTTP reject/upgrade policy
- unexpected host
- redirect to unexpected host
- too many redirects
- URL credentials
- path traversal irrelevant to cache path

### Content

- valid PNG/JPEG
- MIME mismatch
- truncated image
- pixel bomb
- SVG script
- SVG external image/font
- SVG entity
- animated image policy

### Process

- timeout
- converter nonzero
- output missing
- output too large
- cache corruption

---

## 15. Math tests

- TeX only
- MathML only
- both
- inline
- block
- invalid TeX
- huge formula
- dangerous command attempt
- duplicate formula cache

rendererはnetworkなし、timeout、resource limit付き。

---

## 16. EPWING toolchain tests

### Smoke entries

- Japanese title
- ASCII title
- alias
- redirect
- internal link
- image
- narrow gaiji
- wide gaiji
- long article

### Verify operations

- catalog opens
- expected subbook
- entry search
- internal target exists
- graphic referenced file exists
- gaiji file exists
- ebzip artifact readable

### Negative

- missing catalog
- corrupted honmon
- invalid index
- missing graphic
- broken internal target

---

## 17. End-to-end fixture gates

### Gate 1: 3 articles

- toolchain only
- no Wikipedia parser dependency

### Gate 2: 10 articles

- source -> ingest -> model
- no EPWING requirement optional

### Gate 3: 100 articles Mini

- full pipeline
- title/redirect/links

### Gate 4: 100 articles Lite

- tables/infobox/math/images/gaiji

### Gate 5: 10,000 articles Lite

- performance/resource/diagnostics

各Gateに`reports/gates/gate-N.json`を生成します。

---

## 18. Resume tests

stageごとにfailure injection pointを用意します。

例:

```text
WIKIEPWING_FAIL_AFTER_RECORDS=50
WIKIEPWING_FAIL_STAGE=normalize
```

本番コードに隠し挙動を入れる場合はtest-only configで明示します。

検証:

- incomplete manifest
- temporary output残存
- completed prior stage再利用
- failed stage再実行
- downstream invalidated
- lock cleanup

---

## 19. Compatibility tests

詳細thresholdは`COMPATIBILITY.md`。

### Automated

- fixed query result overlap
- fixed article presence
- headword count ratio
- redirect count ratio
- internal link sample success
- image/table/gaiji feature availability

### Manual viewer matrix

| Viewer | Platform | Mini | Lite | Full | Search | Link | Image | Gaiji |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| EBWin | Windows | | | | | | | |
| EBPocket | iOS/Android | | | | | | | |
| Lookup | Emacs | | | | | | | |
| Additional | | | | | | | | |

manual resultは日付、viewer version、OSを記録します。

---

## 20. Performance baseline

### 100記事

主に機能検証。厳しい性能thresholdなし。

### 10,000記事

記録必須:

- ingest records/sec
- normalize records/sec
- render records/sec
- peak RSS
- raw/model/rendered DB bytes/article
- diagnostic/article
- image cache hit
- total stage time

### Regression rule

前回baselineより:

- throughput 30%以上低下
- memory 50%以上増加
- DB bytes/article 50%以上増加

した場合は理由を説明し、意図的変更でなければ失敗扱い。

---

## 21. Full build validation

### Completeness

```text
eligible articles
accepted raw articles
normalized articles
rendered entries
EPWING entries
```

各段階の差分がdiagnostic reasonへ対応すること。

### Random sampling

固定seedでpage IDから100〜1000記事抽出し:

- title
- non-empty body
- internal links
- encoding
- searchability

を検査します。

### Largest/slowest

- largest HTML
- largest model
- largest rendered entry
- slowest normalize
- most diagnostics

の上位をreportします。

---

## 22. Test command contract

Make targets:

```bash
make format
make format-check
make lint
make typecheck
make test-unit
make test-integration
make test-toolchain
make test-e2e
make test-security
make test
make check
```

`make check`はnetwork/slow/manualを除外します。

---

## 23. テスト失敗時の規則

- 期待値を実装へ合わせて安易に更新しない
- failure messageを消さない
- flaky testをskipしない
- network testを通常testへ混ぜない
- platform差は条件分岐で隠さずdocumentする
- full buildだけの失敗は最小fixtureへ縮小する

---

## 24. Release test checklist

- [ ] clean clone
- [ ] clean Docker build
- [ ] toolchain smoke
- [ ] unit/integration/security
- [ ] 100 Mini
- [ ] 100 Lite
- [ ] 10,000 Lite
- [ ] full Mini
- [ ] full Lite
- [ ] full Full candidate
- [ ] source/model/EPWING verify
- [ ] reference compare
- [ ] same-host reproducibility
- [ ] viewer matrix
- [ ] license report
