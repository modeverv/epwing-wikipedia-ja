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

### TASK-D008 [x] Register local source

**依存:** D004,D006

**実装:** predownloaded file without copy optional。

### TASK-D009 [x] Source inspect command

**依存:** D007

**実装:** lock/file/tar/NDJSON sample inspection。

### TASK-D010 [x] Build sanitized NDJSON fixtures

**依存:** D009

**実装:** 10 normal + edge cases、no credentials。

---

## EPIC E — Raw ingest

### TASK-E001 [x] raw DB migrations

**依存:** A003,D010

**実装:** articles, redirects, categories, templates, licenses, diagnostics, metadata。

### TASK-E002 [x] zstd codec

**依存:** E001

**実装:** deterministic settings、roundtrip、size limits。

### TASK-E003 [x] Tar streaming reader

**依存:** D010

**実装:** no full extraction、member validation。

### TASK-E004 [x] NDJSON record parser

**依存:** E003

**実装:** required/optional fields、typed RawArticle。

### TASK-E005 [x] Record safety validation

**依存:** E004

**実装:** field lengths、URL、namespace、HTML size。

### TASK-E006 [x] Duplicate resolver

**依存:** E004

**実装:** page ID/revision/hash rules。

### TASK-E007 [x] Batch repository writer

**依存:** E001,E002,E006

**実装:** transactions、prepared SQL、foreign keys。

### TASK-E008 [x] Ingest command

**依存:** E003-E007

**実装:** progress、diagnostics、manifest。

### TASK-E009 [x] Raw verifier

**依存:** E008

**実装:** integrity_check、FK、counts、sample decompression。

### TASK-E010 [x] Interrupted ingest recovery

**依存:** E008-E009

**実装:** incomplete status、rerun semantics。

---

## EPIC F — Model

### TASK-F001 [x] Diagnostic model

**依存:** E001

### TASK-F002 [x] Inline model

**依存:** F001

### TASK-F003 [x] Block model

**依存:** F002

### TASK-F004 [x] Article model

**依存:** F003

### TASK-F005 [x] Model validator

**依存:** F004

### TASK-F006 [x] Canonical JSON codec

**依存:** F004-F005

### TASK-F007 [x] Compressed model DB schema

**依存:** F006

### TASK-F008 [x] Logical hash

**依存:** F006

**完了:** order-independent sources yield deterministic canonical output where contract permits。

---

## EPIC G — HTML normalization baseline

### TASK-G001 [x] Safe HTML parser

**依存:** F004,D010

**実装:** no network/entities、malformed recovery policy。

### TASK-G002 [x] Root content selection

**依存:** G001

### TASK-G003 [x] Unsafe/UI node removal

**依存:** G002

### TASK-G004 [x] Heading conversion

**依存:** G003

### TASK-G005 [x] Paragraph and text conversion

**依存:** G003

### TASK-G006 [x] Strong/emphasis/code/line break

**依存:** G005

### TASK-G007 [x] Ordered/unordered lists

**依存:** G005

### TASK-G008 [x] Definition lists

**依存:** G005

### TASK-G009 [x] Quote/preformatted

**依存:** G005

### TASK-G010 [x] Unknown DOM fallback

**依存:** G004-G009

### TASK-G011 [x] Whitespace normalization

**依存:** G010

### TASK-G012 [x] Normalize command and model DB write

**依存:** F007-F008,G011

### TASK-G013 [x] Baseline golden snapshots

**依存:** G012

---

## EPIC H — Links and Mini rendering

### TASK-H001 [x] URL-to-title parser

**依存:** G006

### TASK-H002 [x] Internal target resolver

**依存:** H001,E008

### TASK-H003 [x] External link policy

**依存:** H001

### TASK-H004 [x] Redirect alias extraction

**依存:** E008

### TASK-H005 [x] Stable entry IDs

**依存:** F004

### TASK-H006 [x] RenderedEntry model

**依存:** H005

### TASK-H007 [x] Mini layout renderer

**依存:** H006,G012

### TASK-H008 [x] SearchTerm model and title terms

**依存:** H004,H006

### TASK-H009 [x] FreePWING source writer

**依存:** B009,H007-H008

