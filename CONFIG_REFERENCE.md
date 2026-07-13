# CONFIG_REFERENCE.md

## 1. 方針

設定はTOMLで管理します。

読み込み順:

1. `config/default.toml`
2. `config/projects/<project>.toml`
3. `config/profiles/<profile>.toml`
4. CLI `--config`追加ファイル
5. 許可されたCLI override

後勝ちです。ただしunknown keyはエラーにします。

秘密情報をTOMLへ書きません。

---

## 2. 全体例

```toml
schema_version = 1
project = "jawiki"
profile = "lite"

[paths]
sources = "/data/sources"
reference = "/data/reference"
work = "/data/work"
cache = "/data/cache"
output = "/data/output"
reports = "/data/reports"
logs = "/data/logs"

[source]
provider = "enterprise"
namespace = 0
snapshot = "latest"
allow_xml_fallback = true
verify_sha256 = true

[source.enterprise]
api_base = "https://api.enterprise.wikimedia.com/v2"
auth_base = "https://auth.enterprise.wikimedia.com/v1"
request_timeout_seconds = 60
download_timeout_seconds = 300
max_retries = 5

[source.xml]
base_url = "https://dumps.wikimedia.org/jawiki/latest/"
include_redirect_sql = true
include_page_sql = false

[ingest]
batch_size = 500
max_title_bytes = 4096
max_url_bytes = 16384
max_html_bytes = 67108864
max_wikitext_bytes = 67108864
zstd_level = 6
strict_required_fields = true

[normalize]
workers = 8
queue_depth = 64
html_recover = true
preserve_unknown_text = true
max_dom_depth = 512
remove_edit_ui = true
remove_navboxes = true
remove_authority_control = true

[text]
internal_unicode_normalization = "NFC"
index_unicode_normalization = "NFKC"
normalize_index_spaces = true
casefold_ascii = true
generate_hiragana_variant = true
generate_katakana_variant = true
remove_index_punctuation = false

[tables]
enabled = true
simple_max_columns = 5
simple_max_rows = 100
wide_max_columns = 20
max_rows = 2000
max_cells = 20000
oversized_action = "split"

[infobox]
enabled = true
max_fields = 60
remove_empty_fields = true

[references]
enabled = true
max_references = 2000
external_urls = "plain-text"

[images]
enabled = true
max_per_article = 3
preferred_width = 320
max_download_bytes = 10485760
max_pixels = 40000000
allowed_hosts = ["upload.wikimedia.org"]
allow_svg = true
allow_animated = false
missing_license_action = "warn"

[math]
enabled = true
render_graphics = true
max_source_bytes = 65536
render_timeout_seconds = 10

[gaiji]
enabled = true
font_family = "Noto Sans CJK JP"
font_package_id = "debian-fonts-noto-cjk"
fallback_format = "[U+{codepoint}]"

[search]
include_titles = true
include_redirects = true
include_aliases = true
include_categories = false
include_heading_keywords = false
include_infobox_keywords = false
max_terms_per_article = 64
max_key_bytes = 255

[epwing]
backend = "freepwing"
book_title = "Wikipedia Japanese 2026"
subbook_name = "WIKIJA26"
ebzip_level = 5
entry_budget_bytes = 1048576
archive_timestamp = "2000-01-01T00:00:00Z"

[resources]
worker_count = 8
image_worker_count = 4
math_worker_count = 2
sqlite_cache_mib = 4096
minimum_free_disk_gib = 200

[verification]
random_sample_size = 500
fixed_seed = 20260713
fail_on_fatal = true
max_article_error_rate = 0.001

[distribution]
mode = "personal"
include_attribution_appendix = true
exclude_images_without_license = false
```

---

## 3. `schema_version`

整数。設定構造に破壊的変更があると増やします。未対応versionはエラー。

---

## 4. `project`

初期対応:

```text
jawiki
```

将来:

```text
enwiki
simplewiki
```

project-specific title normalization、base URL、DOM ruleを選択します。

---

## 5. `[paths]`

すべてabsolute pathを推奨。container標準pathから外れる場合はdoctorが警告します。

- `sources`: immutable source bundles
- `reference`: read-only reference EPWING
- `work`: run DB/temp
- `cache`: media/math
- `output`: final artifacts
- `reports`: JSON/HTML/CSV
- `logs`: logs

`reference`へwriteしようとした場合はfatal。

---

## 6. `[source]`

### provider

- `enterprise`: standard
- `local-enterprise`: predownloaded tar.gz
- `xml`: fallback Mini-oriented

### snapshot

- `latest`: acquisition時にconcrete versionへ解決
- concrete version/date: provider supported format

build manifestへ`latest`を残しません。

### allow_xml_fallback

