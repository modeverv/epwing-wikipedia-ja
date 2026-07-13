# PLAN.md

# Wikipedia EPWING Builder Implementation Plan

## 1. Objective

Build a reproducible Docker-based system that converts a current Japanese Wikipedia dump into a high-functionality EPWING dictionary.

The project should first prove correctness with a small fixture and then scale to the complete Japanese Wikipedia dump.

The implementation must favor:

* Testable stages
* Resumable builds
* Explicit diagnostics
* Stable intermediate formats
* Practical dictionary readability
* Reproducibility

Do not begin by attempting a complete Wikipedia build.

---

## 2. Delivery strategy

Development is divided into milestones.

Each milestone must end with:

* Working code
* Tests
* Documented commands
* Machine-readable outputs
* No known critical errors

Milestones should be completed in order unless a later milestone is needed to unblock verification.

---

## 3. Phase 0: repository and execution skeleton

**Status: completed (2026-07-13).** The Docker builder, validated TOML
configuration, `wikiepwing doctor`, and the documented test/lint/typecheck
commands are implemented and verified in the non-root container.

### Goal

Create a project that starts consistently in Docker and exposes an empty but functional CLI.

### Tasks

* Create the repository structure from `ARCHITECTURE.md`.
* Add `pyproject.toml`.
* Configure `uv`.
* Add Python linting and formatting.
* Add type checking.
* Add pytest.
* Add `compose.yaml`.
* Add a non-root container user.
* Create the `wikiepwing` CLI.
* Create structured logging.
* Create configuration loading from TOML.
* Add `wikiepwing doctor`.
* Add a Makefile with common commands.

### Commands to support

```bash
make build-image
make test
make lint
make doctor
```

### Acceptance criteria

* `docker compose build` succeeds.
* `docker compose run --rm builder wikiepwing doctor` succeeds.
* Unit test command succeeds.
* The container writes only to declared data directories.
* The container process does not run as root.

---

## 4. Phase 1: legacy EPWING toolchain proof

**Status: completed for the automated structural proof (2026-07-13).** The
checksum-verified FreePWING 1.5 and EB Library 4.4.3 Docker toolchain builds a
deterministic three-entry dictionary, compresses it with `ebzip`, packages it,
and independently validates the extracted catalog with EB Library. Manual
opening in an external graphical EPWING reader remains a release gate.

### Goal

Prove that the container can generate and compress a minimal EPWING dictionary.

This phase isolates toolchain risk before Wikipedia parsing begins.

### Tasks

* Build FreePWING from a pinned source archive.
* Build EB Library and `ebzip`.
* Store SHA-256 checksums for every downloaded archive.
* Apply required compatibility patches.
* Create a tiny handcrafted dictionary with 3–10 entries.
* Generate EPWING output.
* Compress it with `ebzip`.
* Verify the catalog and entry count with EB tools.
* Package it as a ZIP file.

### Sample entries

```text
Emacs
Linux
Wikipedia
```

Each entry should include:

* Heading
* Body paragraph
* Internal cross-reference
* One small image if practical

### Acceptance criteria

* The generated dictionary opens in an EPWING reader.
* `ebzip` compression succeeds.
* Two entries can reference each other.
* The generated catalog contains the expected subbook.
* A toolchain image can be rebuilt from scratch.
* Source archive checksums are verified.
* Toolchain versions appear in the build manifest.

### Stop condition

Do not proceed until the minimal dictionary has been manually opened successfully.

---

## 5. Phase 2: dump acquisition

**Status: completed (2026-07-13).** The downloader resolves stable dump URLs,
parses Wikimedia SHA-1 sidecars, resumes locked partial transfers, bounds
retries, verifies final content, supports no-copy local registration, and writes
an atomic source manifest. HTTP Range behavior is covered by a response fixture.

### Goal

Reliably obtain and verify Wikimedia dump files.

### Tasks

* Implement dump URL resolution.
* Download dump checksum files.
* Implement resumable HTTP downloads.
* Verify SHA-1 or SHA-256 according to Wikimedia metadata.
* Record source URLs and checksums.
* Support local predownloaded dump files.
* Add file locking to prevent concurrent duplicate downloads.
* Add disk-space preflight checks.

### CLI

```bash
wikiepwing download --project jawiki --date latest
wikiepwing download --project jawiki --date 20260701
wikiepwing download --local /data/import/jawiki.xml.bz2
```

### Acceptance criteria

