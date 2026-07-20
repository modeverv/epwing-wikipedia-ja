# ARCHITECTURE.md

# Wikipedia EPWING Builder Architecture

## 1. Project overview

This project builds a modern, reproducible EPWING/JIS X 4081 dictionary from Wikimedia dumps.

The initial target is Japanese Wikipedia, with optional support for English Wikipedia and other Wikimedia projects.

The generated dictionary should provide more functionality than the traditional `wikipedia-fpw` output:

* Full-text article body
* Headword search
* Alternate-title and redirect search
* Keyword search
* Cross-reference links
* Image inclusion
* Table rendering
* Infobox rendering
* Math formula rendering
* Category metadata
* Disambiguation handling
* Compressed EPWING output using `ebzip`
* Reproducible builds using Docker
* Incremental and resumable build stages
* Build verification and statistics

The project must not depend on the host operating system beyond Docker and basic filesystem access.

---

## 2. Goals

### 2.1 Primary goals

1. Generate a usable Japanese Wikipedia EPWING dictionary from current Wikimedia dumps.
2. Preserve substantially more article information than legacy `wikipedia-fpw`.
3. Make the build reproducible across macOS and Linux.
4. Allow failed builds to resume without repeating all stages.
5. Make every transformation stage observable and testable.
6. Separate Wikipedia parsing from EPWING generation.
7. Support future output formats without rewriting the parser.

### 2.2 Secondary goals

* Support Simple English Wikipedia and English Wikipedia.
* Support Wiktionary or other MediaWiki-based projects.
* Allow image-free and lightweight build profiles.
* Allow article filtering by namespace, category, or popularity.
* Allow deterministic nightly or monthly builds.
* Produce machine-readable build reports.

### 2.3 Non-goals

The first implementation does not need to:

* Reproduce the live Wikipedia website exactly.
* Execute arbitrary Lua modules or MediaWiki extensions.
* Download every original image at full resolution.
* Support article editing.
* Provide a standalone EPWING viewer.
* Implement a complete MediaWiki rendering engine.
* Guarantee perfect rendering of every template.

---

## 3. Design principles

### 3.1 Pipeline over monolith

The system must be implemented as explicit stages.

Each stage:

* Reads well-defined input artifacts
* Writes immutable or replaceable output artifacts
* Produces logs and metrics
* Can be rerun independently
* Can be skipped when outputs are still valid

### 3.2 Parser and renderer separation

MediaWiki parsing must not directly emit EPWING records.

The system first generates a normalized intermediate representation.

```text
Wikimedia dump
    ↓
Parsed article model
    ↓
Normalized article model
    ↓
Rendered dictionary entry
    ↓
EPWING source
    ↓
EPWING binary
```

### 3.3 Deterministic builds

Given identical:

* Source code
* Configuration
* Dump files
* Image files
* Toolchain image

the generated logical dictionary contents should be identical.

Timestamps and archive metadata may be normalized where necessary.

### 3.4 Graceful degradation

Unsupported markup must not abort the entire build.

Preferred behavior:

1. Render supported content.
2. Replace unsupported elements with readable fallback text.
3. Record the unsupported construct in diagnostics.
4. Continue processing.

### 3.5 No silent data loss

Every skipped article, template, image, table, formula, or malformed record must be counted.

Representative samples must be included in the final build report.

---

## 4. High-level architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         CLI / Orchestrator                   │
│  build / download / parse / render / package / verify       │
└───────────────────────────────┬──────────────────────────────┘
                                │
        ┌───────────────────────┼─────────────────────────┐
        │                       │                         │
        ▼                       ▼                         ▼
┌───────────────┐      ┌─────────────────┐       ┌────────────────┐
│ Dump Manager  │      │ Build Manifest  │       │ Cache Manager  │
│ download/hash │      │ stages/versions │       │ content cache  │
└───────┬───────┘      └─────────────────┘       └────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│                     MediaWiki Ingestion                      │
│ XML stream parser / page filter / revision extraction       │
└───────────────────────────────┬──────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    Article Normalization                     │
│ templates / redirects / links / sections / tables / math   │
└───────────────────────────────┬──────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    Intermediate Database                     │
│ SQLite or partitioned JSONL/MessagePack                     │
└───────────────┬───────────────────────────────┬──────────────┘
                │                               │
                ▼                               ▼
