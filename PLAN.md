# PLAN.md

## 1. 実装計画の目的

この計画は、能力の弱い実装エージェントでも、巨大なWikipedia変換プロジェクトを小さな検証可能単位で完遂できるようにするものです。

重要な方針:

- 各Phaseは明確な入口条件と出口条件を持つ
- 出口条件を満たさず次へ進まない
- フルデータは最後まで使わない
- 失敗を成果として記録する
- 1つのPhase内でも`TASKS.md`の1タスクずつ進める
- 実装順序を勝手に入れ替えない

---

## 2. リリース目標

### v0.1 Toolchain Proof

- Docker起動
- FreePWING/EB toolchain固定
- 手作り3記事辞書
- ebzip圧縮
- 自動structure verify

### v0.2 Source and Model

- Enterprise Snapshot取得
- NDJSON ingest
- 10記事HTML normalization
- 中間モデルとdiagnostics

### v0.3 Mini Vertical Slice

- 100記事fixture
- title/redirect/internal link
- Mini EPWING生成
- 中断再開

### v0.4 Content Features

- table
- infobox
- references
- gaiji
- math fallback

### v0.5 Lite

- representative images
- math bitmap
- alias/kana search
- 10,000記事試験

### v0.8 Full Candidate

- Full indexes
- image attribution
- Boookends比較
- 全件trial

### v1.0 Stable Personal Builder

- Mini/Lite/Full全件生成
- reproducibility
- compatibility thresholds
- monthly rebuild workflow
- documentation complete

---

## 3. Phase共通の進め方

各Phaseで必ず次を行います。

1. `CURRENT_TASK.md`へ1タスクを設定
2. fixtureまたは失敗テストを追加
3. 最小実装
4. 局所テスト
5. 標準テスト
6. manifest/report確認
7. `LOG.md`更新
8. Phase gate確認

---

## 4. Phase 0 — リポジトリ基盤

### 目的

コードを安全・一貫して実行できる最小リポジトリを作ります。

### 作業

- Python 3.12 package作成
- `uv`導入
- `ruff`、type checker、pytest設定
- CLI skeleton
- config loader
- structured logging
- Makefile
- Docker app image
- non-root user
- `.env.example`
- Git ignore
- docs配置

### 必須CLI

```bash
wikiepwing --help
wikiepwing doctor
```

### doctor検査

- Python version
- OS/architecture
- locale
- timezone
- `/data` path書込
- free disk
- Docker environment marker
- external executablesの存在（この時点ではmissingでも明示）
- config parse

### テスト

- config default test
- invalid config test
- CLI help test
- doctor JSON output test
- non-root container test

### 出口条件

- [ ] `docker compose build`成功
- [ ] `make test`成功
- [ ] `make lint`成功
- [ ] `make typecheck`成功
- [ ] container UID 0ではない
- [ ] `doctor --json`がschemaに沿う

### 禁止

このPhaseでFreePWINGやWikipedia parsingを実装しません。

---

## 5. Phase 1 — EPWING toolchain proof

### 目的

最も古く不確実なFreePWING/EB部分を、Wikipedia処理より先に確定します。

### 作業

1. source archive取得URLとSHA-256固定
2. Debian base image digest固定
3. EB Library build
4. FreePWING build
5. `ebzip`確認
6. toolchain version出力
7. 3記事の手作り辞書source生成
8. internal link
9. 複数headword
10. 1画像
11. gaiji sample
12. package
13. machine verify

### 手作り記事

- Emacs
- Linux
- Wikipedia

機能:

- 相互内部リンク
- 日本語本文
- ASCII
- 標準外候補文字
- 小画像
- redirect相当headword

### Toolchain probe

probe項目:

- catalog
- subbook
- search types
- key length
- graphic format
- gaiji width
- entry size
- ebzip read

### 成果物

```text
reports/toolchain-capabilities.json
output/toolchain-smoke.epwing.zip
```

### 出口条件

- [ ] clean Docker buildでtoolchain生成
- [ ] 3記事を機械検索できる
- [ ] internal link検査成功
- [ ] image/gaiji検査成功または明示的な制約判明
- [ ] ebzip後も読める
- [ ] capability JSON固定