* Interrupted downloads can resume.
* A corrupted file is rejected.
* A local dump can be registered without copying.
* The manifest records the exact dump date and checksum.
* No code assumes that `latest` remains unchanged after download.

---

## 6. Phase 3: streaming XML ingestion

### Goal

Parse Wikimedia XML without fully expanding it to disk.

### Tasks

* Implement a streaming XML parser.
* Extract page ID, title, namespace, revision ID, and Wikitext.
* Detect redirects.
* Filter namespaces based on configuration.
* Store raw page records in SQLite.
* Commit records in configurable batches.
* Add progress reporting.
* Add malformed-page diagnostics.
* Create a synthetic fixture XML.
* Create a small real-world fixture containing representative Japanese articles.

### Database tables

At minimum:

```sql
raw_pages
build_diagnostics
stage_metadata
```

### Acceptance criteria

* Memory use remains bounded while parsing.
* The fixture produces the expected page count.
* Redirect pages are identified.
* Namespace filtering works.
* The stage can be interrupted and rerun safely.
* A duplicate page ID cannot silently overwrite unrelated data.
* Parsing speed and record count are reported.

---

## 7. Phase 4: title normalization and redirect graph

### Goal

Create stable article identities and search aliases.

### Tasks

* Normalize Unicode using NFKC.
* Normalize whitespace.
* Implement project-aware title normalization.
* Parse redirect targets.
* Resolve redirect chains.
* Detect redirect cycles.
* Generate aliases from redirects.
* Detect disambiguation pages where practical.
* Build indexes on normalized titles.

### Acceptance criteria

* One-step redirects resolve.
* Multi-step redirects resolve.
* Redirect cycles are reported.
* Broken redirect targets are reported.
* Exact original titles are preserved.
* Search normalization does not destroy Japanese distinctions unnecessarily.

---

## 8. Phase 5: intermediate article model

### Goal

Define and serialize the normalized semantic model.

### Tasks

* Implement article, block, inline, media, and diagnostic dataclasses.
* Add schema versioning.
* Add JSON serialization for debugging.
* Add database serialization.
* Add stable ordering rules.
* Add model validation.
* Create snapshot tests.

### Acceptance criteria

* A parsed article round-trips through storage.
* Schema version is recorded.
* Invalid block nesting is rejected.
* Serialization output is deterministic.
* Snapshot changes require intentional test updates.

---

## 9. Phase 6: baseline Wikitext parsing

### Goal

Render ordinary text-heavy articles correctly.

### Supported initially

* Paragraphs
* Headings
* Bold and italic text
* Internal links
* External links
* Ordered lists
* Unordered lists
* Definition lists
* Preformatted text
* Horizontal rules
* Categories
* Basic HTML entities
* Basic `<br>` handling

### Tasks

* Integrate `mwparserfromhell`.
* Convert parse nodes into the internal model.
* Resolve internal links against canonical titles.
* Preserve readable anchor text.
* Drop comments.
* Normalize whitespace.
* Sanitize unsupported control characters.
* Produce diagnostics for unsupported nodes.

### Acceptance criteria

* Text-heavy fixture articles render readably.
* Internal links point to canonical targets.
* Missing targets remain readable.
* Unsupported markup does not terminate the build.
* Article sections preserve source order.
* Parser tests cover malformed Wikitext.

---

## 10. Phase 7: template rule engine

### Goal

Handle common templates without implementing full MediaWiki execution.

### Tasks

* Define YAML rule format.
* Implement exact-name and regular-expression matching.
* Support actions:

```text
drop
keep_arguments
format_text
internal_link
external_link
notice
citation
infobox
custom_handler
```

* Add Japanese maintenance-template rules.
* Add link-related template rules.
* Add date and unit formatting rules where simple.
* Count unknown templates.
* Produce a top-unknown-template report.

### Initial strategy

Implement common templates according to frequency.

Do not attempt hundreds of templates before collecting statistics from a real sample.

### Acceptance criteria

* Rule loading is validated.
* Unknown templates have readable fallback behavior.
* Maintenance templates can be removed.
* Template frequency reporting works.
* Rule changes are testable without rerunning XML ingestion.

---

## 11. Phase 8: EPWING text-only vertical slice

### Goal

Generate a usable text-only Wikipedia EPWING from a small fixture.

### Tasks

* Implement article-to-entry rendering.
* Generate FreePWING input.
* Create title and redirect indexes.
* Generate catalog metadata.
* Build EPWING.
* Compress with `ebzip`.
* Verify generated entries.
* Add `wikiepwing inspect`.