### TASK-H010 [x] EPWING generate command

**依存:** H009

### TASK-H011 [x] EPWING verifier baseline

**依存:** H010

### TASK-H012 [x] 100-article fixture

**依存:** D010

### TASK-H013 [x] Mini end-to-end build

**依存:** H011-H012

---

## EPIC I — Pipeline resume

### TASK-I001 [x] Stage manifest schema

**依存:** E008,G012,H010

### TASK-I002 [x] Fingerprint calculation

**依存:** I001

### TASK-I003 [x] Stage lock

**依存:** I001

### TASK-I004 [x] Atomic stage output

**依存:** I001

### TASK-I005 [x] Resume decision

**依存:** I002-I004

### TASK-I006 [x] `--from-stage` and `--force-stage`

**依存:** I005

### TASK-I007 [x] Kill/restart integration tests

**依存:** I006

---

## EPIC J — Japanese search

### TASK-J001 [x] Index normalization contract

**依存:** H008

### TASK-J002 [x] NFKC/case/space variants

**依存:** J001

### TASK-J003 [x] Kana variants

**依存:** J001

### TASK-J004 [x] Punctuation variants

**依存:** J001

### TASK-J005 [x] Alias priorities

**依存:** J002-J004

### TASK-J006 [x] Collision repository/report

**依存:** J005

### TASK-J007 [x] Backend search mapping

**依存:** B009,J006

---

## EPIC K — Tables and infoboxes

### TASK-K001 [x] Table DOM parser

**依存:** G001,F003

### TASK-K002 [x] Row/col span normalization

**依存:** K001

### TASK-K003 [x] Table complexity classifier

**依存:** K002

### TASK-K004 [x] Simple table renderer

**依存:** K003,H007

### TASK-K005 [x] Wide table renderer

**依存:** K003,H007

### TASK-K006 [x] Oversized table policy

**依存:** K004-K005

### TASK-K007 [x] Infobox detector

**依存:** K001

### TASK-K008 [x] Infobox field parser

**依存:** K007

### TASK-K009 [x] Infobox renderer

**依存:** K008,H007

### TASK-K010 [x] Table/infobox golden set

**依存:** K006,K009

---

## EPIC L — References and categories

### TASK-L001 [x] Reference marker parser

**依存:** G001

### TASK-L002 [x] Reference list parser

**依存:** L001

### TASK-L003 [x] Reference renderer

**依存:** L002,H007

### TASK-L004 [x] Category appendix

**依存:** E008,H007

### TASK-L005 [x] Category search terms

**依存:** L004,J007

---

## EPIC M — Unicode and gaiji

### TASK-M001 [x] Backend representability table

**依存:** B009

### TASK-M002 [x] Unicode classifier

**依存:** M001

### TASK-M003 [x] Safe substitutions

**依存:** M002

### TASK-M004 [x] Gaiji registry schema

**依存:** M002

### TASK-M005 [x] Glyph bitmap renderer

**依存:** M004

### TASK-M006 [x] Gaiji code assignment

**依存:** M005

### TASK-M007 [x] FreePWING gaiji integration

**依存:** M006,H009

### TASK-M008 [x] Unrepresentable fallback

**依存:** M002

### TASK-M009 [x] Unicode report

**依存:** M003-M008

---

## EPIC N — Math

### TASK-N001 [x] Math node extraction

**依存:** G001

### TASK-N002 [x] Canonical math source

**依存:** N001

### TASK-N003 [x] Isolated renderer

**依存:** N002

### TASK-N004 [x] Math cache

**依存:** N003

### TASK-N005 [x] Raster conversion

**依存:** N003

### TASK-N006 [x] Inline/block layout

**依存:** N004-N005,H007

### TASK-N007 [x] Failure fallback

**依存:** N001

---

## EPIC O — Images

### TASK-O001 [x] MediaReference extraction

**依存:** G001,F004

### TASK-O002 [x] Role classification

**依存:** O001,K008

### TASK-O003 [x] Selection policy

**依存:** O002

### TASK-O004 [x] Secure downloader

**依存:** A004

### TASK-O005 [x] MIME/magic/pixel validation

**依存:** O004

