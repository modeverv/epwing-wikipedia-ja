# AGENTS.md

# Wikipedia EPWING Builder — Agent Instructions

## 1. Purpose of this file

This file defines the mandatory working rules for AI coding agents operating in this repository.

The project builds a reproducible, Docker-based system that converts current Wikimedia dumps into high-functionality EPWING/JIS X 4081 dictionaries.

The primary target is Japanese Wikipedia.

The system must remain:

* Reproducible
* Resumable
* Observable
* Testable
* Deterministic where practical
* Safe against untrusted dump content
* Independent of the host environment
* Maintainable without depending on undocumented legacy behavior

Agents must treat this file as binding project policy.

---

## 2. Required reading order

Before making changes, read these files in order:

1. `AGENTS.md`
2. `ARCHITECTURE.md`
3. `PLAN.md`
4. `README.md`
5. Relevant source files and tests

Do not begin implementation based only on an issue title or user prompt.

If the requested change conflicts with `ARCHITECTURE.md`, do not silently change the architecture.

Either:

* Implement the request within the existing architecture, or
* Update the architecture documentation explicitly as part of the same change

---

## 3. Source of truth

The following priority order applies when instructions conflict:

1. Explicit current user request
2. `AGENTS.md`
3. `ARCHITECTURE.md`
4. `PLAN.md`
5. Existing tests
6. Existing implementation
7. Comments and historical behavior

Existing code is not automatically correct merely because it exists.

Existing tests are not automatically correct if they contradict the documented architecture, but they must not be changed merely to make a broken implementation pass.

---

## 4. Primary development rule

Implement the smallest complete vertical improvement that satisfies the current milestone.

Do not attempt to build the entire system in one pass.

Prefer:

```text
small fixture
→ parser
→ normalized model
→ renderer
→ EPWING output
→ verification
```

over:

```text
large speculative implementation
→ full Wikipedia build
→ debugging thousands of unrelated failures
```

---

## 5. Milestone discipline

Follow the milestone order in `PLAN.md`.

The first required sequence is:

1. Repository and CLI skeleton
2. Docker toolchain
3. Handcrafted minimal EPWING dictionary
4. `ebzip` compression
5. Dump download and checksum verification
6. Streaming XML ingestion
7. Title and redirect normalization
8. Intermediate article model
9. Baseline Wikitext parser
10. Text-only renderer
11. Small end-to-end fixture build

Do not begin the following before the text-only vertical slice works:

* Image downloading
* Formula rendering
* Advanced table layout
* Large keyword indexes
* Full English Wikipedia
* Full Japanese Wikipedia production build

A complete Wikipedia build is not an acceptable substitute for unit and fixture testing.

---

## 6. Definition of a completed task

A task is complete only when all applicable conditions are met:

* Implementation is present
* Tests are present or updated
* Tests pass
* Type checking passes
* Linting passes
* Documentation is updated when behavior changes
* New configuration options are documented
* New diagnostics are documented
* Failure behavior is explicit
* No generated build artifacts are committed
* No unrelated files are modified
* The implementation works inside Docker
* The implementation does not require undocumented host setup

Do not report a task as complete merely because code was written.

---

## 7. Architecture boundaries

Maintain these boundaries.

### 7.1 MediaWiki ingestion

Responsible for:

* Reading Wikimedia XML
* Extracting page metadata
* Extracting revision text
* Detecting raw redirects
* Namespace filtering

It must not generate EPWING files.

### 7.2 MediaWiki parsing

Responsible for:

* Parsing Wikitext
* Producing semantic article structures
* Recording unsupported constructs
* Resolving syntax into the intermediate model

It must not know FreePWING output syntax.

### 7.3 Intermediate model

Responsible for:

* Representing articles
* Representing blocks and inline content
* Representing media references
* Representing diagnostics

It must remain independent of the EPWING backend.

### 7.4 Rendering

Responsible for:

* Turning semantic articles into logical dictionary entries
* Applying readable layout rules
* Simplifying tables and templates
* Preparing internal references

It must not invoke dump downloads or mutate source records.

### 7.5 EPWING adapter

All FreePWING-, EB Library-, and `ebzip`-specific behavior belongs under:

```text
src/wikiepwing/epwing/
```

Do not leak FreePWING-specific tags, path assumptions, encoding workarounds, or catalog rules throughout the parser.