HTML missing記事でWikitext parsing fallbackを使う許可。初期実装ではfallback機能が未完成ならwarningを出し、無視しません。

---

## 7. `[source.enterprise]`

API endpointは通常変更しません。テスト用mock serverでoverride可能。

retry対象:

- timeout
- 429
- 5xx

retryしない:

- 400
- 401
- 403
- 404
- schema error

---

## 8. `[ingest]`

### batch_size

SQLite transactionあたりの記事数。大きすぎると中断時損失とmemoryが増えます。

### zstd_level

raw/model BLOBの圧縮。再現性が保たれる固定設定を使用。

### strict_required_fields

required field欠落をrejectする。通常true。

---

## 9. `[normalize]`

### workers

0ならresource設定から自動。SQLite書込は別制御。

### html_recover

malformed HTML recovery。falseではparse error記事をreject。

### preserve_unknown_text

unknown DOMからvisible textをfallback保存。true推奨。

### remove_navboxes

本文末の巨大navigation tableを除外。table class判定test必須。

---

## 10. `[text]`

本文と索引のnormalizationを分けます。

`remove_index_punctuation=true`はcollision増加の可能性があるためFullでも慎重に使用。

kana variantsは読みを推定する機能ではありません。既存かな文字列のひらがな/カタカナvariantだけです。

---

## 11. `[tables]`

### oversized_action

- `split`: 続きentry
- `truncate`: report付き切り詰め
- `fallback`: plain text
- `reject-article`: 原則非推奨

### max_cells

rowspan展開後ではなく、source cell countとlogical countのどちらかを設計で固定しテストします。

---

## 12. `[images]`

### missing_license_action

- `warn`
- `exclude`
- `fail`

`distribution.mode=public`では`exclude`以上を強制可能にします。

### allowed_hosts

redirect後の最終hostにも適用。

### preferred_width

取得URLにthumbnail sizeを指定できる場合の目標。EPWING出力時にさらに変換可能。

---

## 13. `[gaiji]`

`font_family`はDocker内に存在することをdoctor/toolchain probeで検証します。

fontファイルを最終archiveへ含めません。

---

## 14. `[search]`

### max_terms_per_article

keyword/cross termsの爆発防止。title/redirectは別budget扱い可能。

### max_key_bytes

toolchain probeで得た安全値以下に設定。超過keyのshorteningは無言で行わずdiagnostic。

---

## 15. `[epwing]`

### subbook_name

backend制約へ適合するASCII名。長さ・文字種はprobe結果でvalidate。

### entry_budget_bytes

backend hard limitではなく安全budget。toolchain capabilitiesより大きい設定はエラー。

### archive_timestamp

deterministic archive用。

---

## 16. `[distribution]`

### mode

- `personal`: 個人利用build
- `public`: 再配布前提の厳格policy

public modeの強制:

- attribution appendix
- missing image license exclusion
- source/license metadata
- no local absolute path in artifact

---

## 17. Profile defaults

### mini.toml

```toml
profile = "mini"

[images]
enabled = false

[math]
render_graphics = false

[tables]
enabled = true
oversized_action = "fallback"

[search]
include_aliases = false
include_categories = false
include_heading_keywords = false
include_infobox_keywords = false
max_terms_per_article = 8

[references]
max_references = 100
```

### lite.toml

```toml
profile = "lite"

[images]
enabled = true
max_per_article = 3
preferred_width = 320

[math]
render_graphics = true

[search]
include_aliases = true
include_categories = false
include_heading_keywords = true
include_infobox_keywords = false
max_terms_per_article = 32
```

### full.toml

```toml
profile = "full"

[images]
enabled = true
max_per_article = 8
preferred_width = 480

[search]
include_aliases = true
include_categories = true
include_heading_keywords = true
include_infobox_keywords = true
max_terms_per_article = 128

[distribution]
include_attribution_appendix = true
```

---

## 18. Environment variables

秘密:

```text
WME_USERNAME
WME_PASSWORD
WME_ACCESS_TOKEN
WME_REFRESH_TOKEN
```

非秘密override:

```text
WIKIEPWING_CONFIG
WIKIEPWING_LOG_LEVEL
WIKIEPWING_RUN_ID
WIKIEPWING_FAIL_STAGE       # test only
WIKIEPWING_FAIL_AFTER_RECORDS # test only
```

一般設定を大量の環境変数へ展開しません。TOMLを正本にします。

---

## 19. Validation rules

- unknown key: error
- negative limit: error
- image enabled + max_per_article 0: warning/error contract
- public mode + missing license warn: override/error
- entry budget > toolchain capability: error
- source path inside reference path: error
- output inside read-only path: error
- worker count > configured max: error
- snapshot `latest` in build stage: error; acquire stage only