### CLI

```bash
wikiepwing build \
  --fixture tests/fixtures/jawiki-small.xml \
  --profile minimal
```

### Acceptance criteria

* At least 100 fixture articles build successfully.
* Exact-title search works.
* Redirect search works.
* Cross-references work.
* Japanese characters render correctly.
* No manual file editing is required after generation.
* The dictionary opens in two readers where available.

### Important checkpoint

This is the first complete vertical slice.

Do not add images or complex tables before this milestone is stable.

---

## 12. Phase 9: table support

### Goal

Preserve the information content of Wikipedia tables.

### Tasks

* Parse Wiki table syntax into rows and cells.
* Support row and column spans in the model.
* Strip nonessential CSS.
* Detect narrow and wide tables.
* Implement compact table rendering.
* Implement row-oriented fallback rendering.
* Limit maximum table size.
* Add diagnostics for malformed tables.
* Add snapshot fixtures.

### Rendering rules

For narrow tables:

```text
Year | Event | Result
2024 | Example | Success
```

For wide tables:

```text
Row 1
  Year: 2024
  Event: Example
  Result: Success
```

### Acceptance criteria

* Simple tables preserve headers and cells.
* Wide tables remain readable.
* Malformed tables do not abort article generation.
* Very large tables are truncated or summarized according to configuration.
* Truncation is reported.

---

## 13. Phase 10: infobox support

### Goal

Present important article metadata near the beginning of entries.

### Tasks

* Detect infobox templates.
* Preserve selected key/value fields.
* Ignore style-only fields.
* Normalize nested links.
* Resolve image fields through the media pipeline.
* Add per-template field preference rules.
* Provide a generic fallback for unknown infobox types.

### Acceptance criteria

* Common Japanese person, location, software, and organization infoboxes render.
* Empty fields are removed.
* Internal links in values remain functional.
* Infoboxes do not overwhelm the lead section.
* Unknown infoboxes degrade into generic key/value metadata.

---

## 14. Phase 11: image pipeline

### Goal

Include selected article images in a reproducible and legally traceable manner.

### Tasks

* Extract image references during parsing.
* Resolve image metadata.
* Resolve Commons redirects.
* Download thumbnails only.
* Cache source files.
* Convert SVG to raster.
* Convert unsupported formats.
* Limit dimensions and size.
* Deduplicate by content hash.
* Generate attribution metadata.
* Map graphics into EPWING resources.
* Add image-free configuration.

### Image selection policy

Initial default:

1. Lead image
2. Infobox image
3. First meaningful article image
4. Hard limit per article

Skip:

* Icons
* Flags used decoratively
* Maintenance graphics
* Tiny images
* Tracking pixels
* Most navigation images

### Acceptance criteria

* A fixture article includes at least one image.
* Duplicate images are stored once.
* Missing images do not break article generation.
* Image source and license metadata are recorded where available.
* The full pipeline can run with images disabled.
* The ImageMagick policy forbids unsafe delegates.

---

## 15. Phase 12: math support

### Goal

Render common mathematical formulas as EPWING-compatible graphics.

### Tasks

* Extract TeX source.
* Render using a pinned toolchain.
* Rasterize to a viewer-friendly format.
* Cache formulas by source hash.
* Generate inline and block formula layouts.
* Fall back to textual TeX.
* Add formula diagnostics.

### Acceptance criteria

* Inline formulas render.
* Block formulas render.
* Duplicate formulas are cached.
* Invalid TeX falls back to text.
* Formula rendering is deterministic.
* Mathematical articles remain navigable.

---

## 16. Phase 13: enhanced search indexes

### Goal

Provide practical dictionary search beyond exact page titles.

### Tasks

* Index redirects.
* Index aliases.
* Index normalized title variants.
* Generate Hiragana/Katakana variants.
* Generate Latin case-folded variants.
* Support optional category lookup.
* Evaluate keyword search feasibility.
* Enforce index-size limits.
* Report collisions.

### Keyword search approach

Do not immediately index every word in every article.

Evaluate these options:

1. Lead-section keywords only
2. Section-title keywords
3. Category names
4. High-information noun extraction
5. A separate reduced full-text subbook

Implement exact-title and alias search first.

### Acceptance criteria

* Redirect titles find the canonical article.
* Kana variants work for configured cases.
* Alias collisions are deterministic.
* Index generation does not exceed configured limits.
* Index statistics appear in the report.

---

## 17. Phase 14: complete Japanese Wikipedia trial build