### 7.6 Verification

Verification must inspect generated artifacts independently.

Do not consider generation success proof that the result is valid.

---

## 8. Pipeline stage rules

Every significant build stage must:

* Have a stable name
* Have a version
* Declare its inputs
* Declare its outputs
* Record input hashes
* Record relevant configuration hashes
* Write a completion manifest
* Support safe reruns
* Avoid treating partially written output as complete
* Emit structured progress information
* Emit structured diagnostics

A stage may be skipped only when its cache manifest proves that its outputs are valid.

File modification times alone are not sufficient cache validation.

---

## 9. Resumability requirements

Long-running operations must be resumable where practical.

Use these patterns:

* Atomic rename after successful file generation
* Transaction boundaries for database writes
* Batch checkpoints
* Stage completion manifests
* Content-addressed caches
* Explicit incomplete status
* Bounded retry state

Do not:

* Mark a stage complete before verification
* Reuse partially generated databases without checking status
* Delete valid previous output before replacement succeeds
* Depend on an in-memory-only progress state for long builds

---

## 10. Determinism requirements

Given identical inputs, configuration, code, and toolchain, logical output must be stable.

Always define deterministic ordering for:

* Articles
* Titles
* Redirect aliases
* Sections
* Diagnostic reports
* Images
* Index keys
* Archive file lists
* Generated metadata

Do not rely on:

* Dictionary iteration order without an explicit guarantee
* Filesystem enumeration order
* Process completion order
* Unordered SQL queries
* Current wall-clock time in logical content
* Random sampling without a fixed seed

When concurrency is used, reorder output deterministically before committing final artifacts.

---

## 11. No silent data loss

Unsupported or malformed content must never disappear silently.

When content cannot be represented:

1. Preserve readable text where possible.
2. Emit a structured diagnostic.
3. Continue processing if the failure is recoverable.
4. Count the occurrence in the final report.
5. Retain representative examples.

Examples of diagnostic conditions:

```text
TEMPLATE_UNSUPPORTED
TEMPLATE_ARGUMENT_DROPPED
TABLE_PARSE_FAILED
TABLE_TRUNCATED
IMAGE_METADATA_MISSING
IMAGE_DOWNLOAD_FAILED
MATH_RENDER_FAILED
INVALID_INTERNAL_LINK
REDIRECT_CYCLE
UNSUPPORTED_UNICODE
ENTRY_SIZE_EXCEEDED
ARTICLE_SKIPPED
```

Diagnostic identifiers are an API.

Do not rename or remove them casually.

---

## 12. Error classification

Classify failures as one of the following.

### Fatal

The stage cannot safely continue.

Examples:

* Dump checksum mismatch
* SQLite corruption
* Required executable missing
* Output filesystem full
* FreePWING generation failure
* Invalid build configuration
* Catalog verification failure

Fatal errors must stop the affected stage.

### Recoverable

One item failed, but the larger build can continue.

Examples:

* Unsupported template
* Invalid article markup
* Missing image
* Invalid formula
* Broken internal link

Recoverable failures must produce diagnostics.

### Retryable

The operation may succeed later.

Examples:

* Network timeout
* Temporary DNS failure
* Wikimedia HTTP 5xx response
* Rate limiting

Retryable operations must use:

* Bounded retries
* Exponential backoff
* Timeouts
* Final explicit failure reporting

Never retry indefinitely.

---

## 13. Docker requirements

The host must require only:

* Docker
* Docker Compose
* Sufficient disk space

Do not require host installation of:

* Python
* Perl
* FreePWING
* EB Library
* ImageMagick
* TeX
* Wikimedia tools

The container must:

* Run as a non-root user
* Use pinned base images where practical
* Use pinned dependencies
* Verify downloaded source archive checksums
* Store high-I/O working data in named volumes
* Write final artifacts to the designated output mount
* Avoid modifying the source tree during normal builds
* Use read-only configuration mounts where practical

Do not place large intermediate databases or millions of small files in macOS bind mounts.

Use named volumes for:

* Dumps
* Intermediate databases
* Media cache
* Formula cache
* Temporary FreePWING source
* Uncompressed EPWING output

Use bind mounts for:

* Source code during development
* Configuration
* Final archives
* Reports
* Explicitly requested logs

---

## 14. Toolchain rules

Legacy native tools must be isolated and reproducible.