┌────────────────────────────┐      ┌──────────────────────────┐
│ Image and Media Pipeline   │      │ Search Index Pipeline    │
│ metadata/thumb/cache       │      │ headword/redirect/keyword│
└───────────────┬────────────┘      └────────────┬─────────────┘
                │                                │
                └───────────────┬────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                     EPWING Renderer                          │
│ article layout / references / graphics / menus             │
└───────────────────────────────┬──────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│              FreePWING / EB Toolchain Adapter               │
│ catalog / honmon / indexes / graphics / sound placeholders │
└───────────────────────────────┬──────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                    Packaging and Verification                │
│ ebzip / archive / smoke tests / report / checksums          │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Repository structure

```text
wikipedia-epwing/
├── AGENTS.md
├── ARCHITECTURE.md
├── PLAN.md
├── README.md
├── LICENSE
├── Makefile
├── compose.yaml
├── pyproject.toml
├── uv.lock
├── config/
│   ├── default.toml
│   ├── jawiki.toml
│   ├── enwiki.toml
│   ├── profiles/
│   │   ├── minimal.toml
│   │   ├── standard.toml
│   │   └── full.toml
│   └── template-rules/
│       ├── common.yaml
│       └── ja.yaml
├── docker/
│   ├── builder.Dockerfile
│   ├── toolchain.Dockerfile
│   └── scripts/
├── src/
│   └── wikiepwing/
│       ├── cli.py
│       ├── config.py
│       ├── manifest.py
│       ├── logging.py
│       ├── pipeline/
│       │   ├── orchestrator.py
│       │   ├── stage.py
│       │   └── cache.py
│       ├── dump/
│       │   ├── downloader.py
│       │   ├── checksum.py
│       │   └── xml_reader.py
│       ├── mediawiki/
│       │   ├── parser.py
│       │   ├── templates.py
│       │   ├── redirects.py
│       │   ├── links.py
│       │   ├── tables.py
│       │   ├── math.py
│       │   └── namespaces.py
│       ├── model/
│       │   ├── article.py
│       │   ├── block.py
│       │   ├── inline.py
│       │   ├── media.py
│       │   └── diagnostics.py
│       ├── storage/
│       │   ├── database.py
│       │   ├── schema.sql
│       │   └── partitions.py
│       ├── media/
│       │   ├── commons.py
│       │   ├── downloader.py
│       │   ├── converter.py
│       │   └── cache.py
│       ├── search/
│       │   ├── headwords.py
│       │   ├── redirects.py
│       │   ├── aliases.py
│       │   └── keywords.py
│       ├── render/
│       │   ├── article.py
│       │   ├── text.py
│       │   ├── tables.py
│       │   ├── infobox.py
│       │   ├── references.py
│       │   └── epwing_source.py
│       ├── epwing/
│       │   ├── freepwing.py
│       │   ├── catalog.py
│       │   ├── graphics.py
│       │   ├── indexes.py
│       │   └── package.py
│       └── verify/
│           ├── structure.py
│           ├── content.py
│           ├── encoding.py
│           └── report.py
├── patches/
│   ├── freepwing/
│   ├── eb/
│   └── legacy/
├── scripts/
│   ├── build.sh
│   ├── smoke-test.sh
│   └── inspect-entry.sh
├── tests/
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   ├── snapshot/
│   └── end_to_end/
├── work/
│   └── .gitkeep
└── output/
    └── .gitkeep
```

---

## 6. Technology choices

### 6.1 Primary implementation language

Use Python 3.12 or a later version explicitly pinned in the Docker image.

Reasons:

* Mature streaming XML parsers
* Mature MediaWiki parsing libraries
* Easy Unicode handling
* Good image and archive tooling
* Fast enough when streaming and batching are used
* Easier maintenance than extending old Perl code
* Good compatibility with Codex-assisted development

