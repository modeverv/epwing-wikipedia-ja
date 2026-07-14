# TASKS.md

## 0. 使い方

- 状態は `[ ]` 未着手、`[~]` 作業中、`[x]` 完了、`[!]` blocked。
- 1セッションで原則1タスクだけ実装します。
- 各タスクの完了にはコード、テスト、`LOG.md`更新が必要です。
- 依存タスクが未完了なら開始しません。
- Task IDを変更しません。

---

## EPIC A — Repository foundation

### TASK-A001 [x] Python package skeleton

**依存:** なし

**変更:** `pyproject.toml`, `src/wikiepwing/__init__.py`, `src/wikiepwing/cli.py`

**実装:**

- Python 3.12 requirement
- package metadata
- `wikiepwing` console script
- `--version`, `--help`

**テスト:** CLI help/version

**完了:** `uv run wikiepwing --help`成功。

### TASK-A002 [x] Quality tools

**依存:** A001

**変更:** `pyproject.toml`, `Makefile`

**実装:** ruff format/lint、type checker、pytest command。

**完了:** 空に近いprojectで`make check`成功。

### TASK-A003 [x] Configuration loader

**依存:** A001

**変更:** `src/wikiepwing/config.py`, `config/default.toml`

**実装:** TOML load、default merge、unknown key reject、path resolution。

**テスト:** valid/invalid/unknown key。

### TASK-A004 [x] Structured logging

**依存:** A001

**実装:** console + JSONL、secret redaction、run_id/stage context。

**テスト:** token文字列が出力されない。

### TASK-A005 [x] Docker app image

**依存:** A001-A004

**実装:** Debian slim、Python 3.12、uv、non-root、read/write paths。

**テスト:** container UID非0。

### TASK-A006 [x] Compose and volumes

**依存:** A005

**実装:** source/work/cache named volume、output/report bind mount。

**完了:** `docker compose run --rm app wikiepwing --version`。

### TASK-A007 [x] Doctor command

**依存:** A003-A006

**実装:** architecture, locale, timezone, free disk, paths, tools, config、JSON mode。

**テスト:** JSON schema。

---

## EPIC B — Legacy toolchain

### TASK-B001 [x] Pin EB source

**依存:** A006

**実装:** URL、SHA-256、download script、checksum failure test。

### TASK-B002 [x] Build EB Library

**依存:** B001

**実装:** multi-stage toolchain image、version command。

### TASK-B003 [x] Pin FreePWING source

**依存:** B002

**実装:** URL、SHA-256、patch directory。

### TASK-B004 [x] Build FreePWING

**依存:** B003

**実装:** reproducible build、required Perl/runtime deps。

### TASK-B005 [x] Verify ebzip

**依存:** B002

**実装:** command path/version、roundtrip fixture。

### TASK-B006 [x] Handcrafted three-entry source

**依存:** B004

**実装:** Emacs/Linux/Wikipedia、links、aliases、日本語。

### TASK-B007 [x] Graphic sample

**依存:** B006

**実装:** generated small bitmap only。

### TASK-B008 [x] Gaiji sample

**依存:** B006

**実装:** narrow/wide sample、no silent fallback。

### TASK-B009 [x] Toolchain probe command

**依存:** B005-B008

**出力:** `toolchain-capabilities.json`。

### TASK-B010 [x] Toolchain smoke package

**依存:** B009

**実装:** generate、ebzip、zip、verify。

---

## EPIC C — Reference inspection

### TASK-C001 [x] Reference path validation

**依存:** A007

**実装:** read-only expectation、CATALOGS discovery、no writes。

### TASK-C002 [x] Reference inventory

**依存:** C001, B002

**実装:** file tree、sizes、subbook candidates。

### TASK-C003 [x] Reference DB schema

**依存:** C001

**実装:** explicit SQL migrations。

### TASK-C004 [x] Fixed query definition

**依存:** C003

**実装:** config/query-set.toml。

### TASK-C005 [x] Execute reference searches

**依存:** C002-C004

**実装:** EB utility adapter、timeout、result persistence。

### TASK-C006 [x] Reference entry sampling

**依存:** C005

**実装:** extract available text/metadata; unsupported is manual item。

### TASK-C007 [x] Reference report

**依存:** C006

**出力:** JSON/HTML/manual checklist。

---

## EPIC D — Source acquisition

### TASK-D001 [x] Secret model and env example

**依存:** A003-A004