### Goal

Run the complete pipeline against a current Japanese Wikipedia dump.

### Preparation

Before starting:

* Confirm at least 200 GB free space.
* Set Docker disk image limit appropriately.
* Use named volumes.
* Disable images for the first complete trial.
* Set a conservative worker count.
* Persist logs outside ephemeral containers.

### First full-build profile

Use:

```text
Text
Headwords
Redirects
Basic tables
Basic infoboxes
No images
Math as text fallback
No full-text keyword index
```

### Tasks

* Run all stages.
* Record stage durations.
* Record peak disk use.
* Record failure counts.
* Inspect top unsupported templates.
* Inspect encoding failures.
* Inspect largest entries.
* Inspect random articles.
* Verify final dictionary structure.

### Acceptance criteria

* The build completes without manual intervention.
* At least 99.9% of eligible articles produce entries or a documented skip reason.
* No fatal encoding errors remain.
* The generated archive opens successfully.
* A fixed regression set is readable.
* Redirect searches work.
* Build manifest and report are complete.

---

## 18. Phase 15: quality iteration from real statistics

### Goal

Improve functionality based on actual failure frequencies.

### Tasks

Use the complete-build report to rank:

* Unknown templates
* Broken tables
* Missing links
* Oversized entries
* Unsupported Unicode
* Failed formulas
* Missing images
* Slowest article types

Implement fixes in descending impact order.

### Rule

Do not optimize rare constructs before high-frequency failures.

### Acceptance criteria

* Top unsupported-template count decreases substantially.
* Entry readability improves on sampled articles.
* No regression in previously supported fixtures.
* Build time does not regress without explanation.

---

## 19. Phase 16: image-enabled full build

### Goal

Generate the standard high-functionality dictionary.

### Tasks

* Enable selected thumbnails.
* Monitor cache size.
* Verify attribution output.
* Measure final EPWING graphics size.
* Tune image limits.
* Confirm reader compatibility.
* Add image-specific verification samples.

### Acceptance criteria

* Images appear in supported readers.
* Missing images do not cause broken entries.
* Attribution metadata is included.
* Output size remains within configured budget.
* Image cache is reusable across builds.

---

## 20. Phase 17: reproducibility verification

### Goal

Prove that the build can be repeated.

### Tasks

* Build the same fixture twice.
* Compare manifests.
* Compare logical entry hashes.
* Normalize non-deterministic archive metadata.
* Build on macOS Docker Desktop.
* Build on native Linux Docker.
* Compare logical outputs.
* Record expected platform-dependent binary differences.

### Acceptance criteria

* Fixture logical content hashes match.
* Index contents match.
* Entry counts match.
* Image hashes match.
* Any remaining binary differences are documented.
* Toolchain image digest is recorded.

---

## 21. Phase 18: update workflow

### Goal

Make monthly rebuilding routine.

### Tasks

* Add a command that resolves a requested dump date.
* Reuse cached images and formulas.
* Reuse toolchain images.
* Permit stage invalidation from changed inputs.
* Generate output names from source dump dates.
* Add old-work cleanup commands.
* Add disk-usage reporting.

### CLI

```bash
wikiepwing update --project jawiki --profile standard
wikiepwing clean --keep-builds 2
wikiepwing disk-usage
```

### Acceptance criteria

* A new dump can be built with one command.
* Existing source dumps are not redownloaded unnecessarily.
* Cache reuse is visible in metrics.
* Old build data can be removed safely.
* Final archives are never deleted by default.

---

## 22. Phase 19: English Wikipedia support

### Goal

Support English Wikipedia without coupling language-specific behavior to Japanese logic.

### Tasks

* Add `enwiki.toml`.
* Add English title normalization.
* Add English template rules.
* Add English namespace handling.
* Add English infobox policies.
* Test Simple English Wikipedia first.
* Evaluate full English Wikipedia storage and build time.

### Acceptance criteria

* Simple English Wikipedia builds successfully.
* Language-specific rules are configuration-driven where practical.
* Japanese builds remain unchanged.
* Full English Wikipedia can at least complete a minimal-profile trial.

---

## 23. Performance work

Performance optimization should begin only after profiling.

### Likely hotspots

* Wikitext parsing
* Template traversal
* SQLite writes
* Image downloads and conversion
* FreePWING generation
* Index sorting
* `ebzip`

### Optimization options