For every external source archive:

* Pin the version
* Pin the URL
* Record the SHA-256 checksum
* Verify the checksum before extraction
* Record applied patches
* Record the resulting tool version

Do not download and execute unversioned install scripts.

Do not depend on mutable branches such as:

```text
main
master
latest
HEAD
```

unless the exact commit is recorded and checked out.

Patches must live under:

```text
patches/
```

Each patch must have:

* A descriptive filename
* A comment or adjacent documentation explaining why it exists
* A test or build step that proves it is still necessary

---

## 15. Dependency policy

All runtime and development dependencies must be pinned.

For Python:

* Use `uv`
* Commit `uv.lock`
* Add type annotations
* Avoid unnecessary dependencies
* Prefer maintained libraries
* Document why a substantial new dependency is needed

Before adding a dependency, determine whether the standard library or an existing dependency is sufficient.

Do not add multiple libraries that solve the same problem without justification.

Do not upgrade unrelated dependencies during a feature change.

---

## 16. Python coding rules

Use modern typed Python.

Required:

* Python 3.12 or the project-pinned version
* Type annotations for public functions
* Dataclasses or validated models for domain data
* `pathlib.Path` for filesystem paths
* Context managers for resources
* Explicit exceptions
* Structured logging
* Small modules with clear responsibilities

Avoid:

* Global mutable state
* Hidden singleton configuration
* Broad `except Exception` without rethrow or diagnostic
* Shell command strings assembled by concatenation
* Passing unstructured dictionaries throughout the domain layer
* Mixing parsing, database writes, and rendering in one function
* Functions with unclear side effects

Prefer immutable domain models where practical.

---

## 17. Database rules

SQLite is the initial intermediate store.

All schema changes must be explicit.

Required:

* Schema file or migration
* Primary keys
* Appropriate indexes
* Foreign-key policy documented
* Batched inserts
* Explicit transaction boundaries
* Deterministic queries
* Versioned schema metadata

Every query whose order matters must use `ORDER BY`.

Do not load the entire article database into memory.

Do not use an ORM unless the architecture is explicitly changed.

Prefer direct, parameterized SQL.

Never interpolate article content into SQL strings.

---

## 18. XML ingestion rules

Wikimedia dumps are large and untrusted.

The XML parser must:

* Stream records
* Keep bounded memory
* Reject unsafe entity expansion
* Avoid expanding the entire dump to disk by default
* Extract only required fields
* Release processed XML nodes
* Record malformed records
* Preserve page and revision identifiers

Do not parse the complete dump using an API that constructs the full XML tree.

Tests must include:

* Normal page
* Redirect
* Empty revision
* Non-main namespace
* Malformed or incomplete record
* Unicode title
* Large text field

---

## 19. Wikitext parsing rules

The parser produces the semantic intermediate model.

The parser must not attempt pixel-perfect Wikipedia rendering.

Prioritize:

1. Correct article text
2. Correct section structure
3. Correct internal links
4. Readable lists
5. Readable tables
6. Useful infobox fields
7. Selected images
8. Decorative formatting

Never execute:

* Lua modules
* Template code
* Arbitrary HTML scripts
* External commands derived from article content

Unknown templates must use a documented fallback.

Do not remove all unknown template content automatically.

Prefer preserving useful positional and named arguments as readable text.

---

## 20. Template support policy

Implement templates based on measured frequency and user value.

Before adding many template handlers:

1. Run the parser against a representative sample.
2. Produce the unknown-template frequency report.
3. Rank by occurrence count.
4. Implement the highest-impact templates first.
5. Add fixtures and tests.

Template behavior should normally be configuration-driven.

Use custom Python handlers only when declarative rules are insufficient.

A custom handler must:

* Be narrowly scoped
* Have tests
* Have fallback behavior
* Avoid network access
* Avoid global side effects

---

## 21. Rendering rules

EPWING output must prioritize readability on constrained viewers.

Preferred article layout:

```text
Title
Aliases or pronunciation
Compact metadata

Lead section

1. Heading
   Body

2. Heading
   Body

Categories
Related articles
Source metadata
```

Rendering must:

* Preserve source section order
* Limit excessive blank lines
* Avoid overly wide layouts
* Degrade tables to row-oriented text when necessary
* Keep link labels readable when targets are missing
* Avoid exposing raw parser internals
* Avoid dropping content solely because formatting is unsupported

