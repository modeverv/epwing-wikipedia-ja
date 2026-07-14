# LOG.md

実装作業の時系列ログです。新しい記録を末尾へ追記します。過去の記録を整理目的で書き換えないでください。

## 記録テンプレート

### YYYY-MM-DD HH:MM UTC — TASK-XXX

**目的**

- 

**変更**

- 

**実行コマンド**

```bash

```

**結果**

- 

**判断・注意点**

- 

**次タスク**

- 

### 2026-07-13 11:38 UTC — TASK-A001

**目的**

- Python 3.12系に固定した最小パッケージと`wikiepwing` CLIを作成する。

**変更**

- `pyproject.toml`と`uv.lock`を追加し、console scriptを定義した。
- package versionを公開する`src/wikiepwing/__init__.py`を追加した。
- argparseベースの`--help`と`--version`を`src/wikiepwing/cli.py`へ追加した。
- CLIの回帰テスト2件を`tests/test_cli.py`へ追加した。

**実行コマンド**

```bash
python3 -m unittest discover -s tests
uv lock
uv run python -m unittest discover -s tests
uv run wikiepwing --help
uv run wikiepwing --version
uv build
```

**結果**

- 実装前テストは2件とも`ModuleNotFoundError`で失敗し、要求未実装を確認した。
- `uv`はCPython 3.12.13を選択し、実装後テスト2件が成功した。
- helpと`wikiepwing 0.1.0`のversion表示が成功した。
- sdistとwheelの生成が成功した。
- `make format-check`、`make lint`、`make typecheck`、`make test`はTASK-A002で導入するため未実行。

**判断・注意点**

- Python要件は「3.12系を固定」に合わせて`>=3.12,<3.13`とした。
- 既存の未追跡`.DS_Store`と`v1/`配下には触れていない。

**次タスク**

- TASK-A002 Quality tools

### 2026-07-13 11:41 UTC — TASK-A002

**目的**

- formatter、linter、型検査、テストを固定バージョンと統一Makeターゲットで実行可能にする。

**変更**

- `pyproject.toml`へruff 0.11.13、mypy 1.16.0、pytest 8.4.0と各設定を追加した。
- `Makefile`へ`format`、`format-check`、`lint`、`typecheck`、`test`、`check`を追加した。
- `uv.lock`を更新した。
- 保管済みの別実装`v1/`をルートv2のruff検査対象から除外した。

**実行コマンド**

```bash
make check
uv lock
make check
make format
git diff --check
```

**結果**

- 実装前の`make check`はターゲット未定義で失敗した。
- 初回format-checkで`v1/`内2ファイルだけが対象になったため、`v1/`を除外して再実行した。
- format-check、ruff lint、mypy strictが成功した。
- pytest 8.4.0でCLIテスト2件が成功した。
- network、slow、manual markerは通常の`make test`から除外される。
- `make format`と`git diff --check`も成功した。

**判断・注意点**

- ツールは既存`v1/`で使用実績のあるバージョンへ固定した。
- `v1/`のコードや既存の未追跡`.DS_Store`は変更していない。

**次タスク**

- TASK-A003 Configuration loader

### 2026-07-13 11:47 UTC — TASK-A003

**目的**

- TOML設定を安全に検証し、既定値と追加設定を決定的にマージしてパスを解決する。

**変更**

- `config/default.toml`へ`CONFIG_REFERENCE.md`の既定設定を追加した。
- `src/wikiepwing/config.py`へ明示キースキーマ、型検証、deep merge、immutableな設定結果を追加した。
- 相対パスを各TOMLの親ディレクトリ基準で絶対化した。
- 負の数値、画像有効時の0件上限、危険なpublic配布方針、reference配下の書込パスを拒否した。
- `tests/test_config.py`へ正常系、merge、path、unknown key、不正TOML・型・version・安全方針のテストを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_config.py
make format
uv run ruff check --fix tests/test_config.py
make check
git diff --check
```

**結果**

- 実装前は`wikiepwing.config`が存在せず、テスト収集が失敗した。
- 局所テスト11件が成功した。
- format-check、ruff lint、mypy strictが成功した。
- 標準スイート13件が成功した。
- `git diff --check`が成功した。

**判断・注意点**

- schemaはdefault TOMLから推測せず、unknown keyをdefaultでも検出できるよう明示した。
- toolchain capability依存のentry budget検証とbuild stageでの`latest`拒否は、必要な実測値・stage contextが揃う後続タスクで扱う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-A004 Structured logging

### 2026-07-13 11:51 UTC — TASK-A004

**目的**

- 人間可読consoleログと機械可読JSON Linesログを、共通contextと秘密情報保護付きで出力する。

**変更**

- `src/wikiepwing/logging.py`へ`StructuredLogger`、context bind、console/JSONL formatterを追加した。
- JSONLへtimestamp、level、stage、run_id、event、page_id、title、diagnostic_code、messageを常に出力する。
- timestampをUTCのtimezone-aware datetimeからミリ秒精度の`Z`表記で生成する。
- 設定済みsecret、Authorization Bearer、password、各種token形式を両出力のformatter境界でredactする。
- `tests/test_logging.py`へ出力形式、必須フィールド、context bind、秘密情報非出力のテストを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_logging.py
make format
uv run ruff check --fix src/wikiepwing/logging.py
make check
git diff --check
```

**結果**

- 実装前は`wikiepwing.logging`が存在せず、テスト収集が失敗した。
- logging局所テスト3件が成功した。
- format-check、ruff lint、mypy strictが成功した。
- 標準スイート16件が成功した。
- secret文字列がconsoleとJSONLのどちらにも残らないことを自動確認した。

**判断・注意点**

- redactionを呼出側ではなくformatterへ集約し、出力先ごとの適用漏れを防いだ。
- loggerはroot loggerを変更せず、呼出単位でhandlerを所有して`close()`でflush・detachする。
- 複数processの単一JSONLへの同時書込とrotationは後続のpipeline運用設計で扱う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-A005 Docker app image

### 2026-07-13 11:55 UTC — TASK-A005

**目的**

- 再現可能なPython app imageをnon-rootと明示的なfilesystem権限境界で実行する。

**変更**

- `docker/app.Dockerfile`を追加し、Python 3.12.13 slim-bookwormのmulti-arch digestを固定した。
- uv 0.11.17と`uv.lock`のproduction packageを`/opt/venv`へ導入した。
- UID/GID 10001の`wikiepwing` userを作成し、root filesystem上の`/app`を非書込にした。
- source/work/cache/output/reports/logsは書込可能、referenceはread-onlyとなる初期directoryを作成した。
- `.dockerignore`へ`v1/`、生成物、cache、`.DS_Store`の除外を追加し、将来のtoolchain contextは保持した。
- `Makefile`へ`app-image`と`test-app-image`を追加した。

**実行コマンド**

```bash
docker buildx imagetools inspect python:3.12.13-slim-bookworm
make test-app-image
make check
docker image inspect wikiepwing-app:dev
git diff --check
```

**結果**

- 実装前の`make test-app-image`はターゲット未定義で失敗した。
- 初回smokeはuvがplatform metadataを付ける出力差だけで失敗し、version番号を厳密に保つpatternへ修正した。
- Debian bookworm、Python 3.12、uv 0.11.17、`wikiepwing 0.1.0`をcontainer内で確認した。
- 実行userはUID/GID 10001で、rootではないことを確認した。
- HOMEと必要な`/data` pathは書込可能、`/data/reference`と`/app`は書込不可だった。
- linux/arm64でimage sizeは68,854,763 bytesだった。
- format-check、ruff lint、mypy strict、標準スイート16件が成功した。

**判断・注意点**

- baseは`python:3.12.13-slim-bookworm@sha256:8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b`へ固定した。
- uv versionはbuild argumentで差し替えられないようDockerfileへ直接固定した。
- no-new-privileges、capability drop、named volume/bind mountはTASK-A006のCompose runtimeで設定する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-A006 Compose and volumes

### 2026-07-13 11:59 UTC — TASK-A006

**目的**

- 大量I/Oと最終成果物を適切なDocker volume種別へ分離し、Compose runtimeのsecurity境界を実証する。

**変更**

- `compose.yaml`へapp service、sources/work/cache named volume、output/reports/logs bind mountを追加した。
- root filesystemをread-onlyにし、`/tmp`だけをnon-root所有tmpfsとして追加した。
- UID/GID 10001、全capability drop、no-new-privilegesをCompose runtimeへ設定した。
- `docker/compose-smoke.sh`でCLI、権限、kernel security state、実mount type、cleanupを検査した。
- `Makefile`へ`test-compose`を追加した。

**実行コマンド**

```bash
make test-compose
sh -n docker/compose-smoke.sh
make check
docker inspect wikiepwing-tmpfs-inspect
docker volume ls --filter label=com.docker.compose.project=epwing-wikipedia
git diff --check
```

**結果**

- 実装前の`make test-compose`はターゲット未定義で失敗した。
- `docker compose run --rm app wikiepwing --version`は`wikiepwing 0.1.0`を返した。
- sources/work/cacheはvolume、output/reports/logsはbindとして実containerで確認した。
- UID 10001、read-only root、writable tmpfs、`NoNewPrivs: 1`、`CapEff: 0`を確認した。
- tmpfsは`.Mounts`ではなく`HostConfig.Tmpfs`へ現れるため、実際のinspect境界に検査を修正した。
- smoke用containerはtrapで削除され、sources/work/cache volumeは再開用に保持された。
- format-check、ruff lint、mypy strict、標準スイート16件が成功した。

**判断・注意点**

- named volumeは`docker compose down --volumes`で意図せず消さない運用を前提とする。
- 既存の`wikiepwing-data` volumeは旧`v1`由来の可能性があるため削除していない。
- reference dictionaryのread-only bind mountは参照pathを受け取るTASK-C001で追加する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-A007 Doctor command

### 2026-07-13 12:06 UTC — TASK-A007

**目的**

- build開始前にenvironment、config、storage、toolchain前提を人間と機械の両方が判定できるようにする。

**変更**

- `src/wikiepwing/doctor.py`へenvironment/config/path/storage/tool checkと共通reportを追加した。
- `src/wikiepwing/cli.py`へ`doctor`、追加`--config`、`--json`を追加した。
- `schemas/doctor-report.schema.json`へdraft 2020-12 JSON Schemaを追加した。
- `tests/test_doctor.py`でschema、text、exit 0/1/2を検証した。
- dev dependencyにjsonschema 4.25.1を固定し、`uv.lock`を更新した。
- `Makefile`へCompose内で実行する`doctor` targetを追加した。

**実行コマンド**

```bash
uv lock
uv run pytest tests/test_doctor.py
make format
make check
make doctor
docker compose run --rm app wikiepwing doctor --json
docker compose run --rm app wikiepwing doctor --json | uv run python -c '<schema validation>'
git diff --check
```

**結果**

- 実装前はdoctor subcommandが認識されず、局所テスト3件が失敗した。
- doctor局所テスト4件が成功し、JSON Schema format checkも成功した。
- successはexit 0、required path/storage failureはexit 1、configuration errorはexit 2になった。
- Compose内ではlinux/aarch64、Python 3.12.13、C.UTF-8、UTC、container markerを確認した。
- 全7 pathの存在・期待権限、約1.95TBの空き、200GiB threshold、uv pathを確認した。
- fpwmake、ebzip、ebinfo、fc-matchの未導入はoptional warningとして明示された。
- format-check、ruff lint、mypy strict、標準スイート20件が成功した。
- smoke終了後にCompose containerが残っていないことを確認した。

**判断・注意点**

- textとJSONは同じ`DoctorReport`から生成し、判定の二重実装を避けた。
- referenceはread-onlyであることを正、その他のdata pathは実probeでwritableであることを正とした。
- external legacy toolsはPhase 1前なのでwarningとし、uvだけをrequired toolにした。
- toolchain capability依存の検査はTASK-B009でrequired化する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B001 Pin EB source

### 2026-07-13 12:12 UTC — TASK-B001

**目的**

- EB Library sourceを公式配布元、version、size、SHA-256で固定し、差し替えや破損を公開前に拒否する。

**変更**

- `docker/toolchain/eb-source.env`へEB Library 4.4.3の公式release URL、filename、505510 bytes、SHA-256を固定した。
- `docker/toolchain/fetch-verified.sh`へHTTPS限定取得、local mirror入力、size/SHA-256検証、一時ファイルcleanup、検証後のatomic publishを追加した。
- `docker/toolchain/download-eb.sh`でlock値を常に適用するEB専用wrapperを追加した。
- `tests/test_eb_source.py`へ固定値、正常取得、size/checksum failure、wrapper迂回防止のoffline test 5件を追加した。
- `Makefile`へ`test-eb-source` targetを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_eb_source.py
sh -n docker/toolchain/fetch-verified.sh docker/toolchain/download-eb.sh
docker/toolchain/download-eb.sh <temporary-destination>
make format
make test-eb-source
make check
git diff --check
```

**結果**

- 実装前はlock fileとscriptsが存在せず、局所テスト5件が要求どおり失敗した。
- 公式GitHub release assetの実取得結果は505510 bytes、SHA-256 `abe710a77c6fc3588232977bb2f30a2e69ddfbe9fa8d0b05b0d67d95e36f4b5f`だった。
- archive先頭が`eb-4.4.3/`であることを確認し、一時取得物は削除した。
- checksumまたはsizeが一致しない入力は非0で終了し、destinationもpartial fileも残さなかった。
- format-check、ruff lint、mypy strict、標準スイート25件が成功した。

**判断・注意点**

- 公式ホームページが案内するGitHub release assetをcanonical URLとした。GitHub APIのasset metadataにはdigestがなかったため、実ファイルを取得してSHA-256を計算した。
- standard testはnetworkを使わず、同じverification pathへlocal fixtureを渡す。実URL確認は明示的なsmokeとして分離した。
- lockのhashとsizeはruntime override不可とし、local mirrorも同じ固定値で検証する。
- aarch64用config patchの必要性はTASK-B002の実buildで判定する。既存`v1/patches`は流用していない。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B002 Build EB Library

### 2026-07-13 12:27 UTC — TASK-B002

**目的**

- 固定済みEB Library 4.4.3 sourceを、hostへ依存を入れず再現可能なmulti-stage Docker imageでbuildする。

**変更**

- `docker/toolchain.Dockerfile`へdigest固定Debian bookworm-slimのbuilder/runtime stagesを追加した。
- Debian package取得先を2026-07-01の署名付きsnapshotへ固定し、top-level build package versionも固定した。
- `docker/toolchain/build-eb.sh`でverified download、archive path検査、patch、configure、make、upstream check、installを実行するようにした。
- `patches/eb/eb-4.4.3-modern-linux.patch`でaarch64識別、EBNet無効時の到達不能呼び出し、glibc iconv型互換を修正した。
- network dictionary accessを使わないため`--disable-ebnet`を明示し、legacy network surfaceを除外した。
- `toolchain-version`と`docker/toolchain/eb-image-smoke.sh`を追加した。
- `tests/test_eb_toolchain_definition.py`へbase/snapshot/source boundary/multi-stage/runtime定義テスト3件を追加した。
- `Makefile`へ`toolchain-image`とcacheなしの`test-eb-image` targetを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_eb_toolchain_definition.py
docker run <disposable-builder> ./configure --prefix=/opt/eb
patch --dry-run --directory=<source> --strip=1 --input=patches/eb/eb-4.4.3-modern-linux.patch
docker build --check --file docker/toolchain.Dockerfile .
make test-eb-image
make format
make check
git diff --check
```

**結果**

- 実装前はtoolchain Dockerfile/scriptsがなく、定義テスト3件が要求どおり失敗した。
- 未patch sourceはlinux/arm64で`config.guess: unable to guess system type`となることを使い捨てcontainerで再現した。
- patch後はbuild/hostとも`aarch64-unknown-linux-gnu`と判定された。
- 初回buildで検出したEBNetの1-byte境界外write warningを、不要なEBNetの無効化で除外した。
- EBNet無効化で露出した到達不能呼び出しとglibc iconv型差をscoped compatibility patchで直し、最終compiler warningは0件だった。
- upstream `make check`は成功した。ただしupstreamには実行されるtest bodyがなく、各directoryで`Nothing to be done`だったため、独自runtime smokeを完了判定に使用した。
- cacheなしlinux/arm64 buildとsmokeが成功した。runtime imageは29,106,125 bytes、UID 10001だった。
- `ebinfo (EB Library) version 4.4.3`、header、static/shared library、`ldd -r`、EBNet無効、compiler/curl非同梱を確認した。
- Dockerfile build checkはwarningなし、format-check、ruff lint、mypy strict、標準スイート28件が成功した。

**判断・注意点**

- APT snapshotはHTTPだがDebianの署名付きInReleaseとpackage hashで検証される。EB source取得はHTTPS限定のままである。
- final imageにbuild-essential、curl、source treeをコピーせず、`/opt/eb`だけをmulti-stage copyした。
- no-install-recommendsのためxz packageが存在しないmanpage symlinkをskipするwarningを出すが、runtime fileやEB buildには影響しない。
- `ebappendix`が必要とするPerl runtimeはFreePWINGとrequired Perl depsを扱うTASK-B004で追加する。
- `ebzip` binaryはbuild済みだが、path/version/roundtripの完了判定はTASK-B005で行う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B003 Pin FreePWING source

### 2026-07-13 12:31 UTC — TASK-B003

**目的**

- FreePWING sourceのversion、取得元、size、SHA-256を固定し、後続buildへ検証済みsourceだけを渡す。

**変更**

- `docker/toolchain/freepwing-source.env`へFreePWING 1.6.1、Debian stableのHTTPS orig tarball URL、119373 bytes、SHA-256、archive rootを固定した。
- `docker/toolchain/download-freepwing.sh`で既存のverified fetch境界を再利用し、network取得とlocal mirrorの両方にlock値を強制した。
- `patches/freepwing/README.md`へpatch directoryの目的、TASK-B004での実測先行、lexical order、`patch -p1`適用方針を記録した。
- `tests/test_freepwing_source.py`へ固定値、改ざんlocal mirror拒否、patch policyのoffline test 3件を追加した。
- `Makefile`へ`download-freepwing`と`test-freepwing-source` targetを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_freepwing_source.py
make download-freepwing FREEPWING_SOURCE=<temporary-destination>
tar -tjf <temporary-destination>
make format
make check
git diff --check
```

**結果**

- 実装前はlock、wrapper、patch policyがなく、局所テスト3件が要求どおり失敗した。
- 実URLから取得したarchiveは119373 bytes、SHA-256 `274a8cf392e2c46662bcf3eedce331fe84e65f7e5e6044d0178b2150a0704fc2`だった。
- archive rootが`freepwing-1.6.1/`であることを確認し、一時取得物は削除した。
- 改ざんlocal mirrorはsize mismatchで非0終了し、destinationを残さなかった。
- format-check、ruff lint、mypy strict、標準スイート31件が成功した。

**判断・注意点**

- 1.6.1 archive内のupstream ChangeLogはMotoyuki Kasaharaによる2009-10-24 releaseと記録しており、1.5後の大容量HONMON、inline color graphic、link backend省メモリ化を含むため、旧版1.5ではなく本流最新の1.6.1を採用した。
- upstream archive indexは参照情報として残し、現存するHTTPS取得元としてDebian stableが配布するunmodified orig tarballをcanonical URLにした。
- source identityとbuild compatibilityを分離するため、このタスクではpatchを作らない。現行Perl/toolchainでの必要性をTASK-B004のclean buildで実測する。
- standard testはnetworkを使わず、実URL確認だけを明示的smokeとして分離した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B004 Build FreePWING

### 2026-07-13 12:39 UTC — TASK-B004

**目的**

- 固定済みFreePWING 1.6.1を再現可能なtoolchain imageへ統合し、生成時に必要なruntime依存を機械確認する。

**変更**

- `docker/toolchain/build-freepwing.sh`へverified download、archive root/member type検査、決定的patch順、configure、check、install、module load検証を追加した。
- FreePWINGの標準install先が`/usr/local/lib/site_perl`へ逸脱するため、`--with-perllibdir=/opt/freepwing/lib/perl5`でmulti-stage copy対象内へ固定した。
- `docker/toolchain.Dockerfile`のbuilder/runtimeへPerl 5.36.0-7+deb12u3を固定し、runtimeへGNU Make 4.3-4.1を固定した。
- runtimeに`/opt/freepwing`だけをcopyし、`PATH`と`PERL5LIB`、source version/hash labelを追加した。
- `toolchain-version`へFreePWING 1.6.1表示を追加し、image smokeで`fpwmake`、全libexec command、Hash/GDBM/BDB module、package version、install boundaryを検証した。
- `tests/test_freepwing_toolchain_definition.py`へsource/build/runtime/smoke境界の定義テスト3件を追加した。
- `patches/freepwing/README.md`へ無改変build成功とpatch不要の実測結果を反映した。

**実行コマンド**

```bash
docker build --target eb-builder --tag wikiepwing-eb-builder:probe .
docker run <probe-builder> ./configure --prefix=/opt/freepwing && make && make check && make install
uv run pytest tests/test_freepwing_toolchain_definition.py tests/test_eb_toolchain_definition.py
docker build --check --file docker/toolchain.Dockerfile .
make test-eb-image
make format
make check
git diff --check
```

**結果**

- 実装前はbuild script、runtime packages、install boundaryがなく、局所テスト3件が要求どおり失敗した。
- 無改変FreePWING 1.6.1はlinux/arm64、Perl 5.36でconfigure/build/installに成功し、compatibility patchは不要だった。
- upstream `make check`は全directoryで成功したが、実行されるtest bodyはなかったため、独自runtime smokeを完了判定に使用した。
- cacheなしbuildとsmokeが成功し、runtime imageは40,796,305 bytes、UID 10001だった。
- FreePWING 1.6.1、GNU Make 4.3、Perl module `Text`、`Link::GDBM`、`Link::BDB`、全12 libexec commandを確認した。
- compiler、curl、build directory、`/usr/local/lib/site_perl/FreePWING`がruntimeに存在しないことを確認した。
- Dockerfile build checkはwarningなし、format-check、ruff lint、mypy strict、標準スイート34件が成功した。

**判断・注意点**

- FreePWING自身のversion optionはなく、`fpwmake --version`は埋め込まれた`gmake`のversionを返す。FreePWING versionは検証済みsource lockを`toolchain-version`が表示する。
- `perl` packageが標準moduleに加えてDB_File/GDBM_Fileと必要shared librariesを提供し、追加CPAN packageは不要だった。
- archiveは固定root配下のregular file/directoryだけを許可し、link memberを拒否してから展開する。
- `make`と`perl`以外のbuild dependencyはruntimeへ持ち込んでいない。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B005 Verify ebzip

### 2026-07-13 12:42 UTC — TASK-B005

**目的**

- toolchain runtimeの`ebzip` path/versionを固定し、最小EPWING fixtureの圧縮・展開可逆性を機械確認する。

**変更**

- `docker/toolchain/ebzip-roundtrip-smoke.sh`へ1 subbookの決定的CATALOGS/HONMON生成、圧縮、情報取得、展開、byte比較を追加した。
- runtime内で`ebzip`、`ebunzip`、`ebzipinfo`が`/opt/eb/bin`にあり、EB Library 4.4.3であることを確認するようにした。
- 圧縮結果の`EBZip` magic、level 0表示、入力より小さいことを検証した。
- `tests/test_ebzip_definition.py`へroundtrip定義と実行可能script/Make targetのoffline test 2件を追加した。
- `Makefile`へ`test-ebzip` targetを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_ebzip_definition.py
sh -n docker/toolchain/ebzip-roundtrip-smoke.sh
make test-ebzip
make format
make check
git diff --check
```

**結果**

- 実装前はroundtrip scriptとMake targetがなく、局所テスト2件が要求どおり失敗した。
- non-root runtimeで2048-byte CATALOGSと9020-byte HONMONからなる1 subbook fixtureを生成した。
- `ebzip --level 0`はHONMONを297-byteの`HONMON.ebz`へ圧縮し、先頭5 bytesは`EBZip`だった。
- `ebzipinfo`は`9020 -> 297 bytes`と`ebzip level 0 compression`を報告した。
- `ebunzip`後のCATALOGSとHONMONはともに`cmp`で入力と一致した。
- format-check、ruff lint、mypy strict、標準スイート36件が成功した。

**判断・注意点**

- このfixtureはtransport可逆性だけを測る。日本語本文、検索index、内部linkはTASK-B006以降でFreePWING生成物を使って測る。
- CATALOGSは1 sectorの最小recordを作り、subbook directoryを8-byteの`ROUNDTRP`に固定した。
- fixtureは一時container内だけに生成し、成功・失敗にかかわらずcontainer削除でhostへ生成物を残さない。
- 圧縮率は互換性条件ではないため、固定値297 bytesは完了条件にせず、入力より小さいことと可逆性を判定した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B006 Handcrafted three-entry source

### 2026-07-13 12:49 UTC — TASK-B006

**目的**

- Wikipedia parserに依存しない3記事sourceから、日本語本文、複数headword、内部linkを持つ最小EPWINGを生成する。

**変更**