**実装:** environment names、redaction、validation。

### TASK-D002 [x] Enterprise auth client

**依存:** D001

**実装:** access/refresh/login priority、timeouts、no persistence。

### TASK-D003 [x] Snapshot metadata client

**依存:** D002

**実装:** jawiki namespace 0 filter、specific version object。

### TASK-D004 [x] Source lock schema

**依存:** D003

**実装:** JSON schema、canonical serialization。

### TASK-D005 [x] Resumable downloader

**依存:** D003

**実装:** HEAD、Range、partial、atomic rename、bounded retry。

### TASK-D006 [x] Checksum and file fingerprint

**依存:** D005

**実装:** streaming SHA-256、size verify。

### TASK-D007 [x] Acquire command

**依存:** D004-D006

**実装:** metadata -> download -> verify -> lock。

### TASK-D008 [ ] Register local source

**依存:** D004,D006

**実装:** predownloaded file without copy optional。

### TASK-D009 [ ] Source inspect command

**依存:** D007

**実装:** lock/file/tar/NDJSON sample inspection。

### TASK-D010 [ ] Build sanitized NDJSON fixtures

**依存:** D009

**実装:** 10 normal + edge cases、no credentials。

---

## EPIC E — Raw ingest

### TASK-E001 [ ] raw DB migrations

**依存:** A003,D010

**実装:** articles, redirects, categories, templates, licenses, diagnostics, metadata。

### TASK-E002 [ ] zstd codec

**依存:** E001

**実装:** deterministic settings、roundtrip、size limits。

### TASK-E003 [ ] Tar streaming reader

**依存:** D010

**実装:** no full extraction、member validation。

### TASK-E004 [ ] NDJSON record parser

**依存:** E003

**実装:** required/optional fields、typed RawArticle。

### TASK-E005 [ ] Record safety validation

**依存:** E004

**実装:** field lengths、URL、namespace、HTML size。

### TASK-E006 [ ] Duplicate resolver

**依存:** E004

**実装:** page ID/revision/hash rules。

### TASK-E007 [ ] Batch repository writer

**依存:** E001,E002,E006

**実装:** transactions、prepared SQL、foreign keys。

### TASK-E008 [ ] Ingest command

**依存:** E003-E007

**実装:** progress、diagnostics、manifest。

### TASK-E009 [ ] Raw verifier

**依存:** E008

**実装:** integrity_check、FK、counts、sample decompression。

### TASK-E010 [ ] Interrupted ingest recovery

**依存:** E008-E009

**実装:** incomplete status、rerun semantics。

---

## EPIC F — Model

### TASK-F001 [ ] Diagnostic model

**依存:** E001

### TASK-F002 [ ] Inline model

**依存:** F001

### TASK-F003 [ ] Block model

**依存:** F002

### TASK-F004 [ ] Article model

**依存:** F003

### TASK-F005 [ ] Model validator

**依存:** F004

### TASK-F006 [ ] Canonical JSON codec

**依存:** F004-F005

### TASK-F007 [ ] Compressed model DB schema

**依存:** F006

### TASK-F008 [ ] Logical hash

**依存:** F006

**完了:** order-independent sources yield deterministic canonical output where contract permits。

---

## EPIC G — HTML normalization baseline

### TASK-G001 [ ] Safe HTML parser

**依存:** F004,D010

**実装:** no network/entities、malformed recovery policy。

### TASK-G002 [ ] Root content selection

**依存:** G001

### TASK-G003 [ ] Unsafe/UI node removal

**依存:** G002

### TASK-G004 [ ] Heading conversion

**依存:** G003

### TASK-G005 [ ] Paragraph and text conversion

**依存:** G003

### TASK-G006 [ ] Strong/emphasis/code/line break

**依存:** G005

### TASK-G007 [ ] Ordered/unordered lists

**依存:** G005

### TASK-G008 [ ] Definition lists

**依存:** G005

### TASK-G009 [ ] Quote/preformatted

**依存:** G005

### TASK-G010 [ ] Unknown DOM fallback

**依存:** G004-G009

### TASK-G011 [ ] Whitespace normalization

**依存:** G010

### TASK-G012 [ ] Normalize command and model DB write

**依存:** F007-F008,G011

### TASK-G013 [ ] Baseline golden snapshots

**依存:** G012

---

## EPIC H — Links and Mini rendering

### TASK-H001 [ ] URL-to-title parser

**依存:** G006