### TASK-O006 [x] SVG sanitizer

**依存:** O005

### TASK-O007 [x] Raster converter

**依存:** O005-O006

### TASK-O008 [x] Content-addressed cache

**依存:** O007

### TASK-O009 [x] Dedup

**依存:** O008

### TASK-O010 [x] Attribution model

**依存:** O001

### TASK-O011 [x] EPWING graphics integration

**依存:** O007,H009

### TASK-O012 [x] Image plan/fetch/convert commands

**依存:** O003-O011

### TASK-O013 [x] Incremental fetch report and report rebuild

**依存:** O012

---


## EPIC P — Profiles and Lite

### TASK-P001 [x] Profile schema

**依存:** A003

### TASK-P002 [x] Mini profile finalize

**依存:** H013,J007,K010,L004,M009

### TASK-P003 [x] Lite profile

**依存:** N007,O012,P001

### TASK-P004 [x] Profile-driven renderer

**依存:** P002-P003

### TASK-P005 [x] 100-article Lite build

**依存:** P004

### TASK-P006 [x] 10,000-article sample builder

**依存:** P005

### TASK-P007 [x] 10,000-article Lite run

**依存:** P006

---

## EPIC Q — Full search and compatibility

### TASK-Q001 [x] Heading keyword extraction

**依存:** J007

### TASK-Q002 [x] Infobox keyword extraction

**依存:** K009,J007

### TASK-Q003 [x] Lead alias extraction

**依存:** G012,J007

### TASK-Q004 [x] Cross component extraction

**依存:** J007

### TASK-Q005 [x] Search budgets and stop rules

**依存:** Q001-Q004

### TASK-Q006 [x] Full profile

**依存:** O012,Q005,L005

### TASK-Q007 [x] Reference comparison engine

**依存:** C007,H011

### TASK-Q008 [x] Compatibility thresholds

**依存:** Q007

### TASK-Q009 [x] Compatibility HTML report

**依存:** Q008

---

## EPIC R — Full-scale builds

### TASK-R001 [x] Stratified 10,000 sample report

**依存:** P007,Q009

### TASK-R002 [x] Full-build preflight gate

**依存:** R001,I007

### TASK-R003 [x] Full jawiki ingest

**依存:** R002

### TASK-R004 [x] Full jawiki normalize

**依存:** R003

### TASK-R005 [x] Full Mini generate

**依存:** R004,P002

### TASK-R006 [x] Full Mini verify/report

**依存:** R005

### TASK-R007 [x] Full Lite media run

**依存:** R006,P003

### TASK-R008 [x] Full Lite generate/verify

**依存:** R007

### TASK-R009 [x] Full profile generate/verify

**依存:** R008,Q006

---

## EPIC S — Reproducibility and operations

### TASK-S001 [x] BUILD-INFO.json

**依存:** I001

### TASK-S002 [x] Logical content hash

**依存:** H010,M007,O011

### TASK-S003 [x] Deterministic archive metadata

**依存:** H010

### TASK-S004 [x] Same-host rebuild comparison

**依存:** R006,S001-S003

### TASK-S005 [x] Cross-host comparison

**依存:** S004

### TASK-S006 [x] Update command

**依存:** D007,I006

### TASK-S007 [x] Disk usage command

**依存:** A007

### TASK-S008 [x] Safe clean command

**依存:** S007

### TASK-S009 [x] Monthly update report

**依存:** S006

---

## EPIC T — Release documentation

### TASK-T001 [x] Build guide

**依存:** R006

### TASK-T002 [x] Configuration examples

**依存:** P003,Q006

### TASK-T003 [x] Troubleshooting

**依存:** R009

### TASK-T004 [x] Viewer verification guide

**依存:** Q009,R009

### TASK-T005 [x] Licensing/attribution guide

**依存:** O010,R009

### TASK-T006 [x] v1.0 release checklist

**依存:** S005,T001-T005

### TASK-T007 [x] Production EPWING build script

**依存:** T006

ユーザー依頼により追加(RELEASE_CHECKLIST.mdで発見した「entries.jsonlから全件規模でHONMONをビルドする本番スクリプトが無い」ギャップへの対応)。`docker/toolchain/build-epwing.sh`と`make build-epwing`を追加し、README.mdを実態に合わせて更新する。