- `tests/fixtures/handcrafted/entries.tsv`へEmacs・Linux・WikipediaのUTF-8 sourceを追加し、各title、2 alias、日本語本文、循環するlink targetを定義した。
- `build_fixture.pl`でfield数、tag、alias数、headword重複、link target存在を検証し、FreePWINGのheading、text、word2、referenceへ登録するようにした。
- `catalogs.txt`とfixture `Makefile`を追加し、`WIKIEP` 1 subbookのCATALOGS/HONMONを生成できるようにした。
- runtime smokeでUTF-8からEUC-JPへ変換後に`fpwmake`を実行し、CATALOGS 2048 bytes、HONMON非空、EB LibraryのJIS X 0208・1 subbook・`wikiep`構造を検証した。
- `tests/test_handcrafted_fixture.py`へsource contract、parser wiring、runtime smoke wiringのoffline test 3件を追加し、`Makefile`へ`test-handcrafted`を追加した。

**実行コマンド**

```bash
uv run pytest tests/test_handcrafted_fixture.py
sh -n docker/toolchain/handcrafted-three-entry-smoke.sh
make test-handcrafted
make format
make check
git diff --check
```

**結果**

- 実装前はfixture、parser、smoke、Make targetがなく、局所テスト3件が要求どおり失敗した。
- FreePWINGは3記事のHONMONと10240-byteのファイルを生成し、`catdump`は2048-byteのCATALOGSを生成した。
- `ebinfo`はcharacter code `JIS X 0208`、subbook数1、directory `wikiep`、search methods `word endword`を報告した。
- format-check、ruff lint、mypy strict、標準スイート39件が成功した。

**判断・注意点**

- `catdump`のTitleは空白を含め2-byte文字のみを許容するため、ASCIIを含む初期案を「手作り百科事典辞書」へ変更した。記事title/headwordはEmacs、Linux、Wikipediaのままである。
- HONMONはEUC-JP sourceの生byte配列ではなくJIS X 0208制御表現になる。本文取得とlink位置は生byte探索ではなく、TASK-B009のEB Library API probeで測定する。
- graphic、gaiji、ebzip/packageは依存順にB007、B008、B010へ分離した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B007 Graphic sample

### 2026-07-13 12:53 UTC — TASK-B007

**目的**

- 外部assetに依存しない小型bitmapを手作り辞書へ登録し、FreePWINGのgraphic生成経路を実測する。

**変更**

- `generate_bitmap.pl`を追加し、2×2 pixels、24-bit BGR、無圧縮、70 bytesのBMPを外部toolなしで決定的に生成するようにした。
- `cgraphs.txt`に`wiki-mark` 1件だけを登録し、fixture `Makefile`の`CGRAPHS`でFreePWINGへ渡すようにした。
- Wikipedia記事のtextに`add_color_graphic_start/end`の参照を追加した。
- runtime smokeでcolor graphic recordのheader、size、BMP payloadを検証し、同じpayloadが最終HONMONに埋め込まれたことをbyte単位で確認するようにした。
- `tests/test_handcrafted_graphic.py`へBMP構造/決定性、FreePWING定義、runtime検証配線のoffline test 3件を追加した。

**実行コマンド**

```bash
uv run pytest tests/test_handcrafted_graphic.py tests/test_handcrafted_fixture.py
sh -n docker/toolchain/handcrafted-three-entry-smoke.sh
sh docker/toolchain/handcrafted-three-entry-smoke.sh wikiepwing-toolchain:dev
make format
make check
git diff --check
```

**結果**

- 実装前はgenerator、graphic定義、HONMON検証がなく、局所テスト3件が要求どおり失敗した。
- 2回生成したBMPはbyte単位で一致し、file size 70、pixel offset 54、DIB size 40、2×2、24-bit、compression 0、pixel data 16 bytesだった。
- FreePWING生成の`work/cgr`は`data` recordとBMP size/payloadが一致し、最終HONMON 12288 bytesにBMP payloadが完全に含まれた。
- `ebinfo`はgraphic追加後もJIS X 0208、1 subbook、directory `wikiep`の構造を正常に読んだ。
- format-check、ruff lint、mypy strict、標準スイート42件が成功した。

**判断・注意点**

- B007では生成、参照解決、最終artifactへの埋め込みを測定した。EB Libraryのfull text hookによるgraphic参照位置と抽出は、包括的なTASK-B009 toolchain probeで測定する。
- BMPはsourceとしてGitに保存せず、runtimeでgeneratorから生成するため、binary fixture差替えや来歴不明assetを避けた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B008 Gaiji sample

### 2026-07-13 12:59 UTC — TASK-B008

**目的**

- FreePWINGの必須16-dot narrow/wide gaijiを各1字生成し、記事参照、CATALOGS、EB Library読取までを機械検証する。

**変更**

- `generate_gaiji.pl`を追加し、8×16 narrowと16×16 wideのXBMを決定的に生成するようにした。
- `halfchars.txt`と`fullchars.txt`に各1字だけ登録し、fixture `Makefile`の`HALFCHARS`/`FULLCHARS`へ接続した。
- Linux記事から`add_half_user_character("half-mark")`と`add_full_user_character("full-mark")`を各1回呼び、すべての失敗を`or die`で停止するようにした。
- CATALOGSに`GA16HALF`/`GA16FULL`を定義し、runtime smokeで生成した4096-byteの`gai16h`/`gai16f`をEPWING gaiji directoryへ配置した。
- `tests/test_handcrafted_gaiji.py`へXBM構造/決定性、登録/失敗配線、runtime stagingのoffline test 3件を追加した。

**実行コマンド**

```bash
uv run pytest tests/test_handcrafted_gaiji.py
sh -n docker/toolchain/handcrafted-three-entry-smoke.sh
sh docker/toolchain/handcrafted-three-entry-smoke.sh wikiepwing-toolchain:dev
make format
make check
git diff --check
```

**結果**

- 実装前はXBM generator、gaiji定義、参照、stagingがなく、局所テスト3件が要求どおり失敗した。
- narrow XBMは8×16/16 bitmap bytes、wide XBMは16×16/32 bitmap bytesで、2回の生成結果が一致した。
- FreePWINGは情報blockとbitmap blockからなる4096-byteの`gai16h`と`gai16f`を生成した。
- `ebinfo`はfont size 16、narrow characters `0xa121 -- 0xa121`、wide characters `0xa121 -- 0xa121`を報告した。
- `ebzip --test`はHONMONに加えて両gaiji fileを認識し、圧縮simulationに成功した。
- format-check、ruff lint、mypy strict、標準スイート45件が成功した。

**判断・注意点**

- JIS X 4081/FreePWINGで必須の16-dot fontのみをB008の範囲とし、24/30/48-dot fontは準備しない。
- narrow/wideは別のname tableを持つため、両方の最初の1字はそれぞれ`0xa121`になる。
- 実Unicodeからgaiji/置換への分類はPhase 14の責務であり、このtoolchain fixtureでは明示名参照と失敗境界だけを証明した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B009 Toolchain probe command

### 2026-07-13 13:05 UTC — TASK-B009

**目的**

- 手作りEPWINGをEB Library APIで検索・読取し、toolchain capabilityを機械可読JSONに固定する。

**変更**

- `eb-probe.c`を追加し、EB Library 4.4.3のword search、hit list、text read、text hook APIを使うprobe binaryを実装した。
- `build-eb.sh`でwarning/errorを禁止してprobeをbuildし、`/opt/eb/bin/wikiepwing-eb-probe`へruntime library rpath付きでinstallするようにした。
- handcrafted smokeが生成artifactにprobeを実行し、必要な場合はhostの指定outputへJSONをcopyするようにした。
- `probe.sh`と`make probe-toolchain`を追加し、`reports/toolchain-capabilities.json`の生成後に全schema/valueを読み戻し検証するようにした。
- `tests/test_toolchain_probe.py`へAPI/hook使用、build境界、command wiring、JSON schemaのoffline test 4件を追加した。

**実行コマンド**

```bash
uv run pytest tests/test_toolchain_probe.py
sh -n docker/toolchain/probe.sh docker/toolchain/handcrafted-three-entry-smoke.sh
docker build --file docker/toolchain.Dockerfile --tag wikiepwing-toolchain:dev .
make probe-toolchain
make format
make check
git diff --check
```

**結果**

- 実装前はprobe source/binary/commandがなく、局所テスト3件が要求どおり失敗した。
- runtime imageのprobeが1 subbook `wikiep`を開き、Emacs 1 hit、Linux 3 hits、Wikipedia 1 hitを得て、3本文の読取に成功した。
- hook callbackはreference 6回、BMP 3回、narrow gaiji 2回、wide gaiji 2回を検出した。
- `reports/toolchain-capabilities.json`はEB Library 4.4.3、word/endword search、query hit数、text読取数、hook回数を固定順で記録し、読み戻し検証に成功した。
- format-check、ruff lint、mypy strict、標準スイート49件が成功した。

**判断・注意点**

- word searchは完全一致数ではなく、`Linux`はalias/index表現を含む3 hitsとなった。probeは実測値をそのまま記録する。
- hook回数は論理要素数ではなくEB内部表現上のcallback回数である。capability判定は1回以上を条件とし、回数自体もregression検出用に保存する。
- ebzip後の同probe再実行とZIP packageはTASK-B010に分離した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-B010 Toolchain smoke package

### 2026-07-13 13:10 UTC — TASK-B010

**目的**

- 手作りEPWINGを実圧縮・ZIP化し、圧縮後と再展開後にEB Libraryで同じ機能を読めることを証明する。

**変更**

- toolchain runtimeにDebian snapshotの`zip=3.0-13`を固定した。
- handcrafted smokeでCATALOGS、HONMON、narrow/wide gaijiを`ebzip --level 0`で実圧縮し、圧縮後にEB Library probeを再実行するようにした。
- 未圧縮/圧縮後のcapability JSONを`cmp`し、各memberの時刻を固定後に`zip -X`でpackageを生成するようにした。
- `package-smoke.sh`でZIP memberの完全一致、absolute/parent path、symlinkを検証し、展開後のEB Library probe結果も比較するようにした。
- `make package-toolchain`と`tests/test_toolchain_package.py`のoffline test 2件を追加し、Phase 1の出口条件をすべて完了にした。

**実行コマンド**

```bash
uv run pytest tests/test_toolchain_package.py
make package-toolchain
sh docker/toolchain/package-smoke.sh wikiepwing-toolchain:dev output/toolchain-smoke.epwing.zip
make format
make check
git diff --check
```

**結果**

- 実装前はpackage commandとZIP検証がなく、局所テスト2件が要求どおり失敗した。
- ebzipはHONMON 12288→6627 bytes、GA16HALF 4096→93 bytes、GA16FULL 4096→90 bytesへ圧縮した。
- 圧縮後とZIP再展開後の両方で、未圧縮時と同じsearch/text/hook capability JSONを得た。
- ZIPは`CATALOGS`とHONMON/GA16HALF/GA16FULLの3 `.ebz`だけを含み、path traversalやsymlinkはなかった。
- 連続生成のSHA-256が一致し、最終値は`33541e73324ef808de48a8bf6e6ba3b009e2330f79dd1894a39bc946bb192701`、sizeは1958 bytesだった。
- format-check、ruff lint、mypy strict、標準スイート51件が成功した。

**判断・注意点**

- ZIPの再現性のため、member mtimeを2000-01-01 00:00に固定し、追加metadataを`-X`で除外した。
- `ebzip --output-directory`は入力stageを消費するため、圧縮後の検証対象は出力artifactに固定した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-C001 Reference path validation（Boookends 2023版のread-only path/mountの確認が必要）

### 2026-07-13 13:18 UTC — TASK-C001 scope adjustment

- scannerとdoctorの非変更検証だけでは、実参照辞書を`/data/reference`へread-only mountする再現可能な入口が欠けることが分かった。
- C001の「read-only expectation」を実運用で満たすため、予定変更ファイルに`compose.reference.yaml`と定義テスを追加する。host pathは自動生成せず、利用時に明示指定させる。

### 2026-07-13 13:19 UTC — TASK-C001

**目的**

- Boookends 2023版のreference rootとEPWING `CATALOGS`を、参照辞書を書き換えずに安全に検証する。

**変更**

- `reference/scanner.py`にreal directory/read-only判定と、symlinkを追跡しない深さ4・10,000 entry上限の`CATALOGS`探索を追加した。
- `CATALOGS`をregular file、1 MiB以下、非空、2048-byte整列として検証し、不正root・未発見・不正サイズを明示エラーにした。
- `doctor`のreference検査を一時ファイル作成から非変更のstat/mode/filesystem検査へ変更した。
- `compose.reference.yaml`に、明示したhost pathを自動生成せず`/data/reference`へread-only bind mountするoverrideを追加した。
- scanner、Compose定義、doctor非書込みのoffline testを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_reference_scanner.py tests/test_reference_compose.py tests/test_doctor.py
docker compose -f compose.yaml -f compose.reference.yaml config
make format
make check
git diff --check
```

**結果**

- 実装前はreference moduleとCompose overrideがなく、局所テストが要求どおり失敗した。
- 局所テスト13件が成功し、検証中のreference rootに書込みが発生しないことを確認した。
- Composeは`read_only: true`と`create_host_path: false`を解決済み設定に保持した。
- format-check、ruff lint、mypy strict、標準スイート60件、`git diff --check`がすべて成功した。

**判断・注意点**

- read-onlyの判定はfilesystem flag、mode bit、effective accessを用い、probe fileは作成しない。
- 実物のBoookends 2023版はworkspaceになく、`WIKIEPWING_REFERENCE_PATH`も未設定のため、実物inventoryは未実行。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-C002 Reference inventory（Boookends 2023版の絶対パス指定が必要）

### 2026-07-13 13:27 UTC — TASK-C002

**目的**

- Boookends 2023版のreference rootから、非変更でfile tree、size集計、subbook候補を生成する。

**変更**

- `reference/inventory.py`を追加し、directory/file/symlink/otherを決定的にソートしたschema-versioned JSONにした。
- symlinkは追跡せず、深さ16、100,000 entries、relative path 4,096 bytesの上限と、全regular file/directoryのread-only検査を追加した。
- `HONMON`/`HONMON.EBZ`の配置からcatalogごとのsubbook候補を抽出し、関連gaiji pathも列挙するようにした。
- `wikiepwing reference-inventory`と、reference root内を拒否する原子的JSON出力を追加した。
- safety limit、決定性、subbook抽出、出力境界、CLIのoffline testを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_reference_inventory.py tests/test_cli.py
make format
make check
WIKIEPWING_REFERENCE_PATH=/Users/seijiro/work/004_dic/Wikip_ja20230120 \
  docker compose -f compose.yaml -f compose.reference.yaml build app
WIKIEPWING_REFERENCE_PATH=/Users/seijiro/work/004_dic/Wikip_ja20230120 \
  docker compose -f compose.yaml -f compose.reference.yaml run --rm app \
  wikiepwing doctor --json
WIKIEPWING_REFERENCE_PATH=/Users/seijiro/work/004_dic/Wikip_ja20230120 \
  docker compose -f compose.yaml -f compose.reference.yaml run --rm app \
  wikiepwing reference-inventory --output /data/reports/reference-inventory.json
git diff --check
```

**結果**

- 実装前は`wikiepwing.reference.inventory`が存在せず、局所テストが要求どおり収集失敗した。
- 局所テス8件、format-check、ruff lint、mypy strict、標準スイート66件、`git diff --check`が成功した。
- `doctor`は実物mountを`filesystem is read-only`と判定した。
- inventoryは1 subbook候補`WIKIP`、3 directories、7 files、16,097,091,422 bytes、HONMON 1件、gaiji 2件を記録した。
- 連続2回のJSON SHA-256は`9fbaef17d0e49f1103602a1f4760af2b6bb7f0c513f4ffbcb59f9edffbfd1e7e`で一致した。
- 参照CATALOGSのSHA-256は走査後も`5751a37c296a20c80efe69230e36511c35dcb05cb91e14f2067d9f524fb710a6`のままだった。

**判断・注意点**

- `/Users/seijiro/work/004_dic/Wikip_ja20230120`を実物として採用した。同期コピーとCATALOGS hash・主要file sizeが一致し、名称と2023-02-15のmtimeが目的と整合する。
- 16 GBのHONMON payloadは読まず、filesystem metadataだけを走査した。
- 生成reportは`reports/`配下のため既存`.gitignore`によりGit管理外である。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-C003 Reference DB schema

### 2026-07-13 13:32 UTC — TASK-C003

**目的**

- `reference.sqlite3`の明示SQL schemaと番号付きmigration適用境界を定義する。

**変更**

- `migrations/reference/001_initial.sql`に`schema_migrations`と、設計7テーブルをSTRICT tableとして追加した。
- book/subbook/query/result/entry/metric/diagnostic間のforeign key、CHECK、UNIQUE、検索用indexを定義した。
- `reference/database.py`へ番号連続性、ファイル名、UTF-8、1 MiB上限、symlink、SHA-256を検証するmigration loaderを追加した。
- migration単位のtransaction、履歴改変検出、foreign key、5秒busy timeout、integrity/foreign-key checkを追加した。
- app imageへrootの`migrations/`をcopyし、container内も同じSQLを使うようにした。
- schema/constraint/idempotence/history/rollback/invalid migrationのschema testを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_reference_database.py
make format
make check
git diff --check
```

**結果**

- 実装前は`wikiepwing.reference.database`が存在せず、schema testが要求どおり収集失敗した。
- schema test 8件で全テーブルのSTRICT定義、pragma、制約、冪等性、改変検出、rollbackを確認した。
- format-check、ruff lint、mypy strict、標準スイート74件、`git diff --check`が成功した。
- `001_initial.sql`のSHA-256は`a98c1004eae8c294372de2a849e4d13aa827260d55d3b355e6ae3a78c9b5014b`だった。

**判断・注意点**

- migration履歴に時刻を入れず、version/name/SHA-256のみを固定して再現性を保った。
- DBへの実データ投入はC005以降に分離した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-C004 Fixed query definition

### 2026-07-13 13:35 UTC — TASK-C004

**目的**

- Boookends比較の固定queryセットを機械可読設定として固定する。

**変更**

- `config/query-set.toml`にPLAN Phase 2の9 queryを順序どおり追加した。
- word/endwordの2 mode、queryごと最大100 results、正の8 queryと存在しない1 queryの存在期待を明示した。
- `reference/queries.py`にtyped immutable modelとsource SHA-256 fingerprintを返すloaderを追加した。
- 64 KiB file上限、query 4,096 UTF-8 bytes上限、最大1,000 queries、symlink非許可、unknown key・型・重複・制御文字検証を追加した。
- 固定値と各negative boundaryのoffline testを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_reference_queries.py
make format
make check
git diff --check
shasum -a 256 config/query-set.toml
```

**結果**

- 実装前は`wikiepwing.reference.queries`が存在せず、局所テストが要求どおり収集失敗した。
- 局所テス8件で固定9 queryと安全境界を確認した。
- format-check、ruff lint、mypy strict、標準スイート82件、`git diff --check`が成功した。
- `config/query-set.toml`のSHA-256は`b98bcd6ece75730780b91ce58266d358677353b2568d4bb9efdd16f5b25ae013`だった。

**判断・注意点**

- modeはB009のtoolchain probeで実証済みのword/endwordに限定した。
- 存在期待はC005の実測結果と照合し、不一致を隠さず診断化する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-C005 Execute reference searches

### 2026-07-13 13:39 UTC — TASK-C005 scope adjustment

- 実物のword searchで、`Emacs`は異なるrank/headingが同じtext locatorを指す結果を返すことが分かった。
- C003の`UNIQUE (query_id, subbook_id, entry_locator)`は実データを欠落させるため、`001_initial.sql`は改変せず、C005の最小前提修正として`002_allow_duplicate_query_locators.sql`を追加する。rankの一意性は維持する。

### 2026-07-13 13:47 UTC — TASK-C005

**目的**

- 固定9 query×word/endwordを実参照辞書に実行し、ランク付き結果と診断を`reference.sqlite3`へ固定する。

**変更**

- `eb-search.c`を追加し、JIS X 0208辞書向けUTF-8→EUC-JP変換、word/endword、heading/text positionのASCII protocol出力を実装した。
- C adapterはroot/query/max resultsを検証し、`nftw`+`FTW_PHYS`で16階層・100,000 entries上限とsymlink拒否を行うようにした。
- `reference/searches.py`に配列subprocess、query単位timeout、stdout/stderrの逐次上限監視、strict protocol parseを追加した。
- 18 queryをtemporary DBへtransactionalに保存し、integrity/foreign-key/query-count検証後に置換する`reference-search` CLIを追加した。
- 存在期待不一致とresult truncationを`reference_diagnostics`へ保存するようにした。
- `002_allow_duplicate_query_locators.sql`を追加し、同rankは禁止したまま同locatorの複数heading/rankを保存可能にした。
- toolchain runtimeを固定Python 3.12 app統合imageにし、read-only/non-root/cap-drop/no-new-privilegesの`reference-inspector` Compose serviceを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_reference_searches.py tests/test_reference_search_definition.py
make toolchain-image
docker run --rm --read-only --user 10001:10001 \
  --mount type=bind,source=/Users/seijiro/work/004_dic/Wikip_ja20230120,target=/data/reference,readonly \
  wikiepwing-toolchain:dev wikiepwing-eb-search /data/reference word 日本 3
WIKIEPWING_REFERENCE_PATH=/Users/seijiro/work/004_dic/Wikip_ja20230120 \
  docker compose -f compose.yaml -f compose.reference.yaml run --rm reference-inspector \
  wikiepwing reference-search --database /data/work/reference.sqlite3
make package-toolchain
make format
make check
git diff --check
```

**結果**

- 実装前は`wikiepwing.reference.searches`が存在せず、局所テストが要求どおり収集失敗した。
- 実物のcharacter codeはJIS X 0208、subbookは`wikip`、titleは「日本語ウィキペディア」と取得できた。
- 18 queryは合計820 ranked resultsとなり、固定存在期待の不一致は0件だった。
- max 100件に到達した6 searchを`REF_QUERY_RESULTS_TRUNCATED`として保存した。
- `PRAGMA integrity_check` は`ok`、foreign key errorは0、再生成DB SHA-256は2回とも`378a2d44e3b7b782080c2908bf65f600901ddee935d00bcc6ecb9839e4375674`だった。
- 既存toolchain package smokeは生成・ebzip・ZIP・再展開・EB probeまで成功した。
- format-check、ruff lint、mypy strict、標準スイート92件、`git diff --check`が成功した。

**判断・注意点**

- query結果の同locator重複は実データであり、dedupeせずrankどおり保存した。
- truncation 6件は失敗ではないが、C007 reportで可視化する。
- `001_initial.sql`のSHA-256は変更せず`a98c1004eae8c294372de2a849e4d13aa827260d55d3b355e6ae3a78c9b5014b`、`002`は`59775f9490a6a549a750b5079328e08f31df659e0b8c62ddeac92b57afc0666e`だった。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-C006 Reference entry sampling

### 2026-07-13 14:19 UTC — TASK-C006

**目的**

- 固定queryのrank 1から重複locatorを除いたentryを上限付きで読み、本文hash・抜粋・hook数を参照DBへ固定する。

**変更**

- `eb-entry.c`にsubbook directoryとtext positionの検証、最大256 KiBの本文読取、reference/BMP/narrow/wide gaiji hook計数を実装した。
- C adapterのroot走査は`nftw`+`FTW_PHYS`、16階層・100,000 entries上限とsymlink拒否を維持した。
- `reference/entries.py`にadapterのtimeout・出力上限・strict protocol parse、rank 1 locatorの決定的dedupe、冪等DB保存を追加した。
- entry単位の回復可能なEB読取失敗は`REF_ENTRY_READ_FAILED`、本文上限到達は`REF_ENTRY_TEXT_TRUNCATED`、機械判定不能な表示品質は`REF_MANUAL_VIEWER_RENDER_REQUIRED`として保存するようにした。
- `reference-sample` CLIとofflineテストを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_reference_entries.py tests/test_reference_entry_definition.py tests/test_cli.py
make toolchain-image
WIKIEPWING_REFERENCE_PATH=/Users/seijiro/work/004_dic/Wikip_ja20230120 \
  docker compose -f compose.yaml -f compose.reference.yaml run --rm reference-inspector \
  wikiepwing reference-sample --database /data/work/reference.sqlite3
make package-toolchain
make check
git diff --check
```

**結果**

- rank 1のunique locatorは8件で、7 entryを保存した。
- 本文byte数は4,427～182,024、internal reference hookは40～1,563、gaiji hookは0～14だった。image hookは全sampleで0だった。
- `8013341:1392`（第二次世界大戦）はEB Libraryが1,024回の空read後も本文を返さず、1件の`REF_ENTRY_READ_FAILED`として保存した。
- `PRAGMA integrity_check`は`ok`、foreign key errorは0だった。
- 再実行前後のDB SHA-256はともに`0a8054fdfe162e09b843382f09546e4e8f3ae488180ff07f2921784b757a59da`だった。
- toolchain package smoke、format-check、ruff lint、mypy strict、標準スイート99件、`git diff --check`が成功した。

**判断・注意点**

- 読取失敗を無視せず診断として残し、他のentry sample採取は継続する境界にした。
- viewerの表示・レイアウト・media品質は推測せず、C007のmanual checklistへ回す。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-C007 Reference report

### 2026-07-13 14:31 UTC — TASK-C007

**目的**

- 参照DBの観測結果を決定的なJSON/HTMLへまとめ、自動取得不能な表示品質をmanual checklistへ分離する。

**変更**