* Batch database inserts
* WAL mode
* Partitioned article processing
* Multiprocessing for CPU-bound parsing
* Asynchronous image downloads
* Content-addressed caches
* Rust replacement for XML or Wikitext parsing
* Pre-sorted index streams
* Native Linux builds for final production

### Prohibited optimization

Do not trade silent data corruption for speed.

---

## 24. Failure handling

All stages must classify failures.

### Fatal failures

Examples:

* Dump checksum mismatch
* Database corruption
* Missing required toolchain executable
* EPWING catalog generation failure
* Output filesystem full

Fatal failures stop the stage.

### Recoverable failures

Examples:

* One malformed article
* One unsupported template
* One unavailable image
* One invalid formula
* One broken internal link

Recoverable failures produce diagnostics and continue.

### Retryable failures

Examples:

* HTTP timeout
* Wikimedia 5xx response
* Temporary DNS failure

Use bounded retries with exponential backoff.

---

## 25. Codex working rules

Codex should follow these rules while implementing.

1. Read `ARCHITECTURE.md` before changing architecture.
2. Implement one milestone at a time.
3. Do not start a full Wikipedia build until the fixture vertical slice works.
4. Add tests with every parser or renderer feature.
5. Do not hide unsupported markup.
6. Do not add unpinned dependencies.
7. Do not place build artifacts in Git.
8. Do not broaden scope without updating documentation.
9. Preserve stage resumability.
10. Avoid shell commands constructed from untrusted article content.
11. Do not rewrite the entire pipeline to fix one stage.
12. Keep FreePWING-specific code inside the EPWING adapter.
13. Use typed data structures.
14. Prefer deterministic ordering.
15. Update the build report when adding a new diagnostic category.

---

## 26. Initial Codex task sequence

Codex should execute the first implementation in this order.

### Task 1

Create repository skeleton, Python package, CLI, configuration loader, tests, Docker image, and `doctor` command.

### Task 2

Build FreePWING and EB Library in Docker with pinned archives and checksums.

### Task 3

Generate a handcrafted three-entry EPWING dictionary.

### Task 4

Create and verify a compressed archive using `ebzip`.

### Task 5

Implement Wikimedia dump downloader and checksum verification.

### Task 6

Implement streaming XML parsing into SQLite.

### Task 7

Implement title normalization and redirect resolution.

### Task 8

Implement the intermediate article model.

### Task 9

Implement baseline Wikitext parsing.

### Task 10

Implement text-only article rendering and indexes.

### Task 11

Generate a fixture Wikipedia EPWING end to end.

Only after Task 11 succeeds should Codex begin table, infobox, image, and math work.

---

## 27. Release criteria for version 0.1

Version 0.1 is a text-first technical preview.

Required:

* Docker build
* Pinned legacy toolchain
* Japanese Wikipedia dump ingestion
* Text article parsing
* Headword search
* Redirect search
* Internal cross-references
* Resumable stages
* Minimal build report
* Complete fixture tests
* Successful limited real-dump build

Not required:

* Images
* Formula graphics
* Advanced tables
* Full English Wikipedia
* Keyword search

---

## 28. Release criteria for version 0.5

Version 0.5 is a practical personal-use release.

Required:

* Complete Japanese Wikipedia build
* Tables
* Generic infoboxes
* Selected images
* Formula fallback or rendering
* Enhanced aliases
* Detailed diagnostics
* Reproducibility manifest
* EPWING reader verification
* Monthly update command

---

## 29. Release criteria for version 1.0

Version 1.0 is a stable repeatable builder.

Required:

* Reliable Japanese full build
* Reliable Simple English build
* Documented full English limitations
* Image attribution output
* Stable configuration schema
* Stable intermediate schema or migration process
* Complete recovery and resume behavior
* Resource usage documentation
* Reproducibility verification
* Security review
* User-facing installation and build guide

---

## 30. Final definition of done

The project is done when a user can run:

```bash
git clone <repository>
cd wikipedia-epwing
docker compose build
docker compose run --rm builder \
  wikiepwing build \
  --project jawiki \
  --date latest \
  --profile standard
```

and receive:

```text
output/jawiki-YYYYMMDD-epwing-standard.zip
```

without manually installing FreePWING, Perl modules, EB Library, ImageMagick, or MediaWiki tooling on the host.

The resulting dictionary must:

* Open in common EPWING readers
* Search Japanese article titles
* Resolve redirects
* Navigate internal links
* Display readable article structure
* Preserve common tables and infoboxes
* Include selected images in the standard profile
* Record unsupported content
* Identify the exact Wikimedia dump and build toolchain used