### TASK-T008 [x] Acquire progress reporting

**依存:** T007

ユーザー依頼により追加。`acquire`が実行中に一切進捗を出力せず、実際にユーザーが「動いているのか固まっているのか分からない」という問題に遭遇したため、チャンク単位・チャンク内バイト単位の進捗コールバックを追加し、CLIで標準エラー出力に表示するようにする。

### TASK-T009 [x] Normalize CPU-bound step parallelization

**依存:** T008

ユーザー依頼により追加。`normalize`の処理時間についてユーザーから懸念があり、「処理時間が短縮できる変更ならば実装してほしいが、速度低下やバグ増加のリスクがあるならこのままにしたい」という条件付きで、16コア機での並列化による高速化を検討した。`normalize_html`によるDOM正規化からバリデーション・ハッシュ計算までの、記事1件ごとに副作用のないCPU律速な計算部分のみを`ProcessPoolExecutor`でプロセスプールに分散し、`raw.sqlite3`の読み込みと`model.sqlite3`への書き込みはこれまで通りメインプロセスで`page_id`順に逐次実行する(バッチ単位で分散・収集するため、メモリ使用量は既存の`batch_size`のままで変わらない)。以前から`config`の`[normalize]`に宣言されていた`workers`(デフォルト8)を初めて実際に使用するようにした。小規模フィクスチャで`workers=1`(逐次)と`workers=4`(並列)が完全にバイト単位で同一の`model.sqlite3`を生成することをテストで検証済み。

### TASK-T010 [x] Image fetch concurrency and fetch-count limit mode

**依存:** T009

ユーザー依頼により追加。`image-fetch`が`upload.wikimedia.org`への完全逐次ダウンロードで、全件(約250万ユニークURL)実行すると4〜12日かかる見積もり([RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md))だった。相手サーバーに迷惑をかけない範囲(既定4並列)で`ThreadPoolExecutor`による並列ダウンロードに対応し(ネットワークI/Oのため、normalizeのプロセスプールと違いスレッドプールを使用)、加えて「画像が不足した状態で一旦EPWINGビルドを最後まで通して動かしてみたい」という要望に応えるため、先頭N件のユニークURLを取得した時点で打ち切る`--limit`オプションを追加した。`config`の`[images]`に`fetch_concurrency`(既定4)を新設。並列時も出力順序(plan順)が逐次実行時と一致することをテストで検証済み。

### TASK-T011 [x] Image fetch progress reporting

**依存:** T010

ユーザー依頼により追加。TASK-T010で並列化・limitモードを追加した`image-fetch`が、`acquire`と同様に実行中の進捗を一切出力しないため「動いているのか分からない」状態だった。`fetch_media`にURL1件完了ごとの進捗コールバック(`FetchProgress`: completed/total/succeeded/failed)を追加し、CLIで標準エラー出力に表示するようにする。並列実行時は完了順(plan順ではない)でコールバックが呼ばれるが、返り値の`tuple`は従来通りplan順を維持する。

### TASK-T012 [x] Fix build-epwing.sh relative-path bind mount bug

**依存:** T007

ユーザーが実際に`make build-epwing`を実行した際、`cp: -r not specified; omitting directory '/input/entries.jsonl'`というエラーで失敗した。原因は`docker run -v`の仕様: ホスト側パスが`/`や`./`で始まらない相対パス(例: `entries-mini.jsonl`)の場合、Dockerはこれをbind mountではなく名前付きボリュームとして解釈し、空のディレクトリを作ってマウントしてしまう。`build-epwing.sh`内で`entries`/`graphics_dir`/`gaiji_dir`を`docker run -v`に渡す前に絶対パスへ解決するよう修正した。実際に`hundred_articles.ndjson`フィクスチャから生成した100記事entries.jsonlを相対パスで指定してビルドし、`ebinfo`・`wikiepwing-eb-search`での検索成功まで確認済み。

### TASK-T013 [x] Simple workaround for JIS X 0212 characters crashing the build

**依存:** T012