Do not assume all readers support identical graphic or link behavior.

---

## 22. Search index rules

Implement search in this priority order:

1. Exact titles
2. Normalized titles
3. Redirect titles
4. Explicit aliases
5. Kana variants
6. Selected metadata
7. Optional keyword indexes

Do not implement an unbounded all-word index in the first version.

Index generation must:

* Be deterministic
* Report collisions
* Record entry counts
* Enforce configured limits
* Preserve the canonical article
* Handle aliases pointing to the same target
* Avoid silently overwriting duplicate keys

Japanese normalization rules must be independently tested.

---

## 23. Image pipeline rules

Images are optional.

The complete text-only build must work with all media functionality disabled.

Treat all image input as untrusted.

Required protections:

* Download timeout
* Maximum download size
* Maximum decoded dimensions
* MIME verification
* Filename sanitization
* Path traversal protection
* ImageMagick delegate restrictions
* SVG rasterization in a constrained environment
* Content-hash cache
* Duplicate suppression

Default selection should favor:

* Lead image
* Infobox image
* First meaningful content image

Default selection should reject or deprioritize:

* Decorative icons
* Maintenance graphics
* Tiny images
* Flags used only as icons
* Navigation images
* Duplicate images

Every distributed image should have traceable source metadata where practical.

---

## 24. Math pipeline rules

Formula rendering must be deterministic and cached.

Preferred process:

```text
TeX
→ pinned renderer
→ SVG
→ constrained raster image
→ EPWING graphic
```

If rendering fails:

* Preserve the TeX source as readable text
* Emit `MATH_RENDER_FAILED`
* Continue processing

Never execute shell commands constructed from formula content.

Formula cache keys must include:

* Formula source
* Renderer version
* Rendering configuration
* Font or style configuration when relevant

---

## 25. Security requirements

Wikimedia dumps, templates, links, filenames, and media files are untrusted.

Mandatory rules:

* Never execute content from the dump
* Never use `eval`
* Never invoke a shell with unescaped article content
* Prefer subprocess argument arrays
* Disable unsafe image delegates
* Prevent path traversal
* Limit decompression
* Limit file sizes
* Limit image dimensions
* Use network timeouts
* Validate redirect destinations
* Validate archive extraction paths
* Run as non-root
* Keep secrets out of images and logs
* Do not require credentials for normal public dump builds

Any security-relevant compromise must be documented explicitly.

---

## 26. Testing requirements

Every feature must have the smallest effective test.

### Unit tests

Required for:

* Title normalization
* Redirect resolution
* Template rules
* Internal link handling
* Table parsing
* Character sanitization
* Index generation
* Cache validation
* Manifest hashing

### Snapshot tests

Use for:

* Parsed article models
* Rendered article text
* Table fallback formatting
* Infobox formatting
* Diagnostics
* FreePWING source generation

Snapshot updates must be reviewed intentionally.

Do not update snapshots blindly to make tests pass.

### Integration tests

Must cover:

```text
fixture XML
→ ingestion
→ parsing
→ normalization
→ rendering
→ EPWING source
→ EPWING generation
→ verification
```

### Regression fixtures

Maintain representative fixtures for:

* Japanese prose
* Redirect chains
* Redirect cycles
* Disambiguation
* Infobox
* Wide table
* Nested template
* Math
* Images
* Unusual Unicode
* Malformed Wikitext
* Oversized entry
* Missing link

---

## 27. Test commands

Use repository-provided commands when available.

Expected commands include:

```bash
make test
make lint
make typecheck
make format-check
make integration-test
make smoke-test
```

Or their direct equivalents inside Docker:

```bash
docker compose run --rm builder pytest
docker compose run --rm builder ruff check .
docker compose run --rm builder mypy src
```

Do not claim tests passed unless they were actually run.

When a required test cannot run, report:

* The exact command
* The exact reason
* What was tested instead
* Remaining uncertainty

---

## 28. Full dump build restrictions

Do not run a complete Japanese or English Wikipedia build unless:

* The user explicitly requests it, or
* The current milestone requires it and all prerequisite acceptance criteria pass

Before a full build:

* Run `doctor`
* Confirm free disk space
* Confirm output paths
* Confirm toolchain versions
* Confirm dump checksum
* Run the small fixture build
* Run the limited real-sample build
* Persist logs
* Use resumable stages
* Use conservative parallelism