### Stop rule

このPhaseが通らない限り、Wikipedia取得へ進みません。

---

## 6. Phase 2 — Boookends参照検査器

### 目的

手元の2023版を「目で見た印象」ではなく測定可能な参照データにします。

### 作業

- read-only mount
- path validation
- CATALOGS scan
- subbook scan
- file inventory
- EB utilitiesで可能なmetadata抽出
- fixed queries定義
- search result保存
- fixed entries取得
- manual checklist生成
- reference.sqlite3

### 固定query初期セット

```text
Emacs
Linux
日本
東京都
源氏物語
微分積分学
量子力学
第二次世界大戦
存在しない語
```

### 固定記事観測

- title
- result rank
- body text hashまたは先頭数百文字
- internal links数
- graphics/gaiji検出可能数
- search mode別結果数

### 出口条件

- [ ] 参照辞書を変更しない
- [ ] reference report生成
- [ ] 自動取得不能項目がmanual checklistに分離
- [ ] query結果を再実行して同じDBが得られる

---

## 7. Phase 3 — Source acquisition

### 目的

Wikimedia Enterprise Snapshotを安全にローカル固定します。

### 作業

- auth client
- token redaction
- metadata取得
- project/namespace filter
- concrete snapshot version解決
- HEAD size確認
- resumable download
- partial file
- atomic finalize
- SHA-256
- source lock
- local source registration

### 開発用データ

フルSnapshotを最初から取らず、次を用意します。

1. 公式または実データから抽出した10記事NDJSON fixture
2. edge case fixture
3. malformed fixture

fixtureにtokenや個人情報を含めません。

### 可用性ゲート

- metadata endpointで`jawiki_namespace_0`を確認する
- 実sampleでHTML fieldの存在を確認する
- Snapshotが利用不能ならLite/Fullを黙ってXML-onlyへ落とさない
- XML fallbackはMini向けの明示モードとして扱う

### 出口条件

- [ ] access tokenがログに出ない
- [ ] 途中download再開
- [ ] corrupt file拒否
- [ ] `latest`が具体versionへ解決
- [ ] source lockから再検証可能
- [ ] local file mode動作

---

## 8. Phase 4 — Raw ingest

### 目的

NDJSONをbounded memoryで検証・重複除去し、raw.sqlite3へ保存します。

### 作業

- tar.gz streaming
- NDJSON line parsing
- schema validation
- field extraction
- zstd compression
- batch transaction
- duplicate resolution
- redirect/category/license保存
- diagnostic保存
- progress
- interruption handling

### fixture edge cases

- HTMLあり
- HTMLなし、Wikitextあり
- 同page IDでrevision違い
- 同revision同hash重複
- 同revision異hash
- title長すぎ
- invalid URL
- empty license
- large article sample

### 出口条件

- [ ] 10記事期待件数
- [ ] duplicate ruleテスト
- [ ] bounded memory
- [ ] DB integrity check
- [ ] interruption後rerun可能
- [ ] manifestのlogical hash安定

---

## 9. Phase 5 — Article modelとcodec

### 目的

HTMLとEPWINGの間に安定したsemantic modelを作ります。

### 作業

- dataclasses / discriminated union
- validation
- JSON debug codec
- compressed DB codec
- schema version
- roundtrip tests
- canonical ordering/hash

### 最初に対応するblock

- Heading
- Paragraph
- List
- DefinitionList
- Quote
- Preformatted
- Table placeholder
- Infobox placeholder
- Image reference
- Math placeholder
- References placeholder
- Unsupported

### 出口条件

- [ ] roundtrip一致
- [ ] invalid nesting拒否
- [ ] canonical hash安定
- [ ] unknown typeを黙って無視しない

---

## 10. Phase 6 — Baseline HTML normalization

### 目的

普通の文章中心記事を読みやすいArticle modelへ変換します。

### 初期対応

- headings
- paragraphs
- bold/italic
- internal/external links
- ordered/unordered list
- definition list
- pre/code
- line break
- simple quote
- horizontal rule
- HTML entities
- section anchors

### 除外