ユーザーが全件規模の`entries-mini.jsonl`でビルドを試したところ、`invalid character: \x8f`で`fpwmake`が失敗した。原因調査の結果、gaiji(外字)のクエリに対しユーザーへ「本格対応にはnormalize/generateへの外字置換パイプライン統合が必要で相応の規模の作業になる」と説明したところ、「簡易的な回避策を先に試したい」との回答を得た。原因は`docker/toolchain/freepwing_build_entries.pl`の`to_euc_jp`: PerlのEncodeモジュールは`euc-jp`エンコード時にJIS X 0212(SS3、`\x8f`プレフィックス)の文字も変換してしまうが、FreePWINGのFPWParserはJIS X 0208の2バイトコードしか理解せず`\x8f`を見ると死ぬ。実データの本文には(表現できないほど珍しい漢字ではなく)JIS X 0212にしか無い通常の漢字が普通に含まれるため、フィクスチャでは再現しなかった。`to_euc_jp`を文字単位のループに変更し、EUC-JPエンコード結果の先頭バイトが`0x8f`になる文字だけを全角下駄記号(〓、U+3013、JIS X 0208内)に置換するようにした(本格的なgaiji置換の代替であり、該当文字の情報は失われる簡易回避策であることを明記)。既存の`freepwing-build-entries-smoke.sh`回帰確認、およびJIS X 0212専用文字(凜)を含む新規フィクスチャでビルドが成功することを確認済み。

### TASK-T014 [x] freepwing_build_entries.pl progress reporting

**依存:** T013

ユーザーが`make build-epwing`実行中に「進捗も何も出ない、遅すぎる」と報告。`docker/toolchain/build-epwing.sh`が呼ぶ`freepwing_build_entries.pl`は、entries.jsonl全件をパースする段階(TASK-T013の1文字ずつのEUC-JP変換込み)とFPWParserへ登録する段階の2ループがあり、どちらも進捗出力が一切無かった。1.5万件ずつ(`$PROGRESS_EVERY = 20_000`)標準エラー出力に`parse N/total`・`index N/total`を出力するようにした。45,000件の合成フィクスチャで実際に途中経過が出力されることを確認済み。`fpwsort`/`fpwindex`等それ以降のFreePWING/EB付属バイナリ側は今回対象外(ソースを持たないコンパイル済みツールのため)。

### TASK-T015 [x] Speed up freepwing_build_entries.pl's to_euc_jp

**依存:** T014

ユーザーから`freepwing_build_entries.pl`が「めちゃくちゃ遅い」、進捗表示や並列化で何とかならないか問い合わせがあった。調査の結果、TASK-T013で入れた`to_euc_jp`の1文字ずつの`encode()`呼び出しループが、全件規模(約150万記事)で数億〜十億回規模のPerl関数呼び出しになっており、これが主要なボトルネックと判明した。JIS X 0212のSS3シーケンス(`\x8f`+2バイト)は他の正当なEUC-JPシーケンスの末尾バイトとして出現し得ない(JIS X0208・SS2かなの2バイト目はいずれも`0xA1`以上)ため、文字列全体を1回で`encode()`し、結果のバイト列に対して正規表現で`\x8f..`を下駄記号に一括置換する実装に変更した(全エッジケースでバイト単位の完全一致を確認済み)。10万件の合成ベンチマークで134秒→68秒(約2倍)の高速化を確認。FPWParserへの登録ループ(`text`/`heading`/`word2`)は`entry_position()`が処理順に依存する内部状態を持つため並列化はリスクが高く、今回は対象外とした。

### TASK-T016 [x] More frequent freepwing_build_entries.pl progress interval

**依存:** T015

ユーザー依頼により、TASK-T014で追加した進捗出力の間隔(2万件ごと)を10件ごとに変更した。あわせて、`make build-epwing`実行のたびに最新の`freepwing_build_entries.pl`が反映されるか(Dockerイメージにファイルが焼き込まれてキャッシュされていないか)という質問に回答: `docker/toolchain.Dockerfile`はこのファイルを一切COPYしておらず、`build-epwing.sh`が実行時にホスト上の現在のファイルを一時ディレクトリへコピーしてbind mountするため、常に最新版が使われることを`grep`で確認して回答した。