The architecture must permit performance-critical stages to be replaced by Rust later.

### 6.2 Package management

Use `uv` with a committed lockfile.

All Python dependencies must be pinned.

### 6.3 MediaWiki parsing

Start with `mwparserfromhell` for syntactic parsing.

Do not assume it renders templates semantically.

Template handling must be implemented as a separate rule system.

Potential future alternatives:

* `wikitextparser`
* Parsoid output
* A Rust parser
* MediaWiki API-assisted template expansion

### 6.4 Intermediate storage

Use SQLite initially.

Reasons:

* One-file artifact
* Transactional
* Searchable during debugging
* Supports resumable stages
* Supports indexes
* Available everywhere
* Adequate for sequential bulk import

SQLite configuration:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 8589934592;
```

For very large builds, split data into shards by page ID range or normalized title prefix.

### 6.5 Container base

Use Debian, not Alpine.

Preferred base:

```text
debian:bookworm-slim
```

Create a dedicated toolchain image containing:

* FreePWING
* EB Library
* ebzip
* ImageMagick
* librsvg
* fonts
* TeX or Math rendering tools where required
* patched legacy dependencies

Pin downloaded source archives by URL and SHA-256.

---

## 7. Core domain model

The parser must produce a semantic intermediate model rather than HTML.

### 7.1 Article

```python
@dataclass(frozen=True)
class Article:
    page_id: int
    revision_id: int
    title: str
    normalized_title: str
    namespace: int
    redirect_target: str | None
    language: str
    blocks: tuple["Block", ...]
    categories: tuple[str, ...]
    aliases: tuple[str, ...]
    media: tuple["MediaReference", ...]
    diagnostics: tuple["Diagnostic", ...]
```

### 7.2 Block types

```text
Paragraph
Heading
ListBlock
DefinitionList
QuoteBlock
CodeBlock
PreformattedBlock
TableBlock
InfoboxBlock
ImageBlock
MathBlock
HorizontalRule
ReferenceList
NoticeBlock
UnsupportedBlock
```

### 7.3 Inline types

```text
Text
Emphasis
Strong
InternalLink
ExternalLink
Ruby
Code
MathInline
LineBreak
UnsupportedInline
```

### 7.4 Diagnostics

Every recoverable parser or renderer issue must use structured diagnostics.

```python
@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Literal["info", "warning", "error"]
    page_id: int
    title: str
    message: str
    source_fragment: str | None
```

Diagnostic codes must be stable and documented.

Examples:

```text
TEMPLATE_UNSUPPORTED
TABLE_COLUMN_OVERFLOW
IMAGE_METADATA_MISSING
INVALID_INTERNAL_LINK
UNSUPPORTED_UNICODE
ENTRY_SIZE_EXCEEDED
```

---

## 8. Pipeline stages

## 8.1 Stage 00: environment inspection

Validate:

* Docker architecture
* Disk availability
* Memory availability
* Required executable versions
* Locale
* Writable work directories
* Current configuration

Output:

```text
work/manifest/environment.json
```

## 8.2 Stage 01: dump acquisition

Download:

* `pages-articles-multistream.xml.bz2`
* multistream index
* optional page metadata
* optional image metadata
* dump checksums

Features:

* Resume partial downloads
* Verify checksums
* Record exact source URLs
* Never silently use a partially downloaded file

## 8.3 Stage 02: raw page extraction

Stream the XML dump.

Do not fully decompress the dump to disk unless explicitly configured.

Extract:

* Page ID
* Namespace
* Title
* Latest revision ID
* Latest revision text
* Redirect information

Write raw records into SQLite or compressed partition files.

## 8.4 Stage 03: title and redirect graph

Build:

* Canonical title table
* Redirect map
* Case normalization map
* Namespace map
* Alias candidates
* Disambiguation markers

Resolve redirect chains with cycle detection.

## 8.5 Stage 04: article parsing

Convert Wikitext into the intermediate article model.

Operations:

* Parse sections
* Parse paragraphs
* Parse links
* Parse lists
* Parse tables
* Detect infoboxes
* Detect image references
* Detect math
* Extract categories
* Extract display-title aliases
* Remove maintenance markup
* Record unsupported templates

The stage must support parallel workers with deterministic output ordering.

## 8.6 Stage 05: template normalization

Templates are classified into:

1. Semantic templates
2. Formatting templates
3. Navigation templates
4. Maintenance templates
5. Infobox templates
6. Citation templates
7. Unknown templates

Rule examples:

```yaml
templates:
  - pattern: "^Infobox"
    action: infobox

  - names:
      - 要出典
      - 出典の明記
      - Cleanup
    action: drop

  - names:
      - 仮リンク
    action: internal_link

  - pattern: "^Cite "
    action: citation