- `reference/report.py`にDB integrity/FK検証、book/subbook/query/results/entries/diagnosticsの決定的読取を実装した。
- JSON、escape済みでscript・外部resourceを持たないHTML、viewer確認用Markdownを同一DBから生成するようにした。
- 出力fileとdirectoryのsymlinkを拒否し、同じ出力directory内のtemporary fileをfsyncしてからatomic replaceするようにした。
- `reference-report` CLIと、完全性・escape・再現性・symlink境界のofflineテストを追加した。
- `PLAN.md`のPhase 2出口条件を実測結果に基づいて完了にした。

**実行コマンド**

```bash
uv run pytest tests/test_reference_report.py tests/test_cli.py
make toolchain-image
WIKIEPWING_REFERENCE_PATH=/Users/seijiro/work/004_dic/Wikip_ja20230120 \
  docker compose -f compose.yaml -f compose.reference.yaml run --rm reference-inspector \
  wikiepwing reference-report --database /data/work/reference.sqlite3 \
  --output-directory /data/reports
make check
git diff --check
```

**結果**

- report summaryは1 subbook、18 queries、820 results、7 entries、8 diagnosticsだった。
- diagnosticsは検索上限到達6件、entry読取失敗1件、manual viewer確認1件を欠落なく含む。
- 再生成前後のSHA-256はJSON `3aeb3143366a8588e1526930dc5c25cbf22cb6cd5a73f492c712b48e0c5d7a63`、HTML `5cb27f8cdb3b9b8acdb8f718f76f92df8969b43cd305c366b43fae4fb2bcbe48`、checklist `d7ebaa5167a3348335815311ef86031bbeed6a849b3d496085f3b087d3c519df`で一致した。
- 参照`CATALOGS` SHA-256はC002時点と同じ`5751a37c296a20c80efe69230e36511c35dcb05cb91e14f2067d9f524fb710a6`で、read-only参照を変更していない。
- format-check、ruff lint、mypy strict、標準スイート102件、`git diff --check`が成功した。

**判断・注意点**

- `reports/reference-manual-checklist.md`のviewer表示・link・media・gaiji確認は機械的に代替せず、人間レビュー境界として残した。
- reportには生成時刻を入れず、同じDBから同じbytesを得るようにした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- 人間によるreference manual checklistレビュー後、TASK-D001 Secret model and env example

### 2026-07-14 00:00 UTC — セッション開始点検

**目的**

- 継続作業の開始前に、直前セッションの成果物と未コミット状態を確認する。

**発見事項**

- TASK-A001〜C007の実装一式(`src/`, `tests/`, `migrations/`, `schemas/`, `config/`, `docker/`, `pyproject.toml`, `uv.lock`, `Makefile`, `compose*.yaml`等)がgitに一切コミットされていなかった。
- `reports/reference-manual-checklist.md`は生成済みだが、viewerによる目視確認欄は未記入だった。

**判断**

- ユーザーに確認し、(1) manual checklistレビュー未完のままTASK-D001へ進める、(2) 未コミットの実装一式を現状のまま1コミットにまとめる、の2点で承認を得た。
- 未コミット分を`740e627`としてコミットした。

**次タスク**

- TASK-D001 Secret model and env example

### 2026-07-14 00:10 UTC — TASK-D001

**目的**

- Wikimedia Enterprise認証情報の環境変数名・読取・検証を1箇所へ固定し、`.env.example`で必要な環境変数名を明示する。

**変更**

- `src/wikiepwing/secrets.py`に`WME_USERNAME`/`WME_PASSWORD`/`WME_ACCESS_TOKEN`/`WME_REFRESH_TOKEN`の名前定数、`EnterpriseSecrets`データクラス、`load_enterprise_secrets`、`redaction_values()`を実装した。
- 空文字は未設定として扱い、前後空白・空白のみ・制御文字(`\n`/`\r`/`\t`)を含む値は`SecretError`で拒否した。
- `WME_USERNAME`と`WME_PASSWORD`は対でのみ許可し、片方だけの設定を拒否した。値は環境変数からのみ読み、どこにも永続化しない。
- `.env.example`に4変数の名前と設定方法のコメントのみを記載し、実値は含めていない。
- `.gitignore`へ`.env`を追加した。
- `tests/test_secrets.py`に11件のオフラインテストを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_secrets.py
make check
git diff --check
```

**結果**

- 標準スイート113件(新規11件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- access/refresh/login優先順位に基づく実HTTP認証処理はTASK-D002で扱う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D002 Enterprise auth client

### 2026-07-14 00:20 UTC — TASK-D002

**目的**

- Wikimedia Enterprise認証クライアントを実装し、access token優先→refresh token→username/passwordの固定優先順位で1つのaccess tokenを解決する。timeoutを強制し、tokenをどこにも永続化しない。

**変更**

- `src/wikiepwing/source/auth.py`に`EnterpriseAuthClient`(優先順位解決)、`AuthTransport` Protocol、`HttpAuthTransport`(bounded urllib実装)、`ResolvedAccessToken`を追加した。
- access tokenが存在する場合はtransportを一切呼ばない。refresh tokenをlogin(username/password)より優先する。
- HTTPレスポンスは64 KiB上限で読み、上限超過・不正JSON・`access_token`欠落・空文字tokenを`AuthError`として拒否した。
- 401/403、5xx、timeout、URLErrorはリトライせず即座に`AuthError`として失敗させた。
- `HttpAuthTransport`はhttps以外のbase URLを拒否し、非正のtimeoutは両クラスで拒否した。
- モジュールはファイルシステムへ一切触れず、tokenは戻り値のdataclassとしてのみ保持する。

**実行コマンド**

```bash
uv run pytest tests/test_auth.py
make check
git diff --check
```

**結果**

- 標準スイート130件(新規17件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際のWikimedia Enterprise auth APIのendpoint path(`/login`、`/token-refresh`)は一次資料未確認の仮定であり、`SOURCES.md`に確認記録がない。実クレデンシャルでの疎通確認は今後の作業または人間による実施が必要。
- 5xx/timeoutのbounded retryはこのクライアントの責務外とし、将来のacquireコマンド(TASK-D007)に委ねた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D003 Snapshot metadata client

### 2026-07-14 00:30 UTC — セッション一時停止

**目的**

- TASK-D003(Snapshot metadata client)へ進む前に、実運用に必要な前提を確認する。

**発見事項・判断**

- ユーザーへ、Wikimedia Enterprise Snapshotの実取得にはWikimedia Enterpriseの実アカウント(`https://enterprise.wikimedia.com/`)登録とcredentials発行が必要であることを説明した。
- ユーザーはアカウント作成を先に行うことを選択し、TASK-D003以降の実装はアカウント作成後まで保留すると回答した。
- コード側(TASK-D001/D002)は実アカウントなしでオフラインテスト可能な形で完成しており、変更は不要。

**次タスク**

- ユーザーがWikimedia Enterpriseアカウントとcredentialsを用意した後、TASK-D003 Snapshot metadata clientを再開する。

### 2026-07-14 01:00 UTC — TASK-D003

**目的**

- Snapshot metadataクライアントを実装する。project/namespaceでSnapshotを絞り込み、`latest`のような曖昧な文字列を残さず1つの具体的versionへ解決する。

**変更**

- `src/wikiepwing/source/enterprise.py`に`SnapshotMetadataClient`、`SnapshotMetadataTransport` Protocol、`HttpSnapshotMetadataTransport`、`SnapshotCandidate`/`ResolvedSnapshot`を追加した。
- project/namespace不一致は明確な`SnapshotMetadataError`とし、該当Snapshotが1件も無い場合にMini/Liteを自動で品質低下させない方針(`ARCHITECTURE.md` 9.1)を守った。
- `latest`は列挙結果から`(date_modified, version_identifier)`最大のものへ解決し、戻り値へ`"latest"`という文字列を残さない。サーバ応答が`version: "latest"`を返す異常系も拒否した。
- メタデータ応答は4 MiB上限で読み、不正JSON・非配列・空配列・必須フィールド欠落・timezone欠落を拒否し、生レスポンスのSHA-256を`metadata_response_sha256`として返した(`DATA_CONTRACTS.md`のsource lock契約と整合)。
- `HttpSnapshotMetadataTransport`はhttps以外のbase URLと空`access_token`を拒否し、401/403/5xx/timeoutを即座に失敗させた。

**実行コマンド**

```bash
uv run pytest tests/test_enterprise_metadata.py
make check
git diff --check
```

**結果**