### TASK-T017 [x] Ingest pre/post-processing progress reporting

**依存:** E008,E010

ユーザー依頼により追加。`wikiepwing ingest` の記事処理前に行う全入力チャンクのSHA-256検証と既存raw DBの整合性検証、および記事処理後に行うraw DB全体のfingerprint計算が無表示で、正常に処理中なのか終了不能なのか判別できない。入力検証は全チャンク合計の処理バイト数、DB整合性検証は開始・継続中・完了、DB fingerprintは処理バイト数を標準エラーへ進捗表示する。

### TASK-T018 [x] Post-ingest command progress audit and reporting

**依存:** T017

ユーザーが実行するnormalize、generate、verify、画像パイプライン、toolchain image/build-epwingの一連のコマンドを対象に、実データ規模で長時間になり得る無表示処理を監査する。既存進捗で十分な区間は維持し、開始前・処理中・終了後に無表示となる重い区間だけへbounded-frequencyの進捗表示と回帰テストを追加する。

### TASK-T019 [x] Ignore generated root gaiji artifacts

**依存:** T018

ユーザーが`generate`実行後に大量の生成物がGit管理候補へ現れたことを報告した。`.gitignore`の履歴を確認し、リポジトリ直下へ既定出力される`gaiji/`、`gaiji.sqlite3`、`unicode-report.json`を、ソースの`src/wikiepwing/gaiji/`へ影響しないroot限定パターンで除外する。

### TASK-T020 [x] Enforce FreePWING gaiji capacity and complete the full build

**依存:** T019

全件`generate`が半角26,837・全角113,761の外字を生成した一方、FreePWINGは各幅8,192文字までしか定義できず、`fpwhalfchar`が`define too many characters`で停止した。各幅で使用頻度上位8,192文字だけを決定的に外字化し、残りを明示的なUnicodeコードポイント表記へフォールバックして、実EPWING ZIPの生成・検証まで行う。

### TASK-T021 [x] Document the verified full-build commands

**依存:** T020

TASK-T020で実際に成功した外字容量調整、toolchain image、EPWING生成、ZIP検証のコマンドと全件ビルドの実測結果をREADMEへ反映する。新規generate出力と、上限制御導入前の既存生成物を再利用する場合を区別する。

### TASK-T022 [x] Record viewer-observed differences as TODOs

**依存:** T021

ユーザーがEmacs Lookupでインターネット配布版と今回の全件ビルドを比較し、本文の読みやすさ、内部リンク、画像、検索候補に差があることを確認した。`DIFF.md`を追加し、確定した実装上の差と、辞書横断検索など追加測定が必要な差を分け、今後の改善TODO・優先順位・完了判定を記録する。

### TASK-T023 [x] Preserve inline internal links in FreePWING output

**依存:** T022

`DIFF.md`の最優先TODO。正規化済み本文中の内部リンク位置・表示ラベル・target entry tagを`RenderedEntry`からFreePWING adapterまで保持し、本文末尾の内部tag列挙ではなく、本文中の表示語句をクリック可能な参照として出力する。missing/externalizedリンクは安全なplain textを維持する。

### TASK-T024 [x] Measure the `日本` query against the distributed reference EPWING

**依存:** T022

比較範囲を`日本`の1 queryに限定し、`ref/Wikip_ja20230120`と今回版へ同一EB Library検索を実行する。検索能力、上位候補、重複、読み表示、Lookup画面との差を`DIFF.md`へ記録する。

### TASK-T025 [x] Preserve block structure inside Parsoid section wrappers

**依存:** T024

実データの「日本」が全17件`UnsupportedBlock`へ平坦化され、見出し・段落・情報ボックス・リンク構造を失っている問題を修正する。Parsoidの`section` wrapperだけを再帰的に展開し、未知のblock要素に対する既存fallbackは維持する。

### TASK-T026 [x] Preserve Parsoid related-link blocks

**依存:** T025

実データ「日本」に42件ある`div.rellink`を未知要素fallbackではなくParagraphBlockへ変換し、「→詳細は…」の表示境界を保持する。anchorの実リンク解決は次タスクへ分離する。