```

Unknown templates should usually degrade to selected positional or named argument text rather than disappear entirely.

## 8.7 Stage 06: image resolution

Resolve image references to Wikimedia Commons or local project files.

Policy options:

```toml
[images]
enabled = true
max_per_article = 4
thumbnail_width = 320
thumbnail_height = 320
max_file_bytes = 2000000
formats = ["jpeg", "png"]
```

The image pipeline must:

* Cache by content hash
* Respect redirects
* Generate thumbnails
* Convert unsupported formats
* Strip metadata
* Record attribution information
* Avoid duplicate images
* Permit image-free builds

SVG should normally be rasterized.

Animated media should use a static preview frame.

## 8.8 Stage 07: table normalization

Convert Wiki tables into structured rows and cells.

Rendering policy:

* Small tables: text grid or compact EPWING layout
* Wide tables: row-oriented key/value representation
* Complex tables: simplified readable fallback
* Nested tables: flatten where practical
* Style attributes: mostly ignored

The renderer must prioritize readable content over visual fidelity.

## 8.9 Stage 08: mathematical formulas

Preferred pipeline:

```text
TeX source
    ↓
KaTeX/LaTeX renderer
    ↓
SVG
    ↓
monochrome or grayscale bitmap
    ↓
EPWING graphic
```

Fallback:

* Preserve original TeX as text
* Record a diagnostic

Formula output must remain readable in monochrome viewers.

## 8.10 Stage 09: entry rendering

Generate an EPWING-oriented logical entry.

Recommended article layout:

```text
Article title
Pronunciation or aliases
Short metadata line

Lead section

1. Heading
   Body

2. Heading
   Body

Categories
Related articles
Source metadata
```

References should use internal EPWING links where possible.

External URLs may be retained as plain text based on profile settings.

## 8.11 Stage 10: index generation

Generate indexes for:

* Exact article titles
* Normalized article titles
* Redirect titles
* Alternate titles
* Japanese readings where available
* Latin aliases
* Optional keywords
* Optional category lookup

Avoid generating unbounded keyword indexes during the first implementation.

Headword normalization must be language-specific.

Japanese normalization may include:

* Unicode NFKC
* Full-width and half-width normalization
* Hiragana and Katakana variants
* Latin case folding
* Space normalization
* Optional punctuation removal

## 8.12 Stage 11: EPWING source generation

Convert rendered entries and indexes into FreePWING-compatible input.

The FreePWING adapter must be isolated behind an interface.

```python
class EpwingBackend(Protocol):
    def write_entry(self, entry: RenderedEntry) -> None: ...
    def write_index(self, index: SearchIndex) -> None: ...
    def write_graphic(self, image: RenderedImage) -> None: ...
    def finalize(self) -> Path: ...