The first full Japanese build must use a reduced profile:

* Text
* Titles
* Redirects
* Basic tables
* Basic infoboxes
* No images
* Math fallback as text
* No full-text keyword index

Do not enable every optional feature during the first complete build.

---

## 29. Performance rules

Correctness comes before optimization.

Before optimizing:

1. Measure
2. Identify the bottleneck
3. Record baseline performance
4. Make one focused change
5. Re-run correctness tests
6. Compare performance

Do not introduce concurrency solely because a stage appears slow.

Concurrency must preserve:

* Deterministic output
* Bounded memory
* Safe database access
* Clear error reporting
* Resumability

Do not default to all CPU cores.

Resource usage must be configurable.

---

## 30. Logging and progress rules

Long-running stages must provide useful progress.

Progress reporting should include, where available:

* Stage name
* Processed record count
* Total record estimate
* Records per second
* Current partition
* Warning count
* Error count
* Cache hit count
* Output size

Do not log every successful article at normal verbosity.

Use structured JSON logs for machine analysis and concise console logs for humans.

Article-specific logs should include:

* Page ID
* Title
* Diagnostic code
* Severity
* Stage

Do not log full article contents by default.

---

## 31. Build report requirements

Every complete build must produce a machine-readable report.

The report must include:

* Wikimedia project
* Dump date
* Dump URL
* Dump checksum
* Git commit
* Container image digest
* Tool versions
* Configuration hash
* Stage durations
* Article count
* Redirect count
* Skipped-page count
* Image count
* Table count
* Formula count
* Diagnostic counts
* Top unknown templates
* Broken link count
* Output size
* Verification results

Human-readable HTML or Markdown reports may be generated from the machine-readable report.

Do not maintain separate manually calculated statistics.

---

## 32. Documentation requirements

Update documentation when changing:

* CLI behavior
* Configuration schema
* Stage names
* Intermediate model
* Database schema
* Diagnostics
* Output layout
* Docker volumes
* Toolchain versions
* Build prerequisites
* Verification procedure

Use examples that can be executed.

Do not document commands that have not been implemented.

Do not leave stale examples after renaming commands.

---

## 33. Configuration policy

Behavioral differences between projects and profiles should normally be configuration-driven.

Configuration must:

* Be validated at startup
* Have documented defaults
* Reject unknown critical keys
* Support stable profile composition
* Be included in the build manifest
* Be hashable for cache invalidation

Avoid hidden environment-variable behavior.

Environment variables may override operational settings such as:

* Paths
* Worker count
* Memory limits
* Network proxy

Semantic dictionary behavior should normally live in TOML or YAML configuration.

---

## 34. Repository hygiene

Never commit:

* Wikimedia dumps
* Generated SQLite databases
* Generated EPWING dictionaries
* Downloaded images
* Formula caches
* Docker named-volume contents
* Build logs
* Temporary files
* Secrets
* Large binary test artifacts without justification

Small deterministic fixtures may be committed.

Before finishing a task, inspect:

```bash
git status --short
git diff --stat
git diff
```

Ensure there are no unrelated changes.

---

## 35. Git change discipline

Make focused changes.

A single task should not combine:

* Dependency upgrades
* Formatting the entire repository
* Architectural refactoring
* New features
* Unrelated bug fixes

Avoid large mechanical rewrites unless explicitly requested.

Preserve user changes.

Do not revert or overwrite code you did not create unless it is necessary for the requested task.

When modifying an existing file, understand its current behavior first.

---

## 36. Refactoring policy

Refactor only when it directly improves the current task or removes a demonstrated obstacle.

A refactor must preserve externally observable behavior unless the change is intentional and documented.

Before a substantial refactor:

* Identify the invariant behavior
* Add or confirm tests
* Make the smallest structural change
* Re-run tests
* Avoid combining the refactor with unrelated features

Do not rewrite working pipeline stages because another design appears cleaner.

---

## 37. Backward compatibility

The project is initially pre-1.0, but build artifacts and manifests still require care.

Treat these as versioned interfaces:

* CLI commands
* Configuration keys
* Stage names
* Manifest schema
* Diagnostic codes
* Intermediate database schema
* Output naming rules

When changing an interface:

* Increment the relevant version
* Invalidate incompatible caches
* Document migration behavior
* Add compatibility handling where practical