### TASK-T027 [x] Preserve article anchors as unresolved internal links

**依存:** T026

normalizeのinline変換で透明化されている`a[href]`を、表示ラベルとtarget title/fragmentを持つ`InternalLinkInline`へ変換する。DB解決前のためresolutionは`missing`とし、安全な外部URLは既存policyに従う。raw DBによるpage ID/redirect解決は次タスクへ分離する。

### TASK-T028 [x] Resolve normalized internal links against raw DB

**依存:** T027

workerで生成したInternalLinkInlineをmain processでraw DBへ照合し、直接記事、redirect、missing、namespace externalizedを確定する。同一projectのabsolute URLも記事URLのoriginと照合して内部リンクへ戻し、解決後のcanonical JSONとlogical hashを保存する。

### TASK-T029 [x] Preserve figure placement as ImageBlock

**依存:** T028

実データ「日本」の42件の`figure`をUnsupportedBlockではなく、media_idとalt textを持つImageBlockへ変換する。captionは同じmedia_idのArticle.media metadataに保持し、画像binary/FreePWING graphic名との接続は次タスクへ分離する。

### TASK-T030 [x] Wire ImageBlock placement to FreePWING graphics

**依存:** T029

image-fetch reportのsource URLからcontent hash（FreePWING graphic名）への対応をgenerateへ渡し、ImageBlock位置にgraphic render nodeとcaptionを出力する。未取得・変換失敗画像はalt/captionのplain text fallbackを維持する。

### TASK-T031 [x] Filter image planning and fetch by page ID

**依存:** T030

`image-plan`と`image-fetch`へ反復可能な`--page-id`を追加し、全Wikipedia画像を走査・取得せず「日本」（page ID 4821051）のselected mediaだけを安全に取得できるようにする。

### TASK-T032 [x] Rebuild the full model with reference-gap fixes

**依存:** T031

既存`model.sqlite3`を保持し、`model-diff.sqlite3`へ1,508,200記事を新しいsection/link/figure正規化処理で再生成する。完了後に「日本」のblock/link/media指標をDB成果物から再測定する。

### TASK-T033 [x] Wire extracted keyword terms to FreePWING keyword search

**依存:** T032

実装済みのheading/infobox keyword抽出とbudgetをgenerateへ接続し、FreePWING::FPWUtils::KeyWord indexを生成する。`ebinfo`のkeyword宣言と`日本`の同一query fixtureを実toolchainで検証する。

### TASK-T034 [x] Determine and implement the EPWING cross-search backend contract

**依存:** T033

本文内referenceだけでは`ebinfo`のcross search能力が有効にならないことを実toolchainで確認済み。配布版のcrossがFreePWING/EPWINGのどのindex/control contractに対応するかを一次資料・参照辞書測定で確定し、cross_component抽出済みtermを対応backendへ接続する。keywordへの単純混載でcross対応とみなしてはいけない。

### TASK-T035 [x] Full rebuild with new normalized model and index fixes

**依存:** T034

全件モデル `model-diff-ram8.sqlite3`（150万記事）から、新規実装された keyword / cross インデックス、インラインリンク、および画像位置反映を含む全件 EPWING 辞書を再ビルドした。一括メモリ保持による OOM (exit code 137) に対処するため generate ステージを 2パス・ストリーム処理へ移行・最適化し、`entries.jsonl` （19.4GB）の出力を成功させた。その後 `make build-epwing` を実行し、全件 EPWING 辞書 `data/output/jawiki.epwing.zip` （7.1GB、4検索方式 `word endword keyword cross` 対応）の正常構築・検証を達成した。

### TASK-T036 [x] Support Infobox image rendering and 16-worker parallel fetch

**依存:** T035

Infobox画像（`InfoboxBlock.images`）の EPWING グラフィック表示化（`cgraph`化）対応および、画像取得処理 (`image-fetch`) の並列数 16 への増強。`mini_layout.py` の `_render_infobox` でグラフィック表示制御コード `\x1eG:graphic_name\x1f` を選択出力できるように改修し、全テストにパスした。

### TASK-T037 [x] Support resumable image-fetch from existing report/originals

**依存:** T036