### TASK-H002 [ ] Internal target resolver

**依存:** H001,E008

### TASK-H003 [ ] External link policy

**依存:** H001

### TASK-H004 [ ] Redirect alias extraction

**依存:** E008

### TASK-H005 [ ] Stable entry IDs

**依存:** F004

### TASK-H006 [ ] RenderedEntry model

**依存:** H005

### TASK-H007 [ ] Mini layout renderer

**依存:** H006,G012

### TASK-H008 [ ] SearchTerm model and title terms

**依存:** H004,H006

### TASK-H009 [ ] FreePWING source writer

**依存:** B009,H007-H008

### TASK-H010 [ ] EPWING generate command

**依存:** H009

### TASK-H011 [ ] EPWING verifier baseline

**依存:** H010

### TASK-H012 [ ] 100-article fixture

**依存:** D010

### TASK-H013 [ ] Mini end-to-end build

**依存:** H011-H012

---

## EPIC I — Pipeline resume

### TASK-I001 [ ] Stage manifest schema

**依存:** E008,G012,H010

### TASK-I002 [ ] Fingerprint calculation

**依存:** I001

### TASK-I003 [ ] Stage lock

**依存:** I001

### TASK-I004 [ ] Atomic stage output

**依存:** I001

### TASK-I005 [ ] Resume decision

**依存:** I002-I004

### TASK-I006 [ ] `--from-stage` and `--force-stage`

**依存:** I005

### TASK-I007 [ ] Kill/restart integration tests

**依存:** I006

---

## EPIC J — Japanese search

### TASK-J001 [ ] Index normalization contract

**依存:** H008

### TASK-J002 [ ] NFKC/case/space variants

**依存:** J001

### TASK-J003 [ ] Kana variants

**依存:** J001

### TASK-J004 [ ] Punctuation variants

**依存:** J001

### TASK-J005 [ ] Alias priorities

**依存:** J002-J004

### TASK-J006 [ ] Collision repository/report

**依存:** J005

### TASK-J007 [ ] Backend search mapping

**依存:** B009,J006

---

## EPIC K — Tables and infoboxes

### TASK-K001 [ ] Table DOM parser

**依存:** G001,F003

### TASK-K002 [ ] Row/col span normalization

**依存:** K001

### TASK-K003 [ ] Table complexity classifier

**依存:** K002

### TASK-K004 [ ] Simple table renderer

**依存:** K003,H007

### TASK-K005 [ ] Wide table renderer

**依存:** K003,H007

### TASK-K006 [ ] Oversized table policy

**依存:** K004-K005

### TASK-K007 [ ] Infobox detector

**依存:** K001

### TASK-K008 [ ] Infobox field parser

**依存:** K007

### TASK-K009 [ ] Infobox renderer

**依存:** K008,H007

### TASK-K010 [ ] Table/infobox golden set

**依存:** K006,K009

---

## EPIC L — References and categories

### TASK-L001 [ ] Reference marker parser

**依存:** G001

### TASK-L002 [ ] Reference list parser

**依存:** L001

### TASK-L003 [ ] Reference renderer

**依存:** L002,H007

### TASK-L004 [ ] Category appendix

**依存:** E008,H007

### TASK-L005 [ ] Category search terms

**依存:** L004,J007

---

## EPIC M — Unicode and gaiji

### TASK-M001 [ ] Backend representability table

**依存:** B009

### TASK-M002 [ ] Unicode classifier

**依存:** M001

### TASK-M003 [ ] Safe substitutions

**依存:** M002

### TASK-M004 [ ] Gaiji registry schema

**依存:** M002

### TASK-M005 [ ] Glyph bitmap renderer

**依存:** M004

### TASK-M006 [ ] Gaiji code assignment

**依存:** M005

### TASK-M007 [ ] FreePWING gaiji integration

**依存:** M006,H009

### TASK-M008 [ ] Unrepresentable fallback

**依存:** M002

### TASK-M009 [ ] Unicode report

**依存:** M003-M008

---

## EPIC N — Math

### TASK-N001 [ ] Math node extraction

**依存:** G001

### TASK-N002 [ ] Canonical math source

**依存:** N001

### TASK-N003 [ ] Isolated renderer

**依存:** N002

### TASK-N004 [ ] Math cache

**依存:** N003

### TASK-N005 [ ] Raster conversion

**依存:** N003

### TASK-N006 [ ] Inline/block layout