- edit UI
- script/style
- navigation boxes
- hidden metadata

### 作業順

1. HTML parse
2. root selection
3. unsafe node removal
4. heading conversion
5. paragraph/inline conversion
6. list conversion
7. unknown fallback
8. whitespace normalization
9. model validation

### 出口条件

- [ ] 10記事golden一致
- [ ] unknown node diagnostic
- [ ] internal link label保持
- [ ] source order保持
- [ ] malformed HTMLでprocess全体が落ちない

---

## 11. Phase 7 — Link graphとredirect

### 目的

記事間移動と別名検索を成立させます。

### 作業

- URL -> normalized title
- page ID resolution
- fragment保存
- redirect aliases
- broken link diagnostic
- external link policy
- stable entry ID

### テスト

- relative/absolute URL
- percent encoding
- fragment
- missing target
- redirect alias
- title containing slash/parenthesis/unicode

### 出口条件

- [ ] fixture internal link解決率100%（意図的missing除く）
- [ ] redirect検索語生成
- [ ] title変更に影響しないpage ID entry ID

---

## 12. Phase 8 — Mini EPWING vertical slice

### 目的

100記事fixtureから実際に使えるMini辞書を生成します。

### 作業

- RenderedEntry
- headword/index term
- FreePWING source writer
- catalog
- internal references
- generate
- ebzip
- zip
- verify
- inspect command

### Miniの範囲

- text
- headings
- lists
- title
- redirects
- internal links
- table/infoboxはfallback text
- no images
- math text

### 出口条件

- [ ] 100記事entry数一致
- [ ] fixed title search
- [ ] redirect search
- [ ] internal link sample
- [ ] Japanese text
- [ ] verify JSON success
- [ ] EBWin等で手動確認

### Gate A

ここまででend-to-end vertical slice完成です。以降は機能追加のみであり、pipelineを全書き換えません。

---

## 13. Phase 9 — Stage cacheとresume

### 目的

長時間ビルドを安全に中断・再開します。

### 作業

- manifests
- input fingerprints
- stage version
- lock
- atomic output
- incomplete cleanup
- `--resume`
- `--from-stage`
- `--force-stage`

### テスト

- normalize途中kill
- incomplete manifest
- output hash mismatch
- config change invalidation
- unrelated config does not invalidate
- stage version bump

### 出口条件

- [ ] completed stage再利用
- [ ] corrupt output再利用拒否
- [ ] interrupted stageだけ再実行
- [ ] manifest chain追跡可能

---

## 14. Phase 10 — 日本語索引

### 目的

Boookends系の実用的な検索体験へ近づけます。

### 作業

- normalized title
- redirect
- ASCII casefold
- space normalization
- kana variant
- punctuation variant
- alias priority
- collision report
- backend search type mapping

### 非対象

- 本文全文token index
- MeCab必須化
- LLMによるalias生成

### 出口条件

- [ ] title/redirectにregressionなし
- [ ] configured kana variant
- [ ] collision deterministic
- [ ] dropped terms report

---

## 15. Phase 11 — Table

### 目的

Wikipediaの表情報をEPWINGで読みやすく保ちます。

### 作業

- DOM table parser
- headers
- row/col span
- caption
- nested content
- complexity classification
- simple renderer
- wide renderer
- oversized split/truncate policy

### fixture

- 2x2 simple
- multi-header
- rowspan
- colspan
- wide 12 columns
- nested table
- malformed table
- very large table

### 出口条件

- [ ] simple cells lossless
- [ ] wide table readable vertical layout
- [ ] malformed fallback
- [ ] oversized diagnostic

---

## 16. Phase 12 — Infobox

### 目的

記事冒頭の重要メタデータを読みやすく表示します。

### 作業

- class/role detection
- label/value
- title
- image refs
- nested links
- empty/style row removal
- field ordering
- max fields
- generic fallback

### 出口条件

- [ ] person/location/software/organization fixture
- [ ] lead本文より前にcompact表示
- [ ] duplicate data抑制
- [ ] empty infobox非表示

---

## 17. Phase 13 — Referencesと関連情報

### 目的

脚注・参考文献・カテゴリを過不足なく残します。