`image-fetch` 実行時に既存の `report` および `originals-dir` を参照し、すでにダウンロード・検証成功済みの画像 URL に対する二重 HTTP リクエストを自動スキップして途中から再開・復帰（レジューム）できるように改修し、全テストにパスした。

### TASK-T038 [x] Implement EDIT.md layout rules (Infobox, Headings, Lists, Tables)

**依存:** T037

ユーザー指定の表示ルール（`EDIT.md`）に従い、`mini_layout.py` のレンダリング処理を改修した。Infobox `【項目|値】` 形式、見出し `■ 見出し` 形式、リスト `1. ` / ` ・` 形式、Table のテキストグリッド化を適用し、全テストにパスした。

### TASK-T039 [x] Add Makefile targets for wikiepwing CLI and update README.md

**依存:** T038

`wikiepwing` の主要サブコマンド（`generate`, `build`, `image-plan`, `image-fetch`, `image-convert`, `verify`, `preview`）を `Makefile` へ統合し、`README.md` のドキュメントを更新・整備した。

### TASK-T040 [x] Add acquire and normalize targets to Makefile

**依存:** T039

Wikipedia Enterprise Snapshot チャンクダウンロード (`acquire`) やダンプ登録・取り込み・正規化 (`register-local-source`, `ingest`, `normalize`) ターゲットを `Makefile` に追加し、`README.md` を更新した。

### TASK-T041 [x] Fix EPWING newline rendering in freepwing_build_entries.pl

**依存:** T040

FreePWING ツールチェーン (`freepwing_build_entries.pl`) 内でテキスト内の `\n` を分割して `$writer->add_newline()` を呼び出すよう改修し、EPWING ビューアで改行が反映されずべたーっと繋がる問題を修正した。

### TASK-T042 [x] Fix Makefile build target to call build-epwing script

**依存:** T041

`Makefile` の `build` ターゲットを `build-epwing` 呼び出しに修正し、`make build` 実行時の CLI オプション引数エラーを解消した。

### TASK-T043 [x] Add automatic fallback for ENTRIES path in Makefile

**依存:** T042

`Makefile` の `ENTRIES` パスに `data/work/entries-mini.jsonl` への自動フォールバックを実装し、ビルド時の `entries.jsonl not found` エラーを解消した。

### TASK-T044 [x] Fix duplicate add_newline FPWParser error in freepwing_build_entries.pl

**依存:** T043

`freepwing_build_entries.pl` で `$last_was_newline` 状態フラグを導入して `add_newline()` の二重呼び出しを防止し、ビルド時の `Error 255` を解決した。

### TASK-T045 [x] Set default GAIJI_DIR path in Makefile

**依存:** T044

`Makefile` 内の `GAIJI_DIR` デフォルトパス（`data/work/gaiji`）を設定し、EPWING ビルド時に外字定義ファイルが FreePWING へ正常伝播されず `add_half_user_character failed (narrow-XXXX)` となる不具合を解決した。

### TASK-T046 [x] Guard add_newline during reference modifiers in freepwing_build_entries.pl

**依存:** T045

内部リンク修飾中に `add_newline()` が実行されることで発生する `modifier not terminated before newline` エラーを防止するため、リンクラベル内改行の置換およびアクティブリンク中の改行ガードを実装した。

### TASK-T047 [x] Output 【画像|URL】 fallback for ImageBlock in mini_layout.py

**依存:** T046

`mini_layout.py` の `ImageBlock` で、ローカルBMP画像が存在しない場合のフォールバックとして `【画像|URL】` 形式を出力するように改修し、Emacs Lookup (`lookup-image-url.el`) でのインラインWeb画像自動描画に対応した。

### TASK-T048 [x] Allow duplicate headwords across entries in backend_mapping and verify

**依存:** T047

FreePWING backend において記事を跨ぐ同一見出し語（同名タイトル・リダイレクト・曖昧さ回避）の削除・間引きを行わず、全記事に対して見出し語（aliases / word2）として登録するように `backend_mapping.py` を改修した。また `verify.py` で同名見出し語を不具合としていた `DUPLICATE_HEADWORD` エラー判定を削除し、全テストにパスした。
