Never reuse an old stage version for incompatible output.

---

## 38. Licensing rules

Project source licensing and generated Wikipedia content licensing are separate.

Do not remove:

* Wikipedia attribution
* Wikimedia project identification
* Dump date
* License notices
* Image source metadata
* Build-tool attribution

Do not claim ownership of Wikipedia content.

Image-enabled public releases require additional care.

Do not assume that all Wikimedia Commons images have identical licenses.

The image pipeline must retain enough metadata to audit included media.

---

## 39. Agent decision policy

When several implementations are possible, prefer the option that is:

1. Easier to verify
2. Easier to resume
3. More deterministic
4. Less coupled to FreePWING
5. Safer with untrusted input
6. Simpler to maintain
7. Adequately performant

Do not choose a complex distributed architecture for a local single-machine build without measured need.

Do not introduce:

* Redis
* PostgreSQL
* Message brokers
* Kubernetes
* Microservices
* Remote worker systems

unless the architecture is explicitly revised and the need is demonstrated.

SQLite, local files, Docker, and explicit stages are the default.

---

## 40. Uncertainty policy

Do not guess about:

* FreePWING syntax
* EB Library behavior
* EPWING reader compatibility
* Wikimedia dump structure
* Licensing requirements
* Image conversion safety
* Encoding limits

When uncertain:

1. Inspect existing source or documentation.
2. Create a minimal reproducible experiment.
3. Record the observed result.
4. Add a regression test where practical.
5. Document remaining uncertainty.

A small verified prototype is preferred over a confident speculative implementation.

---

## 41. When blocked

If blocked by one subsystem, continue only with work that remains valid independently.

Examples:

* If FreePWING compilation fails, improve the isolated toolchain proof rather than implementing the entire parser.
* If image metadata resolution is unclear, keep the text-only build working.
* If full template handling is incomplete, implement explicit fallback and diagnostics.
* If a complete dump is too expensive to test, use representative fixtures and sampled records.

Do not bypass a failing verification step merely to proceed to later milestones.

---

## 42. Completion report format

At the end of a coding task, report:

### Implemented

List concrete changes.

### Verification

List commands actually run and their results.

### Remaining limitations

List known gaps and risks.

### Suggested next milestone

Name one appropriate next task from `PLAN.md`.

Do not say that work is complete when required verification failed.

---

## 43. Prohibited actions

Agents must not:

* Start with a full Wikipedia build
* Install dependencies directly on the host
* Run the container as root without documented necessity
* Execute Wikitext or Lua
* Hide unsupported markup
* Ignore dump checksums
* Use mutable dependency versions without recording commits
* Place FreePWING details throughout the parser
* Parse the full XML dump into memory
* Add an ORM without architectural approval
* Use shell interpolation with article content
* Retry network operations forever
* Mark partial output as complete
* Delete previous valid output before new output succeeds
* Change tests solely to conceal a regression
* Commit generated dumps or dictionaries
* Add images before the text-only vertical slice works
* Claim compatibility without opening or inspecting the generated dictionary
* Claim reproducibility after only one build
* Optimize without measuring
* Rewrite unrelated code during a focused task

---

## 44. Immediate implementation priority

Unless the repository has already progressed beyond these tasks, begin with:

1. Dockerized CLI skeleton
2. `wikiepwing doctor`
3. Pinned FreePWING and EB Library toolchain
4. Handcrafted three-entry dictionary
5. `ebzip` packaging
6. Automated structural verification
7. Small end-to-end fixture

Do not implement current Wikipedia download parsing until the minimal handcrafted EPWING artifact has been generated and opened successfully.

---

## 45. Project success criteria

The project succeeds when this command:

```bash
docker compose run --rm builder \
  wikiepwing build \
  --project jawiki \
  --date latest \
  --profile standard
```

produces a verified archive such as:

```text
output/jawiki-YYYYMMDD-epwing-standard.zip
```

without requiring host installation of the legacy toolchain.

The resulting dictionary must:

* Open in common EPWING readers
* Search canonical Japanese titles
* Search redirect titles
* Navigate internal references
* Preserve readable article structure
* Render common tables and infoboxes
* Optionally include selected images
* Report unsupported content
* Identify the exact source dump
* Identify the exact build toolchain
* Be rebuildable from the repository and Docker configuration