```

This permits future replacement of FreePWING.

## 8.13 Stage 12: package and compression

Run:

* FreePWING generation
* structural validation
* `ebzip -l 5`
* checksum generation
* archive creation

Output example:

```text
output/
├── jawiki-20260701-epwing-full.zip
├── jawiki-20260701-epwing-full.zip.sha256
├── jawiki-20260701-build-report.json
├── jawiki-20260701-build-report.html
└── jawiki-20260701-manifest.json
```

## 8.14 Stage 13: verification

Verification must include:

* EPWING directory structure
* Catalog readability
* Index readability
* Entry count
* Redirect count
* Image count
* Missing link count
* Invalid character count
* Random article sampling
* Fixed regression article set
* Archive checksum

Where possible, use EB Library command-line utilities to inspect generated entries.

---

## 9. Build profiles

### 9.1 Minimal

```text
Article text
Headword search
Redirect search
No images
No formulas as graphics
Simplified tables
```

### 9.2 Standard

```text
Article text
Headword and redirect search
Selected images
Tables
Infoboxes
Math graphics
Cross references
```

### 9.3 Full

```text
Standard profile
More images
More aliases
Category metadata
Keyword index
References
Additional diagnostic metadata
```

Profiles must be configuration only. They must not fork the implementation.

---

## 10. CLI contract

Primary commands:

```bash
wikiepwing doctor
wikiepwing download
wikiepwing parse
wikiepwing normalize
wikiepwing media
wikiepwing render
wikiepwing generate
wikiepwing verify
wikiepwing package
wikiepwing build
wikiepwing inspect "Emacs"
wikiepwing report
```

Typical build:

```bash
docker compose run --rm builder \
  wikiepwing build \
  --config config/jawiki.toml \
  --profile standard
```

Resume:

```bash
docker compose run --rm builder \
  wikiepwing build \
  --resume
```

Rebuild one stage:

```bash
wikiepwing build --from-stage render
```

Small fixture build:

```bash
wikiepwing build \
  --fixture tests/fixtures/jawiki-small.xml \
  --profile standard
```

---

## 11. Manifest and stage cache

Each stage must write a manifest.

```json
{
  "stage": "parse",
  "version": 3,
  "input_hashes": {
    "dump": "sha256:..."
  },
  "config_hash": "sha256:...",
  "code_version": "git:...",
  "started_at": "...",
  "completed_at": "...",
  "record_count": 1234567,
  "status": "complete"
}
```

A stage is reusable only when:

* Stage version matches
* Input hashes match
* Relevant configuration hash matches
* Output files exist
* Completion status is valid

Do not use file timestamps alone for cache validity.

---

## 12. Docker architecture

Use two images.

### 12.1 Toolchain image

Contains slow-changing native dependencies:

```text
FreePWING
EB Library
ebzip
ImageMagick
SVG renderer
font packages
legacy patches
```

### 12.2 Application image

Contains:

```text
Python runtime
locked dependencies
project source
CLI
```

Example volume design:

```yaml
services:
  builder:
    build:
      context: .
      dockerfile: docker/builder.Dockerfile
    volumes:
      - wiki-dumps:/data/dumps
      - wiki-work:/data/work
      - wiki-cache:/data/cache
      - ./output:/data/output
      - ./config:/app/config:ro

volumes:
  wiki-dumps:
  wiki-work:
  wiki-cache:
```

Do not place high-I/O intermediate files in macOS bind mounts.

Only final output, logs, and selected reports should be written to bind-mounted host directories.

---

## 13. Resource management

The pipeline must support configured limits.

```toml
[resources]
workers = 12
memory_limit_gb = 64
sqlite_cache_mb = 8192
image_workers = 8
download_workers = 4
```

Do not default to using all cores or all memory.

Large stages must stream data and commit in batches.

A stage should report:

* Records per second
* Estimated remaining records
* Current memory use where available
* Current partition
* Error count

---

## 14. Testing strategy

### 14.1 Unit tests

Cover:

* Title normalization
* Redirect resolution
* Template rules
* Link conversion
* Table parsing
* Image selection
* Character sanitization
* Index key generation

### 14.2 Snapshot tests

Maintain expected normalized and rendered output for representative articles.

Fixtures should include:

* Japanese article
* Redirect
* Disambiguation page
* Infobox-heavy article
* Table-heavy article
* Math-heavy article
* Image-heavy article
* Article containing uncommon Unicode
* Deeply nested templates
* Malformed Wikitext

### 14.3 Integration tests

Run:

```text
fixture XML
    ↓