### 作業

- superscript reference link
- references list
- backlink除去
- external URL policy
- reference count
- category appendix
- related article section detection optional

### 出口条件

- [ ] reference labelと本文対応
- [ ] broken reference diagnostic
- [ ] profile別省略
- [ ] category index準備

---

## 18. Phase 14 — Unicodeとgaiji

### 目的

現代Wikipediaの文字をできるだけ失わず表示します。

### 作業

- backend representability probe
- substitution table
- NFC
- variation selector
- combining sequence
- narrow/wide gaiji
- bitmap generation
- registry
- usage count
- fallback codepoint text

### fixture

- JIS標準
- CJK拡張
- rare symbol
- emoji
- combining dakuten
- variation selector
- mathematical symbol

### 出口条件

- [ ] silent replacementゼロ
- [ ] gaiji reuse
- [ ] fallback text
- [ ] reportに頻出文字
- [ ] viewer manual check

---

## 19. Phase 15 — Math

### 目的

数式をtext fallbackからbitmap表示へ拡張します。

### 作業

- MathML/alt/TeX extraction
- canonical source
- renderer isolation
- cache
- SVG sanitize/rasterize
- inline/block sizes
- fallback

### 出口条件

- [ ] inline/block formula
- [ ] invalid formula fallback
- [ ] same formula cache hit
- [ ] deterministic bitmap hash

---

## 20. Phase 16 — Image planning and download

### 目的

安全に代表画像を取得し、Lite/Fullへ含めます。

### 作業

- main/infobox/lead/body classification
- selection policy
- download client
- allowlist
- MIME/magic validation
- size/pixel limit
- SVG sanitize
- conversion
- dedup
- attribution metadata

### 段階

1. fixture local images only
2. mocked HTTP
3. network marker test
4. 100記事real sample
5. 10,000記事trial

### 出口条件

- [ ] networkless normal tests
- [ ] unsafe URL reject
- [ ] duplicate hash reuse
- [ ] missing image nonfatal
- [ ] attribution missing policy

---

## 21. Phase 17 — Lite profile

### 目的

日常利用できる画像・表・数式付き辞書を100〜10,000記事で成立させます。

### 作業

- profile config
- image max
- table/infobox full render
- math bitmap
- aliases
- package name
- report

### 出口条件

- [ ] 100記事Lite
- [ ] 10,000記事Lite
- [ ] fixed viewer checklist
- [ ] no fatal diagnostic
- [ ] output size予測

### Gate B

10,000記事Liteが成功するまで全件へ進みません。

---

## 22. Phase 18 — Full indexes

### 目的

条件検索・クロス検索に相当する実用索引を追加します。

### 候補source

- heading
- category
- infobox field/value
- lead bold terms
- redirect/alias components

### 作業

- extraction policy
- term budget/article
- global term budget
- stop words
- priority
- collision
- backend mapping
- comparison query set

### 出口条件

- [ ] index size budget
- [ ] fixed query precision
- [ ] false-positive sample report
- [ ] search time/viewer behavior確認

---

## 23. Phase 19 — Boookends compatibility comparison

### 目的

「同等」の意味を数値化します。

### 作業

- fixed query compare
- fixed article compare
- feature matrix
- search result overlap
- missing article count
- layout manual checklist
- image/table/gaiji checks

### 出口条件

- [ ] `compare-reference` JSON/HTML
- [ ] COMPATIBILITY thresholds evaluated
- [ ] intentional differences documented
- [ ] brand-independent naming

---

## 24. Phase 20 — 10,000記事耐久試験

### 目的

全件前に、速度・メモリ・容量・診断傾向を把握します。

### sample

page ID rangeだけでなく、次を含むstratified sample:

- long article
- table-heavy
- image-heavy
- math-heavy
- Japanese history/literature
- technical
- disambiguation
- list article
- rare Unicode

### 収集

- stage duration
- records/sec
- peak memory
- DB size
- image cache
- diagnostics histogram
- largest entries
- slowest articles

### 出口条件

- [ ] no unbounded memory
- [ ] no DB integrity error
- [ ] fatal rate 0
- [ ] article error rate threshold内
- [ ] full size/time estimate