- 標準スイート153件(新規23件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- Snapshot一覧APIの実endpoint(`GET {api_base}/snapshots`)とレスポンス形状は、`ARCHITECTURE.md`のnestedオブジェクト形式(`namespace.identifier`等)からの類推であり、一次資料の確認記録が`SOURCES.md`にない。
- ユーザーはWikimedia Enterpriseアカウントを作成しusername/passwordを`.env`へ設定済みだが、本タスクはモック/テストダブルのみで実装し、実API呼び出しの疎通確認はまだ行っていない。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D004 Source lock schema、または実アカウントでの疎通確認(D002/D003)

### 2026-07-14 01:20 UTC — TASK-D002/D003 実アカウント疎通確認

**目的**

- ユーザーが`.env`へ設定した実Wikimedia Enterpriseアカウントで、TASK-D002(auth)/TASK-D003(Snapshot metadata)のコードを実際のAPIに対して疎通確認する。credentialsをログや文書へ出力しない。

**手順**

- スクラッチパッド上の一時スクリプト(リポジトリ外)から`.env`を読み、`EnterpriseAuthClient`→`SnapshotMetadataClient`の順で実行した。出力はtoken長・成功可否・snapshotのnon-secretフィールドのみに限定した。

**発見事項**

- `POST https://auth.enterprise.wikimedia.com/v1/login`は`username`/`password`フィールドで成功し、`access_token`(1067文字)を含むJSONを返した。TASK-D002の仮定は正しかった。
- `GET https://api.enterprise.wikimedia.com/v2/snapshots`は3,262件のproject×namespace entryを返した(応答約1.16 MB)。project/namespaceの絞り込みはserver側で行われず、client側filterが必須だった(設計通り)。
- 実レスポンス形状がTASK-D003の当初仮定と3点異なっていた。
  1. project識別子は`project.identifier`ではなく`is_part_of.identifier`。
  2. `size`はbyte数の整数ではなく`{"value": <float>, "unit_text": <string>}`という近似値オブジェクト。
  3. `chunks`という文字列配列が必須フィールドとして存在し、jawiki namespace 0は81個のchunk(`jawiki_namespace_0_chunk_0`〜`_80`)に分割されている。単一tar.gzという`ARCHITECTURE.md` 9.2の例示は簡略化だった。
- jawiki namespace 0のSnapshotは実際に1件だけ列挙され、2026-07-14時点でサイズ約30,896 MBだった。

**変更**

- `src/wikiepwing/source/enterprise.py`を実データに合わせて修正した: `is_part_of`フィールドの読取、`size_bytes: int`を`size_estimate: SnapshotSizeEstimate`(value/unit_text)へ変更、`chunk_identifiers: tuple[str, ...]`(非空必須)を追加した。
- `tests/test_enterprise_metadata.py`のfixtureとassertionを実データ形状に更新し、size/chunksの欠落・不正値を拒否するテストを追加した(23件→28件)。
- `SOURCES.md`に2026-07-14の実疎通確認内容(認証・Snapshot metadata APIの実フィールド)を記録した。
- `DECISIONS.md`にADR-016(Snapshotはchunk単位でdownloadする)を追加し、TASK-D005の設計方針とTASK-D004でのsource lock schema更新の必要性を明記した。

**実行コマンド**

```bash
uv run pytest tests/test_enterprise_metadata.py
make check
git diff --check
```

**結果**

- 標準スイート158件(新規28件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- credentials(username/password/access_token)は一度もファイル・ログ・本記録へ出力していない。一時検証スクリプトはリポジトリ外のスクラッチパッドに置き、コミットしていない。
- `ARCHITECTURE.md` 9.2のsource lock単一ファイル例は、TASK-D004(source lock schema)実装時に複数chunk対応へ更新する必要がある。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D004 Source lock schema(chunk単位の`files`配列を前提に設計する)

### 2026-07-14 01:40 UTC — TASK-D004

**目的**

- `source.lock.json`のJSON schemaと、それを構築・正準直列化・往復検証するモデルを実装する。ADR-016のchunk単位ダウンロードを前提にする。

**変更**

- `schemas/source-lock.schema.json`を追加した。`files`entryへ`chunk_identifier`を必須化し、`sha256`/`metadata_response_sha256`は64桁小文字hex、`snapshot_version`は`"latest"`を拒否する制約を持つ。
- `src/wikiepwing/source/lockfile.py`に`SourceLockFile`/`SourceLockAcquirer`/`SourceLock`、`build_source_lock`、`canonical_json`、`parse_source_lock`を実装した。
- `build_source_lock`はchunk_identifier/relative_path重複、絶対path、`.`/`..`セグメント、負のnamespace/size_bytes、不正な64桁hex、timezone-awareでないtimestamp、不正な`git_commit`を拒否する。
- `canonical_json`はtimestampをUTCへ正規化し秒精度のRFC3339へ固定するため、同じ内容は常に同じbytesになる。`parse_source_lock`で再parseし元のモデルと一致することを確認した。
- `DATA_CONTRACTS.md`のsource lock契約例を単一ファイルからchunk対応へ更新した。

**実行コマンド**

```bash
uv run pytest tests/test_source_lockfile.py
make check
git diff --check
```

**結果**

- 標準スイート180件(新規22件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際のfile書き込み・atomic replaceはTASK-D007(acquireコマンド)の対象とし、本タスクはモデルと直列化/parseのみに限定した。
- `git_commit`は呼び出し側が渡す前提とし、実行環境からの自動取得はacquireコマンド側の責務とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D005 Resumable downloader(ADR-016のchunk単位取得を前提に設計する)

### 2026-07-14 02:00 UTC — TASK-D005着手前の実ダウンロード疎通確認とセッション一時停止

**目的**

- TASK-D005(Resumable downloader)の実装前に、実credentialsでchunkダウンロードendpointの形状を確認する。TASK-D003で「Snapshot metadata形状の仮定が実データと異なっていた」ことを踏まえ、ダウンロード経路も先に実疎通確認する。

**発見事項**

- `GET https://api.enterprise.wikimedia.com/v2/snapshots/{chunk_identifier}/download` (Bearer認証)は307で署名付きS3 URLへredirectする。redirect先key名は`{chunk_identifier}_group_1.tar.gz`だった。
- 署名(`X-Amz-Expires=60`)は60秒で失効するため、resumable downloaderは大きなfileの途中で署名を再取得する設計が必要になる。
- redirect先S3 URLへは`Authorization`headerを転送してはいけない(転送すると`InvalidArgument: Only one auth mechanism allowed`)。素朴なurllibの自動redirect追従はこのheaderを保持するため使えず、redirectを手動処理してから素のGETを送る必要がある。
- 実際にS3 URLへRangeリクエストすると、jawiki namespace 0のchunkだけでなく最も小さい`aawiki_namespace_0_chunk_0`(約1 KB)でも一貫して`404 NoSuchKey`が返った。署名検証自体は通っている(`AccessDenied`や`SignatureDoesNotMatch`ではない)ため、リクエスト形式の誤りではなく、対象オブジェクトがバケットに実在しないことを示す。

**判断**

- ユーザーへ状況を説明し、TASK-D005の実装をコードのみ(モック/テストダブル)で進めるか、先にWikimedia Enterpriseアカウントのプラン・ダウンロード権限を確認するかを尋ねた。
- ユーザーは先にアカウントのプラン・権限を確認することを選択した。TASK-D005の実装はここで保留する。
- 探索に使った一時スクリプトはリポジトリ外のスクラッチパッドに置き、コミットしていない。credentialsは一切ログ・文書へ出力していない。

**次タスク**

- ユーザーがWikimedia Enterpriseアカウントのプラン・ダウンロード権限を確認した後、TASK-D005 Resumable downloaderを再開する。

### 2026-07-14 02:15 UTC — Chunk downloadエンドポイントの訂正

**目的**

- ユーザーが提示した公式APIリファレンス(login/snapshots/chunks/download)と照合し、前回の404がアカウント権限ではなくendpoint pathの誤りだったことを確認する。

**発見事項**

- 正しいchunk download pathは`GET /v2/snapshots/{snapshot_identifier}/chunks/{identifier}/download`であり、chunkはsnapshotと同列の`/v2/snapshots/{chunk_identifier}/download`ではなく子resourceだった。前回の疎通確認はこの誤ったpathを叩いていた。
- 正しいpathで実際にダウンロードが成功した: `jawiki_namespace_0`の`jawiki_namespace_0_chunk_0`に対し`Range: bytes=0-63`で`206 Partial Content`、`Content-Range: bytes 0-63/331920287`(chunk単体で約316 MB)、応答先頭はgzip magic numberで有効なtar.gzだった。Rangeが機能するため、resumable downloadは実現可能と確認した。
- S3 redirect先のkey構造は`chunks/{snapshot_identifier}/chunk_{N}_group_{M}.tar.gz`(前回誤って想定した`{chunk_identifier}_group_1.tar.gz`とは異なる)。
- Structured Contents Snapshot(`/v2/snapshots/structured-contents`)は9project(jawiki含まず)のみ対応という公式記載を確認し、ADR-002の判断が引き続き妥当であることを再確認した。

**変更**

- `SOURCES.md`のChunk download API節を、誤ったpathの記録から正しいpath・実測結果へ差し替えた。

**判断・注意点**

- アカウントのプラン・権限は問題ではなく、こちらのendpoint pathの誤りだった。ユーザーへの前回の説明(プラン起因の可能性)は誤りだったため訂正する。
- credentialsは引き続き一切ログ・文書へ出力していない。一時検証スクリプトはリポジトリ外に置き、コミットしていない。

**次タスク**

- TASK-D005 Resumable downloaderを、正しいchunk download endpointで実装する。

### 2026-07-14 02:30 UTC — TASK-D005

**目的**

- Snapshot chunkのresumable downloaderを実装する。正しいchunk download endpoint(`GET /v2/snapshots/{snapshot_identifier}/chunks/{identifier}/download`)を使い、Range再開・atomic rename・bounded retry・401/403即時失敗を持つ。

**変更**

- `src/wikiepwing/source/downloader.py`に`ResumableChunkDownloader`、`ChunkTransport` Protocol、`HttpChunkTransport`、`ChunkDownloadResult`、`ChunkDownloadError`/`ChunkDownloadAuthError`を実装した。
- `HttpChunkTransport`は自前の`HTTPErrorProcessor`overrideで自動redirect追従を無効化し、307等のredirectを手動処理してからS3 URLへ`Authorization`無しの素のGET(`Range`のみ)を送る。
- `ResumableChunkDownloader.download`は`.partial`ファイルの末尾からRangeで再開し、`Content-Range`/`Content-Length`で期待total sizeを検証、完了後にSHA-256を計算して`os.replace`でatomic renameする。401/403は即座に失敗、それ以外の失敗はbounded retry(既定5回)する。

**実行コマンド**

```bash
uv run pytest tests/test_chunk_downloader.py
make check
git diff --check
```

**実データ検証**

- 実credentialsで`aawiki_namespace_0_chunk_0`(1,252 bytes)を実際に完全ダウンロードし、gzip展開して`chunk_0.ndjson`が入っていることを確認した。
- 実ファイルを途中まで切り詰めた状態から実APIに対してresumeを実行し、フルダウンロードと完全に同一のbytesが得られることを確認した(resumeロジックが実データで実証された)。
- 検証に使った一時スクリプトはリポジトリ外に置き、コミットしていない。credentialsは一切出力していない。

**結果**

- 標準スイート205件(新規25件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 前回セッションの404は、アカウント権限ではなくendpoint pathの誤りだった(訂正済み、`SOURCES.md`参照)。
- disk空き容量の事前確認と`source.lock.json`書込はTASK-D007(acquireコマンド)へ委ねた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D006 Checksum and file fingerprint

### 2026-07-14 02:45 UTC — TASK-D006

**目的**

- fileのstreaming SHA-256計算とsize検証を1つの再利用可能なmoduleへ集約し、TASK-D005のdownloader内にあった同等ロジックの重複を解消する。

**変更**

- `src/wikiepwing/source/checksums.py`に`FileFingerprint`、`compute_fingerprint`、`verify_fingerprint`を実装した。symlink拒否、read失敗の明確なエラー、`read_chunk_bytes`非正値拒否、期待SHA-256の64桁小文字hex検証、負のsize拒否を持つ。
- `src/wikiepwing/source/downloader.py`の独自`_sha256_file`実装を削除し、`compute_fingerprint`を使うよう置き換えた。

**実行コマンド**

```bash
uv run pytest tests/test_checksums.py tests/test_chunk_downloader.py
make check
git diff --check
```

**結果**

- 標準スイート216件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- source.lock.jsonへの実際の検証呼び出しはTASK-D007(acquireコマンド)の対象とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D007 Acquire command

### 2026-07-14 03:00 UTC — TASK-D007

**目的**

- metadata解決→chunk download→verify→source.lock.json書込を1つのacquireオーケストレーションとCLIコマンドへ組み上げる。

**変更**

- `src/wikiepwing/source/acquire.py`に`acquire_snapshot`、`AcquireResult`、`AuthResolver`/`MetadataResolver`/`ChunkDownloader` Protocolを実装した。
- 既にdestinationが存在するchunkは再downloadせず`compute_fingerprint`で再計算し、新規downloadしたchunkは`verify_fingerprint`で再検証する。`snapshot_directory`・chunk destination・`sources_root`の絶対path/symlink検証を行う。
- `src/wikiepwing/cli.py`に`wikiepwing acquire`コマンドを追加した。`--namespace`/`--snapshot-version`/`--git-commit`のoverrideと、configからのendpoint/timeout/retry組み立て、`git rev-parse HEAD`によるgit commit自動解決(失敗時は`--git-commit`を明示要求)を実装した。
- `DATA_CONTRACTS.md`のsource lock例の拡張子を実データに合わせ`.ndjson.gz`から`.tar.gz`へ訂正した。

**実行コマンド**

```bash
uv run pytest tests/test_acquire.py tests/test_cli.py
make check
git diff --check
```

**実データ検証**

- 一時configで`project=aawiki`へ差し替え、実credentialsで`wikiepwing acquire --namespace 0 --snapshot-version latest`を実行した。
- 認証→metadata解決→chunk download→verify→`source.lock.json`書込までend-to-endで成功し、生成された`source.lock.json`は`DATA_CONTRACTS.md`契約通りの構造だった。SHA-256(`49b4b126e0831c71e6c83b2ddaba14607a4650d11bdb20cb7efad7acb7e1034b`)は前回セッションの手動疎通確認と一致した。
- 検証に使った一時スクリプトはリポジトリ外に置き、コミットしていない。credentialsは一切出力していない。

**結果**

- 標準スイート224件(新規7+1件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- disk空き容量事前確認はdoctorコマンド側の対象として残した。
- ローカル既存source登録(コピー無しのpredownloaded file利用)はTASK-D008の対象とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D008 Register local source

### 2026-07-14 03:20 UTC — TASK-D008

**目的**

- 既に取得済みのpredownloaded fileを、再downloadせずcopyまたはsymlinkでsource.lock.jsonへ登録できるようにする。

**変更**

- `src/wikiepwing/source/register.py`に`register_local_source`、`LocalSourceFile`、`RegisterError`を実装した。destinationが既に存在する場合は再copy/再symlinkせずfingerprintを再計算するだけにした。
- `copy=True`(既定)はatomic copy(一時file→fsync→`os.replace`)、`copy=False`は解決済み絶対pathへの`symlink_to`を使う。呼び出し側の`expected_sha256`と不一致なら拒否する。
- Wikimedia Enterprise metadataが存在しないため、`metadata_response_sha256`は登録入力の正準JSONへのSHA-256として合成した(同じ入力から決定的に同じ値になることを確認済み)。
- `SourceLock`のatomic書込を`lockfile.write_source_lock`として`lockfile.py`へ切り出し、`acquire.py`の重複private実装を解消して`register.py`と共有した。
- `src/wikiepwing/cli.py`に`wikiepwing register-local-source`コマンドを追加した(`--file PATH:CHUNK_IDENTIFIER[:SHA256]`複数指定、`--copy`/`--no-copy`、`--date-modified`、`--git-commit`)。完全オフラインで動作する。

**実行コマンド**

```bash
uv run pytest tests/test_register.py tests/test_cli.py
make check
git diff --check
```

**結果**

- 標準スイート238件(新規14件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `metadata_response_sha256`のローカル合成方式は一次資料が無いための仮定であり明示的に記録した。
- `source.provider`設定値自体の検証・切替はこのタスクの対象外とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D009 Source inspect command

### 2026-07-14 03:40 UTC — TASK-D009

**目的**

- `source.lock.json`を読み、記録済みfingerprintとの再検証(file)、tar構造の列挙(tar)、NDJSON内容のbounded sample(NDJSON)を行うinspectコマンドを実装する。

**変更**

- `src/wikiepwing/source/inspect.py`に`inspect_source`、`SourceInspection`、`FileInspection`、`TarMember`、`NdjsonSample`、`InspectError`を実装した。
- 各fileを`compute_fingerprint`で再検証し、一致した場合のみ`tarfile`でtar構造を列挙、`.ndjson`で終わるmemberを`readline(N+1)`でbounded sample・parseする。symlink登録されたfileは解決済み実体を対象にする。
- `src/wikiepwing/cli.py`に`wikiepwing inspect-source --lock-path --sample-lines`を追加した。JSON結果を出力し、不一致時は終了コード1を返す。完全オフライン動作。

**実行コマンド**

```bash
uv run pytest tests/test_source_inspect.py tests/test_cli.py
make check
git diff --check
```

**実データ検証**

- 実credentialsで`acquire`(project=aawiki)→`inspect-source`をend-to-endで実行し、`ok: true`、tar member `chunk_0.ndjson`、NDJSON sample1件を正しく取得した。
- sample内容から実際のWME記事レコードの全フィールド構造(`article_body.html`、`license`、`redirects`、`version`、`main_entity`等)が判明し、今後のEPIC E(Raw ingest)設計の参考情報として記録した。

**結果**

- 標準スイート254件(新規16件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `tarfile.getmembers()`はtar形式の性質上archive全体を順次スキャンする。bytes-in-memoryは境界内だが、大きなchunkでは時間がかかる。手動inspect用途として許容範囲とした。
- HTML/Wikitextの内容検証自体は対象外とし、NDJSON行がJSON objectとしてparseできることのみ確認する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-D010 Build sanitized NDJSON fixtures

### 2026-07-14 04:00 UTC — TASK-D010

**目的**

- TASK-D009で確認した実フィールド構造に基づき、EPIC E(Raw ingest)が使う10記事の正常fixtureと`PLAN.md`記載のedge case fixtureを作成する。

**変更**

- `tests/fixtures/enterprise/normal_articles.ndjson`(10記事)、`edge_case_articles.ndjson`(11行、8種のedge case)、`edge_case_index.json`(シナリオ名→行番号)を追加した。
- `tests/test_enterprise_fixtures.py`に12件のテスト(行数、必須フィールド、secrets不在、各edge caseの実在)を追加した。
- 実jawiki記事本文の再現ではなく、既存のhandcrafted fixture(Emacs/Linux系)と一貫したテーマの安全な合成内容を使った。

**実行コマンド**

```bash
uv run pytest tests/test_enterprise_fixtures.py
make check
git diff --check
```

**結果**

- 標準スイート266件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- fixture作成中にBashツールのコード実行系(`uv run`)が一時的に利用不能になったため、`jq`/`sed`で各edge caseの内容を1行ずつ手動検証してから、復旧後に自動テストで最終確認する手順を取った。
- malformed(JSON構文自体が壊れている)fixtureは対象外とし、将来のE004/E005タスクへ委ねた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- EPIC E(Raw ingest)のTASK-E001 raw DB migrations(依存: A003, D010は完了)

### 2026-07-14 04:20 UTC — TASK-E001

**目的**

- `raw.sqlite3`のSQL migrationと、それを安全に適用・検証・接続するmoduleを実装する。

**変更**

- `migrations/raw/001_initial.sql`に`DATA_CONTRACTS.md` 4節のtable(articles/redirects/categories/templates/licenses/article_licenses/main_images/ingest_duplicates/diagnostics/metadata)を作成した。全tableをSTRICT(`WITHOUT ROWID`と組み合わせを含む)とし、`migrations/reference`の慣例に合わせて長さCHECK制約を追加した。`PRAGMA application_id = 1380013892`(ASCII "RAWD")を設定した。
- `src/wikiepwing/ingest/database.py`に`connect_raw_database`/`initialize_raw_database`/`RawDatabaseError`を実装した。`reference/database.py`と同じmigration engineパターン(schema_migrations追跡、checksum検証、失敗時rollback、symlink/欠番/サイズ超過拒否)を踏襲した。

**実行コマンド**

```bash
uv run pytest tests/test_raw_database.py
make check
git diff --check
```

**結果**

- 標準スイート274件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- セッション中盤でBashツールのコード実行系(`uv run`/`python3`)が一時的に利用不能になったが、本タスク着手前に復旧した。
- `reference/database.py`と`ingest/database.py`のmigration engineロジックはほぼ同一で重複が生じているが、既存moduleへの影響を避けるため意図的に別moduleとして実装した。将来model/rendered/index dbが増える際に共通化を検討する。
- `DATA_CONTRACTS.md`のdraftには無い、`WITHOUT ROWID` tableへのSTRICT追加は契約に反しない強化として扱った。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E002 zstd codec

### 2026-07-14 04:35 UTC — TASK-E002

**目的**

- raw/model BLOB圧縮用のzstd codecを、決定的設定・roundtrip・入出力サイズ上限付きで実装する。

**変更**

- `pyproject.toml`へ実行時依存`zstandard==0.25.0`を追加した(プロジェクト初の実行時依存、`uv.lock`更新)。
- `src/wikiepwing/ingest/zstd_codec.py`に`compress`/`decompress`/`ZstdCodecError`を実装した。`threads=0`で単一スレッド圧縮とし決定性を保証、level 1〜22の範囲検証、入出力サイズ上限を持つ。
- decompress前に`get_frame_parameters`でframeの`content_size`を検査し、既知の宣言サイズが上限超過なら実際の展開前に拒否する。`ZSTD_CONTENTSIZE_UNKNOWN`/`_ERROR`のsentinel値は「未知」として扱い、`decompress()`自体の`max_output_size`で保護する。

**実行コマンド**

```bash
uv run pytest tests/test_zstd_codec.py
make check
git diff --check
```

**結果**

- 標準スイート286件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `zstandard`のAPIで`content_size`「未知」はNoneではなくsentinel整数(2^64-1等)で表現されることを実装中に発見し、正しく処理するよう修正した。
- `docker/app.Dockerfile`は`uv sync --frozen`で依存解決するため変更不要だった。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E003 Tar streaming reader

### 2026-07-14 04:50 UTC — TASK-E003

**目的**

- acquireされたchunkの`.tar.gz`から、全展開せずにNDJSON行をstreamingで読み出すreaderを実装する。

**変更**

- `src/wikiepwing/ingest/tar_reader.py`に`iter_ndjson_lines`、`TarStreamError`を実装した。`tarfile.open(..., mode="r|gz")`の純粋streamingモードで、唯一の`*.ndjson`通常file memberを検証してgeneratorとして1行ずつ返す。symlink・directory・path traversal名・2つ目のmemberを拒否する。streaming modeの制約上、「member数」検証はgenerator完全消費後に完了する(tarfileが未読データを自動skipする性質を利用)。
- 1行あたりのbyte数上限(既定8 MiB)を実装した。

**実行コマンド**

```bash
uv run pytest tests/test_tar_reader.py
make check
git diff --check
```

**結果**

- `tests/fixtures/enterprise/normal_articles.ndjson`(TASK-D010)を実際にtar.gz化し、end-to-endで10行すべて正しく読めることを確認した。
- 標準スイート298件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実データではchunk archiveが常に1 memberのみだった前提(TASK-D005/D009で確認済み)を踏襲し、複数member・0 memberを異常として拒否した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E004 NDJSON record parser

### 2026-07-14 05:05 UTC — TASK-E004

**目的**

- 1つのNDJSON行を型付き`RawArticle`へparseする。

**変更**

- `src/wikiepwing/ingest/record_parser.py`に`RawArticle`、`LicenseRecord`、`SourceImage`、`parse_record`、`RecordParseError`を実装した。required field(`identifier`/`version.identifier`/`name`/`namespace.identifier`/`url`/`date_modified`/`article_body`)を検証し、optional field(`html`/`wikitext`/`redirects`/`categories`/`templates`/`license`/`image`)の省略を許容する。
- `source_hash`は生NDJSON行のSHA-256とした。

**実行コマンド**

```bash
uv run pytest tests/test_record_parser.py
make check
git diff --check
```

**結果**

- TASK-D010の10正常記事+8 edge caseすべてを実際にparseし、期待通りの結果(html/wikitext省略、同page ID別revision、重複hash、conflicting hash等)を確認した。
- 標準スイート317件(新規19件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `image`フィールドの実shapeは未確認(実サンプルに存在しなかった)ため、`content_url`/`url`いずれかをbest-effortで受け入れる仮定とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E005 Record safety validation

### 2026-07-14 05:20 UTC — TASK-E005

**目的**

- parseされた`RawArticle`のfield length・URL形式・namespace一致・HTML/wikitext sizeを検証し、記事単位で受理/拒否と構造化診断を返す。

**変更**

- `src/wikiepwing/ingest/validate.py`に`ValidationLimits`(`from_config`)、`Diagnostic`、`ValidationResult`、`validate_article`を実装した。title/url/html/wikitext長超過、非https URL、namespace不一致を検出し、error重大度の診断があれば`accepted=False`とする。
- TASK-D010の`title_too_long` edge case(3549 bytes)が`config/default.toml`の実際の既定`max_title_bytes=4096`を超えていなかったため、5250 bytesへ拡張し修正した。

**実行コマンド**

```bash
uv run pytest tests/test_ingest_validate.py
make check
git diff --check
```

**結果**

- title長すぎ/invalid URL edge caseが正しく拒否され、正常な10記事は全件受理されることを確認した。
- 標準スイート332件(新規15件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ingest.strict_required_fields`設定の配線先(E004の必須field強制と記事単位skipの関係)は未決定のままTASK-E007/E008へ持ち越した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E006 Duplicate resolver

### 2026-07-14 05:35 UTC — TASK-E006

**目的**

- 同一page_idの重複記事を`ARCHITECTURE.md` 10.5の規則(revision ID優先、同revision同hashは無視、同revision異hashはfatal診断候補)で解決する。

**変更**

- `src/wikiepwing/ingest/deduplicate.py`に`ResolutionAction`、`ExistingArticleState`、`DuplicateRecord`、`Resolution`、`resolve_duplicate`を実装した。5種の決定(`FIRST_SEEN`/`REPLACED_BY_NEWER_REVISION`/`KEPT_EXISTING_NEWER_REVISION`/`IGNORED_IDENTICAL_DUPLICATE`/`CONFLICT_KEPT_EXISTING`)をrevision ID比較とhash比較のみで行い、titleは一切参照しない。
- conflict時は既存を安全側に維持しつつ`REC_REVISION_HASH_CONFLICT`診断(severity=error)を発行する。

**実行コマンド**

```bash
uv run pytest tests/test_deduplicate.py
make check
git diff --check
```

**結果**

- TASK-D010の3つのedge case(同page ID別revision、同revision同hash重複、同revision異hash)すべてが期待通りに解決されることを確認した。
- 標準スイート338件(新規6件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際のDB状態取得・`ingest_duplicates`書込はTASK-E007の責務とし、本タスクは純粋な決定ロジックのみとした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E007 Batch repository writer

### 2026-07-14 05:50 UTC — TASK-E007

**目的**

- `raw.sqlite3`への実際の書込を行うrepositoryを実装する。transaction・prepared SQL・foreign keyを守る。

**変更**

- `src/wikiepwing/ingest/repository.py`に`RawRepository`、`normalize_title`、`RawRepositoryError`を実装した。
- `get_existing_accepted`は`ingest_status='accepted'`の行のみを対象にする。`write_accepted_article`はUPSERT+zstd圧縮+子行のFK順序を守った置換、`write_rejected_article`はblob/子行無しで記録、`write_duplicate`/`write_diagnostic`は対応tableへ記録する。`batch()`がtransactionを管理する。

**実行コマンド**

```bash
uv run pytest tests/test_repository.py
make check
git diff --check
```

**結果**

- TASK-D010の10正常記事をすべて書込み、`PRAGMA integrity_check`/`foreign_key_check`が共に成功することを確認した。
- 標準スイート350件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- title正規化は最小限のNFKC+trimのみとし、実際の日本語索引正規化はEPIC Jへ委ねた。
- `validate_article`/`resolve_duplicate`の呼び出しはTASK-E008(Ingestコマンド)のオーケストレーション対象とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E008 Ingest command

### 2026-07-14 06:10 UTC — TASK-E008

**目的**

- TASK-E003〜E007を結合し、`source.lock.json`のchunkをstreaming取込→raw.sqlite3書込まで行う`wikiepwing ingest`コマンドを実装する。

**変更**

- `src/wikiepwing/ingest/orchestrate.py`に`run_ingest`、`IngestMetrics`、`IngestManifest`、`IngestResult`、`IngestError`を実装した。各chunkを事前に`verify_fingerprint`で検証してから、NDJSON streaming読取→parse→重複解決→安全性検証→repository書込の順で処理し、`batch_size`件ごとにtransaction commitする。
- `DATA_CONTRACTS.md` 3節のstage manifest契約に沿ったmanifestをatomic書込した(`logical_hash`/image digestはEpic S未整備のためnull)。
- `src/wikiepwing/cli.py`に`wikiepwing ingest --lock-path`コマンドを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_ingest_orchestrate.py tests/test_cli.py
make check
git diff --check
```

**結果**

- TASK-D010の10正常記事+8 edge case(11行)をend-to-endで取り込み、written=17イベント(16 distinct行、うち1件はrevision置換)、rejected=2、duplicate=3、error=3という期待通りの結果を確認した。
- 標準スイート356件(新規6件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `source_sequence`はchunkごとに0から再開し、chunk跨ぎの一意性・追跡性は保証しない(将来の課題として記録)。
- stage manifestはingest専用の実装であり、全stage共通化はTASK-I001で行う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E009 Raw verifier

### 2026-07-14 06:25 UTC — TASK-E009

**目的**

- 取込済み`raw.sqlite3`の整合性を検証するverifierを実装する。

**変更**

- `src/wikiepwing/ingest/verify.py`に`RawVerificationCounts`、`RawVerificationResult`、`verify_raw_database`を実装した。integrity_check/foreign_key_check、全table件数、`ROW_NUMBER() OVER`による決定的な等間隔sample抽出とhtml/wikitext blobの`decompress`検証を行う。
- `wikiepwing verify-raw --raw-database --sample-size`コマンドを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_ingest_verify.py tests/test_cli.py
make check
git diff --check
```

**結果**

- TASK-D010をTASK-E008で取り込んだDBに対し実際に検証し、`ok=True`・件数一致・sample展開成功を確認した。html_zstdを意図的に壊した行でも破損検出を確認した。
- 標準スイート362件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- sampleは決定的な等間隔抽出とした(再現性優先、真の乱数は使わない)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-E010 Interrupted ingest recovery

### 2026-07-14 06:40 UTC — TASK-E010

**目的**

- ingest実行が中断された場合の検出(`status="running"`のまま残るmanifest)と、再実行時の安全性を実装する。

**変更**

- `run_ingest`を、開始直後に`status="running"`のmanifestをatomic書込し、`finally`で成功時"complete"・例外時"failed"を必ず書き込んで例外を再raiseする構造へ変更した。
- `read_manifest_status`を追加した。既存manifestが`status="running"`のまま残っていれば`force=True`が無い限り新規実行を拒否し、壊れたmanifestも明確に拒否する。
- `run_ingest`/CLIへ`--force`を追加した。
- articles tableへの書込が重複解決ロジックにより冪等であることを、同じsource.lock.jsonへの2回連続実行(force=True)で確認した。diagnostics/ingest_duplicatesは現schemaでrun単位追跡が無く監査ログが重複しうることを既知の制約として文書化した。

**実行コマンド**

```bash
uv run pytest tests/test_ingest_orchestrate.py tests/test_cli.py
make check
git diff --check
```

**結果**

- chunk streaming中の失敗でmanifestが正しく"failed"になり例外が伝播すること、runningのまま残ったmanifestが新規実行を拒否すること、forceで上書きできることをすべてテストで確認した。
- 標準スイート369件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 汎用的なstage lock・resume判定はEPIC Iの対象として残し、本タスクはingest専用の最小実装に留めた。
- diagnostics/ingest_duplicatesへのrun_id列追加はschema変更を伴うため対象外とし、既知の制約として文書化した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- EPIC F(Model)のTASK-F001 Diagnostic model(依存: E001は完了済み)

### 2026-07-14 06:55 UTC — TASK-F001

**目的**

- 意味論モデル層の`Diagnostic`(`ARCHITECTURE.md` 11.7)を実装する。Article JSON contractの`diagnostics`配列要素として自己完結的に往復可能にする。

**変更**

- `src/wikiepwing/model/diagnostics.py`に`Diagnostic`、`parse_diagnostic`、`DiagnosticError`を実装した。ingest層の`wikiepwing.ingest.validate.Diagnostic`とは異なり、page_id/title/stageを自身に内包する自己完結型とした。

**実行コマンド**

```bash
uv run pytest tests/test_model_diagnostics.py
make check
git diff --check
```

**結果**

- 標準スイート381件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- ingest層Diagnosticからmodel層Diagnosticへの変換はEpic G以降のnormalize統合時に実装する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-F002 Inline model(`PLAN.md` Phase 6の初期対応範囲: text/strong/emphasis/internal link/external link/code/line break/unsupported)

### 2026-07-14 07:10 UTC — TASK-F002

**目的**

- `ARCHITECTURE.md` 11.3のInline unionのうち`PLAN.md` Phase 6の初期対応範囲を実装する。

**変更**

- `src/wikiepwing/model/inline.py`に8種のInline型(text/strong/emphasis/code/line_break/internal_link/external_link/unsupported)と`Inline` union、`inline_payload`/`parse_inline`を実装した。`InternalLinkInline`は`ARCHITECTURE.md` 11.4通りのfieldを持ち、`resolution`を検証する。

**実行コマンド**

```bash
uv run pytest tests/test_model_inline.py
make check
git diff --check
```

**結果**

- 全種別のroundtrip(nested inline含む)、未知typeの拒否、resolution検証を確認した。
- 標準スイート399件(新規18件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- math/ruby inlineは`PLAN.md` Phase 6の初期対応範囲外のため実装せず、将来epicまでは`UnsupportedInline`が受け皿になる。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-F003 Block model(`PLAN.md` Phase 5の初期対応block: Heading/Paragraph/List/DefinitionList/Quote/Preformatted/各種placeholder/Unsupported)

### 2026-07-14 07:45 UTC — TASK-F003

**目的**

- `ARCHITECTURE.md` 11.2のBlock unionのうち`PLAN.md` Phase 5/6の初期対応範囲を実装する。Table/InfoboxはARCHITECTURE.md 11.5/11.6の完全なfield構成を今のうちに定義する。

**変更**

- `src/wikiepwing/model/blocks.py`に15種のBlock型(paragraph/heading/unordered_list/ordered_list/definition_list/quote/preformatted/code/horizontal_rule/table/infobox/image/math/references/unsupported)と補助型(`ListItem`/`DefinitionEntry`/`TableCell`/`InfoboxField`)、`Block` union、`block_payload`/`parse_block`を実装した。`TableBlock`/`InfoboxBlock`は`ARCHITECTURE.md` 11.5/11.6通りのfieldを持つ。`ImageBlock`/`MathBlock`/`ReferencesBlock`は明文化された仕様が無いため、最小限のplaceholder形状とした(documented assumption)。

**実行コマンド**

```bash
uv run pytest tests/test_model_blocks.py
make check
git diff --check
```

**結果**

- 全15種のroundtrip(list/quote/table cell/infobox fieldのnested block、definition listのnested inline+blockを含む)、未知typeの拒否、`complexity`/`row_span`/`col_span`等のバリデーションを32件のテストで確認した。
- 標準スイート431件(新規32件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `NoticeBlock`は`PLAN.md`の初期rollout対象に無いため今回は実装しなかった。将来必要になった場合もunion拡張のみで既存コードへの破壊的変更は生じない設計。
- `ImageBlock`/`MathBlock`/`ReferencesBlock`のfield構成はARCHITECTURE.mdに明文化されていないため、最小限の仮設計とした。HTMLからの実際の変換(Epic G/K/L/N/O)実装時に必要に応じて拡張する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-F004 Article model(依存: F003)

### 2026-07-14 08:15 UTC — TASK-F004

**目的**

- `ARCHITECTURE.md` 11.1のArticle dataclass、13.3のalias(source/confidence)、15.2のMediaReferenceを実装する。

**変更**

- `src/wikiepwing/model/article.py`に`Article`/`Alias`/`MediaReference`と`payload()`/`parse_article`/`parse_alias`/`parse_media_reference`を実装した。`source_date_modified`はUTC ISO-8601(`...Z`)文字列として往復する。

**実行コマンド**

```bash
uv run pytest tests/test_model_article.py
make check
git diff --check
```

**結果**

- Article/Alias/MediaReferenceのroundtrip(nested blocks/aliases/media/diagnosticsを含む)、非UTCタイムゾーンの往復、各種バリデーション拒否を19件のテストで確認した。
- 標準スイート450件(新規19件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `Alias`の`source`値は`ARCHITECTURE.md` 13.3のalias候補一覧(redirects/記事title/normalized title variant/HTML display title/lead bold/Wikidata)から導出したdocumented assumptionである。
- Model validator(F005)とcanonical JSON codec/hash(F006)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-F005 Model validator(依存: F004)

### 2026-07-14 08:45 UTC — TASK-F005

**目的**

- `ARCHITECTURE.md` 24.3(Model verification)と`PLAN.md` Phase 5出口条件に基づき、Articleの意味的検証(`validate_article`)を実装する。dataclass構築時に検出できない不変条件(nesting深さ、internal linkのresolution/target_page_id整合性、埋め込みDiagnosticの一貫性)を対象とする。

**変更**

- `src/wikiepwing/model/validate.py`に`ModelValidationLimits`(`from_config`付き)と`validate_article`を実装した。block/list/quote/table/infobox/definition-listを横断するnesting深さ計算、`InternalLinkInline`のresolution⇔target_page_id整合性チェック、埋め込み`Diagnostic`のpage_id/title整合性チェックを行う。
- `src/wikiepwing/config.py`の`_SCHEMA`と`config/default.toml`に`[model]`セクション(`max_block_nesting_depth = 32`)を新設した。

**実行コマンド**

```bash
uv run pytest tests/test_model_validate.py tests/test_config.py
make check
git diff --check
```

**結果**

- nesting超過検出、link resolution/page_id不整合の両方向、diagnostic page_id/title不整合、妥当なArticleでの空diagnostics、config読み込みを11件のテストで確認した。
- 標準スイート461件(新規11件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- corpus全体でのpage_id一意性検証(`ARCHITECTURE.md` 24.3記載)は単一Articleのみを扱う本バリデータの範囲外とし、将来のcorpus組み立てstageに委ねる。
- serialization roundtripは既存のpayload/parse往復テストで担保済みのため、実行時チェックとしては実装していない。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-F006 Canonical JSON codec(依存: F004-F005)

### 2026-07-14 09:10 UTC — TASK-F006

**目的**

- `PLAN.md` Phase 5の"JSON debug codec"/"schema version"/"canonical ordering"を実装する。ハッシュ計算(TASK-F008)自体は対象外。

**変更**

- `src/wikiepwing/model/canonical.py`に`encode_article`/`decode_article`と`CanonicalCodecError`を実装した。`schema_version=1`のenvelope、`sort_keys=True`・`ensure_ascii=False`・固定`separators`による決定的出力を行う。

**実行コマンド**

```bash
uv run pytest tests/test_model_canonical.py
make check
git diff --check
```

**結果**

- roundtrip、2回encodeでのbyte完全一致、top-level key sort順、`schema_version`不一致/欠落・不正JSON・非object envelope・不正UTF-8・Articleフィールド不正の拒否を10件のテストで確認した。
- 標準スイート471件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- canonical JSON serializationのkey順/区切り/encodingルールは`ARCHITECTURE.md`/`DATA_CONTRACTS.md`に明文化が無かったため、`sort_keys=True`・`ensure_ascii=False`・`separators=(",", ":")`をdocumented assumptionとして採用した。
- `schema_version`はDATA_CONTRACTS.mdのArticle JSON例通りenvelope fieldとして扱い、Article dataclass自体には持たせていない。
- ハッシュ計算はTASK-F008に委ねる。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-F007 Compressed model DB schema(依存: F006)

### 2026-07-14 09:35 UTC — TASK-F007

**目的**

- `DATA_CONTRACTS.md` 5節の"model.sqlite3 schema draft"を実マイグレーションとして実装する。`migrations/raw/001_initial.sql` + `ingest/database.py`と同じ構造をmodel.sqlite3向けに再現した。

**変更**

- `migrations/model/001_initial.sql`(`PRAGMA application_id = 1297040460`〈ASCII "MODL"〉、`schema_migrations`/`articles`/`links`/`media_references`/`diagnostics`/`metadata`、STRICT/`WITHOUT ROWID, STRICT`/CHECK制約)を新規作成した。
- `src/wikiepwing/model/database.py`に`ModelDatabaseError`/`Migration`/`connect_model_database`/`initialize_model_database`を実装した(`ingest/database.py`のマイグレーションエンジンを踏襲、model向けにパス/エラーメッセージのみ変更)。

**実行コマンド**

```bash
uv run pytest tests/test_model_database.py
make check
git diff --check
```

**結果**

- schema作成・STRICT/PRAGMA検証、CHECK制約による不正行拒否、idempotentな再初期化、checksum不一致検出、失敗マイグレーションのrollback、gap/symlink/oversizedなmigration setの拒否を7件のテストで確認した。
- 標準スイート478件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。
- `docker/app.Dockerfile`は`COPY migrations ./migrations`で`migrations/`配下全体をコピーするため、`migrations/model/`は変更不要で自動的に含まれることを確認した。

**判断・注意点**

- Repository層(実際のarticle書き込み)は`TASK-G012`(依存: F007-F008,G011)に委ね、本タスクではschemaと接続/マイグレーションモジュールのみを実装した。`article_logical_hash`列はTASK-F008のhash関数が返す値を書き込む前提のCHECK制約(sha256 hex, 64文字)のみ定義した。
- `ingest/database.py`とのコード重複は既存の`raw`/`reference`データベースモジュール間の重複と同様、許容する判断とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-F008 Logical hash(依存: F006)

### 2026-07-14 10:00 UTC — TASK-F008

**目的**

- `TASKS.md` TASK-F008の完了条件("order-independent sources yield deterministic canonical output where contract permits")を満たすArticleのlogical hashを実装する。

**変更**

- `src/wikiepwing/model/logical_hash.py`に`compute_logical_hash(article) -> str`を実装した。`aliases`/`categories`/`media`/`diagnostics`/`source_license_ids`を安定キーでソートしてから`canonical.py`と同じ決定的JSON serialization(`sort_keys=True`/`ensure_ascii=False`/固定separators)でsha256 hex digestを計算する。`blocks`は本文順序が意味を持つため並べ替えない。

**実行コマンド**

```bash
uv run pytest tests/test_model_logical_hash.py
make check
git diff --check
```

**結果**

- hash長(64 hex)、決定性、categories/source_license_ids/aliases/media/diagnosticsの順序非依存性、blocks順序変更時のhash変化、内容差分時のhash変化を9件のテストで確認した。
- 標準スイート487件(新規9件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- どのcollectionを"order-independent"とみなすかは`ARCHITECTURE.md`/`DATA_CONTRACTS.md`に明文化が無かったため、抽出順序が非決定的になり得るaliases/categories/media/diagnostics/source_license_idsのみ正規化し、文書順序を持つblocks(と内部のinline/list item/table cell等)は対象外とするdocumented assumptionを採用した。
- EPWINGパッケージ出力のphysical/logical hash(`ARCHITECTURE.md` 26.1)とmodel DBへの実際の書き込み(TASK-G012)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- Epic F完了。TASK-G001以降(HTML normalization baseline)へ進む。

### 2026-07-14 10:25 UTC — TASK-G001

**目的**

- `TASKS.md` TASK-G001の実装要件("no network/entities、malformed recovery policy")を満たす安全なHTMLパーサーを実装する。

**変更**

- `src/wikiepwing/normalize/__init__.py`(新規パッケージ)を作成した。
- `src/wikiepwing/normalize/html_parser.py`に`parse_html`/`HtmlParseResult`/`ElementNode`/`TextNode`/`HtmlParseError`を実装した。標準ライブラリ`html.parser.HTMLParser`(`convert_charrefs=True`)を用い、外部ネットワークアクセスも外部entity解決も行わない。コメント/DOCTYPE/processing instructionは無視、void要素とself-closing要素を判定し、`max_dom_depth`を超えた要素はdiagnosticを記録した上で子要素として追加しない(それ以降の子孫は追加のdiagnosticなしで暗黙的に除外)。未対応の閉じタグ・EOF時の未クローズタグは`html_recover`設定に応じてdiagnostic記録または`HtmlParseError`送出のいずれかを行う。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_html_parser.py
make check
git diff --check
```

**結果**

- 要素木構築、属性保持、void/self-closing要素、コメント/DOCTYPE無視、entity/文字参照の安全なデコード、未対応閉じタグ・未クローズタグ・depth超過それぞれのrecover/raise両モード、空文書を15件のテストで確認した。
- 標準スイート502件(新規15件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- HTMLパーサーとして`lxml`等の新規依存を追加せず、標準ライブラリの`html.parser.HTMLParser`を採用した。ネットワークI/Oを一切行わずentityは組み込みテーブルのみで解決するため、XXE相当のリスクが構造的に存在しない。
- `max_dom_depth`超過時、境界を跨いだ要素についてのみdiagnosticを1件記録し、その配下の子孫については個別のdiagnosticを重複記録しない設計とした(病的に深い入力でdiagnostics件数が爆発しないようにするため)。
- Root content選択(G002)・unsafe/UI node除去(G003)・Block/Inlineへの実際の変換(G004以降)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G002 Root content selection(依存: G001)

### 2026-07-14 10:45 UTC — TASK-G002

**目的**

- `ARCHITECTURE.md` 12.2のpass `N10 Root selection`を実装する。HTML parse後・unsafe node除去前に、記事本文のcontent rootとなるcontainerを選択する。

**変更**

- `src/wikiepwing/normalize/root_selection.py`に`select_root_content(document) -> tuple[Node, ...]`を実装した。`class`属性に`mw-parser-output`トークンを含む最初の`div`を優先し、無ければ`<body>`、それも無ければdocument直下の子要素を返す。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_root_selection.py
make check
git diff --check
```

**結果**

- `mw-parser-output`優先選択(bodyにネストしている場合を含む)、fallback(body/document直下)、class token完全一致(部分文字列誤検知の回避)を5件のテストで確認した。
- 標準スイート507件(新規5件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ARCHITECTURE.md`/`DATA_CONTRACTS.md`/`PLAN.md`のいずれにも具体的なselector名は明文化されていなかった。`mw-parser-output`はMediaWiki/Wikimedia Enterpriseのレンダリング済みHTMLで本文をラップする一般的な規約であるため、これをdocumented assumptionとして採用した。実データでの検証は将来、実際のWikimedia Enterprise HTMLサンプルが入手できた時点で行う。
- Unsafe/UI node除去(G003)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G003 Unsafe/UI node removal(依存: G002)

### 2026-07-14 11:05 UTC — TASK-G003

**目的**

- `ARCHITECTURE.md` 12.2のpass `N20 Remove unsafe/non-content nodes`を実装する。12.1の必須安全策(script/style除去)と、12.3の除外候補のうち既存configフラグを持つ3種(edit UI/navbox/authority control)を対象とする。

**変更**

- `src/wikiepwing/normalize/html_parser.py`に`has_class(node, class_name)`ヘルパーを公開し、`root_selection.py`の重複ロジックをこれに置き換えた。
- `src/wikiepwing/normalize/unsafe_nodes.py`に`UnsafeNodeRemovalOptions`(`from_config`付き)と`remove_unsafe_nodes`を実装した。`script`/`style`は設定に関わらず常に除去し、`.mw-editsection`/`.navbox`/`.authority-control`はそれぞれ対応するconfigフラグが有効な場合のみ除去する。除去はネストした木構造に対して再帰的に行い、無関係な兄弟要素は保持する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_unsafe_nodes.py tests/test_normalize_root_selection.py
make check
git diff --check
```

**結果**

- script/style無条件除去、フラグON/OFFそれぞれでのedit UI/navbox/authority control除去・保持、再帰的除去と兄弟要素保持、除去対象が無い場合の空diagnosticsを13件のテストで確認した(既存のroot selectionテスト5件を含む)。
- 標準スイート515件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ARCHITECTURE.md` 12.3記載の他の除外候補(coordinates UI重複表示/hidden metadata/maintenance category表示/portal box/language switch UI)は、12.3自身が「情報を落とす可能性があるclassは、fixtureで確認してからruleへ追加します」と明記しており、具体的なclass名の裏付けが無い現時点では実装しなかった。
- 12.4記載のTOML `[[remove]]`/`[[classify]]`汎用ルールエンジン化は、既存のboolean flag方式(`config/default.toml`の`[normalize]`)からの大幅なconfig schema拡張を要するため見送り、既存のboolean flag方式を踏襲した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G004 Heading conversion(依存: G003)

### 2026-07-14 11:25 UTC — TASK-G004

**目的**

- `ARCHITECTURE.md` 12.2のpass `N30 Normalize headings and section anchors`を実装する。`<h1>`〜`<h6>`要素を`HeadingBlock`へ変換する。

**変更**

- `src/wikiepwing/normalize/headings.py`に`is_heading`/`convert_heading`を実装した。anchorは要素自身の`id`→ネストした子孫の`id`(`mw-headline`慣行)→平坦化テキストからのslug、の優先順で決定し、全て空の場合はfallback anchor `"section"`とdiagnosticを記録する。見出し内テキストは単一の`TextInline`へ平坦化する(豊かなinline変換はG005/G006以降)。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_headings.py
make check
git diff --check
```

**結果**

- h1〜h6判定、own id/nested id/slug fallbackそれぞれのanchor決定、ネストしたformatting要素のテキスト平坦化、空見出しでのdiagnostic記録、非見出し要素での`ValueError`を8件のテストで確認した。
- 標準スイート523件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- anchor生成アルゴリズムは`ARCHITECTURE.md`に明文化が無く、MediaWikiの一般的な慣行(own id / nested `mw-headline` id / テキストからのslug)をdocumented assumptionとして採用した。
- `TASKS.md`の依存グラフ上G004はG005(paragraph/text conversion)に依存しないため、見出し内容は単純なテキスト平坦化に留めた。豊かなinline変換への統合は将来必要になれば別タスクで検討する。
- 文書全体でのanchor一意性保証は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G005 Paragraph and text conversion(依存: G003)

### 2026-07-14 11:45 UTC — TASK-G005

**目的**

- `ARCHITECTURE.md` 12.2のpass `N50 Convert paragraphs and inline markup`の基礎(`<p>`要素の`ParagraphBlock`変換と、汎用的なinlineノード変換)を実装する。

**変更**

- `src/wikiepwing/normalize/paragraphs.py`に`convert_inline_nodes`/`is_paragraph`/`convert_paragraph`を実装した。テキストノードは`TextInline`へ変換し、未知のinline要素(現時点では全て)は透過的に子要素を再帰変換することで内容を失わない。TASK-G006はこの同じdispatchへ`<b>`/`<strong>`/`<i>`/`<em>`/`<code>`/`<br>`ハンドラを追加する形で拡張する設計とした。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_paragraphs.py
make check
git diff --check
```

**結果**

- テキスト変換、未知要素の透過的な再帰(順序保持、複数のnested wrapperをまたぐ場合を含む)、空段落、非`<p>`要素での`ValueError`を8件のテストで確認した。
- 標準スイート531件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 太字/斜体/code/line break等の具体的なinline要素認識は`TASK-G006`に委ねた。
- リスト/定義リスト/引用/preformatted等の他ブロック変換(G007以降)と、文書全体の組み立て(G010/G012)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G006 Strong/emphasis/code/line break(依存: G005)

### 2026-07-14 12:05 UTC — TASK-G006

**目的**

- `normalize/paragraphs.py`の`_convert_one`ディスパッチへ`<b>`/`<strong>`/`<i>`/`<em>`/`<code>`/`<br>`ハンドラを追加する。

**変更**

- `src/wikiepwing/normalize/paragraphs.py`を拡張し、`<b>`/`<strong>`→`StrongInline`(子要素を再帰変換)、`<i>`/`<em>`→`EmphasisInline`(同様)、`<code>`→`CodeInline`(子要素のテキストを平坦化、空なら省略)、`<br>`→`LineBreakInline`を実装した。
- `tests/test_normalize_paragraphs.py`の既存テストのうち、`<b>`が透過的に処理されることを前提にしていた1件を、真に未知の要素(`<span>`)を使うよう更新した(挙動が正当に変わったため)。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_inline_markup.py tests/test_normalize_paragraphs.py
make check
git diff --check
```

**結果**

- 各tagの変換、`<code>`のテキスト平坦化と空要素の省略、`<b><i>...</i></b>`のネスト保持、未知要素との混在時の透過的な再帰を9件の新規テスト(`tests/test_normalize_inline_markup.py`)で確認した。
- 標準スイート540件(新規9件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- internal/external linkのinline変換は本タスクの対象外(内部リンク解決は`ARCHITECTURE.md` 12.5に別途規定があり、実装タイミングは未定)。
- リスト/定義リスト/引用/preformatted等の他ブロック変換(G007以降)は対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G007 Ordered/unordered lists(依存: G005)

### 2026-07-14 12:25 UTC — TASK-G007

**目的**

- `ARCHITECTURE.md` 12.2のpass `N60 Convert lists`を実装する。`<ul>`/`<ol>`要素を`UnorderedListBlock`/`OrderedListBlock`へ変換する。

**変更**

- `src/wikiepwing/normalize/lists.py`に`is_unordered_list`/`is_ordered_list`/`convert_unordered_list`/`convert_ordered_list`を実装した。各`<li>`直下のテキスト/inline要素は`convert_inline_nodes`で変換して単一の`ParagraphBlock`にまとめ、ネストした`<ul>`/`<ol>`は独立した`Block`として`ListItem.blocks`に追加する(前後にinline contentがあれば別々のParagraphBlockに分離)。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_lists.py
make check
git diff --check
```

**結果**

- ul/ol判定、item毎のParagraphBlock生成、ネストしたlistの独立Block化(nested-onlyのitemで余分なParagraphBlockが生じないことを含む)、非対象要素での`ValueError`、`<li>`以外の子要素の無視、深いネストでの安定動作を10件のテストで確認した。
- 標準スイート550件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 任意のDOMノードをBlockへ振り分ける汎用dispatcherはTASK-G010/G012の範囲であるため実装せず、list itemの典型パターン(inline content + optional nested list)のみを扱った。
- 定義リスト(G008)・引用/preformatted(G009)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G008 Definition lists(依存: G005)

### 2026-07-14 12:45 UTC — TASK-G008

**目的**

- `<dl>`要素を`DefinitionListBlock`へ変換する(`ARCHITECTURE.md` 12.2のpass `N60`の一部)。

**変更**

- `src/wikiepwing/normalize/definition_lists.py`に`is_definition_list`/`convert_definition_list`を実装した。連続する`<dt>`を1entryのterms、続く連続する`<dd>`をそのentryのdefinitionsへグループ化し、`<dd>`の後に新しい`<dt>`が現れると新entryを開始する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_definition_lists.py
make check
git diff --check
```

**結果**

- dl判定、単一entry、複数termsのグループ化、複数definitionsのグループ化、dd後のdtによる新entry開始、非`<dl>`要素での`ValueError`、空`<dl>`を8件のテストで確認した。
- 標準スイート558件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 引用/preformatted(G009)と任意のDOMノード振り分けdispatcher(G010/G012)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G009 Quote/preformatted(依存: G005)

### 2026-07-14 13:05 UTC — TASK-G009

**目的**

- `<blockquote>`要素を`QuoteBlock`へ、`<pre>`要素を`PreformattedBlock`へ変換する(`ARCHITECTURE.md` 12.2のpass `N60`の一部)。

**変更**

- `src/wikiepwing/normalize/quotes.py`に`is_quote`/`is_preformatted`/`convert_quote`/`convert_preformatted`を実装した。blockquote内の`<p>`は個別に変換し、bare inline contentは1つの`ParagraphBlock`へまとめ、混在時は分離する。preformattedのテキストは空白・改行を一切正規化せず抽出する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_quotes.py
make check
git diff --check
```

**結果**

- quote/preformatted判定、単一/複数paragraph、bare inline contentとparagraphの混在分離、preformattedのwhitespace保持とnested要素の平坦化、非対応要素での`ValueError`を10件のテストで確認した。
- 標準スイート568件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ARCHITECTURE.md` 13.1("本文は過剰にNFKCしません")に基づき、preformattedのtext抽出は正規化を一切行わない。
- 任意のDOMノードをBlockへ振り分ける汎用dispatcherはTASK-G010/G012の範囲であるため対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G010 Unknown DOM fallback(依存: G004-G009)

### 2026-07-14 13:30 UTC — TASK-G010

**目的**

- G004-G009の各変換関数を1つのディスパッチャ(`convert_block`)にまとめ、認識できない要素を`UnsupportedBlock`+diagnosticで確実に情報保持するfallbackと、文書レベルで隣接する非ブロック要素を1つの`ParagraphBlock`にまとめる`convert_document`を実装する。

**変更**

- `src/wikiepwing/normalize/convert_block.py`に`convert_block`/`convert_document`を実装した。`convert_block`はheading/paragraph/unordered list/ordered list/definition list/quote/preformatted/`<hr>`をディスパッチし、それ以外は`UnsupportedBlock`(`element_name`/`fallback_text`/`diagnostic_code="DOM_UNKNOWN_ELEMENT"`)+diagnosticへfallbackする。`convert_document`は、既知のblock要素(変換対応済みのもの、および`table`/`div`/`figure`等の既知のHTML block-level tagでまだ変換未対応のもの)が現れるまで、素のテキスト/inline要素を1つの`ParagraphBlock`バッファへ蓄積する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_convert_block.py
make check
git diff --check
```

**結果**

- 各種要素のdispatch、`<hr>`変換、`<table>`等の未知要素のfallback(element_name/fallback_text/diagnostic_code)、文書レベルでの隣接する非ブロック要素のグループ化(単純なtext/inline混在、既知block要素での区切り)、空文書、fallback diagnosticsの伝播を11件のテストで確認した。テスト作成時に、未知のblock-level要素(`<table>`)がinline bufferへ誤って蓄積されるバグを発見し、`_is_block_level`にHTML標準のblock-level tag集合(`div`/`table`/`figure`等)を追加して修正した。
- 標準スイート579件(新規11件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `_ADDITIONAL_BLOCK_TAGS`(未変換だがinlineとして扱ってはいけないHTML標準block-level tag)はdocumented assumption。Table/Infobox/Image/Math/Referencesの実HTML変換はEpic K/L/N/O以降で、この一覧が置き換えられていく。
- 空白正規化(G011)とArticle/model DBへの統合(G012)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G011 Whitespace normalization(依存: G010)

### 2026-07-14 13:55 UTC — TASK-G011

**目的**

- `ARCHITECTURE.md` 13.1(保存用本文の処理)を実装するpass `N120 Normalize whitespace`を実装する。

**変更**

- `src/wikiepwing/normalize/whitespace.py`に`normalize_text`(CRLF→LF、C0/C1制御文字除去、ゼロ幅文字除去、連続空白の単一スペース圧縮)と`normalize_block_whitespace`(Block/Inlineの全variantを再帰的に処理)を実装した。`PreformattedBlock.text`/`CodeInline.value`/`CodeBlock.text`/`MathBlock.source`はverbatim保持のため変更しない。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_whitespace.py
make check
git diff --check
```

**結果**

- `normalize_text`の各変換(CRLF/CR→LF、制御文字除去、ゼロ幅文字除去、連続空白圧縮、冪等性)、Block木全体の再帰的正規化(paragraph/heading/nested strong/list/quote/unsupported fallback_text)、preformatted/code系のverbatim保持を14件のテストで確認した。
- 標準スイート593件(新規14件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- ゼロ幅文字の対象はZWSP(U+200B)/ZWNJ(U+200C)/ZWJ(U+200D)/BOM(U+FEFF)とした(明文化された一覧が無いためdocumented assumption)。
- 索引用文字列の正規化(13.2、NFKC/全角半角統一等)は別の関数・別タスクの範囲であり、本タスクでは実装していない。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G012 Normalize command and model DB write(依存: F007-F008,G011)

### 2026-07-14 14:20 UTC — TASK-G012

**目的**

- raw.sqlite3の`accepted`記事を読み、既存のHTML正規化パイプライン(G001-G011)経由でArticleを組み立て、`model/validate.py`で検証、`model/canonical.py`+`model/logical_hash.py`でcanonical JSON化・ハッシュ計算した上でzstd圧縮しmodel.sqlite3(TASK-F007のschema)へ書き込む。`ingest/orchestrate.py`と同じmanifest lifecycleパターンに従う。`wikiepwing normalize` CLIコマンドを追加する。

**変更**

- `src/wikiepwing/normalize/pipeline.py`に`NormalizeOptions`/`normalize_html`を実装した(parse→root selection→unsafe node除去→document変換→whitespace正規化を一関数化)。
- `src/wikiepwing/model/repository.py`に`ModelRepository`(batch書き込み、links/media_references/diagnostics子テーブルの置換)を実装した。
- `src/wikiepwing/normalize/orchestrate.py`に`run_normalize`/`NormalizeMetrics`/`NormalizeManifest`/`NormalizeResult`/`read_manifest_status`を実装した。raw.sqlite3の`redirects`/`categories`/`article_licenses`+`licenses`/`main_images`からAlias/categories/media/source_license_idsを組み立て、`normalize_status`を`complete`/`fallback`(UnsupportedBlockを含む)/`rejected`(validate_articleがerror/fatalを検出)の3値で判定する。
- `src/wikiepwing/cli.py`に`normalize`サブコマンドを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_pipeline.py tests/test_model_repository.py tests/test_normalize_orchestrate.py tests/test_cli.py
make check
git diff --check
```

**結果**

- pipeline統合(mw-parser-output選択、edit UI除去、whitespace圧縮、未知要素fallback、recovery無効時の例外伝播)、ModelRepositoryの書き込み・子テーブル置換、raw→normalize→model.sqlite3のend-to-end(`tests/fixtures/enterprise/normal_articles.ndjson`の10記事)・manifestのidempotent再実行・running manifest拒否/`--force`・CLI `normalize`サブコマンドを合計30件の新規テストで確認した。
- 標準スイート609件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実装中の静的レビューで、`ReferencesBlock.items`(`tuple[tuple[Inline,...],...]`)と`UnorderedListBlock.items`(`tuple[ListItem,...]`)が同名fieldだが型が異なるため、duck-typingしていたblock木走査ヘルパー(`_child_blocks`)がReferencesBlockに対して`AttributeError`を起こしうるバグを発見し、`isinstance`チェックへ修正した(`model/repository.py`・`normalize/orchestrate.py`双方)。現在のpipelineはReferencesBlockを生成しないため実害は無かったが、回帰テストを追加した。
- `<a>`要素の実HTML変換(internal/external link)はEpic Hの範囲であり本タスクでは実装していないため、`links`テーブルは現時点で実質空になる。`media`はraw.sqlite3の`main_images`由来のみとした。
- 作業中に長時間のBash実行環境の一時的な利用不可(safety classifier起因)が発生し、その間は静的コードレビューで対応し、上記バグを発見した。復旧後にテスト実行・確認を完了した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-G013 Baseline golden snapshots(依存: G012)

### 2026-07-14 14:45 UTC — TASK-G013

**目的**

- `PLAN.md` Phase 6出口条件"10記事golden一致"を実装する。`ARCHITECTURE.md`の`tests/golden/`ディレクトリ構成に沿って、初期対応範囲を代表する10個のHTML入力+期待Block JSON出力のペアを配置する。

**変更**

- `tests/golden/normalize/`に10組のHTML/JSONペアを新規作成した(01 heading+paragraph, 02 bold/italic, 03 ordered list, 04 nested unordered list, 05 definition list, 06 preformatted/code, 07 line break, 08 blockquote, 09 horizontal rule, 10 HTML entities+section anchor)。JSONは`normalize_html`の実出力を目視確認した上で`block_payload`でシリアライズして保存した。
- `tests/test_golden_normalize.py`に、10ファイルの存在確認と各fixtureの`normalize_html`出力が保存済みJSONと完全一致することを検証するparametrizeテストを実装した。

**実行コマンド**

```bash
uv run pytest tests/test_golden_normalize.py
make check
git diff --check
```

**結果**

- 10 golden fixtureすべてで`normalize_html`出力が保存済み期待値と完全一致し、diagnosticsが空であることを11件のテストで確認した。
- 標準スイート620件(新規11件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- internal/external link(Epic H未実装)、Table/Infobox/Image/Math/References(Epic K/L/N/O未実装)を含むgolden fixtureは対象外とした。
- これでEpic G(HTML normalization baseline)が完了した。

**次タスク**

- Epic H(Links and Mini rendering)へ進む。

### 2026-07-14 15:05 UTC — TASK-H001

**目的**

- `ARCHITECTURE.md` 12.5(内部リンク解決)の手順1-4(URL decode/fragment分離/project base URL確認/namespace-title抽出)を実装する。

**変更**

- `src/wikiepwing/links/__init__.py`(新規パッケージ)、`src/wikiepwing/links/url_parser.py`に`parse_internal_url`/`ParsedInternalUrl`/`UrlParseError`を実装した。`/wiki/Title`(site-relative)・project base URLに一致する完全URL・`./Title`(document-relative)の3形状を解析し、fragment分離、percent-decoding、underscore→space変換、既知namespace prefix(Category等)検出を行う。該当しないURLは外部linkとして`None`を返す。

**実行コマンド**

```bash
uv run pytest tests/test_links_url_parser.py
make check
git diff --check
```

**結果**

- 3種のURL形状の解析、fragment分離、percent-encoding+underscore decode(実データ由来の`GNU%E3%83%97...`→`GNUプロジェクト`を含む)、既知/未知namespace prefixの判別、外部URL・非wikiパス・空URLでの拒否を12件のテストで確認した。
- 標準スイート632件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 既知namespace prefix一覧(Category/Template/File/Talk/User/Wikipedia/Help/Portal/Module/MediaWiki/Special、及びtalk派生)はMediaWikiの一般的な慣行に基づくdocumented assumption。
- page ID解決(手順6)・redirect扱い(手順7)・EPWING entry ID変換(手順8)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H002 Internal target resolver(依存: H001,E008)

### 2026-07-14 15:25 UTC — TASK-H002

**目的**

- `ARCHITECTURE.md` 12.5の手順5-7(normalized title生成/raw DBでpage ID解決/redirect targetの扱い)を実装する。

**変更**

- `src/wikiepwing/links/resolver.py`に`resolve_internal_link`/`ResolvedLink`を実装した。`ingest/repository.py`の`normalize_title`を再利用し、raw.sqlite3の`articles.normalized_title`直接一致→`redirects.normalized_redirect_title`一致(`follow_redirects`制御)→`missing`の順で解決する。`parsed.namespace`が非`None`(Category等)の場合は本プロジェクトの初期scope(namespace 0のみ取り込み)の範囲外として`externalized`を返す。

**実行コマンド**

```bash
uv run pytest tests/test_links_resolver.py
make check
git diff --check
```

**結果**

- 直接一致解決、redirect経由解決(`follow_redirects`のON/OFF)、非一致時の`missing`、namespace付きlinkの`externalized`、fragment保持を6件のテストで確認した。
- 標準スイート638件(新規6件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- namespace付きlinkを`externalized`とする判断は、本プロジェクトの初期scope(`source.namespace=0`)がnamespace 0のみを取り込む前提に基づくdocumented assumption。
- EPWING entry IDへの変換、External link policy(H003)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H003 External link policy(依存: H001)

### 2026-07-14 15:45 UTC — TASK-H003

**目的**

- `ARCHITECTURE.md` 12.5最終行"外部サイトへのリンクはplain URLまたは注記として残します"を実装する。H001が内部linkでは無いと判定したURLを安全に`ExternalLinkInline`化するか、labelのみへfallbackする。

**変更**

- `src/wikiepwing/links/external_policy.py`に`apply_external_link_policy`/`ExternalLinkPolicyError`を実装した。`http`/`https`および`//host/...`(protocol-relative、`https:`を補完)のみを`policy="plain-text"`で`ExternalLinkInline`化し、`javascript:`/`data:`/`mailto:`等の安全でないURLはlabelをそのまま返す(情報を失わない)。未知の`policy`値は明示的にエラーとする。

**実行コマンド**

```bash
uv run pytest tests/test_links_external_policy.py
make check
git diff --check
```

**結果**

- http/https/protocol-relativeの`ExternalLinkInline`化、javascript:/data:/mailto:のlabelのみfallback、未知policyの拒否、空labelの保持を8件のテストで確認した。
- 標準スイート646件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 現時点で`config/default.toml`の`[references] external_urls`には`"plain-text"`のみが設定されており、他のpolicy値は明文化されていないため`"plain-text"`のみを受け付ける設計とした。将来別の値(footnote等)が必要になれば拡張する。
- Redirect alias抽出(H004)、References/footnote sectionでの実際のrendering(Epic L)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H004 Redirect alias extraction(依存: E008)

### 2026-07-14 16:05 UTC — TASK-H004

**目的**

- `ARCHITECTURE.md` 13.3(alias source: redirects)を独立した公開関数として実装する。TASK-G012実装時に`normalize/orchestrate.py`へprivateに埋め込んでいた同等ロジックを`links`パッケージへ移設する。

**変更**

- `src/wikiepwing/links/redirect_aliases.py`に`extract_redirect_aliases(connection, page_id) -> tuple[Alias, ...]`を実装した(`source="redirect"`, `confidence=1.0`固定)。
- `src/wikiepwing/normalize/orchestrate.py`の`_read_aliases`を削除し、この関数を利用するようリファクタした。

**実行コマンド**

```bash
uv run pytest tests/test_links_redirect_aliases.py tests/test_normalize_orchestrate.py
make check
git diff --check
```

**結果**

- ordinal順でのalias抽出、該当redirectが無い場合の空tuple、既存のnormalize orchestrationのend-to-endテストが引き続き成功することを7件のテストで確認した。
- 標準スイート648件(新規2件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- redirect以外のalias source(title/normalized title variant/HTML display title/lead bold/Wikidata)は本タスクの対象外、将来のtaskで対応する。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H005 Stable entry IDs(依存: F004)

### 2026-07-14 16:20 UTC — TASK-H005

**目的**

- `ARCHITECTURE.md` 16.1(entry ID: `p<page_id>`)を実装する。

**変更**

- `src/wikiepwing/render/__init__.py`(新規パッケージ)、`src/wikiepwing/render/entry_id.py`に`compute_entry_id`/`EntryIdError`を実装した。

**実行コマンド**

```bash
uv run pytest tests/test_render_entry_id.py
make check
git diff --check
```

**結果**

- `p<page_id>`形式の生成、page_id 0以下の拒否を4件のテストで確認した。
- 標準スイート652件(新規4件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- RenderedEntry model本体(H006)・Mini layout renderer(H007)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H006 RenderedEntry model(依存: H005)

### 2026-07-14 16:40 UTC — TASK-H006

**目的**

- `ARCHITECTURE.md` 16(RenderedEntry)を実装する。型定義のみを対象とし、ArticleからRenderedEntryへの実際の変換はTASK-H007の範囲とする。

**変更**

- `src/wikiepwing/render/render_node.py`に`TextRenderNode`/`LineBreakRenderNode`/`RenderNode`を実装した(`ARCHITECTURE.md`にRenderNodeの詳細仕様が無いため、H007が拡張できる最小限のtext/line break表現とした)。
- `src/wikiepwing/render/rendered_entry.py`に`RenderedEntry`(`entry_id`/`page_id`/`title`/`headwords`/`body`/`internal_targets`/`graphics`/`estimated_size`/`diagnostics`)と`RenderedEntryError`を実装した。

**実行コマンド**

```bash
uv run pytest tests/test_render_render_node.py tests/test_render_rendered_entry.py
make check
git diff --check
```

**結果**

- RenderNode2種の構築、RenderedEntryの構築とfield保持、entry_id/page_id/title/estimated_sizeのバリデーション拒否を8件のテストで確認した。
- 標準スイート660件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `RenderNode`の具体的な形状は`ARCHITECTURE.md`に明文化が無いため、text/line breakのみの最小限のdocumented assumptionとした。Table/Infobox等の表現が必要になれば、H007以降で拡張する。
- ArticleからRenderedEntryへの実際の変換(H007)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H007 Mini layout renderer(依存: H006,G012)

### 2026-07-14 17:10 UTC — TASK-H007

**目的**

- `ARCHITECTURE.md` 16.2(標準レイアウト)を実装する。ArticleをRenderedEntryへ変換する。

**変更**

- `src/wikiepwing/render/mini_layout.py`に`render_article_to_entry`を実装した。title/別名/更新日/導入文/見出し番号付き本文(`_HeadingNumberer`によるsibling連番・nesting復帰)/カテゴリ/出典情報をplain textへ変換する。paragraph/list/definition list/quote/preformatted/code/horizontal rule/unsupportedの各blockに対応する。`internal_targets`は`InternalLinkInline`(resolution="resolved")をblock木から収集し`compute_entry_id`で変換する。

**実行コマンド**

```bash
uv run pytest tests/test_render_mini_layout.py
make check
git diff --check
```

**結果**

- entry_id一致、title/更新日/導入文の本文出力、headwords(title+aliases)、見出し番号付け(兄弟連番・深いネストからの復帰)、カテゴリ/出典情報、list/horizontal rule/preformatted/unsupported fallback_textの出力、estimated_sizeのUTF-8バイト数一致、diagnostics引き継ぎ、internal_targetsの抽出(resolved/missing双方)を12件のテストで確認した。
- 標準スイート672件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- Table render policy(16.3)・Entry size budget超過時の分割(16.4)は対象外とした。現状Table/InfoboxBlockを生成する変換器が無く(Epic K/L未実装)発生しない。
- `RenderNode`は現時点で単一の`TextRenderNode`にレイアウト全体を格納する形とした(構造化が必要になればH007以降で見直す)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H008 SearchTerm model and title terms(依存: H004,H006)

### 2026-07-14 17:30 UTC — TASK-H008

**目的**

- `ARCHITECTURE.md` 14.1(SearchTerm)を実装し、Articleから記事title自身とredirect由来aliasを`SearchTerm`列(title terms)へ変換する関数を実装する。

**変更**

- `src/wikiepwing/search/__init__.py`(新規パッケージ)、`src/wikiepwing/search/search_term.py`に`SearchTerm`/`SearchTermError`/`title_terms_for_article`を実装した。`kind="title"`(priority=0)と`kind="redirect"`(priority=10、`source="redirect"`のaliasのみ対象)を生成する。

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- SearchTermのバリデーション(key/target_page_id/kind)、title termの生成、redirect aliasからのterm生成、非redirect aliasの除外、priorityの大小関係を7件のテストで確認した。
- 標準スイート679件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- reading/category/keyword/cross_component kindの生成、衝突規則(14.2)、プロファイル別索引(14.3)は本タスクの対象外。
- priority値(title=0, redirect=10)は具体的な数値がARCHITECTURE.mdに明文化されていないためdocumented assumption。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H009 FreePWING source writer(依存: B009,H007-H008)

### 2026-07-14 18:15 UTC — TASK-H009

**目的**

- `ARCHITECTURE.md` 17.2(FreePWING adapterの責務"FreePWING source file生成")を実装する。任意件数・可変alias数・可変target数の`RenderedEntry`を`FreePWING::FPWUtils::FPWParser` Perl APIへ渡し、`fpwmake`が消費するsourceを生成する。

**変更**

- `src/wikiepwing/render/freepwing_source.py`に`write_entries_jsonl`を実装した(`RenderedEntry`列をtag/title/aliases/body/targetsのJSON Linesへ書き出す)。
- `docker/toolchain/freepwing_build_entries.pl`に汎用Perl driverを実装した。既存の`tests/fixtures/handcrafted/build_fixture.pl`(entry数3・alias数2に固定)を一般化し、任意件数・可変alias数・可変target数を処理する。UTF-8のJSON Linesを`Encode::encode('euc-jp', ...)`でEUC-JPへ変換してから`FPWParser`へ渡す(既存smoke testの`iconv`変換と同等の処理をPerl側で行う)。
- `docker/toolchain/freepwing-build-entries-smoke.sh`に実Docker end-to-end smoke testを実装した。Python側`write_entries_jsonl`で3entry(alias数0/1/4、target数0/1/2)のJSON Linesを生成し、Perl driver経由で`fpwmake`を実行、`wikiepwing-eb-search`で実際にtitle/alias headwordが正しく検索・解決できることを検証する(単なる非クラッシュ確認ではなく、実際のcontent検証)。
- `Makefile`に`test-freepwing-build-entries`ターゲットを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_render_freepwing_source.py tests/test_freepwing_build_entries_smoke.py
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
make check
git diff --check
```

**結果**

- Python側writer(JSON Lines書き出し、alias/target無しの場合、複数entry順序、親ディレクトリ作成、複数行bodyの保持)を10件のテストで確認した。
- 実Docker smoke testを`wikiepwing-toolchain:dev`イメージ(ローカルに既存)で実行し、`honmon`/`work/cgr`生成に加え、`wikiepwing-eb-search`で実際に"Entry One"(title)と"Alias A"(4alias中の1つ)を検索し、それぞれ異なる正しいheadingへ解決することを実機で確認した(単体テストでは検証できないPerl/FreePWING toolchain統合の実地検証)。
- 標準スイート689件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実装中、`iconv`によるUTF-8→EUC-JP変換ステップを見落とし、生成したJSON LinesをそのままFPWParserへ渡すバグに気づいた(ASCII文字のみのsmoke test entryでは偶然動作していたが、日本語文字では文字化けする設計ミス)。Perlスクリプト内で`Encode::encode('euc-jp', ...)`を明示的に適用する修正を行った。
- `fpwmake`が全ての外部スクリプトへ`-workdir work`引数を渡すこと、および`FreePWING::FPWUtils::FPWParser`のuse時に`@ARGV`からこれを消費する挙動(スクリプト側で明示的な引数処理をしていないにも関わらず正しく動作する理由)を実機検証で確認した。
- graphic/gaijiの実際の登録内容の一般化、EPWING generate command全体の配線(H010)、catalog/subbook設定の動的生成は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H010 EPWING generate command(依存: H009)

### 2026-07-14 18:40 UTC — TASK-H010

**目的**

- `ARCHITECTURE.md` 17.1/17.2に基づき`wikiepwing generate` CLIコマンドを実装する。model.sqlite3の`normalize_status != 'rejected'`な記事を`RenderedEntry`へ変換し`entries.jsonl`へ書き出す。実際の`fpwmake`実行・catalog/subbook動的生成・実運用gaiji管理は対象外(未実装の前提subsystemが必要なため)。

**変更**

- `src/wikiepwing/render/generate.py`に`run_generate`/`GenerateMetrics`/`GenerateManifest`/`GenerateResult`/`read_manifest_status`を実装した(`ingest`/`normalize`と同じmanifest lifecycle)。model.sqlite3の各記事をzstd展開+`decode_article`でArticle化し、`render_article_to_entry`でRenderedEntry化、`rejected`をスキップしてカウントし、`write_entries_jsonl`で書き出す。
- `src/wikiepwing/cli.py`に`generate`サブコマンドを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_render_generate.py tests/test_cli.py
make check
git diff --check
```

**結果**

- rejected記事の除外、manifestのrunning/complete/failed lifecycle、`--force`挙動、CLI `generate`サブコマンド(register-local-source→ingest→normalize→generateの実end-to-end連鎖含む)を22件のテスト(新規)で確認した。
- 標準スイート695件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際の`fpwmake`実行によるEPWINGバイナリ生成・catalog/subbook設定の動的生成・実運用gaiji文字集合管理は、これらのsubsystem自体が未実装のため対象外とした。TASK-H009で構築済みの`freepwing_build_entries.pl`は本コマンドが生成する`entries.jsonl`をそのまま読めるため、手動運用としては既に接続可能。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H011 EPWING verifier baseline(依存: H010)

### 2026-07-14 19:00 UTC — TASK-H011

**目的**

- `ARCHITECTURE.md` 7.1の`wikiepwing verify`コマンドの基礎を実装する。`entries.jsonl`(TASK-H010出力)に対し、`freepwing_build_entries.pl`(TASK-H009)がPerl側で行っているのと同じ不変条件をDocker無しでPython側から先に検査する。

**変更**

- `src/wikiepwing/render/verify.py`に`verify_entries_jsonl`/`VerificationResult`/`VerificationIssue`/`EntriesVerificationError`を実装した。空tag/空title/重複tag/entry間の重複headword/未知link targetを検出する。
- `src/wikiepwing/cli.py`に`verify`サブコマンド(`--entries`)を追加した。

**実行コマンド**

```bash
uv run pytest tests/test_render_verify.py tests/test_cli.py
make check
git diff --check
```

**結果**

- 正常entries、空tag/空title/重複tag/entry間重複headword(entry内の同一headwordは許容)/未知target/空ファイル/不正JSON/ファイル欠如それぞれの検出を10件のテストで確認した。CLI側は`register-local-source`→`ingest`→`normalize`→`generate`→`verify`の実end-to-end連鎖、および問題ありreportでの非0終了コードを含め追加のテストで確認した。
- 標準スイート707件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際に構築されたEPWINGバイナリ(honmon等)へのEB Library経由の検証は本タスクの対象外とし、Docker不要で高速に実行できるentries.jsonlレベルの静的検査に留めた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H012 100-article fixture(依存: D010)

### 2026-07-14 19:20 UTC — TASK-H012

**目的**

- `TASK-D010`の10記事`normal_articles.ndjson`を拡張し、`TASK-H013`(Mini end-to-end build)向けに100記事規模のfixtureを作成する。

**変更**

- `tests/fixtures/enterprise/generate_hundred_articles.py`(決定的生成スクリプト)と、それが生成する`tests/fixtures/enterprise/hundred_articles.ndjson`(100記事)を追加した。既存の`normal_articles.ndjson`と同じWikimedia Enterprise NDJSONスキーマに従い、redirect数(0-2)・category数(1-2)・画像fieldの有無を記事ごとに変化させ、`article_body.html`内に他fixture記事への内部link(`/wiki/Title`形式)を含める。

**実行コマンド**

```bash
uv run python3 tests/fixtures/enterprise/generate_hundred_articles.py
uv run pytest tests/test_hundred_articles_fixture.py
make check
git diff --check
```

**結果**

- 100記事であること、identifierの一意性、既存スキーマとの整合、redirect数の分布、内部linkが他fixture記事のみを指すこと、生成スクリプトの決定性(2回実行して同一出力)を6件のテストで確認した。
- 標準スイート713件(新規6件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- identifier範囲は既存fixture(`normal_articles.ndjson`の900xxx、`edge_case_articles.ndjson`の1100xxx)と衝突しないよう920001-920100とした。
- Mini end-to-end build自体の実行・検証は本タスクの対象外(TASK-H013)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-H013 Mini end-to-end build(依存: H011-H012)

### 2026-07-14 19:45 UTC — TASK-H013

**目的**

- `DECISIONS.md` ADR-015の100記事Gateとして、`register-local-source`→`ingest`→`normalize`→`generate`→`verify`の全パイプラインを100記事fixtureに対してend-to-endで実行し、加えて実toolchainで実際にhonmonを構築して`wikiepwing-eb-search`で検証する。

**変更**

- `tests/test_mini_end_to_end_build.py`にPython側のみのend-to-endテスト(Docker不要)を実装した。100記事fixtureを`register_local_source`→`run_ingest`→`run_normalize`→`run_generate`→`verify_entries_jsonl`に通し、各manifestが`complete`になること、100記事すべてが処理されること、`entries.jsonl`が100件・一意なtagを持ちverifyでokになることを検証する。
- `docker/toolchain/mini-end-to-end-smoke.sh`に実Docker toolchainでの検証を実装した。同じPythonパイプラインをコンテナ内で実行して`entries.jsonl`を生成し、`freepwing_build_entries.pl`(TASK-H009)経由で実際に100記事分のhonmonを構築、`wikiepwing-eb-search`で複数の異なるtitle("Emacs"、"Linux"、"GNU Project")とalias("Vim alias")が正しく解決できることを実機で確認した。
- `Makefile`に`test-mini-end-to-end`ターゲットを追加した。

**実行コマンド**

```bash
uv run pytest tests/test_mini_end_to_end_build.py
sh docker/toolchain/mini-end-to-end-smoke.sh wikiepwing-toolchain:dev
make check
git diff --check
```

**結果**

- Python側end-to-endテストが成功した(標準スイートに追加、Docker不要)。
- 実Docker smoke testを`wikiepwing-toolchain:dev`イメージで実行し、100記事から実際にhonmonを構築、4種類の異なるtitle/aliasクエリすべてで正しいhitを確認した(単なる非クラッシュ確認ではなく実際のcontent検証)。
- 標準スイート714件(新規1件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 現時点で`<a>`要素の実HTML変換(internal link conversion)は未実装(Epic H内でURL解析/解決モジュールH001-H004は独立して構築済みだが、normalize pipeline自体への統合はまだ)であるため、fixture内の内部linkは本文中のplain textとして扱われ、`internal_targets`は実質空になる。これは既知の制約であり、本タスクの検証対象外とした。
- これでEpic H(Links and Mini rendering)が完了した。

**次タスク**

- TASK-I001 Stage manifest schema(依存: E008,G012,H010)

### 2026-07-14 20:10 UTC — TASK-I001

**目的**

- `DATA_CONTRACTS.md` 3節(Stage manifest contract)を形式化した共有モジュールを実装し、`ingest/orchestrate.py`・`normalize/orchestrate.py`・`render/generate.py`に重複していたmanifest読み込み・atomic書き込みロジックを集約する。

**変更**

- `src/wikiepwing/pipeline/__init__.py`(新規パッケージ)、`src/wikiepwing/pipeline/stage_manifest.py`に`validate_stage_manifest_payload`(envelope必須field・status enum検証)/`read_manifest_payload`/`extract_status`/`write_stage_manifest_payload`(atomic書き込み)を実装した。
- `ingest/orchestrate.py`・`normalize/orchestrate.py`・`render/generate.py`の`read_manifest_status`/`_write_manifest`を共有実装を呼び出す薄いwrapperへリファクタし、重複していたJSON parse/atomic write処理を削除した。各モジュール固有の例外型(`IngestError`/`NormalizeError`/`GenerateError`)とエラーメッセージ文言は保持し、既存テストの後方互換性を維持した。

**実行コマンド**

```bash
uv run pytest tests/test_pipeline_stage_manifest.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py
make check
git diff --check
```

**結果**

- `validate_stage_manifest_payload`の必須field検証・status enum全値受理・不正値拒否、read/write往復、atomic書き込みのJSON妥当性を25件のテストで確認した。
- リファクタ中に実際のバグを発見した: `read_manifest_payload`に`validate_stage_manifest_payload`のフル検証を組み込んだ結果、既存テストが使う最小限の`{"schema_version":1,"status":"running"}`形式のmanifest(running中かどうかのチェック専用、fullなenvelopeを意図的に持たない)が「missing required field」で拒否されるようになり、2件のテストが壊れた。`read_manifest_payload`はstatus読み取り専用の緩い検証(dictであることのみ)に留め、フル検証は`write_stage_manifest_payload`(書き込み時)のみに適用するよう設計を修正した。
- 既存3モジュールのテスト(ingest/normalize/generate orchestrate)がすべて変更無しで成功することを確認した。標準スイート739件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- Fingerprint計算(I002)・Stage lock(I003)・Atomic stage output(I004、本タスクは既存のatomic書き込みパターンを集約したのみ)・Resume判定・`--from-stage`/`--force-stage`(I005-I006)は本タスクの対象外。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-I002 Fingerprint calculation(依存: I001)

### 2026-07-14 20:30 UTC — TASK-I002

**目的**

- `ARCHITECTURE.md` 7.3(`Stage.input_fingerprints`)と`DATA_CONTRACTS.md` 3節のmanifest `inputs`欄(`sha256:...`形式)を実装する。

**変更**

- `src/wikiepwing/pipeline/fingerprint.py`に`compute_input_fingerprint(path) -> str`を実装した(`sha256:<hex>`形式、`source/checksums.py`の`compute_fingerprint`を再利用)。
- `normalize/orchestrate.py`・`render/generate.py`の`inputs`欄を、入力DB(raw.sqlite3/model.sqlite3)の実際のcontent fingerprintを含むよう修正した(従来はpath文字列のみだった)。
- `ingest/orchestrate.py`の`inputs`欄のkeyを`source_lock`、値を`sha256:`プレフィックス付きへ統一した。

**実行コマンド**

```bash
uv run pytest tests/test_pipeline_fingerprint.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py
make check
git diff --check
```

**結果**

- fingerprintの`sha256:`プレフィックス形式、決定性、content変更での差分、既知値との一致を4件のテストで確認した。既存3モジュールのorchestrateテストが変更無しで成功することを確認した(inputs欄の値を検証するテストが存在しないため後方互換上の問題は無かった)。
- 標準スイート743件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- リファクタ前、`normalize`/`generate`の`inputs`欄が入力DBの**path文字列**をそのまま入れており、実際のcontent fingerprintでは無かったことに気づいた。これでは入力の実際の変更を検出できず、TASK-I005(Resume判定)が正しく機能しないため、本タスクで修正した。
- configファイル自体のfingerprint化は、config file pathが各run関数に渡されていないため本タスクの範囲では対応しなかった。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-I003 Stage lock(依存: I001)

### 2026-07-14 20:50 UTC — TASK-I003

**目的**

- `ARCHITECTURE.md` 7.2(Orchestratorの責務"lock取得")を実装する。manifestの`status`確認だけでは真の同時実行を防げないため、`fcntl.flock`によるOS-level advisory lockを実装する。

**変更**

- `src/wikiepwing/pipeline/stage_lock.py`に`acquire_stage_lock`(context manager)/`StageLockError`を実装した。`fcntl.flock`で排他ロックを取得し、lock fileへ取得プロセスのPIDを記録する。例外発生時も確実にロックを解放する。

**実行コマンド**

```bash
uv run pytest tests/test_pipeline_stage_lock.py
make check
git diff --check
```

**結果**

- lock取得成功、PID記録、同一lock pathへの2回目取得の拒否、context終了後の解放と再取得成功、例外発生時の解放、親ディレクトリ自動作成を6件のテストで確認した。
- 標準スイート749件(新規6件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 本プロジェクトはDocker/Linuxコンテナ上でのみ実行される前提(既存toolchain運用と整合)のため、POSIX専用の`fcntl`を採用した。
- 既存のingest/normalize/generate orchestrateモジュールへのlock統合は将来のtaskに委ねた(本タスクはlock機構自体の実装のみ)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-I004 Atomic stage output(依存: I001)

### 2026-07-14 21:20 UTC — TASK-I004

**目的**

- `ARCHITECTURE.md` 7.3(Stage出力はcrash時にも部分書き込みを残さない)を満たす、汎用atomic-write処理を実装する。TASK-I001実装時点で`write_stage_manifest_payload`はtempfile+`os.replace`のatomic書き込みを個別実装していたが、`write_entries_jsonl`(TASK-H009)は開いたファイルハンドルへ直接行単位で書き込んでおり、クラッシュ時にentries.jsonlが不完全な状態で残るリスクがあった。

**変更**

- `src/wikiepwing/pipeline/atomic_write.py`を新規実装した。`atomic_write_bytes`/`atomic_write_text`はtempfile書き込み→`fsync`→`os.replace`による原子的な置き換えを行う共通処理。
- `src/wikiepwing/render/freepwing_source.py`の`write_entries_jsonl`を、全文をメモリ上で組み立ててから`atomic_write_text`を1回呼ぶ形にリファクタリングした(従来は開いたファイルハンドルへ直接行単位で書き込んでいた)。
- `src/wikiepwing/pipeline/stage_manifest.py`の`write_stage_manifest_payload`が持っていた重複したtempfile+`os.replace`実装を、新しい`atomic_write_text`呼び出しに置き換えた(未使用となった`os`/`tempfile` importを削除)。

**実行コマンド**

```bash
uv run pytest tests/test_pipeline_atomic_write.py tests/test_render_freepwing_source.py tests/test_pipeline_stage_manifest.py
make check
git diff --check
```

**結果**

- `atomic_write`の正常書き込み・親ディレクトリ自動作成・上書き・temp fileの残留無し・`os.replace`失敗時に宛先ファイルが元のまま保持されることを6件のテストで確認した。
- `write_entries_jsonl`について、`os.replace`失敗をシミュレートしても宛先の既存内容が変更されないことを新規テストで確認した。
- 標準スイート756件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- raw.sqlite3/model.sqlite3のようにトランザクションで逐次更新されるファイルは対象外とし、entries.jsonlやstage manifestのような単発生成・置き換え型の出力にのみ適用する方針をモジュールのdocstringに明記した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-I005 Resume decision(依存: I002-I004)

### 2026-07-14 21:45 UTC — TASK-I005

**目的**

- `ARCHITECTURE.md` 7.2(Orchestratorの責務"manifest比較"・"resume判定")を実装する。既存3 orchestrateモジュールは直前manifestの`status`が`running`かどうかしか見ておらず、`status: complete`な直前実行を再利用してstageを丸ごとskipする判定ロジックが存在しなかった。

**変更**

- `src/wikiepwing/pipeline/resume.py`を新規実装した。`decide_resume(previous_manifest, *, stage_version, current_inputs) -> ResumeDecision`は、(1)manifestが存在しない、(2)`status`が`complete`でない、(3)`stage_version`が異なる、(4)`inputs`が異なる、のいずれかに該当すれば`should_skip=False`+理由を返し、すべて一致すれば`should_skip=True`を返す純粋関数。

**実行コマンド**

```bash
uv run pytest tests/test_pipeline_resume.py
make check
git diff --check
```

**結果**

- manifest無し・各status(failed/running)・stage_version不一致・inputs不一致(欠落/追加/変更)・完全一致の7パターンを確認するテストを実装し、全件成功した。
- 標準スイート763件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 本タスクは判定ロジックのみを実装し、既存orchestrateモジュール(ingest/normalize/generate)への実配線は、`--from-stage`/`--force-stage`と合わせてTASK-I006で行う方針とした(CLIフラグの意味論と一体で設計した方が手戻りが少ないため)。
- outputsファイルの実在性・sha256一致チェックは対象外とした(manifestの`inputs`/`stage_version`/`status`比較のみ)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-I006 `--from-stage`/`--force-stage`(依存: I005)

### 2026-07-14 22:40 UTC — TASK-I006

**目的**

- `PLAN.md` Phase 9(`--from-stage`/`--force-stage`)と`ARCHITECTURE.md` 7.1の`wikiepwing build`を実装する。TASK-I005の`decide_resume`をまだどのorchestratorも呼んでおらず、複数stageを繋ぐコマンドが無ければ`--from-stage`は意味を持たないため、両方を一度に実装した。

**変更**

- `src/wikiepwing/pipeline/stage_manifest.py`に`parse_manifest_timestamp()`を追加した(manifestのISO 8601タイムスタンプ文字列を`datetime`へ戻す)。
- `src/wikiepwing/ingest/orchestrate.py`・`src/wikiepwing/normalize/orchestrate.py`・`src/wikiepwing/render/generate.py`の各`run_*`関数に`decide_resume`を配線した。直前manifestが`complete`かつ`stage_version`/`inputs`一致なら実処理を一切行わず、直前manifestのフィールド(`run_id`/timestamps/`inputs`/`outputs`/`metrics`/`software`)からResultを再構築して返す`_resume_result`ヘルパーを各モジュールに追加した。`force=True`は「runningの拒否を上書き」と「resume判定を上書き」の両方を意味するよう拡張した。
- `src/wikiepwing/pipeline/build.py`を新規実装した。`STAGE_ORDER = ("ingest", "normalize", "generate")`、`stages_from(from_stage)`(指定stage以降のみを返す純粋関数)、`is_forced_stage(stage, force_stage)`(指定した1 stageだけを強制対象とする純粋関数)。
- `src/wikiepwing/cli.py`に`wikiepwing build`サブコマンドを追加した。`--lock-path`必須、`--namespace`/`--run-id`/`--git-commit`は既存コマンドと同じ意味論、`--from-stage`/`--force-stage`は`{ingest,normalize,generate}`から選択。各stageのmanifest pathを1行ずつ出力し、いずれかのstageが`complete`以外なら即座に非0で終了する。

**実行コマンド**

```bash
uv run pytest tests/test_pipeline_build.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py tests/test_cli.py
make check
git diff --check
```

**結果**

- `pipeline/build.py`の純粋関数(`stages_from`/`is_forced_stage`)を7件のテストで確認した。
- ingest/normalize/generateそれぞれで「直前実行が`complete`かつ入力不変なら同じ`run_id`を返す(実処理skip)」「`force=True`なら新しい`run_id`で強制再実行する」ことを既存3モジュールのテストに追加した6件で確認した。
- CLI `build`コマンドについて、(1)3 stage全てを通しでentries.jsonlまで生成する、(2)同一`--run-id`で2回叩くと2回目は各stageの`started_at`が変化しない(実処理skip)、(3)`--from-stage generate`だと生成されるmanifestが50-generateの1件だけになる、の3シナリオをend-to-endで実行するテストを追加し、全て成功した。
- 標準スイート780件(新規24件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- manifest pathが既存の各CLIコマンド同様`paths.work/runs/<run-id>/manifests/<stage>.json`という**run-id別**のパスであるため、resumeは「同一run-idでの再実行(クラッシュ後の再試行やCIでの冪等実行)」を意味し、異なるrun-idを渡すたびに新規manifest履歴が作られる(既存の単一stageコマンド群と同じ設計)。異なるrun-id間でstageを再利用したい場合は、明示的に同じ`--manifest-path`を渡す必要がある(この制約はテストのコメントとして明記した)。
- `--force-stage`で指定した1 stageだけを強制対象にし、下流stageへは明示的な連鎖をしない設計にした。下流stageのmanifest `inputs`には上流の出力fingerprintが記録されているため、上流を強制再実行しても出力内容が変わらなければ下流は自然にresume判定でskipされ、内容が変われば自然に再実行される(fingerprint比較による自動連鎖)。
- media/render等の将来stageは`STAGE_ORDER`に追加するだけで良い設計にした(本タスクでは追加しない)。
- outputsファイルの実在性・sha256一致チェックはTASK-I005同様、対象外とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-I007 Kill/restart統合テスト(依存: I006)

### 2026-07-14 23:20 UTC — TASK-I007

**目的**

- `PLAN.md` Phase 9の出口条件("corrupt output再利用拒否"・"interrupted stageだけ再実行")とテスト観点("normalize途中kill"・"output hash mismatch")を実装・検証する。TASK-I005/I006の`decide_resume`は`status`/`stage_version`/`inputs`のみを比較しており、manifestが`complete`と主張していても実際の出力ファイルが消失・破損している場合に誤って再利用してしまうギャップに気づいたため、まずこれを修正した。

**変更**

- `src/wikiepwing/pipeline/resume.py`の`decide_resume`に`current_output_fingerprint: tuple[int, str] | None`引数を追加した。直前manifestの`outputs`が非空の場合、渡されたfingerprintが一致しない、またはNone(ファイル消失)なら`should_skip=False`を返すfail-closed設計にした。`outputs`が空/未記録なら従来通りこのチェックをスキップする。
- `ingest/orchestrate.py`・`normalize/orchestrate.py`・`render/generate.py`に`_current_output_fingerprint(path)`ヘルパーを追加し、実際の出力ファイルのfingerprintを`decide_resume`へ渡すよう配線した。
- `run_normalize`/`run_ingest`に、出力先が壊れたsqliteファイルだった場合のフォールバック(`sqlite3.DatabaseError`を捕捉してファイルを削除し再初期化)を追加した。

**実行コマンド**

```bash
uv run pytest tests/test_pipeline_resume.py tests/test_ingest_orchestrate.py tests/test_normalize_orchestrate.py tests/test_render_generate.py
make check
git diff --check
```

**結果**

- `decide_resume`の出力fingerprint比較を4件のテスト(missing/corrupt/matching/no-outputs-recorded)で確認した。
- normalizeについて、出力ファイルが破損していても正しく再構築され10記事全件が復元されることを確認するテストを追加した。
- `multiprocessing`(fork context)で`run_normalize`をbatch_size=1・記事ごとに0.2秒sleepするon_progressで起動し、0.4秒後に実プロセスへ`SIGKILL`を送るkill/restart統合テストを追加した。manifestが`running`のまま残ること、`force=False`では拒否されること、`force=True`での再実行が成功し10記事全件・`PRAGMA integrity_check`が`ok`であることを確認した(3回連続実行して安定性を確認済み)。
- 標準スイート786件(新規19件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `initialize_model_database`/`initialize_raw_database`が壊れたsqliteファイルへ直接接続しようとして`sqlite3.DatabaseError`で失敗するバグを、テスト実装中に発見・修正した(元々のTASK-I005/I006では出力ファイルの実在性チェック自体が無かったため露見していなかった)。
- kill/restartテストはタイミング依存だが、`batch_size=1`+記事ごとの明示的sleepにより実処理時間(約2秒)がkillまでの待機時間(0.4秒)を十分上回る設計にし、フレーキーにならないようにした。
- ingest/generateの実プロセスkillテストは追加していない(normalizeの1本でパターンを代表させる方針は事前に決めた通り)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- EPIC J(日本語検索、依存: H008)

### 2026-07-14 23:55 UTC — TASK-J001

**目的**

- `ARCHITECTURE.md` 14と`DATA_CONTRACTS.md` 8(SearchTerm contract、`"Ｅｍａｃｓ"` -> `"normalized_key": "emacs"`の例)が要求する索引キー正規化を、単一の正本関数として明文化する。既存`search_term.py`は`ingest.repository.normalize_title`(NFKC+strip、case-fold無し)を流用しており、全角`Ｅｍａｃｓ`は`Emacs`にはなるが`emacs`にはならず、DATA_CONTRACTS.mdの例と食い違っていたことに気づいた。

**変更**

- `src/wikiepwing/search/normalize_key.py`に`normalize_index_key()`/`NormalizeKeyError`を実装した。NFKC正規化→`str.casefold()`→空白ランの畳み込み→trimを行う。
- `search_term.py`の`title_terms_for_article`を`normalize_index_key`を使うよう変更した。ingest側の重複解決に使う`ingest.repository.normalize_title`自体は別の関心事として据え置いた。

**実行コマンド**

```bash
uv run pytest tests/test_search_normalize_key.py tests/test_search_term.py
make check
git diff --check
```

**結果**

- 全角→半角小文字化・大文字小文字畳み込み・空白畳み込み・日本語保持・空文字列エラーを8件のテストで確認した。既存`test_search_term.py`は変更無しで成功した。
- 標準スイート794件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ingest.repository.normalize_title`(raw ingest時の重複解決用、case-preserving)と検索索引用の`normalize_index_key`(case-fold有り)を意図的に分離した。両者を混同すると、ingest側の重複判定基準が検索要件に引きずられて変わってしまうため。
- 優先度定数(`_TITLE_PRIORITY`/`_REDIRECT_PRIORITY`)はDATA_CONTRACTS.md 8のpriority proposal(1000〜100スケール)とまだ整合していないが、これはTASK-J005(alias priorities)の対象として据え置いた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-J002 NFKC/case/space variants(依存: J001)

### 2026-07-15 00:20 UTC — TASK-J002

**目的**

- `ARCHITECTURE.md` 14 / `PLAN.md`のNFKC/case/space variantsを実装する。設計を詰める過程で、NFKC・case-fold軸は(クエリ側にも`normalize_index_key`を適用する前提で)J001の1関数だけで双方向に吸収され、追加のSearchTerm登録が不要であることに気づいた。空白だけは`normalize_index_key`が「連続runの畳み込み」しか行わず「除去」はしないため、"New York"と"NewYork"のように別文字列のまま残る。このギャップを埋めるため、空白除去バリアントの明示的なSearchTerm生成を実装した。

**変更**

- `src/wikiepwing/search/space_variant.py`に`space_removed_variant()`を実装した。
- `search_term.py`の`title_terms_for_article`を拡張し、title・redirectエイリアスそれぞれについて空白除去バリアントが元と異なる場合に`kind="alias"`・`source="nfkc_case_space_variant"`のSearchTermを追加登録するようにした。

**実行コマンド**

```bash
uv run pytest tests/test_search_space_variant.py tests/test_search_term.py tests/test_search_normalize_key.py
make check
git diff --check
```

**結果**

- 空白除去バリアント生成を4件、`title_terms_for_article`での配線を3件のテストで確認した。既存の`test_title_terms_include_redirect_aliases`はSearchTermの並びが変わったため、redirect種別のみを抽出する形に修正して成功させた。
- NFKC/case軸が`normalize_index_key`単体で双方向に吸収されることを2件のテストで明示した。
- 標準スイート803件(新規9件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 「NFKC/case/space variants」という名前だが、実装が必要だったのは空白軸のみで、NFKC/case軸は既存の`normalize_index_key`(TASK-J001)で既に解決済みだった。この判断根拠(なぜ新規SearchTermが不要か)をモジュールdocstringとテストに明記した。
- クエリ側にも`normalize_index_key`を適用する実配線はTASK-J007(backend search mapping)の対象として据え置いた。
- 優先度定数(`_SPACE_VARIANT_PRIORITY = 20`)はTASK-J005(alias priorities)でDATA_CONTRACTS.mdのpriority proposalスケールへ統一する前提の暫定値。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-J003 Kana variants(依存: J001)

### 2026-07-15 00:45 UTC — TASK-J003

**目的**

- `ARCHITECTURE.md` 14.3(Lite profileの"kana variant")と`DATA_CONTRACTS.md` 8のpriority proposal("600 kana variant")を実装する。ひらがな/カタカナのどちらで書かれたタイトル・エイリアスでも、もう一方の表記での検索でヒットするようにする。

**変更**

- `src/wikiepwing/search/kana_variant.py`に`kana_variant()`を実装した。ひらがな(U+3041-3096)⇔カタカナ(U+30A1-30F6)を1文字ずつコードポイントオフセット(0x60)で機械的に入れ替え、対象外の文字(漢字・ASCII・長音記号ーなど)はそのまま保持する。
- `search_term.py`の変種生成ロジックを`_variant_terms`に統合し、space variant(TASK-J002)とkana variantの両方を生成するよう拡張した(`_KANA_VARIANT_PRIORITY = 30`)。

**実行コマンド**

```bash
uv run pytest tests/test_search_kana_variant.py tests/test_search_term.py
make check
git diff --check
```

**結果**

- ひらがな→カタカナ・カタカナ→ひらがな・混在文字列・漢字/ASCII不変・漢字とかなの混在・長音記号(かな変換対象外)を6件のテストで確認した。
- `title_terms_for_article`でのkana variant生成(title/redirectエイリアス双方)を3件のテストで確認した。
- 標準スイート812件(新規9件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 半角カタカナはTASK-J001の`normalize_index_key`のNFKC正規化で全角へ既に畳み込まれているため、本タスクでは全角カタカナ⇔ひらがなの単純往復変換のみを実装すれば十分と判断した。
- kana variantとspace variantを組み合わせた複合バリアント(例: 空白除去+かな入れ替え両方を適用したキー)は生成していない。必要性が生じた場合の将来課題とする。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-J004 Punctuation variants(依存: J001)

### 2026-07-15 01:05 UTC — TASK-J004

**目的**

- `ARCHITECTURE.md` 14 / `PLAN.md`のpunctuation variantsを実装する。TASK-J002(space variant)・TASK-J003(kana variant)と同じパターンで、`normalize_index_key`だけでは吸収できない軸(句読点・記号)を補う。

**変更**

- `src/wikiepwing/search/punctuation_variant.py`に`punctuation_removed_variant()`を実装した。個別の記号を列挙するのではなく、`unicodedata.category`が"P"で始まる文字(Punctuation全般: connector/dash/open/close/initial/final/other)を機械的に除去する客観的な定義を採用した。
- `search_term.py`の`_variant_terms`を、`(生成関数, priority, source)`タプルのリスト`_VARIANT_GENERATORS`をループする形にリファクタリングし、space/kana/punctuationの3variantを統一的に生成するようにした。

**実行コマンド**

```bash
uv run pytest tests/test_search_punctuation_variant.py tests/test_search_term.py
make check
git diff --check
```

**結果**

- 中黒・ASCII記号・括弧・日本語句読点の除去、記号が無い場合・記号のみの場合に`None`を返すこと、長音記号ー(Unicode上はPunctuationでなくLm=Modifier Letter)が対象外であることを7件のテストで確認した。
- `title_terms_for_article`でのpunctuation variant生成(title/redirectエイリアス双方)を2件のテストで確認した。
- 標準スイート821件(新規9件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 中黒「・」やダッシュ類など個別の記号を都度追加するのではなく、Unicodeカテゴリによる網羅的な定義を採用したことで、将来未知の記号が出てきても追加実装なしで自然にカバーされる。
- space/kana/punctuationの3 variantは独立に生成しており、組み合わせ(例: 記号除去+かな入れ替え両方適用)は生成していない。必要になった場合の将来課題とする。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-J005 Alias priorities(依存: J002-J004)

### 2026-07-15 01:30 UTC — TASK-J005

**目的**

- `DATA_CONTRACTS.md` 8(SearchTerm contract)のpriority proposal(1000 exact title 〜 100 cross component)と、衝突時の安定sort規則(`normalized_key`, `target_entry_id`, `source`)を実装する。TASK-H008/J002-J004で導入した優先度定数(0/10/20/30/40、小さいほど優先)を正式スケールへ置き換える。

**変更**

- `search_term.py`の優先度定数をDATA_CONTRACTS.mdスケールへ置き換えた: title=1000、redirect=900、space/punctuation variant=800(normalized title variant)、kana variant=600(DATA_CONTRACTS.mdの明示値)。
- `sort_search_terms(terms)`を実装した。priority降順、同priority内は`normalized_key`→`target_page_id`→`source`の昇順で安定sort。

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- 優先度スケールの向き反転により、既存の`test_title_priority_is_higher_than_redirect_priority`のassertionを`<`から`>`へ修正した(意味的には変わらず、"titleの方がredirectより優先度が高い"という主張のまま)。
- 優先度値そのもの(title=1000/redirect=900/space=800/kana=600)を確認するテストと、`sort_search_terms`のpriority降順・tie-break挙動を確認するテスト3件を追加した。
- 標準スイート824件(新規4件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- DATA_CONTRACTS.mdは`target_entry_id`という呼称を使っているが、既存の`SearchTerm`データクラス(ARCHITECTURE.md 14.1のPython定義)は`target_page_id`を正としているため、フィールド名自体は変更しなかった(ARCHITECTURE.mdの型定義を実装の正本として扱う既存方針を維持)。
- space variantとpunctuation variantは共に"800 normalized title variant"の枠として扱った(どちらも正規化由来の派生キーであり、ユーザー入力由来の"700 explicit alias"とは性質が異なるため)。
- alias(700)/category(500)/heading keyword(400)/infobox keyword(300)/lead term(200)/cross_component(100)はまだどのコードも生成していないため、対応する定数は未定義のまま(将来生成コードを実装するタスクで追加する)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-J006 Collision repository/report(依存: J005)

### 2026-07-15 01:55 UTC — TASK-J006

**目的**

- `ARCHITECTURE.md` 14.2(衝突規則: サイレント上書きしない・全候補保持を優先・単一候補backendではpriorityと安定sortで選ぶ・dropped候補をレポートする)を実装する。`rendered.sqlite3`(`search_terms`テーブル、正規化キーへのUNIQUE制約無し)の永続化層自体はまだ存在しないため、本タスクは純粋な検出・解決・レポート関数として実装した。

**変更**

- `src/wikiepwing/search/collision.py`に`SearchTermCollision`・`find_collisions()`・`resolve_single_candidate_per_key()`を実装した。`normalized_key`でグルーピングし、`target_page_id`が2種類以上あるグループのみを衝突として報告する(titleとredirectが偶然同じ正規化キーになっても同一記事なら衝突扱いしない)。

**実行コマンド**

```bash
uv run pytest tests/test_search_collision.py
make check
git diff --check
```

**結果**

- 非衝突(単一候補・同一記事への複数候補)・衝突検出・priorityによるwinner選択・レポートのnormalized_key順整列・単一候補への解決(衝突有り/無し)を7件のテストで確認した。
- 標準スイート831件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `rendered.sqlite3`本体(`entries`/`entry_parts`/`search_terms`/`graphics`/`entry_graphics`テーブルの永続化層、migrations)はまだどのタスクでも実装されていないことに気づいた。`search_terms`テーブルは`normalized_key`にUNIQUE制約が無く全候補を保持できる設計(`DATA_CONTRACTS.md` 7)であるため、本タスクの`find_collisions`/`resolve_single_candidate_per_key`はその永続化層が実装された際にそのまま呼び出せる純粋関数として設計した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-J007 Backend search mapping(依存: B009,J006)

### 2026-07-15 02:20 UTC — TASK-J007

**目的**

- `ARCHITECTURE.md` 17.2(FreePWING adapter)と14(Search architecture)を接続する。既存の`mini_layout.render_article_to_entry`は`article.title`+全aliasという素朴なheadword生成のみで、TASK-H008/J001-J006のSearchTerm基盤(title/redirect/variant、priority、衝突解決)を一切使っていなかったことに気づいた。

**変更**

- `src/wikiepwing/search/backend_mapping.py`に`headwords_for_articles()`を実装した。ビルド対象の全記事のSearchTermをまとめて`resolve_single_candidate_per_key`(TASK-J006)で衝突解決し、`target_page_id`で再グルーピングしてpriority降順のheadwordタプルを返す。自記事のSearchTermが全て他記事との衝突で失われても、`article.title`は必ず先頭に残す。
- `render/mini_layout.py`の`render_article_to_entry`に`headwords`オーバーライド引数を追加した(省略時は従来の素朴な生成にフォールバックし、既存テストとの後方互換を保った)。
- `render/generate.py`の`_render_all`を2パス化した: 先に全articleをデコードし、`headwords_for_articles`を1回だけ呼んでから各entryを構築する(記事間のSearchTerm衝突をグローバルに解決するため)。

**実行コマンド**

```bash
uv run pytest tests/test_search_backend_mapping.py tests/test_render_generate.py tests/test_render_mini_layout.py tests/test_mini_end_to_end_build.py
make check
git diff --check
```

**結果**

- `headwords_for_articles`について、単一記事のtitle+redirect、無関係な2記事がそれぞれ自分のheadwordのみ持つこと、space variantが2記事間で衝突した際に高priority側(title)だけが勝ち残ること、自記事のtitleが必ず残ることを4件のテストで確認した。
- 既存の`test_render_generate.py`(6件)・`test_render_mini_layout.py`(12件)・`test_mini_end_to_end_build.py`(1件)は変更無しで成功し、後方互換を確認した。
- 標準スイート835件(新規4件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `render/verify.py`のDUPLICATE_HEADWORDチェック(異なるentry間で同一headword文字列を許さない)が実質的に単一候補per keyの制約であることに気づき、TASK-J006の`resolve_single_candidate_per_key`をそのまま適用する設計にした。
- `rendered.sqlite3`本体の`search_terms`テーブル(全候補を保持できる設計)はまだ実装されていないため、現状は単一候補解決のみを実データに反映する。将来そのテーブルが実装されたら、dropされた候補も含めた全SearchTermをそこへ書き込む形に拡張できる。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- EPIC K(Tables and infoboxes、依存: D010,G010)

### 2026-07-15 02:45 UTC — TASK-K001

**目的**

- `ARCHITECTURE.md` 11.5(Table)のHTML-to-Table変換の最初の段階として、生の`<table>` DOM要素を中間表現(`RawTable`/`RawTableRow`/`RawTableCell`)へ解析する。row/col span正規化(K002)・複雑度分類(K003)・最終`TableBlock`変換(K004-K006)はまだ行わない狭いスコープ。

**変更**

- `src/wikiepwing/normalize/tables.py`に`RawTableCell`/`RawTableRow`/`RawTable`・`is_table()`・`parse_table_dom()`を実装した。`<caption>`・`thead`/`tbody`/`tfoot`配下も含めた`<tr>`・各セル(rowspan/colspan/is_header)を取り出す。ネストされた`<table>`の行を外側テーブルの行として取り込まないよう、行探索がネストした`<table>`タグに達したら再帰を止める設計にした。
- rowspan/colspan属性が非数値または非正の場合は1へフォールバックし、`TABLE_INVALID_SPAN`という新しいDiagnostic codeを記録するようにした。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_tables.py
make check
git diff --check
```

**結果**

- table判定・非table拒否・行/セル解析・th判定・span読み取り・span欠落時のデフォルト値・不正span時のフォールバック+Diagnostic・caption有無・thead/tbody/tfoot内の行・ネストテーブル除外・class名取得を15件のテストで確認した。
- 標準スイート850件(新規15件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `TABLE_INVALID_SPAN`という新しいDiagnostic codeを追加した(`ARCHITECTURE.md` 11.7の例一覧は網羅的でないことを確認済み)。
- HTML仕様上`rowspan="0"`/`colspan="0"`は「表の終わりまで」という特殊な意味を持つが、本タスクでは単純に1へフォールバックしDiagnosticを残すに留めた(複雑なspan展開はTASK-K002の対象)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K002 Row/col span normalization(依存: K001)

### 2026-07-15 03:10 UTC — TASK-K002

**目的**

- `ARCHITECTURE.md` 11.5(TableBlock/TableCellがspan値を保持したままの設計)を踏まえ、TASK-K001の`RawTable`の各セルが実際にどのグリッド位置(行・列)に属するかを計算する。複雑度分類(K003)・レンダラ(K004-K005)が必要とする中間計算であり、モデル自体には保存しない。

**変更**

- `src/wikiepwing/normalize/table_grid.py`に`PositionedCell`・`NormalizedTable`・`normalize_table_spans()`を実装した。HTML仕様の"table grid formation algorithm"相当: 前の行からのrowspanが占有する列をスキップしながら各セルの開始列を決定し、rowspan+colspanの組み合わせは矩形領域として占有記録し、残り行数が尽きたら解放する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_table_grid.py
make check
git diff --check
```

**結果**

- 単純グリッド・colspanによる列ずれ・rowspanによる次行の列スキップ・rowspan+colspan組み合わせ・rowspanの期限切れ・最大幅による列数計算・空テーブル・caption/class名の保持を8件のテストで確認した。
- 標準スイート858件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 列数(`column_count`)は各セルの`col_index + col_span`の最大値として計算した。当初トレイリングのアクティブスパン追跡で計算しようとしたが、後続行のセルが占有列と無関係な位置にある場合に誤った値になりうるバグに気づき、シンプルなセル単位の最大値計算に修正した。
- 現実のWikipediaテーブルを想定し、仕様上の完全なedge case(重複・不正なspan宣言)への対応は行っていない(素直な逐次占有列スキップで十分と判断)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K003 Table complexity classifier(依存: K002)

### 2026-07-15 03:30 UTC — TASK-K003

**目的**

- `ARCHITECTURE.md` 11.5の`TableBlock.complexity`を決定する分類器を実装する。16.3(Table render policy)は各tierの方針(simple/wide/complex)を述べるのみで具体的な閾値を規定していないため、本タスクで判断基準を定めdocstringに明記した。

**変更**

- `src/wikiepwing/normalize/table_complexity.py`に`classify_table_complexity()`を実装した。判定順序: 行が無ければ`unsupported`→結合セル(rowspan/colspan>1)が1つでもあれば`complex`(列数に関わらず優先)→列数が閾値(デフォルト6)を超えれば`wide`→それ以外は`simple`。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_table_complexity.py
make check
git diff --check
```

**結果**

- 空テーブル・結合無し小規模テーブル・閾値ちょうど/超過・カスタム閾値・rowspan/colspan単独での複雑判定・complexがwideより優先されることを8件のテストで確認した。
- 標準スイート866件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ARCHITECTURE.md`が閾値を規定していないため、Mini-profileのプレーンテキストグリッド表示が読みやすく収まる列数として6をデフォルトに採用した(呼び出し側で`max_simple_columns`により変更可能)。
- 結合セルの有無を列数より優先して判定する設計にした(16.3の"complex"が「row/sectionごとのkey-value化」という構造的複雑さを指しており、列数の多寡とは独立した軸であるため)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K004 Simple table renderer(依存: K003,H007)

### 2026-07-15 03:55 UTC — TASK-K004

**目的**

- `PLAN.md` Phase 11("simple renderer")と`ARCHITECTURE.md` 16.3("simple": grid-like text)を実装する。TASK-K001-K003はDOM解析→span正規化→複雑度分類までだったが、実際の`TableBlock`を組み立てる処理がまだ無かった。

**変更**

- `src/wikiepwing/normalize/table_block.py`に`build_table_block()`を実装した。K001→K002(列数計算用)→K003を連結し、各セル内容を`convert_document`でBlockへ、captionを`convert_inline_nodes`でInlineへ変換して実際の`TableBlock`/`TableCell`を組み立てる。
- `render/mini_layout.py`の`_render_block`に`TableBlock`ケースを追加した。`complexity=="simple"`はcaption+各行を` | `区切りのgrid-likeテキストへレンダリングし、wide/complexはcaption+行数プレースホルダ、unsupported(空テーブル)はcaptionのみを出力し、データを失わない劣化表示にした。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_table_block.py tests/test_render_mini_layout.py
make check
git diff --check
```

**結果**

- `build_table_block`について、simple組み立て・セル内容のBlock変換・captionのInline変換・header/span保持・class名保持・wide/complex分類・空テーブル・Diagnostic伝播を9件のテストで確認した。
- Mini-layoutでのTableBlockレンダリングについて、simple tableのgrid text・非simpleのプレースホルダ(captionは保持)・空テーブルのcaptionのみ出力を3件のテストで確認した。
- 標準スイート878件(新規12件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ARCHITECTURE.md`のEpic K/L完了までの間、wide/complexは「専用レンダラ未実装」の暫定プレースホルダ(caption+行数)で扱い、データ損失(サイレントな空文字列化)を避けた。TASK-K005で本格的な縦record表示に置き換える前提。
- "complex"専用のレンダラtaskがTASKS.mdに存在しないことを確認した。16.3の"wide"(縦record)と"complex"(row/sectionごとのkey-value)の方針が類似しているため、TASK-K005(wide renderer)がcomplexも扱う可能性を次タスクの検討事項として残した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K005 Wide table renderer(依存: K003,H007)

### 2026-07-15 04:15 UTC — TASK-K005

**目的**

- `PLAN.md` Phase 11の出口条件("wide table readable vertical layout")と`ARCHITECTURE.md` 16.3("wide": 1行をrecordとして縦表示)を実装する。TASK-K004の暫定プレースホルダ(wide/complex)を実際の縦record表示に置き換える。

**変更**

- `render/mini_layout.py`に`_render_table_as_records()`を実装した。先頭行が全てヘッダーセルなら、その文字列を以降の各行のフィールドラベルとして使い(無ければ「列N」にフォールバック)、「ラベル: 値」を1行ずつレコード間に空行を挟んで出力する。
- "complex"専用のレンダラtaskがTASKS.mdに存在しないことを確認済み(TASK-K004のLOGで気づいた点)であるため、16.3の"complex"("row/sectionごとのkey-value化")が"wide"の縦record表示と方針的に同一であると判断し、本レンダラを`complexity in ("wide", "complex")`の両方に適用した。

**実行コマンド**

```bash
uv run pytest tests/test_render_mini_layout.py
make check
git diff --check
```

**結果**

- ヘッダー行有り(ラベルとして使用)・ヘッダー行無し(汎用ラベルへフォールバック)・"complex"での縦record表示を3件のテストで確認した(既存の暫定プレースホルダテストを置き換え)。
- 標準スイート880件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 結合セル(rowspan/colspan)を持つ"complex"テーブルは、TASK-K002のグリッド位置計算を使わず、DOM順にそのまま「ラベル: 値」として展開する簡易実装に留めた。正確なグリッド位置に基づくラベル対応付けが必要になれば将来のタスクとする。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K006 Oversized table policy(依存: K004-K005)

### 2026-07-15 04:35 UTC — TASK-K006

**目的**

- `ARCHITECTURE.md` 16.3(oversized: "configured row上限で分割"、"続きentryを作るか、要約とtruncate diagnostic")を実装する。`RenderedEntry`に複数entry分割の基盤が無いため、後者(truncate+diagnostic)を採用する。

**変更**

- `build_table_block`に`max_rows: int = 100`引数を追加した。行数が超過する場合、先頭`max_rows`行のみを保持し、`TABLE_OVERSIZED_ROWS`のDiagnostic(`total_rows`/`kept_rows`)を記録する。複雑度分類は切り詰め前の完全なテーブルに対して行うようにした(行数だけで表示方針が変わらないようにするため)。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_table_block.py
make check
git diff --check
```

**結果**

- 閾値以内で切り詰めが発生しないこと・閾値超過で切り詰め+Diagnostic記録・デフォルト値での小規模テーブルの非切り詰めを3件のテストで確認した。
- 標準スイート883件(新規3件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 続きentry(continuation entry)を作る仕組みは`RenderedEntry`に存在しないため対象外とし、この判断根拠をモジュールdocstringに明記した。
- Entry size budget全体(16.4、nav/reference重複削除等)は対象外とし、表の行数上限のみを扱った。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K007 Infobox detector(依存: K001)

### 2026-07-15 04:50 UTC — TASK-K007

**目的**

- `ARCHITECTURE.md` 11.6(Infobox: TableBlockの単なる別名にせず別型にする)の最初の段階として、`<table>`要素がMediaWikiのinfoboxかどうかを判定する。

**変更**

- `src/wikiepwing/normalize/infobox.py`に`is_infobox()`を実装した。`Template:Infobox`が安定して付与する`class="infobox"`トークン(空白区切りの完全一致、部分文字列一致ではない)の有無で判定する。個別テンプレート実装の列挙は行わない。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_infobox.py
make check
git diff --check
```

**結果**

- 単一class・複数class中の1つ・infobox無し・class属性無し・非table要素・"infoboxen"のような接頭辞一致の誤検出防止を6件のテストで確認した。
- 標準スイート889件(新規6件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 個別のinfoboxテンプレート実装(vcard、biography等)の調査は行わず、Wikipedia全体で安定している共通クラス名"infobox"のみに依拠する設計にした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K008 Infobox field parser(依存: K007)

### 2026-07-15 05:40 UTC — TASK-K008

**目的**

- `ARCHITECTURE.md` 11.6(InfoboxBlock: title/fields/images)の中間表現を、TASK-K007で検出したinfobox `<table>`から抽出する。

**変更**

- `src/wikiepwing/normalize/infobox_fields.py`に`RawInfoboxField`・`RawInfobox`・`parse_infobox_dom()`を実装した。TASK-K001の`parse_table_dom`を再利用し、行を3パターン(単一結合ヘッダーセル=title、2セル=field、`<img>`を含む行/セル=画像参照)に分類する。それ以外の行構造(入れ子table、区切り行等)は静かにスキップする(docstringに明記した既知の単純化)。画像は`<img>`の`src`属性を生文字列として保持するのみで、`MediaReference`化は対象外(別epic)。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_infobox_fields.py
make check
git diff --check
```

**結果**

- title行抽出・2セルfield抽出・画像行/field値内の画像`src`抽出・title無し・未対応行構造のスキップ・`parse_table_dom`からのDiagnostic伝播を7件のテストで確認した。
- 標準スイート896件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実装中、Bashツール(コード実行系コマンド全般: `uv run`/`pytest`/venv直接実行)が長時間利用不可になる障害が発生した(単純なファイル操作コマンドは影響を受けなかった)。この間、新規コードとテストを`RawTableCell`/`RawTableRow`の既存定義と突き合わせて手動でトレースし正しさを確認した上で待機し、復旧後に実際のテスト実行で検証した(ユーザーへ透明性のある状況報告を行った)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K009 Infobox renderer(依存: K008,H007)

### 2026-07-15 06:05 UTC — TASK-K009

**目的**

- `ARCHITECTURE.md` 11.6(InfoboxBlock)の実際のモデル組み立てとMini-profileでのレンダリングを実装する。

**変更**

- `src/wikiepwing/normalize/infobox_block.py`に`build_infobox_block()`を実装した。TASK-K008の`parse_infobox_dom`を使い、各fieldの値を`convert_document`でBlockへ変換して`InfoboxBlock`/`InfoboxField`を組み立てる。title/fields/imagesが全て空の場合は`INFOBOX_EMPTY`(`ARCHITECTURE.md` 11.7の既存例コード)を記録する。
- `render/mini_layout.py`に`InfoboxBlock`の`_render_block`ケースを追加した。title(あれば)+各fieldの「name: value」+各画像srcの`[画像: ...]`プレースホルダ行としてレンダリングする。モジュールdocstringの古い記述(TASK-K005で既に実装済みのTableBlock wide/complexレンダリングを「未実装のプレースホルダのまま」と書いていた古い記述)も気づいたので修正した。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_infobox_block.py tests/test_render_mini_layout.py
make check
git diff --check
```

**結果**

- `build_infobox_block`について、title+fields組み立て・field値のBlock変換・画像srcの伝播・空infoboxでのDiagnostic記録・非空infoboxでの非記録・`parse_infobox_dom`からのDiagnostic伝播を6件のテストで確認した。
- Mini-layoutでのInfoboxBlockレンダリング(title+field+画像プレースホルダ、title無しでもfieldは表示)を2件のテストで確認した。
- 標準スイート904件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- mypy strictで`diagnostics`変数への型不一致な再代入(`tuple`→`list`)エラーを検出し、別名の変数(`raw_diagnostics`)へ分離して修正した。
- 画像は実際にダウンロード・レンダリングせず、`src`文字列をそのままプレースホルダ行として表示するに留めた(実画像処理は別epicの対象)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-K010 Table/infobox golden set(依存: K006,K009)

### 2026-07-15 06:35 UTC — TASK-K010

**目的**

- `PLAN.md` Phase 11の出口条件を実際のend-to-endパイプラインで検証するgolden setを作る。実装中に、TASK-K001-K009で構築した`build_table_block`/`build_infobox_block`が`convert_block.py`の`convert_block()`ディスパッチャから一度も呼ばれておらず、`<table>`要素が依然として`_convert_unsupported`へ落ちていたという重大なギャップに気づき、まずこれを修正した。

**変更**

- `convert_block.py`の`convert_block()`に`is_infobox`/`is_table`判定を追加し、`build_infobox_block`/`build_table_block`へディスパッチするよう配線した。両関数は`convert_document`(`convert_block.py`内で定義)を呼び返すため、モジュール先頭でimportすると循環importになる。関数内local importで回避した(理由をモジュールdocstringに明記)。
- `tests/test_normalize_convert_block.py`・`tests/test_normalize_pipeline.py`の既存の「未知要素fallback」テストが`<table>`を例に使っていたため`<div>`/`<figure>`へ差し替え、新たに`<table>`/infoboxの正しいディスパッチを確認する専用テスト2件を追加した。
- `tests/golden/normalize/`にTASK-G013と同形式のgolden fixture6件を追加した(2x2 simple table、8列wide table、rowspan complex table、不正colspanのmalformed table、infobox、ネストしたtable)。期待JSONは実際のパイプラインを実行して機械生成した。
- `test_golden_normalize.py`を、fixture毎に期待Diagnostic codeを指定できるよう拡張した(`14_table_malformed_span`のみ`TABLE_INVALID_SPAN`を期待、他は従来通り無し)。

**実行コマンド**

```bash
uv run pytest tests/test_golden_normalize.py tests/test_normalize_convert_block.py tests/test_normalize_pipeline.py
make check
git diff --check
```

**結果**

- 新golden fixture6件を含む17件のgolden testが成功した(ネストしたtableが再帰的に正しく変換されることも確認)。
- 標準スイート912件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。実DB経由のend-to-endテスト(`test_mini_end_to_end_build.py`等)も配線変更の影響を受けず成功した。

**判断・注意点**

- このギャップ(convert_blockへの未配線)は、K001-K009の各タスクが独立した関数として実装され、それぞれのユニットテストは通っていたためこれまで気づかれていなかった。実際のWikipedia記事の`<table>`はこれまで全てUnsupportedBlockとしてfallback表示されていたことになる。golden set作成の過程でこの事実に気づき、K010の一部として修正した。
- "very large table"(oversized行数上限)のgolden fixtureは追加しなかった(TASK-K006のユニットテストで既に十分に検証済みのため、golden setには実用的なサイズのfixtureのみを置いた)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- EPIC L(References and categories、依存: G012,H007)

### 2026-07-15 07:00 UTC — TASK-L001

**目的**

- `ARCHITECTURE.md` 12.2の"N100 Convert references"パスの最初の段階として、本文中の脚注マーカー(MediaWiki Cite拡張の`<sup class="reference"><a href="#cite_note-X">[1]</a></sup>`)を解析する。

**変更**

- `src/wikiepwing/normalize/reference_marker.py`に`ReferenceMarker`・`is_reference_marker()`・`parse_reference_marker()`を実装した。可視ラベルと、内部`<a href="#...">`から抽出したフラグメントID(参照リスト項目とのマッチングにTASK-L002で使う)を返す。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_reference_marker.py
make check
git diff --check
```

**結果**

- マーカー検出・非マーカーの非検出・label/target_id抽出・`<a>`欠落時/非フラグメントhref時の`target_id=None`・非マーカーへの呼び出し時のエラーを7件のテストで確認した。
- 標準スイート919件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ARCHITECTURE.md`の`Inline`union(11.3)にreference marker専用の型が無いため、実際のInline変換は既存の透過的wrapper fallback(`convert_inline_nodes`が`<sup>`/`<a>`を再帰し可視テキストを得る)に委ね、本タスクは`target_id`抽出という補助的な解析のみを追加した。本文Inline変換パイプラインへの実配線(target_idの活用)はTASK-L002以降で行う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-L002 Reference list parser(依存: L001)

### 2026-07-15 07:20 UTC — TASK-L002

**目的**

- `ARCHITECTURE.md` 12.2の"N100 Convert references"の続きとして、記事末尾の参照リスト(MediaWiki Cite拡張の`<ol class="references">`)を解析する。

**変更**

- `src/wikiepwing/normalize/reference_list.py`に`RawReferenceItem`・`is_reference_list()`・`parse_reference_list()`を実装した。各`<li>`から`note_id`(`id`属性、TASK-L001のマーカーの`target_id`と対応)と、`<span class="reference-text">`があればその内容、無ければbacklinkを除いた残りを`content`として抽出する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_reference_list.py
make check
git diff --check
```

**結果**

- リスト検出・非検出・note_id+reference-text抽出・複数項目の順序保持・backlinkのみ除去のフォールバック・id欠落時のNone・非リストへの呼び出し時のエラー・非`<li>`子要素の無視を8件のテストで確認した。
- 標準スイート927件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ReferencesBlock`(既存モデル)は`items: tuple[tuple[Inline,...],...]`のみでid情報を保持しない設計のため、`note_id`は将来のマーカー⇔リスト対応付けの布石として抽出するに留め、TASK-L003での実際のBlock組み立てには使わない。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-L003 Reference renderer(依存: L002,H007)

### 2026-07-15 07:45 UTC — TASK-L003

**目的**

- `ARCHITECTURE.md` 12.2の"N100 Convert references"を完成させる。TASK-L002の`RawReferenceItem`から実際の`ReferencesBlock`を組み立て、`convert_block.py`のディスパッチへ配線し、Mini-profileでのレンダリングを実装する。

**変更**

- `src/wikiepwing/normalize/references_block.py`に`build_references_block()`を実装した。`convert_inline_nodes`のみで済み(`convert_document`不要)、TASK-K010で発生したような循環importの心配は無い。
- `convert_block.py`に`is_reference_list`判定を追加した。参照リストも`<ol>`要素であるため、`is_ordered_list`より前にチェックする必要があることに気づき(順序を誤ると通常のOrderedListBlockに変換されてしまう)、その順序で配線した。
- `render/mini_layout.py`に`ReferencesBlock`の`_render_block`ケースを追加した。各項目を"[N] 引用文"としてDOM順の番号付きでレンダリングする(インラインマーカーとの対応はDOM順による暗黙のものに留まる、モデルにid情報が無いため)。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_references_block.py tests/test_normalize_convert_block.py tests/test_render_mini_layout.py
make check
git diff --check
```

**結果**

- `build_references_block`の組み立て・空リスト・インライン変換を3件、`convert_block`での正しいディスパッチ(参照リスト/通常の`<ol>`)を2件、Mini-layoutでの番号付きレンダリング/空リストを2件のテストで確認した。
- 標準スイート934件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 参照リストが`<ol>`要素である事実により、dispatch順序を間違えると通常のリストとして誤変換されるという罠に気づいた。テストで両方の挙動(参照リストとして処理される場合・通常のOrderedListBlockのまま処理される場合)を明示的に確認した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-L004 Category appendix(依存: E008,H007)

### 2026-07-15 08:05 UTC — TASK-L004

**目的**

- `ARCHITECTURE.md` 16.2("標準レイアウト"のカテゴリ付録)を検証するend-to-endテストを追加する。調査の結果、カテゴリ機能自体(TASK-E008のingest取り込み、`normalize/orchestrate.py`の`_read_categories`、TASK-H007の`mini_layout.py`カテゴリ付録レンダリング)はすでに実装済みだったが、raw ingest→normalizeの全体を通してカテゴリが失われずに伝播することを確認する専用テストが一つも無いことに気づいた。

**変更**

- `tests/test_normalize_orchestrate.py`に`test_categories_survive_raw_ingest_through_normalize`を追加した。既知のfixture記事(Emacs、page_id 900001)についてnormalize後の`model.sqlite3`から`article_json_zstd`を実際に解凍・デコードし、`Article.categories == ("Category:Emacs",)`であることを確認する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_orchestrate.py
make check
git diff --check
```

**結果**

- 新規テストを含む標準スイート935件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 本タスクは新規実装ではなく、既存のend-to-end動作確認テストの追加が中心だった。各層(ingest/normalize/render)は個別にテストされていたが、"category appendix"という機能としての結合テストが無かったというギャップをTASKS.mdのタスク番号を辿る過程で発見した。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-L005 Category search terms(依存: L004,J007)

### 2026-07-15 08:25 UTC — TASK-L005

**目的**

- `ARCHITECTURE.md` 14.3(Full profileの"category")と`DATA_CONTRACTS.md` 8("500 category")を実装する。

**変更**

- `src/wikiepwing/search/search_term.py`に`category_terms_for_article()`を実装した。`article.categories`の各カテゴリについて`kind="category"`・priority=500・`source="category"`のSearchTermを生成する。カテゴリは「1カテゴリ名→複数記事」という一対多の性質を持ち、これまでのtitle/redirect/variant term(1キー→1記事、衝突時はTASK-J006で単一勝者に解決)とは相容れないため、`title_terms_for_article`とは独立した関数として実装し、`headwords_for_articles`(TASK-J007)の単一候補解決パスには通さない設計とした(理由をモジュールdocstringに明記)。

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- 複数カテゴリからの複数term生成・`normalize_index_key`の適用・カテゴリ無し記事での空タプル・`title_terms_for_article`に含まれないことを4件のテストで確認した。
- 標準スイート939件(新規4件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- カテゴリ検索は本来`rendered.sqlite3`の`search_terms`テーブル(正規化キーへのUNIQUE制約無し、複数候補を保持できる設計、TASK-J006で気づき済み)向けの機能であり、その永続化層がまだ実装されていないため、本タスクは純粋なterm生成関数のみを提供するに留めた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- EPIC M(Unicode and gaiji、依存: B009)

### 2026-07-15 08:45 UTC — TASK-M001

**目的**

- `ARCHITECTURE.md` 18.1(文字分類categoryA: backend標準文字として表現可能)の基礎となる、backend representability判定を実装する。

**変更**

- 新規パッケージ`src/wikiepwing/gaiji/`を作成し、`representability.py`に`is_backend_representable()`・`unrepresentable_characters()`を実装した。TASK-H009で確立した「EUC-JPエンコードがFPWParserへの必須前処理」という事実に基づき、EUC-JPへ符号化可能かどうかをbackend representabilityの判定基準として採用した。Pythonの標準`codecs`実装(JIS X 0201/0208相当の repertoire)をそのまま利用し、独自の巨大なlookup tableを再実装しない設計にした。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_representability.py
make check
git diff --check
```

**結果**

- ASCII・常用漢字・ひらがな・全角カタカナの表現可能性、絵文字・CJK拡張面文字の表現不能性、文字列中の表現不能文字の出現順抽出、全表現可能文字列での空タプルを8件のテストで確認した。
- 標準スイート947件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `ARCHITECTURE.md`は"backend representability table"の具体的なデータ構造を規定していないため、実際のFreePWINGツールチェーンが要求するEUC-JPエンコード可否をそのまま判定基準として採用した(Python標準ライブラリのcodec実装を「表」として再利用する設計)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M002 Unicode classifier(依存: M001)

### 2026-07-15 09:05 UTC — TASK-M002

**目的**

- `ARCHITECTURE.md` 18.1(文字分類A/B/C/D)を実装する。TASK-M003(安全な置換表構築)がまだ存在しないため、分類器は置換表を呼び出し側から注入する引数として受け取る設計にした。

**変更**

- `src/wikiepwing/gaiji/classifier.py`に`CharacterClass`・`classify_character()`を実装した。判定順序: TASK-M001の`is_backend_representable`→A、置換表(引数、未指定なら何もしない)に登録済み→B、Unicode一般カテゴリがCc/Cf/Cs/Co/Cnのいずれか(意味のあるグリフが無い)→D、それ以外(印字可能だが表現不可)→C。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_classifier.py
make check
git diff --check
```

**結果**

- A/B/C/D各分類の境界(置換表の有無、backend表現可能性が置換表より優先されること、C1制御文字・書式文字・未割り当て・私用領域のD分類)を11件のテストで確認した。
- 標準スイート958件(新規19件、TASK-M001の8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実装中、ASCII C0制御文字(`\x01`等)がEUC-JPでそのままバイト通過するため"A"に分類されてしまうことを発見した。`ARCHITECTURE.md` 18.1のA分類は「エンコード可能性」のみを定義し「意味のあるグリフ」を要求していないため、これは仕様上正しい挙動と判断し、テストをこの実際の挙動に合わせて修正した(C1制御文字で実際のD分類経路を検証する形に差し替えた)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M003 Safe substitutions(依存: M002)