parse
    ↓
normalize
    ↓
render
    ↓
EPWING generation
    ↓
verification
```

### 14.4 Full-build smoke tests

After a real build, inspect a stable regression list.

Suggested Japanese articles:

```text
日本
東京都
Emacs
Linux
源氏物語
量子力学
微分積分学
第二次世界大戦
曖昧さ回避
```

Do not assume current article text. Verify structural properties instead.

---

## 15. Observability

Use structured JSON logs in addition to human-readable console output.

Each log event should include:

```text
timestamp
level
stage
page_id
title
diagnostic_code
message
```

Final reports must include:

* Source dump date
* Source dump checksum
* Git commit
* Container image digest
* Configuration
* Article counts
* Redirect counts
* Image counts
* Table counts
* Formula counts
* Unsupported template counts
* Skipped page counts
* Build duration by stage
* Output file sizes
* Verification results

---

## 16. Licensing and attribution

Wikipedia text is generally distributed under CC BY-SA and may also contain GFDL-licensed history.

The build must include:

* Wikimedia source attribution
* Dump date
* Project URL
* License notices
* Build tool source information
* Image attribution metadata where practical

Do not claim that the generated archive itself changes the licensing of the underlying content.

The project repository license applies only to project source code, not to generated Wikipedia content.

Image licensing is more complicated than text licensing.

For the initial release:

* Include only thumbnails whose source metadata is recorded.
* Generate an attribution database or text appendix.
* Allow users to disable all images.
* Avoid distributing generated image archives publicly until licensing output has been reviewed.

---

## 17. Security

Treat dump content and image files as untrusted input.

Requirements:

* Never execute Wikitext.
* Never execute Lua from templates.
* Disable ImageMagick delegates that can invoke external commands.
* Limit decompression sizes.
* Limit image dimensions and file sizes.
* Use request timeouts.
* Validate downloaded MIME types.
* Prevent path traversal.
* Avoid shell interpolation.
* Run the container as a non-root user.
* Use read-only mounts where possible.

---

## 18. Compatibility strategy

The project must not expose FreePWING-specific details throughout the parser.

FreePWING compatibility belongs only in:

```text
src/wikiepwing/epwing/
```

If legacy tools fail on a newer Debian version, preserve a known-working toolchain image.

The application layer should communicate with the toolchain through files or a stable subprocess interface.

---

## 19. Architectural decisions

### ADR-001: Use a normalized intermediate model

Accepted.

Reason:

Direct Wikitext-to-EPWING conversion makes parsing, rendering, and testing inseparable.

### ADR-002: Use SQLite as initial intermediate storage

Accepted.

Reason:

It provides durability, debugging, indexing, and resumability without running a database server.

### ADR-003: Replace legacy Perl parsing with Python

Accepted.

Reason:

Legacy Perl code may remain as a compatibility reference, but new parsing and normalization logic should be maintainable and testable.

### ADR-004: Keep FreePWING as the first backend

Accepted with isolation.

Reason:

It is a proven path to valid EPWING output, but should not dictate the whole architecture.

### ADR-005: Use Docker named volumes for intermediate data

Accepted.

Reason:

Large intermediate I/O performs poorly through Docker Desktop bind mounts.

### ADR-006: Do not implement full template expansion initially

Accepted.

Reason:

Complete MediaWiki template and Lua execution is too large and creates security and reproducibility problems.

---

## 20. Definition of architectural success

The architecture is successful when:

1. A small fixture dump builds into a readable EPWING dictionary.
2. The same fixture produces equivalent output on macOS and Linux.
3. A failed build resumes at the failed stage.
4. Unsupported templates are reported instead of silently discarded.
5. Article parsing can be tested without FreePWING.
6. EPWING generation can be tested without downloading Wikipedia.
7. Images can be disabled without altering parser behavior.
8. A complete Japanese Wikipedia build can finish without manual intervention.
9. Build inputs and outputs are fully traceable from the manifest.
10. The generated dictionary can be opened by at least two independent EPWING readers.