---

## 25. Phase 21 — 全件Mini trial

### 目的

画像などを除いた最小の全件変換を成功させます。

### 前提

- Gate A/B通過
- 200GB以上の作業余裕をdoctor確認（設定値）
- Docker named volume
- persistent logs
- source lock固定

### 作業

- ingest全件
- normalize全件
- Mini render
- EPWING generate
- package
- verify
- random sample

### 出口条件

- [ ] unattended completion
- [ ] eligible article coverage 99.9%以上を目標
- [ ] fatal 0
- [ ] archive opens
- [ ] fixed queries
- [ ] build report complete

失敗時は全体を即書き換えず、top diagnosticsを順番に修正します。

---

## 26. Phase 22 — 全件Lite trial

### 目的

代表画像・表・数式を含む実用版を生成します。

### 作業

- media plan全件
- image fetch/convert
- math cache
- Lite render
- package
- verify

### 出口条件

- [ ] media failures are nonfatal and reported
- [ ] attribution DB
- [ ] fixed image article display
- [ ] size budget
- [ ] reference comparison

---

## 27. Phase 23 — 全件Full candidate

### 目的

高機能版を生成し、公開可能性を評価します。

### 作業

- richer indexes
- more images
- categories
- attribution appendix
- full verification
- distributable policy

### 出口条件

- [ ] COMPATIBILITY target
- [ ] licensing report
- [ ] no secret/source path leakage
- [ ] reproducibility metadata
- [ ] viewer matrix

---

## 28. Phase 24 — 再現性試験

### 目的

同じ入力で同じ論理辞書が生成されることを確認します。

### 作業

- same machine two builds
- clean image build
- macOS Docker Desktop
- native Linux Docker（可能なら）
- logical hash compare
- archive metadata normalization

### 出口条件

- [ ] entry logical hash一致
- [ ] index logical hash一致
- [ ] graphic hash一致
- [ ] binary差異説明

---

## 29. Phase 25 — 月次更新ワークフロー

### 目的

新Snapshotへ更新する通常運用を1コマンド化します。

### CLI

```bash
wikiepwing update --project jawiki --profile full
wikiepwing clean --keep-runs 2
wikiepwing disk-usage
```

### 作業

- new source lock
- source diff metrics
- cache reuse
- old runs cleanup
- output retention
- release notes

### 出口条件

- [ ] old outputを自動削除しない
- [ ] same media/math cache reuse
- [ ] source version naming
- [ ] update report

---

## 30. Full build前ゲート一覧

全件ビルド前にすべて満たすこと。

- [ ] Phase 0〜20完了
- [ ] toolchain smoke green
- [ ] reference scan complete
- [ ] 100記事Mini green
- [ ] 100記事Lite green
- [ ] 10,000記事Lite green
- [ ] resume test green
- [ ] gaiji test green
- [ ] image security test green
- [ ] no network after acquire verified
- [ ] Docker disk capacity verified
- [ ] logs/reports persistent
- [ ] source.lock concrete
- [ ] user-facing profile settings fixed

---

## 31. v1.0 Definition of Done

次をすべて満たします。

### Build

- [ ] clean clone + Dockerで生成可能
- [ ] hostへlegacy dependency不要
- [ ] Mini/Lite/Full
- [ ] resume
- [ ] source lock

### Content

- [ ] title
- [ ] redirects
- [ ] internal links
- [ ] headings/lists
- [ ] tables
- [ ] infoboxes
- [ ] references
- [ ] gaiji fallback
- [ ] images Lite/Full
- [ ] math Lite/Full

### Quality

- [ ] structured diagnostics
- [ ] source/model/EPWING verify
- [ ] fixed article regression
- [ ] reference comparison
- [ ] compatibility thresholds

### Reproducibility

- [ ] dependency lock
- [ ] toolchain source hashes
- [ ] Docker digest
- [ ] logical hashes
- [ ] BUILD-INFO

### Documentation

- [ ] README build instructions
- [ ] config reference
- [ ] troubleshooting
- [ ] license/attribution notes
- [ ] viewer verification notes