**依存:** N004-N005,H007

### TASK-N007 [ ] Failure fallback

**依存:** N001

---

## EPIC O — Images

### TASK-O001 [ ] MediaReference extraction

**依存:** G001,F004

### TASK-O002 [ ] Role classification

**依存:** O001,K008

### TASK-O003 [ ] Selection policy

**依存:** O002

### TASK-O004 [ ] Secure downloader

**依存:** A004

### TASK-O005 [ ] MIME/magic/pixel validation

**依存:** O004

### TASK-O006 [ ] SVG sanitizer

**依存:** O005

### TASK-O007 [ ] Raster converter

**依存:** O005-O006

### TASK-O008 [ ] Content-addressed cache

**依存:** O007

### TASK-O009 [ ] Dedup

**依存:** O008

### TASK-O010 [ ] Attribution model

**依存:** O001

### TASK-O011 [ ] EPWING graphics integration

**依存:** O007,H009

### TASK-O012 [ ] Image plan/fetch/convert commands

**依存:** O003-O011

---

## EPIC P — Profiles and Lite

### TASK-P001 [ ] Profile schema

**依存:** A003

### TASK-P002 [ ] Mini profile finalize

**依存:** H013,J007,K010,L004,M009

### TASK-P003 [ ] Lite profile

**依存:** N007,O012,P001

### TASK-P004 [ ] Profile-driven renderer

**依存:** P002-P003

### TASK-P005 [ ] 100-article Lite build

**依存:** P004

### TASK-P006 [ ] 10,000-article sample builder

**依存:** P005

### TASK-P007 [ ] 10,000-article Lite run

**依存:** P006

---

## EPIC Q — Full search and compatibility

### TASK-Q001 [ ] Heading keyword extraction

**依存:** J007

### TASK-Q002 [ ] Infobox keyword extraction

**依存:** K009,J007

### TASK-Q003 [ ] Lead alias extraction

**依存:** G012,J007

### TASK-Q004 [ ] Cross component extraction

**依存:** J007

### TASK-Q005 [ ] Search budgets and stop rules

**依存:** Q001-Q004

### TASK-Q006 [ ] Full profile

**依存:** O012,Q005,L005

### TASK-Q007 [ ] Reference comparison engine

**依存:** C007,H011

### TASK-Q008 [ ] Compatibility thresholds

**依存:** Q007

### TASK-Q009 [ ] Compatibility HTML report

**依存:** Q008

---

## EPIC R — Full-scale builds

### TASK-R001 [ ] Stratified 10,000 sample report

**依存:** P007,Q009

### TASK-R002 [ ] Full-build preflight gate

**依存:** R001,I007

### TASK-R003 [ ] Full jawiki ingest

**依存:** R002

### TASK-R004 [ ] Full jawiki normalize

**依存:** R003

### TASK-R005 [ ] Full Mini generate

**依存:** R004,P002

### TASK-R006 [ ] Full Mini verify/report

**依存:** R005

### TASK-R007 [ ] Full Lite media run

**依存:** R006,P003

### TASK-R008 [ ] Full Lite generate/verify

**依存:** R007

### TASK-R009 [ ] Full profile generate/verify

**依存:** R008,Q006

---

## EPIC S — Reproducibility and operations

### TASK-S001 [ ] BUILD-INFO.json

**依存:** I001

### TASK-S002 [ ] Logical content hash

**依存:** H010,M007,O011

### TASK-S003 [ ] Deterministic archive metadata

**依存:** H010

### TASK-S004 [ ] Same-host rebuild comparison

**依存:** R006,S001-S003

### TASK-S005 [ ] Cross-host comparison

**依存:** S004

### TASK-S006 [ ] Update command

**依存:** D007,I006

### TASK-S007 [ ] Disk usage command

**依存:** A007

### TASK-S008 [ ] Safe clean command

**依存:** S007

### TASK-S009 [ ] Monthly update report

**依存:** S006

---

## EPIC T — Release documentation

### TASK-T001 [ ] Build guide

**依存:** R006

### TASK-T002 [ ] Configuration examples

**依存:** P003,Q006

### TASK-T003 [ ] Troubleshooting

**依存:** R009

### TASK-T004 [ ] Viewer verification guide

**依存:** Q009,R009

### TASK-T005 [ ] Licensing/attribution guide

**依存:** O010,R009

### TASK-T006 [ ] v1.0 release checklist

**依存:** S005,T001-T005
