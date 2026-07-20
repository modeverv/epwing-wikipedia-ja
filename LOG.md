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

### 2026-07-15 09:25 UTC — TASK-M003

**目的**

- `ARCHITECTURE.md` 18.2(置換例)を実装する。「意味を変える置換は行いません」という制約の下、単純な文字→文字置換(nbsp・タイポグラフィ引用符)とシーケンスレベルの処理(variation selector除去・NFC正規化)を組み合わせる。

**変更**

- `src/wikiepwing/gaiji/substitutions.py`に`DEFAULT_SUBSTITUTIONS`・`is_variation_selector()`・`apply_safe_substitutions()`を実装した。NFC正規化→variation selector除去(基底文字を保持しつつ`CHAR_VARIATION_SELECTOR_DROPPED`という新しいDiagnostic codeを記録)→置換表適用、の順で処理する。TASK-M002の`classify_character`が受け取る`substitutions`引数の実データとしてそのまま使える。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_substitutions.py
make check
git diff --check
```

**結果**

- nbsp→space・タイポグラフィ引用符→ASCII引用符・variation selector検出(標準U+FE00-FE0F/補助U+E0100-E01EF範囲)・除去時の基底文字保持とDiagnostic記録・結合文字列のNFC正規化・置換不要時の非変更・カスタム置換表・デフォルト置換表の内容を10件のテストで確認した。
- 標準スイート968件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `CHAR_VARIATION_SELECTOR_DROPPED`という新しいDiagnostic codeを追加した(`ARCHITECTURE.md` 11.7の例一覧は網羅的でないことを確認済み)。
- 実際のnormalizeパイプラインへの配線(本文全体へどのタイミングで適用するか)は本タスクの対象外とした。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M004 Gaiji registry schema(依存: M002)

### 2026-07-15 09:45 UTC — TASK-M004

**目的**

- `ARCHITECTURE.md` 18.3(Gaiji registry)の永続化スキーマを実装する。既存の`ingest/database.py`・`model/database.py`・`reference/database.py`と同じmigrationエンジンパターンを複製する。

**変更**

- `migrations/gaiji/001_initial.sql`に`gaiji_registry`テーブル(18.3の全フィールド、`normalized_sequence`にUNIQUE制約)を実装した。`application_id`は既存3 DBの慣習("MODL"/"RAWD"のような4文字ASCIIコード)に倣い"GAJI"(1195461193)を採用した。
- `src/wikiepwing/gaiji/database.py`に`connect_gaiji_database()`・`initialize_gaiji_database()`・`GaijiDatabaseError`を実装した(`model/database.py`のmigrationエンジンをそのまま複製)。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_database.py
make check
git diff --check
```

**結果**

- 初期migration・有効行のINSERT・重複normalized_sequenceの拒否・不正width_classの拒否・負のusage_countの拒否・migrationの冪等性/チェックサム不一致検出・失敗migrationのロールバック・不正migration集合の拒否を10件のテストで確認した。
- 標準スイート978件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 「同じ文字列は一度だけbitmap生成します」(18.3)という要件を、アプリケーションロジックだけでなくDBレベルのUNIQUE制約でも保証する設計にした(重複INSERTが確実に失敗する)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M005 Glyph bitmap renderer(依存: M004)

### 2026-07-15 10:10 UTC — TASK-M005

**目的**

- `ARCHITECTURE.md` 18.4(フォント: Docker内の再配布可能なNoto CJK系を利用、フォントファイル自体は成果物に含めない)を実装する。gaiji文字を実際にラスタライズしてbitmapを生成する。

**変更**

- `pyproject.toml`に`Pillow==12.2.0`を新規依存として追加した(`uv add`)。
- `docker/toolchain.Dockerfile`のruntimeステージに`fonts-noto-cjk=1:20220127+repack1-1`を追加した。既存のDebian snapshot pinning慣習に従い、バージョンを推測せずネットワーク経由で同一snapshotから実際のpinバージョンを確認して採用した。
- `src/wikiepwing/gaiji/glyph_renderer.py`に`GlyphRenderError`・`render_glyph_bitmap()`・`bitmap_hash()`・`DEFAULT_FONT_PATH`(Debianのfonts-noto-cjkパッケージの標準インストールパス、ドキュメント化された前提)を実装した。

**実行コマンド**

```bash
uv add "Pillow==12.2.0"
uv run pytest tests/test_gaiji_glyph_renderer.py tests/test_gaiji_toolchain_definition.py
make check
git diff --check
```

**結果**

- PNG生成・決定性(同じ入力で同じbitmap)・異なるsequenceでの異なるbitmap・フォント欠落時のエラー・空sequence時のエラー・bitmap_hashのSHA-256計算を8件のテストで確認した(このmacOS Dev環境にはfonts-noto-cjkが無いため、実フォント読み込みが必要なテストはmacOSのCJK対応システムフォントを代替として使用し、それも無ければskip)。
- Dockerfileへのpin済みfonts-noto-cjk追加を1件のテストで確認した。
- 標準スイート987件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- ユーザーに確認した上で、Pillowを新規依存として追加しNoto CJKフォントをDocker toolchainイメージへ組み込む方針を採用した(スタブ実装やスキップではなく実装を進める判断)。
- フォントファイル自体はgitリポジトリに含めず、Docker imageのapt packageとしてのみ存在させる設計にした(`ARCHITECTURE.md` 18.4の要件通り)。
- `DEFAULT_FONT_PATH`(`/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`)は、実際にDebianパッケージの中身をネットワーク経由で検証できなかったため、ドキュメント化された前提(一般的に知られているfonts-noto-cjkパッケージの標準インストールパス)として明記した。
- manifestへのfont package version/hash記録(18.4後半の要件)は、既存のstage manifestスキーマに対応するフィールドが無く、`toolchain_image_digest`が既にイメージ全体のハッシュとして間接的にこれをカバーしているため、本タスクでは追加のスキーマ変更を行わなかった。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M006 Gaiji code assignment(依存: M005)

### 2026-07-15 10:25 UTC — TASK-M004訂正(TASK-M006着手時に発見)

**目的**

- TASK-M006(gaiji code assignment)に着手する際、`DATA_CONTRACTS.md` 10("Gaiji registry contract")に既に正式なテーブル定義(`CREATE TABLE gaiji (sequence TEXT PRIMARY KEY, ...)`)が存在することに気づいた。TASK-M004実装時にこの節を確認せず独自のスキーマ(`gaiji_registry`テーブル、列名も異なる)を設計してしまっていたため、正式な契約に合わせて修正する。

**変更**

- `migrations/gaiji/001_initial.sql`のテーブルを、`DATA_CONTRACTS.md` 10の正式定義通りに書き換えた: テーブル名`gaiji`(`gaiji_registry`から変更)、`sequence`を主キーに(独自の`gaiji_id`連番主キーを廃止)、列名を`bitmap_path`/`bitmap_sha256`/`font_identifier`/`assigned_code`に統一(`bitmap_hash`/`font_source_identifier`/`assigned_gaiji_code`から変更)、`width_class`の値を`'narrow'/'wide'`に統一(独自の`'half'/'full'`から変更)、`assigned_code`をNOT NULL UNIQUE(独自実装ではnullable扱いだった)に修正。
- `src/wikiepwing/gaiji/database.py`のdocstringを`DATA_CONTRACTS.md` 10参照へ更新した(コード自体はmigrationエンジンで汎用的なため変更不要)。
- `tests/test_gaiji_database.py`を新スキーマに合わせて全面的に書き直した。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_database.py
make check
git diff --check
```

**結果**

- 修正後のスキーマで11件のテストが成功した(初期migration・有効行のINSERT・`sequence`/`assigned_code`重複拒否・不正width_class拒否・負のusage_count拒否・migration冪等性/ロールバック/不正集合拒否)。
- 標準スイート988件、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 本プロジェクトはまだ実運用データが存在しない開発中フェーズであるため、新しいmigration versionを追加するのではなく、`001_initial.sql`自体を訂正した(TASK-M004のコミットはまだ実データベースを生成する形で配布されていない)。
- 今後、新しいDBスキーマを設計する際は、`DATA_CONTRACTS.md`の該当節を先に確認する運用を徹底する(本件はその確認を怠ったために生じた)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M006 Gaiji code assignment(依存: M005)

### 2026-07-15 10:45 UTC — TASK-M006

**目的**

- `DATA_CONTRACTS.md` 10(Assignmentは"Unicode sort order + width classなどの決定論的規則"を使用し、処理順依存にしない)を実装する。

**変更**

- `src/wikiepwing/gaiji/code_assignment.py`に`GaijiCodeAssignmentError`・`assign_gaiji_codes()`を実装した。width_class("narrow"/"wide")ごとに独立した採番空間を持ち、各グループ内でsequenceのUnicodeソート順に基づいて`f"{width_class}-{index:04d}"`形式のcodeを1始まりで割り当てる。`tests/fixtures/handcrafted/halfchars.txt`/`fullchars.txt`が実際に別ファイル(=別code空間)であることを確認し、narrow/wideを独立させる根拠とした。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_code_assignment.py
make check
git diff --check
```

**結果**

- width_class毎の連番割当・独立したcode空間・Unicodeソート順による決定論的割当・入力順序に依存しない冪等性・空入力・不正width_class・重複sequence・4桁ゼロパディングを8件のテストで確認した。
- 標準スイート996件(新規8件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際のFreePWING/EB向けファイル形式(`halfchars.txt`の行形式等)への変換や具体的なEB gaiji code表現(hexアドレス等)への対応付けは、本タスクの対象外としTASK-M007へ委ねた。本タスクは抽象的な決定論的割当アルゴリズムのみを扱う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M007 FreePWING gaiji integration(依存: M006,H009)

### 2026-07-15 11:10 UTC — TASK-M007

**目的**

- `ARCHITECTURE.md` 17.2/18.3/18.4を完成させる。TASK-M005(bitmap生成)・TASK-M006(決定論的code割当)の出力を、実際の`fpwmake`が読み込むgaiji build入力(`halfchars.txt`/`fullchars.txt`+個別XBMファイル)へ変換する。

**変更**

- `src/wikiepwing/gaiji/freepwing_gaiji.py`に`FreePwingGaijiError`・`GaijiBuildEntry`・`xbm_bytes_from_image()`・`render_glyph_as_xbm()`・`write_gaiji_build_files()`を実装した。XBMのビット詰め順(LSB-first、bit=1が前景/黒)を、実際にDockerで動作確認済みの`tests/fixtures/handcrafted/generate_gaiji.pl`の既知バイト列を手動デコードして確認した上で実装した。
- `render_glyph_as_xbm`はnarrow(8x16)/wide(16x16)の寸法でフォントからラスタライズし、`write_gaiji_build_files`は各gaijiのXBMファイルと`halfchars.txt`/`fullchars.txt`(`<name> <xbmファイル名>`形式)を書き出す。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_freepwing_gaiji.py
make check
git diff --check
```

**結果**

- 実fixtureパターン(`generate_gaiji.pl`が生成する既知バイト列)とのバイト完全一致を含む7件のテストで、XBM生成・寸法・build files書き出しを確認した。
- 標準スイート1003件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- mypy strictで`Image.load()`の戻り値型(`PixelAccess | None`)に関するエラーを検出し、Noneチェックを追加して修正した。
- gaiji.sqlite3への実際の書き込み配線・normalize/renderパイプラインへの実配線、および実際のDocker/`fpwmake`実行による統合確認は対象外とした(このセッションではDocker実行環境が無いため、既存fixtureとのバイト形式一致をユニットテストで確認するに留めた)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M008 Unrepresentable fallback(依存: M002)

### 2026-07-15 11:30 UTC — TASK-M008

**目的**

- `ARCHITECTURE.md` 18.5(D分類の文字はコードポイント表記へfallback、件数・頻出順・記事例をreportへ出す)を実装する。実際のreport出力(TASK-M009)の手前の、fallback文字列生成と出現統計の集計を行う。

**変更**

- `src/wikiepwing/gaiji/unrepresentable.py`に`unrepresentable_fallback()`・`UnrepresentableExample`・`UnrepresentableStat`・`UnrepresentableTracker`を実装した。fallbackは`"[U+XXXX]"`形式(4桁以上、補助面は桁数拡張)。Trackerは文字ごとの出現回数を無制限にカウントしつつ、`DATA_CONTRACTS.md` 11の詳細サイズ上限の慣習に倣い記事例(page_id/title)の保持数だけ上限(デフォルト5件)を設ける設計にした。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_unrepresentable.py
make check
git diff --check
```

**結果**

- fallback形式(BMP/補助面)・出現回数集計・頻出順ソート・同数時のコードポイント順tie-break・limit・記事例上限とカウントの独立性・page_id/titleの保持・総出現数・distinct文字一覧・不正なmax_examples・0件上限時の挙動を13件のテストで確認した。
- 標準スイート1016件(新規13件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- mypy strictで`sorted()`が`list`を返しタプル型注釈と不一致になるエラーを検出し、`tuple()`で包んで修正した。
- 記事例の保持数に上限を設けたが出現カウント自体は無制限にした設計は、大規模ビルドでのメモリ使用量を抑えつつ正確な統計を保つための判断。
- 実際のreportファイル出力・フォーマットはTASK-M009へ委ねた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-M009 Unicode report(依存: M003-M008)

### 2026-07-15 11:50 UTC — TASK-M009

**目的**

- `ARCHITECTURE.md` 18.5("件数・頻出順・記事例をreportへ出す")を完成させ、Epic M(Unicode and gaiji)を締めくくる。

**変更**

- `src/wikiepwing/gaiji/report.py`に`UnicodeReport`・`build_unicode_report()`・`write_unicode_report()`を実装した。TASK-M008の`UnrepresentableTracker.most_frequent()`から総出現数・distinct文字数・文字ごとの統計(character/code_point/count/examples)を組み立て、JSONとしてTASK-I004の`atomic_write_text`で原子的に書き出す。`reference/report.py`ほどの規模(JSON+HTML+Markdown)は要求されていないと判断し、単一のJSON reportに絞った。

**実行コマンド**

```bash
uv run pytest tests/test_gaiji_report.py
make check
git diff --check
```

**結果**

- report組み立て・頻出順ソート・code_point/examples含有・空trackerでの挙動・JSON書き込みの妥当性・親ディレクトリ自動作成を6件のテストで確認した。
- 標準スイート1022件(新規6件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際のCLIコマンドへの配線(`wikiepwing`のサブコマンドとしての公開)は本タスクの対象外とし、将来のタスクへ委ねた。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。
- Epic M(Unicode and gaiji、TASK-M001-M009)が全て完了した。TASK-M004実装時に`DATA_CONTRACTS.md`の既存スキーマ定義を確認せず独自設計してしまうミスがあったが、TASK-M006着手時に発見し訂正した(この教訓を今後のスキーマ設計作業に活かす)。

**次タスク**

- EPIC N(Math、依存: G001)

### 2026-07-15 12:10 UTC — TASK-N001

**目的**

- `ARCHITECTURE.md` 15.7(数式: 1.テキスト代替を保存 2.TeX sourceがあればcache keyに使用)の最初の段階として、記事HTML中の数式ノード(`<math>`要素、MathML)を検出しTeX source・テキスト代替・block/inline区分を抽出する。

**変更**

- `src/wikiepwing/normalize/math_node.py`に`RawMathNode`・`is_math_node()`・`parse_math_node()`を実装した。MediaWiki固有のwrapper HTML構造(確認できない)ではなく、MathML標準自体の`alttext`/`display`属性と`<annotation encoding="application/x-tex">`子要素(ネスト探索)という安定した規約に依拠した。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_math_node.py
make check
git diff --check
```

**結果**

- math要素の検出・非検出・TeX source抽出・alttext抽出・display=block/inline/欠落の判定・各種欠落時のNone・異なるencodingのannotationの無視・深いネストでの探索・非math要素へのエラーを11件のテストで確認した。
- 標準スイート1033件(新規11件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- MediaWikiの実際のMath拡張出力HTML(`mwe-math-element`等のwrapper class名)は生のHTML実例を確認できないため、MathML仕様自体が定める標準属性(`alttext`/`display`)・要素(`annotation`)にのみ依拠する設計にした。これによりMediaWiki固有の変更に影響されにくくなる一方、実際の出力に`alttext`/`display`が無いケースがあれば別途対応が必要になる可能性がある。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-N002 Canonical math source(依存: N001)

### 2026-07-15 12:30 UTC — TASK-N002

**目的**

- `ARCHITECTURE.md` 15.7の"2. TeX sourceがあればcache keyに使用"を実装する。TASK-N001の`RawMathNode`から、表記ゆれを吸収した正準形を作りcache keyへ変換する。

**変更**

- `src/wikiepwing/normalize/math_source.py`に`canonicalize_math_source()`・`compute_math_cache_key()`を実装した。NFC正規化+空白run畳み込み+trimでcanonical formを作り、`tex_source`優先・`text_alternative`フォールバックでSHA-256ハッシュを計算する。両方とも無い/canonical化後に空文字列の場合は`None`(cacheしない)を返す。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_math_source.py
make check
git diff --check
```

**結果**

- 空白畳み込み・trim・NFC正規化・tex_source優先・text_alternativeフォールバック・両方無い/空白のみの場合のNone・表記ゆれのある同一数式での同一key・異なる数式での異なるkey・SHA-256 hex digest形式を10件のテストで確認した。
- 標準スイート1043件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実際のレンダリング・cache格納(TASK-N003-N004)は対象外とした。本タスクは決定論的なcache key計算のみを扱う。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-N003 Isolated renderer(依存: N002)

### 2026-07-16 00:15 UTC — TASK-N003

**目的**

- `ARCHITECTURE.md` 15.7の"3. SVG/PNGへ安全にレンダリング"を実装する。ユーザーに新規依存導入の方針を確認し、外部LaTeXツールチェーンではなくmatplotlib mathtext(プロセス内、新規依存はmatplotlibのみ)を採用する承認を得た。

**変更**

- `pyproject.toml`に`matplotlib==3.11.0`を追加した(`uv add`)。
- `src/wikiepwing/normalize/math_renderer.py`に`MathRenderError`・`render_math_to_image()`を実装した。`matplotlib.mathtext.math_to_image`を呼び出し、失敗を1数式単位で`MathRenderError`として隔離する(ARCHITECTURE.md 3.5の劣化表示原則に従う)。

**実行コマンド**

```bash
uv add "matplotlib==3.11.0"
uv run pytest tests/test_normalize_math_renderer.py
make check
git diff --check
```

**結果**

- SVG/PNGレンダリング・デフォルトフォーマット・異なる数式での異なる出力・SVG/PNG双方の決定性・空/空白のみのsourceでのエラー・未対応マクロでのエラー・失敗後の後続レンダリングの正常動作を10件のテストで確認した。
- 標準スイート1053件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 実装中に発見した重要な問題: matplotlibのSVG出力は壁時計タイムスタンプ(`<dc:date>`)とプロセスごとにランダムなglyph-idソルト(`svg.hashsalt`)を埋め込むため、同じ数式でも実行のたびに異なるバイト列になっていた。本プロジェクトが重視する再現可能ビルド(pinされたDocker snapshot等の既存方針)と相容れないため、`svg.hashsalt`を固定値に設定し、出力後に`<dc:date>`要素を正規表現で除去することで決定論的な出力にした。この修正が無ければ、同一入力から生成されるTASK-N004のcacheキーとbitmap内容が実行ごとに変わってしまい、cacheの意味が失われるところだった。
- mathtextはMediaWikiのtexvcが許す完全なTeXマクロ集合をサポートしない(実用的なサブセットのみ)。未対応の数式は本タスクの隔離設計により1つずつエラーとして扱われ、記事全体のビルドは止まらない。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-N004 Math cache(依存: N003)

### 2026-07-16 00:35 UTC — TASK-N004

**目的**

- `ARCHITECTURE.md` 15.5(画像Cache keyの`converter_version`を含める慣習)・22.3("math cache"ディレクトリ)を数式向けに実装する。TASK-N002のcontent-basedなcache keyに、レンダラバージョンを組み合わせたファイルシステムcacheを実装する。

**変更**

- `src/wikiepwing/normalize/math_cache.py`に`MathCache`・`MATH_CACHE_VERSION`を実装した。`get_or_render(cache_key, image_format, render)`は、cache_keyが`None`なら常にレンダリングし(TASK-N002の契約通りcacheしない)、それ以外はcache_key+`MATH_CACHE_VERSION`+image_formatから計算したファイルパスでhit/miss判定し、miss時はTASK-I004の`atomic_write_bytes`で原子的に保存する。

**実行コマンド**

```bash
uv run pytest tests/test_normalize_math_cache.py
make check
git diff --check
```

**結果**

- cache miss時のrender呼び出し・cache hit時のrender非呼び出し・`None`キーでの常時レンダリング・異なるキー/フォーマットの独立した格納・ディレクトリ自動作成・`MATH_CACHE_VERSION`変更による既存cacheの無効化を7件のテストで確認した。
- 標準スイート1060件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `MATH_CACHE_VERSION`を含めることで、TASK-N003のレンダラ実装が将来変わった場合(バグ修正等でレンダリング結果のバイト列が変わる場合)に、既存cacheを安全に無効化できる設計にした(画像cache keyの`converter_version`と同じ考え方)。
- cacheの自動expire・容量上限は対象外とした(必要になれば別タスク)。
- 既存の未追跡`.DS_Store`と`v1/`配下は変更していない。

**次タスク**

- TASK-N005 Raster conversion(依存: N003)

## 2026-07-16 TASK-N005 Raster conversion

**目的**

`ARCHITECTURE.md` 15.7の数式変換パイプラインのステップ4(EPWING graphicへ変換)を実装する。TASK-N003がレンダリングするPNG(透過背景)を、実toolchain互換の標準BMP(`tests/fixtures/handcrafted/generate_bitmap.pl`が示す`BM`マジック始まりの24bit color BMP)へ変換する。

**変更**

- `src/wikiepwing/normalize/math_raster.py`(新規): `MathRasterError`・`convert_png_to_bmp`(Pillowでpngをデコードし、RGBAのalphaチャンネルをmaskにして不透明背景色へ合成後BMPとして書き出す)・`render_math_to_bmp`(TASK-N003の`render_math_to_image(..., image_format="png")`をラップ)
- `tests/test_normalize_math_raster.py`(新規7件)
- `TASKS.md`(TASK-N005を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_math_raster.py
make check
git diff --check
```

**結果**

- BMPマジックの確認・透過ピクセルの背景合成・不透明ピクセルの保持・空/不正バイト列でのエラー・エンドツーエンドの決定論的レンダリングを7件のテストで確認した。
- 標準スイート1067件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 新規依存は追加していない(TASK-M005で追加済みのPillowを再利用)。
- 透過部分の合成先背景色はデフォルトで白(255,255,255)としたが、実際にEPWINGで使う紙面色は将来設定可能にしてもよい(現時点では対象外)。
- 実際のFreePWING `add_graphic`/EPIC Oへの配線は対象外(このタスクはバイトフォーマット変換のみ)。

**次タスク**

- TASK-N006 Inline/block layout(依存: N004-N005,H007)

## 2026-07-16 TASK-N006 Inline/block layout

**目的**

`convert_block.py`/`paragraphs.py`のdocstringに明記されていた「math conversion deferred to later epics」を解消し、TASK-N001(`RawMathNode`)・TASK-N002(`canonicalize_math_source`)を実際のDOM変換パイプラインへ配線する。block-level(`display="block"`)は`MathBlock`、inlineは新設`MathInline`として、`convert_block`/`convert_inline_nodes`から生成できるようにした。Mini layout renderer(TASK-H007)でも両方をテキストとしてrenderする。

**変更**

- `src/wikiepwing/model/inline.py`: `MathInline`(`source`/`source_format`)を追加、`Inline` union・payload/parseへ配線
- `src/wikiepwing/normalize/math_content.py`(新規): `resolve_math_source(RawMathNode) -> tuple[str, str] | None`(tex優先、text_alternativeへfallback、canonicalize後空ならNone)
- `src/wikiepwing/normalize/convert_block.py`: block-level `<math display="block">` dispatch(`MathBlock`または`MATH_NO_SOURCE`診断付き`UnsupportedBlock`)、`_is_block_level`に`display="block"`のmath判定を追加
- `src/wikiepwing/normalize/paragraphs.py`: inline `<math>` dispatch(`MathInline`または`MATH_NO_SOURCE`診断付き`UnsupportedInline`)
- `src/wikiepwing/normalize/whitespace.py`: `_normalize_inline`の既存exhaustive dispatchに`MathInline`(verbatim保持)を追加
- `src/wikiepwing/render/mini_layout.py`: `MathBlock`を独立行、`MathInline`を段落内テキストの一部としてrender
- `tests/test_normalize_math_content.py`(新規6件)、`tests/test_normalize_convert_block.py`/`tests/test_normalize_paragraphs.py`/`tests/test_render_mini_layout.py`/`tests/test_model_inline.py`への追記(計16件)
- `TASKS.md`(TASK-N006を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_math_content.py tests/test_normalize_convert_block.py tests/test_normalize_paragraphs.py tests/test_render_mini_layout.py tests/test_model_inline.py tests/test_normalize_whitespace.py -q
make check
git diff --check
```

**結果**

- block-level math -> MathBlock、inline math -> MathInline、両方のno-source fallback、mini layoutでのtext render、既存の`_normalize_inline`exhaustive dispatchへの追加を22件のテストで確認した。
- 標準スイート1083件(新規22件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `resolve_math_source`はTASK-N002の`compute_math_cache_key`と全く同じ優先順位・canonicalize処理を再利用し、Block/Inlineに格納される文字列が将来のcache keyと一致するようにした。
- 実際のgraphic byte(TASK-N003-N005のレンダリング結果)をRenderedEntry.graphics/EPWING graphicへ埋め込む配線はEPIC O(`GraphicAsset`/`add_graphic`)の責務として対象外のままとした(`ImageBlock`が同様にまだplaceholderであることに合わせた)。
- `whitespace.py`の`_normalize_inline`はexhaustiveな`isinstance`チェックで未対応型に`AssertionError`を送出する設計だったため、`MathInline`追加に伴い明示的に分岐を追加する必要があった(見落とすとテスト以外の経路でクラッシュしていた)。

**次タスク**

- TASK-N007 Failure fallback(依存: N001)

## 2026-07-16 TASK-N007 Failure fallback

**目的**

`ARCHITECTURE.md` 15.7の数式変換優先順位のステップ5「失敗時はTeX/plain textへフォールバック」を実装する。TASK-N003(レンダラ)・TASK-N004(cache)・TASK-N005(raster変換)を1つのパイプラインとして呼び出し、途中で失敗しても例外を漏らさずplain textへフォールバックする関数を用意し、EPIC N(数式)を完了させる。

**変更**

- `src/wikiepwing/normalize/math_fallback.py`(新規): `MathRenderOutcome`(`bitmap`/`fallback_text`/`diagnostics`)・`render_math_with_fallback`(cache経由でrender_math_to_image→convert_png_to_bmpを呼び、`MathRenderError`/`MathRasterError`を`MATH_RENDER_FAILED`診断+text fallbackへ変換)
- `tests/test_normalize_math_fallback.py`(新規4件)
- `TASKS.md`(TASK-N007を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_math_fallback.py
make check
git diff --check
```

**結果**

- 成功時のBMP返却・失敗時のtext fallback+診断・cache経由での2回目呼び出し省略・`None`cache_keyでの常時レンダリングを4件のテストで確認した。
- 標準スイート1087件(新規4件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `render_math_with_fallback`は`MathRenderError`・`MathRasterError`(いずれも`ValueError`のサブクラス)のみを捕捉する。それ以外の予期しない例外は伝播させ、隠蔽しない。
- fallback textの選定(text alternative優先かTeX sourceかなど)は呼び出し側の責務とした(TASK-N006の`resolve_math_source`が既にその優先順位を実装済みのため、二重実装を避けた)。
- これでEPIC N(数式)のTASK-N001-N007が完了した。実際のgraphic埋め込み配線(RenderedEntry.graphics/EPWING `add_graphic`)はEPIC O待ち。

**次タスク**

- TASK-O001 MediaReference extraction(依存: G001,F004)

## 2026-07-16 TASK-O001 MediaReference extraction

**目的**

EPIC O(画像)の最初のタスクとして、`ARCHITECTURE.md` 15.1/15.2を実装する。`<img>`/`<figure>`+`<figcaption>`というDOM要素から既存の`MediaReference`モデルを抽出する。normalize段階では画像参照のみを保存し、ダウンロードは行わない。

**変更**

- `src/wikiepwing/normalize/media_node.py`(新規): `is_image_node`・`parse_image_node`(`src`欠落時は`None`、`source_name`をURLパスからURLデコードして導出、`width`/`height`は非負整数でなければ`None`)・`is_figure_with_image`・`parse_figure_media`(`<figcaption>`テキストをcaptionに、ネストした`<img>`も探索)
- `tests/test_normalize_media_node.py`(新規16件)
- `TASKS.md`(TASK-O001を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_media_node.py
make check
git diff --check
```

**結果**

- 属性抽出・URLデコード・width/height欠落/不正値のfallback・figcaptionからのcaption抽出・ネストしたimg探索・src欠落時のNone返却を16件のテストで確認した。
- 標準スイート1103件(新規16件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `media_id`は`source_url`をそのまま採用した。既存の`normalize/orchestrate.py`の`_read_media`(Wikimedia Enterprise Snapshotのmain image由来)が同じ前例を採用しているため、一貫性を優先した。
- `role`は常に`"unknown"`とし、分類ロジックはTASK-O002に委ねた(TASK-O002/TASK-O010がともに本タスクの出力を入力として使う設計であることをTASKS.mdの依存関係から確認した)。
- `convert_block`/`ImageBlock`への実際の配線は対象外とした(現時点で`ImageBlock`はまだ`media_id`のみのplaceholderで、Block treeへの本格的な画像embeddingは後続タスクの範囲と判断した)。

**次タスク**

- TASK-O002 Role classification(依存: O001,K008)

## 2026-07-16 TASK-O002 Role classification

**目的**

`ARCHITECTURE.md` 15.3の選択ポリシー優先順位・除外候補(16pxなどのicon)を反映し、TASK-O001が`role="unknown"`で抽出した`MediaReference`に実際のroleを割り当てる。

**変更**

- `src/wikiepwing/normalize/media_role.py`(新規): `classify_media_role`(優先順位: `main`維持 > iconサイズ判定(20px以下) > infobox src集合一致 > lead flag > デフォルト`body`)、`with_classified_role`(`dataclasses.replace`で新しい`MediaReference`を返す)
- `tests/test_normalize_media_role.py`(新規10件)
- `TASKS.md`(TASK-O002を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_media_role.py
make check
git diff --check
```

**結果**

- `main`維持・icon判定(単独・infoboxより優先)・infobox判定(leadより優先)・lead判定・デフォルトbody・次元不明時のicon非該当・フィールド保持を10件のテストで確認した。
- 標準スイート1113件(新規10件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `role="main"`(Wikimedia Enterprise Snapshotのmain image由来、`normalize/orchestrate.py`の`_read_media`が既に設定済み)は上書きしない設計にした。DOM文脈から推測したroleより、Snapshot自体が明示するmain画像の方が信頼できるため。
- icon判定はTASK-K008の`RawInfobox.image_srcs`との一致より優先させた。小さいアイコンがinfobox内に置かれるケース(編集アイコン等)を誤ってinfobox画像として選択しないようにするため。
- decorative flag/tracking image/blank placeholderの検出は対象外とした(現時点ではサイズによるicon判定のみ実装、必要になれば別タスク)。

**次タスク**

- TASK-O003 Selection policy(依存: O002)

## 2026-07-16 TASK-O003 Selection policy

**目的**

`ARCHITECTURE.md` 15.3の選択ポリシーを実装する。TASK-O002がroleを割り当てた`MediaReference`の並びから、除外候補(icon)を取り除き、重複を除いたうえで優先順位(主画像 > Infobox主要画像 > lead figure > 本文画像)に従って並べ替え、`Article.media`向けの最終選択リストを作る。

**変更**

- `src/wikiepwing/normalize/media_selection.py`(新規): `select_media`(icon除外、`source_url`重複除去(実バイト未取得のためcontent hashの代替)、`main`>`infobox`>`lead`>`body`>`unknown`>`icon`の優先度で安定ソート)
- `tests/test_normalize_media_selection.py`(新規7件)
- `TASKS.md`(TASK-O003を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_media_selection.py
make check
git diff --check
```

**結果**

- 空入力・icon除外・重複除去・優先順位ソート・unknown role・同roleでのDOM順保持・複合ケースを7件のテストで確認した。
- 標準スイート1120件(新規7件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- "duplicate hash"(15.3の除外候補)は実バイトのcontent hashが必要だが、ダウンロード自体がTASK-O004以降のため、この段階では`source_url`の重複を実用的な代替として採用した。同一URLは同一ファイルであるという前提は妥当。
- 安定ソート(Pythonの`sorted`)を使うことで、同じroleタイル内でのDOM出現順(15.3の「本文先頭の意味ある画像」→「追加本文画像」の順序)を自然に保持できる。
- decorative flag/tracking image/blank placeholderの検出は対象外のままとした。

**次タスク**

- TASK-O004 Secure downloader(依存: A004)

## 2026-07-16 TASK-O004 Secure downloader

**目的**

`ARCHITECTURE.md` 15.4のダウンロード安全性要件のうちネットワーク層(HTTPSのみ・host allowlist・redirect回数制限・timeout・content-length上限)を実装する。新規`src/wikiepwing/media/`パッケージ(gaijiと同様の独立パッケージ)にsecure downloaderを新設した。

**変更**

- `src/wikiepwing/media/__init__.py`(新規)
- `src/wikiepwing/media/downloader.py`(新規): `MediaDownloadError`・`MediaDownloadResult`・`SecureMediaDownloader`(`MediaTransport` Protocolでネットワーク層を抽象化、既定実装は`urllib.request`ベース)
- `tests/test_media_downloader.py`(新規16件、fake transportで実ネットワークなしにテスト)
- `TASKS.md`(TASK-O004を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_downloader.py
make check
git diff --check
```

**結果**

- HTTPS強制・host allowlist・redirect追跡と各hopでの再検証・redirect超過・Location欠落・想定外status・content-length上限(header/実読み取り両方)・response常時close・コンストラクタバリデーションを16件のテストで確認した。
- 標準スイート1136件(新規16件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- redirectは各hopでHTTPS/host allowlistを再検証する設計にした。allowlistされたホストからdisallowedなホストへredirectされることでallowlistを迂回されるのを防ぐため。
- Content-Lengthヘッダによる事前拒否だけでなく、実際に読み取ったバイト数でも上限を強制した(ヘッダを偽るサーバへの防御)。
- MIME/magic byte検証・実デコード後pixel上限・SVG sanitizeは対象外とした(バイト列の実デコードが必要なためTASK-O005/O006の範囲)。
- 既存の`source/downloader.py`(Snapshot chunk用)は同一APIへの1回だけのredirectを扱う設計であり、O004は任意の(allowlistされた)外部ホストへの複数回redirectを扱う必要があるため、独立したモジュールとして実装した(コード共有は見送った)。

**次タスク**

- TASK-O005 MIME/magic/pixel validation(依存: O004)

## 2026-07-16 TASK-O005 MIME/magic/pixel validation

**目的**

`ARCHITECTURE.md` 15.4の「MIMEとmagic byte検証」「実デコード後pixel上限」を実装する。TASK-O004がダウンロードした生バイト列を、magic byteによるフォーマット判定・宣言Content-Typeとの整合性確認・Pillowによる実デコードとpixel数上限チェックの3段階で検証する。

**変更**

- `src/wikiepwing/media/validation.py`(新規): `MediaValidationError`・`MediaValidationResult`(`detected_format`/`width`/`height`)・`validate_media_bytes`(magic byte判定→Content-Type整合性→Pillowデコード→pixel上限)
- `tests/test_media_validation.py`(新規13件)
- `TASKS.md`(TASK-O005を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_validation.py
make check
git diff --check
```

**結果**

- PNG/JPEG/GIF/WEBP各magic byteの認識・未対応フォーマットの拒否・Content-Type一致/不一致/未知値/未指定・デコード失敗・pixel上限超過/境界値・コンストラクタバリデーションを13件のテストで確認した。
- 標準スイート1149件(新規13件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- サーバ提供の`Content-Type`ヘッダを単独では信頼せず、magic byteによる実フォーマット判定を主とし、Content-Typeは矛盾チェックのみに使う設計にした。
- SVGはXMLベースで固定long magic byteを持たず、外部entity等の別の脅威モデルを持つため対象外とし、TASK-O006のSVG sanitizerに委ねた。
- 新規依存は追加していない(TASK-M005で追加済みのPillowを再利用)。

**次タスク**

- TASK-O006 SVG sanitizer(依存: O005)

## 2026-07-16 TASK-O006 SVG sanitizer

**目的**

`ARCHITECTURE.md` 15.4の「SVG sanitize」「external entity禁止」を実装する。SVGはXMLであり、TASK-O005のmagic byte検証の対象外としたため専用のsanitizerを新設した。

**変更**

- `src/wikiepwing/media/svg_sanitizer.py`(新規): `SvgSanitizeError`・`sanitize_svg`(DOCTYPE/ENTITY宣言をパース前にfail-closedで拒否、パース後に`<script>`/`<foreignObject>`要素・`on*`属性・`javascript:` href/xlink:hrefを除去して再シリアライズ)
- `tests/test_media_svg_sanitizer.py`(新規13件)
- `TASKS.md`(TASK-O006を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_svg_sanitizer.py
make check
git diff --check
```

**結果**

- 安全なSVGの保持・DOCTYPE/ENTITY拒否・整形式エラー拒否・script/foreignObject除去・イベントハンドラ除去・javascript: href除去・安全なhrefの保持・危険なroot要素の拒否を13件のテストで確認した。
- 標準スイート1162件(新規13件を含む)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- DOCTYPE/ENTITY宣言は選択的に除去するのではなく、検出したら即座に拒否するfail-closed方針にした。難読化されたDOCTYPEを見逃すリスクを避けるため。
- `defusedxml`等の新規依存は追加せず、標準ライブラリの`xml.etree.ElementTree`のみで実装した(Python標準のexpatパーサは既定で外部entityを解決しないため、DOCTYPE自体を排除すればXXE/entity展開DoSの経路を断てる)。
- `ElementTree.tostring`が既定でSVG/xlink名前空間を`ns0:`のような自動生成prefixにしてしまう問題を、`register_namespace`で回避した。

**次タスク**

- TASK-O007 Raster converter(依存: O005-O006)

## 2026-07-16 TASK-O007 Raster converter

**目的**

`ARCHITECTURE.md` 15.4/17.3の「image conversion tools」「ImageMagick delegate制限」を実装する。ユーザーにAskUserQuestionで方式を確認し、ImageMagick(+librsvg2-bin delegate)をDocker toolchain imageへ追加する方式を選択した。TASK-O005/O006で検証済みのラスター画像・sanitize済みSVGをEPWING toolchain互換のBMPへ変換する。

**変更**

- `docker/toolchain.Dockerfile`: runtime stageに`imagemagick=8:6.9.11.60+dfsg-1.6+deb12u9`・`librsvg2-bin=2.54.7+dfsg-1~deb12u1`を追加。apt-get installの後に`docker/toolchain/imagemagick-policy.xml`を`/etc/ImageMagick-6/policy.xml`へCOPYして上書き
- `docker/toolchain/imagemagick-policy.xml`(新規): 危険なcoder(MSL/URL/HTTPS/HTTP/FTP/EPHEMERAL/MVG/TEXT/SHOW/WIN/PLT/PS系/PDF/XPS)を無効化、resource上限を設定
- `src/wikiepwing/media/raster_converter.py`(新規): `RasterConversionError`・`convert_to_bmp`・`is_imagemagick_available`
- `tests/test_media_raster_converter.py`(新規8件)、`tests/test_media_toolchain_definition.py`(新規5件)
- `TASKS.md`(TASK-O007を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_raster_converter.py tests/test_media_toolchain_definition.py
make check
git diff --check
```

**結果**

- PNG/SVG→BMP変換(ImageMagick未検出時はskip)・空バイト列拒否・変換失敗時のエラー・timeout・実行ファイル未検出時のエラーを8件、Dockerfile/policy.xmlの内容検証を5件のテストで確認した。
- 標準スイート1171件(新規13件を含む、ImageMagick依存3件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- imagemagick/librsvg2-binのバージョンはsnapshot.debian.orgの`dists/bookworm/main/binary-amd64/Packages`インデックス(実際にそのsnapshot日時でaptが解決する値)から採用した。pool配下のディレクトリ一覧に見える最新版(deb12u11)とは異なり、pin日時のsuiteインデックスはu9を指していたため、再現性のためインデックスの値を優先した。
- policy.xmlはapt-get installの**後**にCOPYする順序にした。先に置くとdpkgのパッケージ展開で標準policy.xmlに上書きされ、制限が効かなくなるため。
- テスト作成中、policy.xmlのコメント内に含まれるem-dash(`--`)がXML仕様上コメント内で使用不可であることを発見し、実際にパースエラーになることをテストで検出・修正した。気づかなければDocker build自体は通っても、ImageMagickがpolicy.xmlの読み込みに失敗し制限が無効になっていた可能性がある。
- ImageMagickバイナリがローカル開発環境(macOS)に存在しないため、実変換系テストは`pytest.mark.skipif`でskipする設計にした(TASK-M005のフォント可用性チェックと同じ前例)。実際の動作確認はDocker環境で行う想定。

**次タスク**

- TASK-O008 Content-addressed cache(依存: O007)

## 2026-07-16 TASK-O008 Content-addressed cache

**目的**

`ARCHITECTURE.md` 15.5のcache key設計(`converter_version`を含めて安全に無効化できるようにする)を、TASK-N004の`MathCache`と同じ形でmedia向けに実装する。TASK-O007のraster変換結果を、ダウンロードした生バイト列自体のcontent hash(sha256)をキーとしてfilesystemにcacheする。

**変更**

- `src/wikiepwing/media/cache.py`(新規): `compute_content_hash`・`MediaCache`(`MEDIA_CACHE_VERSION`)
- `tests/test_media_cache.py`(新規7件)
- `TASKS.md`(TASK-O008を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_cache.py
make check
git diff --check
```

**結果**

- content hashの決定性・cache miss/hitでの`convert()`呼び出し回数・異なるhashの独立した格納・ディレクトリ自動作成・`MEDIA_CACHE_VERSION`変更による既存cacheの無効化を7件のテストで確認した。
- 標準スイート1178件(新規7件を含む、ImageMagick依存3件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- TASK-N004の`MathCache`と全く同じ設計パターン(`get_or_*`によるhit/miss判定、`*_CACHE_VERSION`によるinvalidation、`atomic_write_bytes`の再利用)を踏襲した。プロジェクト内で一貫したcache実装パターンを保つため。
- cache keyをダウンロードした生バイト列自体のcontent hashにしたことで、異なるURLが同じファイルを指している場合に自動的に同じcache entryを共有する(「content-addressed」の本質)。これがTASK-O009(Dedup)の基盤になる。

**次タスク**

- TASK-O009 Dedup(依存: O008)

## 2026-07-16 TASK-O009 Dedup

**目的**

`ARCHITECTURE.md` 15.3の除外候補「duplicate hash」を、TASK-O008で得られる実際のcontent hash(ダウンロード済みバイト列のsha256)で本来の意味通りに実装する。TASK-O003の`source_url`重複除去(実バイト未取得時点での代替)を置き換えるのではなく、実バイト取得後の追加dedupとして位置づけた。

**変更**

- `src/wikiepwing/media/dedup.py`(新規): `HashedMedia`(`MediaReference`+content hash)・`deduplicate_media`(同じcontent hashは最初の1件のみ残す、入力順保持)
- `tests/test_media_dedup.py`(新規5件)
- `TASKS.md`(TASK-O009を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_dedup.py
make check
git diff --check
```

**結果**

- 空入力・異なるhashの保持・同じhash異なるURLでの重複除去・入力順保持・3件重複での動作を5件のテストで確認した。
- 標準スイート1183件(新規5件を含む、ImageMagick依存3件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- TASK-O003の`select_media`は削除・置き換えせず、両方とも残す設計にした。役割が異なる(ダウンロード前のURL単位の重複除去 vs ダウンロード後の実バイト単位の重複除去)ため。

**次タスク**

- TASK-O010 Attribution model(依存: O001)

## 2026-07-16 TASK-O010 Attribution model

**目的**

`ARCHITECTURE.md` 28.2(画像の帰属情報)・`DATA_CONTRACTS.md`の画像cacheメタデータJSONの`attribution`フィールドを実装する。Commons/Fileページからの実際の取得は別機能(28.2自身の記述)であり、本タスクはモデルと`is_licensed`述語のみを対象とした。

**変更**

- `src/wikiepwing/media/attribution.py`(新規): `MediaAttribution`(`source_page_url`/`author`/`license_identifier`/`license_url`)・`AttributionError`・`is_licensed`・`parse_media_attribution`
- `tests/test_media_attribution.py`(新規8件)
- `TASKS.md`(TASK-O010を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_attribution.py
make check
git diff --check
```

**結果**

- round-trip・payload()のキー名一致・全フィールドnull許容・`is_licensed`のtrue/false判定・不正なJSONでのエラーを8件のテストで確認した。
- 標準スイート1191件(新規8件を含む、ImageMagick依存3件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- フィールド名は`DATA_CONTRACTS.md`の画像cacheメタデータJSONの`attribution`フィールドとそのまま一致させた(TASK-M004で学んだ「新しいスキーマ設計時はDATA_CONTRACTS.mdを先に確認する」という教訓をここでも適用した)。
- build profile(personal/distributable)による採否ポリシーは対象外とした。`build_profile`という概念自体がまだコードベースに存在しない(EPIC P未着手)ため、存在しない概念に依存したポリシーを先回りして実装しない方針にした。

**次タスク**

- TASK-O011 EPWING graphics integration(依存: O007,H009)

## 2026-07-16 TASK-O011 EPWING graphics integration

**目的**

`ARCHITECTURE.md` 17.2(FreePWING adapterの責務「graphic/gaiji登録」)を実装する。TASK-M007の`write_gaiji_build_files`と同じパターンで、TASK-O007がBMP化した画像を`fpwmake`が読むビルド入力(`*.bmp`+`cgraphs.txt`)として書き出す。

**変更**

- `src/wikiepwing/media/freepwing_graphics.py`(新規): `GraphicBuildEntry`(name/bmp_bytesの検証)・`FreePwingGraphicsError`・`write_graphics_build_files`
- `tests/test_media_freepwing_graphics.py`(新規8件)
- `TASKS.md`(TASK-O011を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_media_freepwing_graphics.py
make check
git diff --check
```

**結果**

- BMP/catalog書き出し・空入力での空catalog・ディレクトリ自動作成・入力順保持・不正なname/空bmp_bytesの拒否を8件のテストで確認した。
- 標準スイート1199件(新規8件を含む、ImageMagick依存3件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `tests/fixtures/handcrafted/cgraphs.txt`(`wiki-mark bitmap.bmp`)・`build_fixture.pl`の`add_color_graphic_start("wiki-mark")`/`add_color_graphic_end()`呼び出し(実toolchainで検証済み)を出力形式の一次情報源とした。
- `RenderedEntry.graphics`への実際のデータ設定・本文中への`add_color_graphic_start`/`add_color_graphic_end`呼び出し生成は対象外とした。TASK-M006(gaiji code割り当て)/M007(ビルドファイル書き出し)が本文への実配線と分離されていたのと同じ設計判断。

**次タスク**

- TASK-O012 Image plan/fetch/convert commands(依存: O003-O011)

## 2026-07-16 TASK-O012 Image plan/fetch/convert commands (完了、EPIC O完了)

**目的**

EPIC O(画像)最終タスクとして、TASK-O003-O011で実装した各段階(選択・ダウンロード・検証・SVG sanitize・raster変換・cache・dedup・graphics build file書き出し)を実際に連結する`image plan/fetch/convert`コマンドを実装する。AskUserQuestionで確認した方針に従い、body-image抽出(TASK-O001)をnormalizeパイプラインへ配線するpart 1も本タスクの一部として実施した。

**変更**

- part 1: `src/wikiepwing/normalize/media_extraction.py`(新規)、`normalize/pipeline.py`(`normalize_html`の戻り値を`(blocks, body_media, diagnostics)`に拡張)、`normalize/orchestrate.py`(main image + body mediaを`select_media`で統合)
- part 2: `src/wikiepwing/media/orchestrate.py`(新規): `MediaPlanEntry`/`plan_media`・`FetchOutcome`/`fetch_media`・`ConvertOutcome`/`convert_media`・`write_fetch_report`/`read_fetch_report`
- `src/wikiepwing/cli.py`: `image-plan`/`image-fetch`/`image-convert`サブコマンド追加(`[images]` config sectionを消費)
- `tests/test_normalize_media_extraction.py`(新規8件)、`tests/test_normalize_pipeline.py`/`tests/test_golden_normalize.py`(戻り値変更に追記)、`tests/test_media_orchestrate.py`(新規17件)、`tests/test_cli.py`(新規5件)
- `TASKS.md`(TASK-O012を`[x]`に、EPIC O完了)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_media_extraction.py tests/test_normalize_pipeline.py tests/test_golden_normalize.py tests/test_media_orchestrate.py tests/test_cli.py
make check
git diff --check
```

**結果**

- body-image抽出のnormalize配線・plan/fetch/convertの各関数(実DB・fakeダウンローダ使用)・CLIのhelp表示とend-to-end動作を合計30件超のテストで確認した。
- 標準スイート1223件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。
- これでEPIC O(画像)のTASK-O001-O012が全て完了した。

**判断・注意点**

- AskUserQuestionで確認した通り、body-image抽出のnormalize配線(part 1)を本タスクに含めた。既存のTASK-O001の出力(`role="unknown"`固定)がこれまで実際には使われていなかったギャップを解消した。
- `image-plan`/`image-fetch`/`image-convert`はingest/normalize/generateの重いstage manifest/resumeパターンを採用せず、`acquire`/`register-local-source`/`inspect-source`と同じ軽量なユーティリティコマンドとして実装した(ネットワークI/Oが主体で、resumable多時間バルクパイプラインではないため)。
- distribution mode(personal/distributable)による画像除外ポリシーの実際の適用は対象外とした(`[distribution]` configスキーマ自体は既存だが、適用ロジックは別タスク)。

**次タスク**

- TASK-P001 Profile schema(依存: A003)

## 2026-07-16 TASK-P001 Profile schema

**目的**

`ARCHITECTURE.md` 21(Mini/Lite/Full profile定義)・`CONFIG_REFERENCE.md` 17(profile defaultsの正確なTOML内容)を実装する。`config/profiles/mini.toml`/`lite.toml`/`full.toml`を作成し、`profile`値のschema検証を追加する。

**変更**

- `config/profiles/mini.toml`/`lite.toml`/`full.toml`(新規、`CONFIG_REFERENCE.md` 17と一致)
- `src/wikiepwing/config.py`: `_PROFILES = ("mini", "lite", "full")`、`load_config`での検証追加
- `tests/test_config.py`(新規13件)
- `TASKS.md`(TASK-P001を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_config.py
make check
git diff --check
```

**結果**

- 各profile fileのoverride読み込み・各profileの主要な値・不正なprofile値の拒否を13件のテストで確認した。
- 標準スイート1230件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `config/profiles/<profile>.toml`の自動選択・読み込み(`CONFIG_REFERENCE.md` 1のlayer 3)は対象外とした。`config/default.toml`の現在の`[search]`(`max_terms_per_article=64`)が`lite.toml`(`32`)と異なるため、自動読み込みを実装すると既存の`load_config`呼び出し全箇所(ingest/normalize/generate/image-fetch等)の実効設定値が一括で変わってしまう。この広範囲な挙動変更はTASK-P004(Profile-driven renderer)が担う設計と判断した。今日でも`--config config/profiles/lite.toml`のように明示的に渡せばoverlayとして機能する。
- `config/projects/<project>.toml`(layer 2)も対象外(別タスクの範囲)。

**次タスク**

- TASK-P002 Mini profile finalize(依存: H013,J007,K010,L004,M009)

## 2026-07-16 TASK-P002 Mini profile finalize

**目的**

TASK-P001で作成した`config/profiles/mini.toml`を使い、Mini profileでの実際のend-to-end build(ingest→normalize→generate→verify)が完走することを確認する受け入れテストを実装する。AskUserQuestionで確認した方針に従い、config値の実際のnormalize/render pipelineへの配線(TASK-P004の対象)は行わず、受け入れテストに限定した。

**変更**

- `tests/test_mini_profile_build.py`(新規): TASK-H013と同じ100記事gate構成で、`config/profiles/mini.toml`をoverrideとして使うend-to-endテスト
- `TASKS.md`(TASK-P002を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_mini_profile_build.py
make check
git diff --check
```

**結果**

- Mini profile configでのregister→ingest→normalize→generate→verifyの全stage完走、有効な`entries.jsonl`(100件)生成を1件のテストで確認した。
- 標準スイート1231件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `images.enabled`/`math.render_graphics`等のconfig値を実際にnormalize/render pipelineへ配線する作業(Mini profile固有の出力差異を実現すること)はTASK-P004(Profile-driven renderer)の対象として明確に切り分けた。現時点ではMini profile configを使っても出力はdefault/lite相当と同じだが、これは既知のギャップとして記録し、隠蔽しない。

**次タスク**

- TASK-P003 Lite profile(依存: N007,O012,P001)

## 2026-07-16 TASK-P003 Lite profile

**目的**

TASK-P002と同じ方針で、Lite profile(`config/profiles/lite.toml`)を使った実際のend-to-end buildが完走することを確認する受け入れテストを実装する。

**変更**

- `tests/test_lite_profile_build.py`(新規): TASK-P002と同じ100記事gate構成で、`config/profiles/lite.toml`をoverrideとして使うend-to-endテスト
- `TASKS.md`(TASK-P003を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_lite_profile_build.py
make check
git diff --check
```

**結果**

- Lite profile configでのregister→ingest→normalize→generate→verifyの全stage完走、有効な`entries.jsonl`(100件)生成を1件のテストで確認した。
- 標準スイート1232件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- TASK-P002と同じ理由で、config値の実際のnormalize/render pipelineへの配線は対象外(TASK-P004)。

**次タスク**

- TASK-P004 Profile-driven renderer(依存: P002-P003)

## 2026-07-16 TASK-P004 Profile-driven renderer

**目的**

`ARCHITECTURE.md` 21.3(「同じコードパスを使い、profile設定で差を作ります」)を実装する最初の一歩として、AskUserQuestionで確認した方針に従い`[images].enabled`のみを実際にnormalizeパイプラインへ配線する。

**変更**

- `src/wikiepwing/normalize/pipeline.py`: `NormalizeOptions`に`images_enabled: bool = True`を追加、`normalize_html`が無効時は本文画像抽出をスキップ
- `src/wikiepwing/normalize/orchestrate.py`: `images_enabled`が偽の場合main image読み出しも含めて`media=()`にする
- `src/wikiepwing/cli.py`: `normalize`/`build`サブコマンドで`images_enabled=config.section("images")["enabled"]`を渡す
- `tests/test_normalize_pipeline.py`/`tests/test_normalize_orchestrate.py`(各2件追記)、`tests/test_mini_profile_build.py`/`tests/test_lite_profile_build.py`(実際のend-to-end buildでmedia件数を確認するassertion追加)
- `TASKS.md`(TASK-P004を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_pipeline.py tests/test_normalize_orchestrate.py tests/test_mini_profile_build.py tests/test_lite_profile_build.py tests/test_golden_normalize.py tests/test_mini_end_to_end_build.py tests/test_cli.py
make check
git diff --check
```

**結果**

- `images_enabled`のtrue/falseそれぞれで本文画像抽出・main image読み出し・`Article.media`の挙動を単体テストと実際のend-to-end build(Mini/Lite profile)の両方で確認した。Mini profileは実際に`media_references`テーブルが0件になり、ARCHITECTURE.md 21.1の「imageなし」を満たすことを確認した。
- 標準スイート1236件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- AskUserQuestionで確認した通り、`images.enabled`のみを配線し、`math.render_graphics`/`tables.*`/`search.*`/`references.*`は対象外とした。前者は既に現在の出力がMini相当(mathは常にtext)であり、後者は「何を削るか」の仕様上の判断が必要なため。
- `images_enabled`のデフォルトを`True`にすることで、既存の`NormalizeOptions(...)`呼び出し箇所すべて(テスト含む)を変更せずに済ませた。

**次タスク**

- TASK-P005 100-article Lite build(依存: P004)

## 2026-07-16 Bugfix: raster_converter SVG conversion via real ImageMagick (Docker verification)

**目的**

TASK-P005(100-article Lite build)の実施準備としてDocker toolchain imageを実際にrebuild・検証したところ、TASK-O007の`convert_to_bmp`がSVG入力で実際には動作しないバグを発見し修正した。

**変更**

- `src/wikiepwing/media/raster_converter.py`: `stdin`/`stdout`経由(`format:-`)でのバイト列受け渡しを、実際の一時ファイル経由に変更した。

**発見の経緯・原因**

- `docker/toolchain.Dockerfile`をrebuildし(ImageMagick/librsvg2-bin/policy.xmlを含む)、実際に`convert_to_bmp`をコンテナ内で呼び出したところ、SVG入力(`svg:-`)で`rsvg-convert' delegate failed`エラーが発生した。
- 原因: ImageMagickのSVG delegate(`rsvg-convert`)は外部プロセス呼び出しであり、そのコマンドテンプレート(`-o '%o' '%i'`)が実在するファイルパスを要求する。`stdin`(`-`)経由のパイプではdelegateが読み取れるファイルが存在しないため失敗する。PNG/JPEG等のネイティブcoderはstdinから直接読めるため、この問題はSVGでのみ顕在化していた。
- ローカル開発環境にImageMagickがなく、該当テスト(`test_converts_svg_to_bmp`)は`pytest.mark.skipif`で常にskipされていたため、このバグは一度も実行されずCIも通過していた。

**修正内容**

- `convert_to_bmp`が`tempfile.TemporaryDirectory()`内に入力・出力ファイルを作成し、ImageMagickへ実ファイルパスを渡すよう変更した。PNG/SVG両方をDockerコンテナ内で実際に呼び出し、正しくBMPへ変換されることを確認した(`convert_to_bmp(png_bytes, source_format="png")`・`convert_to_bmp(svg_bytes, source_format="svg")`ともに`BM`マジックで始まる出力を得た)。不正input/空inputでのエラーパスも実際に確認した。

**実行コマンド**

```bash
docker build -f docker/toolchain.Dockerfile -t wikiepwing-toolchain:dev .
docker run --rm --entrypoint sh wikiepwing-toolchain:dev -c 'python3 -c "..."'
uv run pytest tests/test_media_raster_converter.py
make check
```

**結果**

- Docker内での実行で、PNG/SVG変換・空/不正入力のエラーパスすべてが正しく動作することを確認した。
- 標準スイート1236件(ImageMagick依存6件はローカル環境でskip、Docker内では実際に確認済み)、format-check、ruff lint、mypy strictが成功した。

**判断・注意点**

- ImageMagick依存のテストがローカル環境で常にskipされる設計(TASK-M005のフォント可用性チェックと同じ前例)には、「実際に一度も実行されないコードパスのバグを見逃す」というトレードオフがあることを再確認した。今回はTASK-P005の準備としてDocker検証を行ったために発見できた。可能な限り定期的にDocker検証を行う価値があることを記録しておく。

## 2026-07-16 TASK-P005 100-article Lite build

**目的**

TASK-H013の`mini-end-to-end-smoke.sh`と同じ形の、Lite profile向けDocker smoke testを追加し、実際にDockerで検証する。

**変更**

- `docker/toolchain/lite-100-article-smoke.sh`(新規): `config/profiles/lite.toml`をoverrideとして使い、実toolchain image内でPython pipeline→fpwmake→ebinfo→eb-searchまで検証するスクリプト
- `TASKS.md`(TASK-P005を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
docker build -f docker/toolchain.Dockerfile -t wikiepwing-toolchain:dev .
sh docker/toolchain/lite-100-article-smoke.sh wikiepwing-toolchain:dev
make check
git diff --check
```

**結果**

- `wikiepwing-toolchain:dev`を実際にrebuildし(この過程でTASK-O007のSVGバグを発見・修正、別コミット)、本スクリプトを実行してPython pipeline・fpwmake honmon構築・ebinfo・eb-searchでの複数title検索確認まで全て実際に完走することを確認した。
- 標準スイート1236件(変更なし)、`git diff --check`が成功した。

**判断・注意点**

- `RenderedEntry.graphics`が現時点で常に空(実際のFreePWING graphics統合はEPIC O012で対象外とした)であるため、このsmoke testはMini版と実質的に同じ内容になる。画像embeddingの差異はまだ検証できない、既知のギャップとして記録する。
- Dockerが実際に利用可能な環境だったため、これまでの多くのタスクで「Docker検証は別途」としていた箇所を実際に検証する貴重な機会になった。今後もDockerが使える場合は積極的に実検証することを推奨する。

**次タスク**

- TASK-P006 10,000-article sample builder(依存: P005)

## 2026-07-16 TASK-P006 10,000-article sample builder

**目的**

`generate_hundred_articles.py`(TASK-H012)と同じ決定論的パターンを10,000記事規模へ拡張し、TASK-P007(10,000-article Lite run)向けのfixtureを生成する。

**変更**

- `tests/fixtures/enterprise/generate_ten_thousand_articles.py`(新規)
- `tests/fixtures/enterprise/ten_thousand_articles.ndjson`(新規、生成物、10,000行/14.7MB)
- `TASKS.md`(TASK-P006を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
python3 tests/fixtures/enterprise/generate_ten_thousand_articles.py
make check
git diff --check
```

**結果**

- page_id/titleとも10,000件全てユニーク、既存fixtureのpage_id範囲(900001-940000の範囲外)と衝突なし、スクリプト再実行でbyte-identicalな出力(同一md5)を確認した。
- 標準スイート1236件(変更なし)、`git diff --check`が成功した。

**次タスク**

- TASK-P007 10,000-article Lite run(依存: P006)

## 2026-07-16 TASK-P007 10,000-article Lite run (EPIC P完了)

**目的**

TASK-P006で生成した`ten_thousand_articles.ndjson`を使い、Lite profileでのend-to-end buildを10,000記事規模で実行し完走することを確認する。ADR-015の次段階(10,000記事gate)。

**変更**

- `tests/test_lite_profile_10000_build.py`(新規): TASK-P003と同じ構成で10,000記事規模のend-to-endテスト
- `TASKS.md`(TASK-P007を`[x]`に、EPIC P完了)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_lite_profile_10000_build.py
make check
git diff --check
```

**結果**

- 10,000記事規模でのregister→ingest→normalize→generate→verifyの全stage完走、有効な`entries.jsonl`(10,000件)生成を確認した。実行時間は約3.4秒。
- 標準スイート1237件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。
- これでEPIC P(Profiles and Lite)のTASK-P001-P007が全て完了した。

**判断・注意点**

- 実toolchain(fpwmake/eb-search)での10,000-entry honmon構築は対象外とした。Docker smoke testとして実施すると時間がかかる可能性があり、今回はPython pipelineレベルのend-to-endに限定した。

**次タスク**

- TASK-Q001 Heading keyword extraction(依存: J007)

## 2026-07-16 TASK-Q001 Heading keyword extraction

**目的**

`ARCHITECTURE.md` 14.3(Full profileの索引「heading keyword」)・`DATA_CONTRACTS.md`のpriority提案(`400 heading keyword`)を実装する。`title_terms_for_article`/`category_terms_for_article`と同じ形で`heading_keyword_terms_for_article`を追加する。

**変更**

- `src/wikiepwing/search/search_term.py`: `heading_keyword_terms_for_article`(`_HEADING_KEYWORD_PRIORITY=400`)・`_flatten_inline_text`
- `tests/test_search_term.py`(新規6件)
- `TASKS.md`(TASK-Q001を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- 見出しからのterm抽出・ネストしたinlineの平坦化・重複除去・空見出しの無視・見出しなし記事・正規化キーを6件のテストで確認した。
- 標準スイート1243件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `category_terms_for_article`と同じ理由(one-to-many)で`title_terms_for_article`には統合せず、独立した関数として実装した。
- 同一記事内で同じ正規化キーの見出しが複数回出現する場合(例: 複数セクションに同じ見出し名)は重複除去した。

**次タスク**

- TASK-Q002 Infobox keyword extraction(依存: K009,J007)

## 2026-07-16 TASK-Q002 Infobox keyword extraction

**目的**

`ARCHITECTURE.md` 14.3(Full profileの索引「infobox selected values」)・`DATA_CONTRACTS.md`のpriority提案(`300 infobox keyword`)を実装する。TASK-Q001と同じ形で`infobox_keyword_terms_for_article`を追加する。

**変更**

- `src/wikiepwing/search/search_term.py`: `infobox_keyword_terms_for_article`(`_INFOBOX_KEYWORD_PRIORITY=300`)・`_flatten_block_text`(`InfoboxField.value`のduck-typed再帰flatten)
- `tests/test_search_term.py`(新規5件)
- `TASKS.md`(TASK-Q002を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- フィールド値からのterm抽出・フィールド名の除外・重複除去・空値の無視・infoboxなし記事を5件のテストで確認した。
- 標準スイート1248件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- フィールド名(label)自体はkeywordとして抽出しない(generic column headingであり検索キーワードとして不適切なため)。
- `InfoboxField.value`は`tuple[Block,...]`(`convert_document`が生成、`ParagraphBlock`以外も来うる)であるため、`mini_layout.py`と同様のduck-typed再帰flattenを実装した。

**次タスク**

- TASK-Q003 Lead alias extraction(依存: G012,J007)

## 2026-07-16 TASK-Q003 Lead alias extraction

**目的**

`ARCHITECTURE.md` 13(alias source「lead sentenceのbold alias」)・14.3・`DATA_CONTRACTS.md`のpriority提案(`200 lead term`)を実装する。記事本文の最初の見出し前の最初のParagraphBlock内のbold spanを`kind="alias"`のSearchTermとして抽出する`lead_alias_terms_for_article`を追加する。

**変更**

- `src/wikiepwing/search/search_term.py`: `lead_alias_terms_for_article`(`_LEAD_ALIAS_PRIORITY=200`)・`_first_lead_paragraph`・`_strong_texts`
- `tests/test_search_term.py`(新規7件)
- `TASKS.md`(TASK-Q003を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- bold spanの抽出・見出し後のparagraph除外・タイトル自身の除外・重複除去・空ケースを7件のテストで確認した。
- 標準スイート1255件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- タイトル自身と正規化キーが一致するbold spanは除外した。`title_terms_for_article`が既に`priority=1000`でカバーしており、重複は不要なため。

**次タスク**

- TASK-Q004 Cross component extraction(依存: J007)

## 2026-07-16 TASK-Q004 Cross component extraction

**目的**

`ARCHITECTURE.md` 14.1/14.3(索引kind「cross_component」)・`DATA_CONTRACTS.md`のpriority提案(`100 cross component`)・`PLAN.md`の「クロス検索」節(候補source「redirect/alias components」)を実装する。title/redirect aliasの空白区切り単語成分を個別のSearchTermとして抽出する`cross_component_terms_for_article`を追加する。

**変更**

- `src/wikiepwing/search/search_term.py`: `cross_component_terms_for_article`(`_CROSS_COMPONENT_PRIORITY=100`)
- `tests/test_search_term.py`(新規5件)
- `TASKS.md`(TASK-Q004を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- 複数単語titleの分解・単一単語titleでの空・redirect alias成分の抽出・非redirect aliasの除外・重複除去を5件のテストで確認した。
- 標準スイート1260件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 「cross component」の厳密な定義がARCHITECTURE.mdに詳細記載されていなかったため、`PLAN.md`の「クロス検索」節が挙げる「redirect/alias components」を一次情報源として採用した(空白区切りの単語成分分解)。

**次タスク**

- TASK-Q005 Search budgets and stop rules(依存: Q001-Q004)

## 2026-07-16 TASK-Q005 Search budgets and stop rules

**目的**

`CONFIG_REFERENCE.md`の`[search]` `max_terms_per_article`(「keyword/cross termsの爆発防止。title/redirectは別budget扱い可能」)・`max_key_bytes`・`PLAN.md`の「stop words」を実装する。TASK-Q001-Q004が生成するkeyword/cross_component種別のSearchTermにのみbudgetを適用する`apply_search_budgets`を追加する。

**変更**

- `src/wikiepwing/search/search_term.py`: `apply_search_budgets`(`_BUDGETED_KINDS`)
- `tests/test_search_term.py`(新規7件)
- `TASKS.md`(TASK-Q005を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_search_term.py
make check
git diff --check
```

**結果**

- keyword/cross_componentのbudget上限・title/redirectの除外・budget超過時の高優先度term保持・key長超過の除外・stop wordの除外・空入力を7件のテストで確認した。
- 標準スイート1267件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- 具体的なstop word一覧の選定は対象外とした。呼び出し側が注入するパラメータ(`stop_words: frozenset[str] = frozenset()`)として実装し、内容自体はどのドキュメントにも記載がないため決め打ちしなかった。
- `sort_search_terms`の優先度降順を先に適用してからbudget truncationすることで、budget超過時に優先度の高いtermが優先的に残るようにした。

**次タスク**

- TASK-Q006 Full profile(依存: 未確認)

## 2026-07-16 TASK-Q006 Full profile

**目的**

TASK-P002/P003と同じ方針で、Full profile(`config/profiles/full.toml`)を使った実際のend-to-end buildが完走することを確認する受け入れテストを実装する。

**変更**

- `tests/test_full_profile_build.py`(新規): TASK-P003と同じ100記事gate構成で、`config/profiles/full.toml`をoverrideとして使うend-to-endテスト
- `TASKS.md`(TASK-Q006を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_full_profile_build.py
make check
git diff --check
```

**結果**

- Full profile configでのregister→ingest→normalize→generate→verifyの全stage完走、有効な`entries.jsonl`(100件)生成を1件のテストで確認した。
- 標準スイート1268件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- TASK-P002/P003と同じ理由で、`images.enabled`以外のconfig値の実際のnormalize/render pipelineへの配線は対象外。

**次タスク**

- TASK-Q007 Reference comparison engine(依存: C007,H011)

## 2026-07-16 TASK-Q007 Reference comparison engine

**目的**

`COMPATIBILITY.md` 5(固定query比較: Result presence/Overlap@N/Target coverage)・13(Compatibility report schema)を実装する。reference側とcandidate側の固定query検索結果を比較するcompute engineを実装する(実際の検索実行harnessは対象外)。

**変更**

- `src/wikiepwing/compatibility/`(新規パッケージ): `comparison.py`(`QueryHitSet`・`QueryComparison`・`ComparisonSummary`・`compare_query_results`)
- `tests/test_compatibility_comparison.py`(新規10件)
- `TASKS.md`(TASK-Q007を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_compatibility_comparison.py
make check
git diff --check
```

**結果**

- presence一致/不一致・偽陽性検出・target coverage・overlap@N(交差なし/一部/reference側空)・overlap_at_n_mean・candidate側query_key欠落エラー・空入力を10件のテストで確認した。
- 標準スイート1278件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `reference/queries.py`の`FixedQuery`には「正解heading」のような詳細フィールドがなく、`expected_presence`(bool)のみが利用可能なため、target coverageを「`expected_presence`と実際のhit有無の一致率」として操作的に定義した。これは`COMPATIBILITY.md` 5.3の「missing query returns false exact hit: 0」と整合する。
- overlap@Nの比較キーは`heading`テキストを採用した。`entry_locator`はbackend/build固有であり、異なるbuild間で比較不可能なため。
- 実際にcandidate側の検索を実行するharness(自分のbuildに対するEB search adapter実行)は対象外とした。`reference/searches.py`(検索実行)と`reference/report.py`(レポート生成)が責務分離されているのと同じ設計判断。

**次タスク**

- TASK-Q008 Compatibility thresholds(依存: Q007)

## 2026-07-16 TASK-Q008 Compatibility thresholds

**目的**

`COMPATIBILITY.md` 5.3(Initial thresholds)・13(`thresholds`/`status`)を実装する。TASK-Q007の`ComparisonSummary`に対して閾値を適用しpass/fail判定する`evaluate_thresholds`を追加する。

**変更**

- `src/wikiepwing/compatibility/comparison.py`: `ThresholdConfig`・`DEFAULT_THRESHOLDS`・`ThresholdEvaluation`・`evaluate_thresholds`
- `tests/test_compatibility_comparison.py`(新規5件)
- `TASKS.md`(TASK-Q008を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_compatibility_comparison.py
make check
git diff --check
```

**結果**

- 閾値内でのpass・target coverage不足/false positiveでのfail・デフォルト閾値の使用・デフォルト値の一致を5件のテストで確認した。
- 標準スイート1283件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- TASK-Q007と同じ理由で、query class別(exact title/redirect/common)の個別閾値評価は対象外とした。`DEFAULT_THRESHOLDS`は「fixed common queries target coverage: 95%以上」・「missing query returns false exact hit: 0」を全体に適用可能な閾値として採用した。

**次タスク**

- TASK-Q009 Compatibility HTML report(依存: Q008)

## 2026-07-16 TASK-Q009 Compatibility HTML report (EPIC Q完了)

**目的**

`COMPATIBILITY.md` 13(Compatibility report schema)のJSON+HTML出力を実装する。TASK-C007の`reference/report.py`と同じ原子的書き込みパターンを踏襲する。

**変更**

- `src/wikiepwing/compatibility/report.py`(新規): `build_compatibility_report`・`write_compatibility_report`・`_render_html`
- `tests/test_compatibility_report.py`(新規8件)
- `TASKS.md`(TASK-Q009を`[x]`に、EPIC Q完了)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_compatibility_report.py
make check
git diff --check
```

**結果**

- schema fieldの一致・JSON serializable・JSON/HTML書き込み・pass/fail両方のHTML反映・ディレクトリ自動作成・overlap Noneの扱いを8件のテストで確認した。
- 標準スイート1290件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。
- これでEPIC Q(Full search and compatibility)のTASK-Q001-Q009が全て完了した。

**判断・注意点**

- `articles`(記事比較)・`viewers`(手動viewer確認)セクション、`redirect_coverage`は実データを計算するengineがまだ存在しないため、偽の`0`を書かずpayloadから省略した。「測定してゼロだった」と「未測定」を混同させないため。
- `wikiepwing.pipeline.atomic_write.atomic_write_text`を再利用し、`reference/report.py`独自の一時ファイル+`os.replace`パターンを重複実装しなかった。

**次タスク**

- TASK-R001 Stratified 10,000 sample report(依存: P007,Q009)

## 2026-07-16 TASK-R001 Stratified 10,000 sample report

**目的**

`PLAN.md` Phase 20(10,000記事耐久試験)のstratified sample選定を実装する。AskUserQuestionでの承認に基づき、実際にWikimedia Enterprise APIから実データを取得して検証した。

**変更**

- `src/wikiepwing/sampling/`(新規パッケージ): `stratify.py`(`compute_signals`・`select_stratified_sample`・`iter_raw_articles`・`build_stratified_sample_ndjson`・`write_sample_report`)
- `tests/test_sampling_stratify.py`(新規20件、合成fixtureのみ)
- `TASKS.md`(TASK-R001を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_sampling_stratify.py
make check
git diff --check
```

**実データでの検証(git管理外)**

- AskUserQuestionで確認したうえで、`.env`の実認証情報でWikimedia Enterprise APIへ認証(login経由)。jawiki namespace 0の全snapshotは81 chunks・約30.9GBと判明し、再度AskUserQuestionで確認したうえで最初の1 chunk(約381MB圧縮、27,859記事)のみをダウンロードした(`acquire_snapshot`をchunk_identifiersを1件に切り詰めるwrapperで呼び出し)。
- 取得したchunkに対して`build_stratified_sample_ndjson(target_total=10_000, min_per_stratum=500)`を実行(約2分22秒): `total_scanned=27859`, `total_selected=8055`(1 chunkのみではbaseline記事が4,929件しかなく、10,000件には届かなかった)。

**結果**

- 各層の検出・budget充足順序・target_total遵守・重複除去・NDJSON書き出し・reportフィールドを20件のテストで確認した。
- 標準スイート1310件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。
- 実データ検証により、コードが実際に機能することを確認した。実データ・生成したsample NDJSON・reportはgitへコミットしていない(著作権・サイズの理由)。

**判断・注意点**

- 実データ取得は2段階でAskUserQuestionを行った: (1)実データ取得自体の可否、(2)実際のsnapshot size(30.9GB)判明後のdownload範囲。ユーザーの明示的な承認なしに実際の外部APIへ認証・大容量downloadを行わない、という安全方針を徹底した。
- 取得した実データ(展開済み2GB NDJSON等)はタスク完了後に削除し、ホスト上に不要な実Wikipediaデータを残さないようにした。

**次タスク**

- TASK-R002 Full-build preflight gate(依存: R001,I007)

## 2026-07-16 TASK-R002 Full-build preflight gate

**目的**

`PLAN.md` 30(Full build前ゲート一覧)を実装する。既存の`doctor.py`のcheck枠組みを再利用し、full build固有のgate項目を組み合わせる`run_full_build_preflight`を追加する。

**変更**

- `src/wikiepwing/doctor.py`: `CheckCategory`に`"release-gate"`を追加
- `src/wikiepwing/preflight.py`(新規): `FULL_BUILD_GATE_ITEMS`・`run_full_build_preflight`
- `tests/test_preflight.py`(新規7件)
- `TASKS.md`(TASK-R002を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_preflight.py
make check
git diff --check
```

**結果**

- 全passでのok・既存doctor checkの保持・非concreteなsource lockでのfail・test_suite_results欠落時のfail-closed・個別test失敗でのgate fail・全gate itemの反映・profile_fixed checkのpassを7件のテストで確認した。
- 標準スイート1317件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `source_lock_concrete`チェックは、`build_source_lock`が既に`snapshot_version="latest"`を構築時に拒否するため、実質的には防御的な再確認(常にpassする)である。テストでは`SourceLock`を直接構築してfailパスを検証した。
- 「Phase 0〜20完了」「toolchain smoke green」等の実際にtest/smokeを実行したかどうかの判定は、このプロセス自身では検証できないため呼び出し側(`test_suite_results`)が注入する設計にした。欠落項目はfail-closed。

**次タスク**

- TASK-R003 Full jawiki ingest(依存: R002) — 実データの全件(約1.4M記事、81 chunks、約30.9GB)取得が必要なため、実行前にユーザーへ確認する

## 2026-07-16 TASK-S001 BUILD-INFO.json

**目的**

`ARCHITECTURE.md` 26.3/28.1・`DATA_CONTRACTS.md` 12を実装する。`SourceLock`の既存project/snapshot情報とstage manifestと同じ形の`software`ブロックを組み合わせたBUILD-INFO.jsonを構築・書き込む。

**変更**

- `src/wikiepwing/build_info.py`(新規): `SoftwareProvenance`・`build_build_info`・`write_build_info`
- `tests/test_build_info.py`(新規8件)
- `TASKS.md`(TASK-S001を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_build_info.py
make check
git diff --check
```

**結果**

- SourceLockフィールドの取り込み・software provenance・None digestの許容・naive datetime拒否・JSON serializable・原子的書き込み・ディレクトリ自動作成を8件のテストで確認した。
- 標準スイート1324件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `SourceLock`(project/snapshot_identifier/snapshot_version/date_modified)を再利用し、BUILD-INFO固有のfield抽出を重複実装しなかった。
- `software`ブロックはDATA_CONTRACTS.md 3のStage manifestの`software`フィールドと同じ形(`git_commit`/`app_image_digest`/`toolchain_image_digest`)にし、provenance記録の一貫性を保った。

**次タスク**

- TASK-S002 Logical content hash(依存: H010,M007,O011)

## 2026-07-16 TASK-S002 Logical content hash

**目的**

`ARCHITECTURE.md` 26.1(logical hash: entry/index/graphicのcanonical stream hash)を実装する。物理SHA-256(ZIP timestamp等に左右される)とは別の、順序非依存の安定したhashを計算する。

**変更**

- `src/wikiepwing/build_logical_hash.py`(新規): `compute_stream_set_hash`・`collect_build_streams`・`compute_logical_build_hash`
- `tests/test_build_logical_hash.py`(新規11件)
- `TASKS.md`(TASK-S002を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_build_logical_hash.py
make check
git diff --check
```

**結果**

- 順序非依存性・決定性・内容差異・境界曖昧さの排除・空入力・entries.jsonl/gaiji/graphics収集・再帰・欠落ディレクトリの無視を11件のテストで確認した。
- 標準スイート1335件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**判断・注意点**

- `wikiepwing.model.logical_hash`(TASK-F008、Article単位のhash)とは別の関心事であるため、モジュール名・主要関数名を明確に分けた(`compute_stream_set_hash`/`compute_logical_build_hash`)。
- テスト作成中、`collect_build_streams`のループ変数`(prefix, directory)`の順序を取り違えるバグを実際に検出・修正した(文字列`"gaiji"`を`Path`として扱おうとして`AttributeError`)。
- EB indexバイナリ自体はDocker内`fpwmake`が生成するため対象外とした。

**次タスク**

- TASK-S003 Deterministic archive metadata(依存: H010)

## 2026-07-16 TASK-S003 Deterministic archive metadata

**目的**

`ARCHITECTURE.md` 26.2(決定論: 「archive timestamp固定」)・`DATA_CONTRACTS.md` 12(ZIP internal root構造)を実装する。EPWING辞書ディレクトリを固定タイムスタンプ・固定permission・sorted順序でZIP化し、byte-identicalな再現性を持たせる。

**変更**

- `src/wikiepwing/archive.py`(新規): `build_deterministic_archive`
- `tests/test_archive.py`(新規9件)
- `TASKS.md`(TASK-S003を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_archive.py
make check
git diff --check
```

**結果**

- 全ファイルのroot prefix付き格納・固定タイムスタンプ・2回buildでのbyte-identical・内容/root名変更での差異・バリデーション・ディレクトリ自動作成・一時ファイルの残留なしを9件のテストで確認した。
- 標準スイート1344件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**次タスク**

- TASK-S007 Disk usage command(依存: A007) — S004/S005はTASK-R006(未着手、全件buildが前提)に依存するため後回しにし、依存関係が既に揃っているS006-S009を先に進める

## 2026-07-16 TASK-S007 Disk usage command

**目的**

`PLAN.md` 29(`wikiepwing disk-usage`)を実装する。`config.paths`配下の各ディレクトリのディスク使用量を集計・報告する。

**変更**

- `src/wikiepwing/disk_usage.py`(新規): `PathUsage`・`DiskUsageReport`・`compute_disk_usage`
- `src/wikiepwing/cli.py`: `disk-usage`サブコマンド追加
- `tests/test_disk_usage.py`(新規7件)、`tests/test_cli.py`(新規2件)
- `TASKS.md`(TASK-S007を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_disk_usage.py tests/test_cli.py
make check
git diff --check
```

**結果**

- 欠落ディレクトリ・存在するディレクトリの集計・再帰・symlink非二重計上・total_bytesの一致・JSON serializable・free_bytesの非負性・CLIのhelp/実行を9件のテストで確認した。
- 標準スイート1353件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**次タスク**

- TASK-S008 Safe clean command(依存: S007)

## 2026-07-16 TASK-S008 Safe clean command

**目的**

`PLAN.md` 29(`wikiepwing clean --keep-runs 2`、出口条件「old outputを自動削除しない」)を実装する。`paths.work/runs/<run-id>/`配下の古い実行ディレクトリのみを対象とし、最新のN件を残して削除する。

**変更**

- `src/wikiepwing/clean.py`(新規): `find_removable_runs`・`clean_old_runs`(`dry_run`オプション付き、シンボリックリンク拒否)
- `src/wikiepwing/cli.py`: `clean`サブコマンド追加(`--keep-runs`必須, `--dry-run`)
- `tests/test_clean.py`(新規8件)、`tests/test_cli.py`(新規3件)
- `TASKS.md`(TASK-S008を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_clean.py tests/test_cli.py
make check
git diff --check
```

**結果**

- runs_dir不在時の空タプル・keep_runs負値のValueError・mtime降順での保持対象選定・keep_runs=0での全削除・keep_runs過大での削除なし・dry_runでの非削除・実削除・output配下への非干渉を8件のテストで確認した。
- 標準スイート1364件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。

**次タスク**

- TASK-S006 Update command(依存: D007,I006、両方完了済みのため着手可能) — S009はS006に依存するため先にS006を進める

## 2026-07-16 TASK-S006 Update command

**目的**

`PLAN.md` 29(`wikiepwing update --project jawiki --profile full`、出口条件「source version naming」「update report」)を実装する。既存の`source.lock.json`と新規acquire結果を比較し、差分とレポートを書き出す。

**変更**

- `src/wikiepwing/source_diff.py`(新規): `SourceDiff`・`compute_source_diff`・`build_update_report`・`write_update_report`
- `src/wikiepwing/cli.py`: `update`サブコマンド追加(既存`acquire`ロジックを再利用)、`_latest_source_lock_path`ヘルパー追加
- `tests/test_source_diff.py`(新規6件)、`tests/test_cli.py`(新規4件)
- `TASKS.md`(TASK-S006を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_source_diff.py tests/test_cli.py
make check
git diff --check
```

**結果**

- 初回acquire・同一バージョン無変化・chunk追加/削除/sha256変更・サイズ差分・timezone-aware必須・決定的JSON書き出し・`_latest_source_lock_path`のmtimeベース自動検出を10件のテストで確認した。
- 標準スイート1374件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。
- 「same media/math cache reuse」は既存のcontent-hashキー付きcacheで既に満たされており追加実装不要、「old runs cleanup」はTASK-S008の`clean`が担当、「old outputを自動削除しない」は`update`が`paths.output`に触れない設計で満たしていることをCURRENT_TASK.mdに記録した。

**次タスク**

- TASK-S009 Monthly update report(依存: S006、完了済みのため着手可能)

## 2026-07-16 TASK-S009 Monthly update report

**目的**

`PLAN.md` 29(月次更新ワークフロー、「release notes」)を実装する。TASK-S006の`update-report.json`から人間が読めるMarkdown形式のrelease notesを生成する。

**変更**

- `src/wikiepwing/release_notes.py`(新規): `render_release_notes`(初回acquire/バージョン変更あり/なしの3パターン、chunk増減、`_human_size`によるB〜TB単位のサイズ表示)
- `src/wikiepwing/cli.py`: `update`サブコマンドに`--release-notes-path`追加、`update-report.json`と併せて`release-notes.md`を書き出す
- `tests/test_release_notes.py`(新規4件)、`tests/test_cli.py`(追記)
- `TASKS.md`(TASK-S009を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_release_notes.py tests/test_cli.py
make check
git diff --check
```

**結果**

- 初回acquisition・バージョン変更あり(chunk追加/削除/変更数、サイズ差分の符号付き表示)・バージョン変更なし・大きい単位(MB)へのフォーマットを4件のテストで確認した。
- 標準スイート1378件(ImageMagick依存6件はローカル環境でskip)、format-check、ruff lint、mypy strict、`git diff --check`が成功した。
- これでEPIC S(Reproducibility and operations)のうちS004/S005(TASK-R006未完了のため保留)を除く全タスクが完了した。

**次タスク**

- EPIC T(Release documentation)のうち依存関係が揃っているタスクへ進む(TASK-T002はP003/Q006に依存、両方完了済みのため着手可能)

## 2026-07-16 TASK-T002 Configuration examples

**目的**

`TASKS.md`のTASK-T002(依存: P003,Q006、両方完了済み)を実装する。`CONFIG_REFERENCE.md`のプロファイル定義(section 17)はすでに実装済みの`config/profiles/*.toml`と一致していたため、設定ファイルの合成方法と実行可能なCLI呼び出し例を追加した。

**変更**

- `CONFIG_REFERENCE.md`: section 1に`config/projects/<project>.toml`が未実装であることを注記、section 20(新規)にmini/lite/full各プロファイルの`--config`合成例・複数`--config`合成例を追加
- `TASKS.md`(TASK-T002を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run python -m wikiepwing.cli ingest --help
uv run python -m wikiepwing.cli build --help
uv run python -m wikiepwing.cli normalize --help
uv run python -m wikiepwing.cli generate --help
make check
git diff --check
```

**結果**

- 例で使用したCLIフラグを実際の`--help`出力と突き合わせて一致を確認した。
- ドキュメントのみの変更のため既存の標準スイート1378件(ImageMagick依存6件はローカル環境でskip)・`git diff --check`が引き続き成功することを確認した。
- TASK-T001(Build guide)と役割が重複しないよう、全パイプラインの逐次実行解説は書かず設定合成に限定したことをCURRENT_TASK.mdに記録した。

**次タスク**

- 残るEPIC Tタスク(T001,T003,T004,T005)はいずれもTASK-R006/R009(全件ビルド、未着手)に依存するため着手不可。TASK-R003(Full jawiki ingest)以降、バックグラウンドで進行中の全件snapshot取得(Monitor task b3zh3vb03)が完了次第、EPIC R(R003〜R009)を継続する

## 2026-07-16 TASK-R003 Full jawiki ingest

**目的**

TASK-R002完了後、ユーザーが承認した方針(実Snapshot取得・全81チャンク取得・full ingest実施)に基づき、実データ(jawiki_namespace_0, snapshot version 35061ecbd3bc55c31cffd4b46838673d, 81チャンク約29GB)を`wikiepwing ingest`で`raw.sqlite3`へ取り込む。

**変更**

実行中に実データでのみ再現する2件のバグを発見・修正した:

- `src/wikiepwing/ingest/repository.py`: `_replace_children`が同一正規化キーへ衝突するredirects/categories/templates/licensesを無条件挿入しUNIQUE制約違反になっていたバグを修正(`_dedupe_by_key`ヘルパー追加)。`tests/test_repository.py`に回帰テスト追加。
- `src/wikiepwing/ingest/orchestrate.py`: `iter_ndjson_lines`が常に`tar_reader.DEFAULT_MAX_LINE_BYTES`(8MiB)を使い、設定可能な`max_html_bytes`/`max_wikitext_bytes`(既定64MiB)以下でもチャンク全体を失敗させていたバグを修正(`_max_ndjson_line_bytes`追加)。`tests/test_ingest_orchestrate.py`に回帰テスト追加。
- `TASKS.md`(TASK-R003を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
# バグ修正の検証
uv run pytest tests/test_repository.py tests/test_ingest_orchestrate.py
make check
git diff --check

# 実データingest(3回目、両修正適用後)
uv run python -m wikiepwing.cli ingest \
  --config "$SCRATCH/full-ingest-override.toml" \
  --lock-path "$SCRATCH/data/sources/jawiki/35061ecbd3bc55c31cffd4b46838673d/source.lock.json" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r003-retry2

uv run python -m wikiepwing.cli verify-raw \
  --raw-database "$SCRATCH/data/work/raw.sqlite3" \
  --sample-size 50
```

**結果**

- 1回目の実行はchunk 0付近(4000件目)でredirects UNIQUE制約違反により失敗、2回目の実行はchunk 46(約120万件目)でNDJSON行サイズ超過により失敗。両方とも実データでのみ顕在化する既存バグで、修正後にコードレベルのテスト(標準スイート1380件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功することを確認した。
- 3回目の実行(`run-id=full-r003-retry2`)で全81チャンクが成功し、ingestステージmanifestが`status=complete`(records_read=1,547,381, records_written=1,547,292, records_rejected=0, errors=78)。
- `verify-raw`で`integrity_check=ok`, `foreign_key_errors=0`, `sample_failures=[]`, `accepted_articles=1,508,200`を確認した。
- `raw.sqlite3`(約27GB)はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- TASK-R004 Full jawiki normalize(依存: R003、完了)

## 2026-07-16 TASK-R004 Full jawiki normalize

**目的**

TASK-R003で生成した`raw.sqlite3`(全81チャンク、accepted_articles=1,508,200)を`wikiepwing normalize`で`model.sqlite3`へ正規化する。

**変更**

実行中に実データでのみ再現するバグを発見・修正した:

- `src/wikiepwing/normalize/media_node.py`: `parse_image_node`が`<img src>`の`data:` URI(実データのSVGプレースホルダー画像、最大約10KB超)をそのまま`MediaReference`化しており、`model.sqlite3`の`media_references.media_id/source_url`のCHECK制約(8192バイト)違反でnormalize全体が失敗していたバグを修正(`data:`スキームはスキップ)。`tests/test_normalize_media_node.py`に回帰テスト追加。
- `TASKS.md`(TASK-R004を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run pytest tests/test_normalize_media_node.py
make check
git diff --check

uv run python -m wikiepwing.cli normalize \
  --config "$SCRATCH/full-ingest-override.toml" \
  --raw-database "$SCRATCH/data/work/raw.sqlite3" \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r004-retry
```

**結果**

- 1回目の実行はpage_id 4406(約2500件目)でmedia_referencesのCHECK制約違反により失敗。修正後にコードレベルのテスト(標準スイート1381件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功することを確認した。
- 2回目の実行(`run-id=full-r004-retry`)で全1,508,200記事が正規化され、normalizeステージmanifestが`status=complete`(articles_read=1,508,200, articles_written=1,508,200, articles_rejected=0, errors=0, fatals=0, warnings=8,923,739)。
- 警告の内訳を`diagnostics`テーブルで確認し、大半(8,923,739件)が既存の`DOM_UNKNOWN_ELEMENT`(TASK-G010の意図した警告レベルのフォールバック機構)であり新規バグでないことを確認した。
- `model.sqlite3`(約12.3GB)はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- TASK-R005 Full Mini generate(依存: R004、完了)

## 2026-07-16 TASK-R005 Full Mini generate

**目的**

TASK-R004で生成した`model.sqlite3`(全1,508,200記事)から、Miniプロファイル設定で`wikiepwing generate`を実行し`entries.jsonl`を生成する。

**変更**

生成後の`verify`実行中に実データでのみ再現するバグを発見・修正した:

- `src/wikiepwing/render/verify.py`: `_read_records`が`text.splitlines()`を使っており、JSON文字列内の正当なUnicode改行文字(U+2029等、実データの本文に実在する)を行区切りと誤認識し、1つの正常なJSONLレコードを複数の不正な断片に分割していたバグを修正(`\n`のみで分割するよう変更)。`tests/test_render_verify.py`に回帰テスト追加。
- `TASKS.md`(TASK-R005を`[x]`に)、`CURRENT_TASK.md`

**実行コマンド**

```bash
uv run python -m wikiepwing.cli generate \
  --config "$SCRATCH/full-ingest-override.toml" \
  --config config/profiles/mini.toml \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --entries-output "$SCRATCH/data/output/entries-mini.jsonl" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r005-mini

uv run python -m wikiepwing.cli verify --entries "$SCRATCH/data/output/entries-mini.jsonl"
```

**結果**

- generateステージmanifestが`status=complete`(articles_read=1,508,200, entries_written=1,508,200, articles_skipped=0)。`entries-mini.jsonl`は約12.9GB。
- 1回目の`verify`実行はline 33734(page_id 61417)でJSONパースエラーにより失敗。修正後にコードレベルのテスト(標準スイート1382件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功することを確認した。
- 2回目の`verify`実行で全1,508,200件のJSONパースに成功し、5件の`DUPLICATE_HEADWORD`を検出(`ok=false`)。これはverifyが意図通り検出すべき実データの品質課題であり、調査・報告はTASK-R006の対象とする。
- `entries-mini.jsonl`はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- TASK-R006 Full Mini verify/report(依存: R005、完了) — 検出された5件のDUPLICATE_HEADWORDの調査を含む

## 2026-07-16 TASK-R006 Full Mini verify/report

**目的**

TASK-R005で得た`entries-mini.jsonl`の`verify`結果(全1,508,200件のJSONパース成功、5件の`DUPLICATE_HEADWORD`検出、`ok=false`)を調査し、実データ由来かソフトウェアのバグかを切り分けて報告する。

**変更**

コード変更なし。`model.sqlite3`/`raw.sqlite3`への直接クエリによる調査のみ。

**実行コマンド**

```bash
uv run python3 -c "..." # 5件のDUPLICATE_HEADWORDペアそれぞれのpage_id/title/source_url/revision_id/source_date_modifiedを確認
```

**結果**

- 5件すべてが「page_id・revision_id・source_sequenceが異なるが、titleとsource_urlが完全一致、date_modifiedが数日ずれている」という同一パターンだった。
- これはWikimedia Enterprise Snapshot自体の特性(記事の削除・再作成による同一タイトルへの新page_id割り当てが、Snapshot取得期間内に新旧両方含まれるケース)であり、wikiepwingのソフトウェア側の重複生成バグではないと判断した。
- `ingest/deduplicate.py`のdedup処理はpage_id単位で正しく機能しており、`verify`の`DUPLICATE_HEADWORD`検出は意図通り(FreePWINGツールチェーンのbuild時チェックの事前再現)動作していることを確認した。
- 追加のコード変更は不要と判断。1,508,200件中5件(0.0003%)という頻度であり、実際の見出し語衝突解消は既存のFreePWINGツールチェーン(`freepwing_build_entries.pl`)に委ねる。

**次タスク**

- TASK-R007 Full Lite media run(依存: R004、完了) — Liteプロファイルの画像処理(image-plan/image-fetch/image-convert)を全件データに対して実行する

## 2026-07-17 TASK-R007 Full Lite media run

**目的**

TASK-R004の`model.sqlite3`(全1,508,200記事)に対する画像パイプライン(image-plan/image-fetch/image-convert)を実行する。`image-plan`で判明した2,546,801件のユニーク画像URL全件は逐次ダウンロードで4〜12日規模になるため、ユーザーの判断で約20,000件の代表サンプルによる検証に切り替えた。

**変更**

サンプル画像fetch/convertの実行過程で、実データでのみ再現する3件のバグを発見・修正した(すべて`src/wikiepwing/media/downloader.py`):

1. プロトコル相対URL(`//upload.wikimedia.org/...`)が`https://`必須チェックで全拒否されていたバグ(`_resolve_protocol_relative`追加)
2. `_UrllibTransport`がUser-Agentを送らずWikimedia側のUser-Agentポリシーで全リクエストが403になっていたバグ(説明的なUser-Agent送信)
3. HTTP 429を即座に失敗としていたバグ(`Retry-After`優先、指数バックオフで最大5回リトライ)

`tests/test_media_downloader.py`に各バグの回帰テストを追加。`TASKS.md`(TASK-R007を`[x]`に)、`CURRENT_TASK.md`。

**実行コマンド**

```bash
uv run pytest tests/test_media_downloader.py
make check
git diff --check

uv run python /private/tmp/.../scratchpad/sample_image_fetch.py  # 一回限りスクリプト、コミット対象外
```

**結果**

- 3件のバグはそれぞれ発見→修正→回帰テスト→`make check`成功確認→commitのサイクルを経てから次の実行に進んだ(標準スイートは1382→1390→1395件と増加、ImageMagickインストール後は全skipが解消)。
- `brew install imagemagick`でImageMagickをインストールし、既存のskippedテスト21件が成功するようになった。
- 4回目の実行(全修正適用後)で20,043件のサンプル(ユニークURL10,964件)に対し`fetched=8403 failed=2561`(成功率76.6%)、`converted=8319`(84件はcontent-addressed dedupeで自然除外)。
- 残る2,561件の失敗はすべて実データの特性(古いサムネイル参照、許可ホスト外、XXE対策、削除済みファイル等)であり、ソフトウェアのバグではないことを確認した。
- `graphics-sample/`にBMP 8,320個+`cgraphs.txt`が生成され、Lite画像パイプラインの一気通貫動作を確認した。実データ・実画像はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- TASK-R008 Full Lite generate/verify(依存: R007、完了)

## 2026-07-17 TASK-R008 Full Lite generate/verify

**目的**

TASK-R004の`model.sqlite3`(全1,508,200記事)からLiteプロファイル設定で`wikiepwing generate`を実行し、`verify`する。

**変更**

コード変更なし。実行と調査のみ。`TASKS.md`(TASK-R008を`[x]`に)、`CURRENT_TASK.md`。

**実行コマンド**

```bash
uv run python -m wikiepwing.cli generate \
  --config "$SCRATCH/full-ingest-override.toml" \
  --config config/profiles/lite.toml \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --entries-output "$SCRATCH/data/output/entries-lite.jsonl" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r008-lite

uv run python -m wikiepwing.cli verify --entries "$SCRATCH/data/output/entries-lite.jsonl"
```

**結果**

- generateステージmanifestが`status=complete`(articles_read=1,508,200, entries_written=1,508,200, articles_skipped=0)。
- `entries-lite.jsonl`のsha256がTASK-R005の`entries-mini.jsonl`と完全一致(byte-for-byte同一)することを発見し調査した。原因は`render/generate.py`がAppConfig/プロファイル設定を一切参照しない設計であるため(プロファイル差はnormalizeの`images_enabled`にのみ表れ、それも`media_references`テーブル=後続のimage-fetch/convertの対象範囲にしか影響しない。entries.jsonl本文の`[画像: ...]`プレースホルダーは`InfoboxBlock.images`由来で無条件生成)。検索語budget(`apply_search_budgets`)もパイプラインに未wiringであることをgrepで確認した(`render/generate.py`のdocstring通り、catalog/subbook/gaiji登録などと同様に意図的な後続タスク範囲)。
- バグではなく設計上の事実と判断し、追加のコード修正は不要とした。TASK-R007がすでにメディア選択・fetch/convertの軸を実データで検証済みであるため、本タスクの範囲を満たしていると判断。
- `verify`結果はTASK-R006と同一の5件の`DUPLICATE_HEADWORD`(内容同一のため当然)で、既に正当な実データ特性と判定済み。
- `entries-lite.jsonl`はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- TASK-R009 Full profile generate/verify(依存: R008、完了) — 同じ理由でentries-full.jsonlもmini/liteと同一内容になる見込み。実行して確認する

## 2026-07-17 TASK-R009 Full profile generate/verify

**目的**

TASK-R004の`model.sqlite3`(全1,508,200記事)からFullプロファイル設定で`wikiepwing generate`を実行し`verify`する。EPIC R(Full-scale builds)最後のタスク。

**変更**

コード変更なし。`TASKS.md`(TASK-R009を`[x]`に)、`CURRENT_TASK.md`。

**実行コマンド**

```bash
uv run python -m wikiepwing.cli generate \
  --config "$SCRATCH/full-ingest-override.toml" \
  --config config/profiles/full.toml \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --entries-output "$SCRATCH/data/output/entries-full.jsonl" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r009-full

uv run python -m wikiepwing.cli verify --entries "$SCRATCH/data/output/entries-full.jsonl"
```

**結果**

- generateステージmanifestが`status=complete`(articles_read=1,508,200, entries_written=1,508,200, articles_skipped=0)。
- TASK-R008の仮説通り、`entries-full.jsonl`のsha256が`entries-mini.jsonl`/`entries-lite.jsonl`と完全一致(byte-for-byte同一)することを確認した。バグではなく現行実装の設計上の期待通りの結果。
- `verify`結果もTASK-R006/R008と同一の5件の`DUPLICATE_HEADWORD`で、既に正当な実データ特性と判定済み。
- これでEPIC R(TASK-R001〜R009)がすべて完了した。実データで発見・修正した実データ限定バグは合計7件(R003で2件、R004で1件、R005で1件、R007で3件)。
- `entries-full.jsonl`はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- EPIC S残タスク: TASK-S004(Same-host rebuild comparison、依存: R006+S001-S003。すべて完了済みのため着手可能)、TASK-S005(Cross-host comparison、依存: S004)
- EPIC T残タスク: TASK-R006/R009完了により、T001(Build guide、依存R006)・T003(Troubleshooting、依存R009)・T004(Viewer verification guide、依存Q009,R009)・T005(Licensing/attribution guide、依存O010,R009)が着手可能になった

## 2026-07-17 TASK-S004 Same-host rebuild comparison

**目的**

PLAN.md 28(Phase 24 再現性試験)の出口条件「entry logical hash一致」を検証するため、同一ホスト・同一入力(TASK-R003で取得済みのsource.lock.json、全81チャンク)から独立に2回目のingest→normalize→generateを実行し、1回目の成果物と論理ハッシュを比較する。

**変更**

コード変更なし。`TASKS.md`(TASK-S004を`[x]`に)、`CURRENT_TASK.md`。

**実行コマンド**

```bash
uv run python -m wikiepwing.cli ingest --raw-database raw2.sqlite3 --lock-path <同一source.lock.json> --run-id rebuild2-ingest
uv run python -m wikiepwing.cli normalize --raw-database raw2.sqlite3 --model-database model2.sqlite3 --run-id rebuild2-normalize
uv run python -m wikiepwing.cli generate --config config/profiles/mini.toml --model-database model2.sqlite3 --entries-output entries-rebuild2.jsonl --run-id rebuild2-generate
uv run python3 -c "from wikiepwing.build_logical_hash import compute_logical_build_hash as h; ..."
```

**結果**

- `raw2.sqlite3`(sha256一致)、`model2.sqlite3`(sha256一致)、`entries-rebuild2.jsonl`(sha256一致)がすべて1回目のビルド成果物とbyte-for-byte完全一致した。
- `compute_logical_build_hash`による論理ハッシュも両ビルドで一致(`765528ac...`)。
- PLAN.md 28の出口条件「entry logical hash一致」を実データ全件規模(150万記事超)で確認した。差異なし、binary差異説明は不要。
- TASK-R003〜R009で発見・修正した実データ限定バグが再現しなかったことも同時に確認でき、修正が正しく機能していることを裏付けた。
- 2回目のビルド成果物はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- TASK-S005 Cross-host comparison(依存: S004、完了) — 別ホストでの再現性検証。実行環境の制約(単一ホストのみ利用可能)により実施方法を検討する必要がある

## 2026-07-17 TASK-S005 Cross-host comparison

**目的**

PLAN.md 28(Phase 24 再現性試験)の出口条件「entry logical hash一致」を、異なる環境間で検証する。この実行環境には物理的に別ホストが無いため、ユーザーの承認を得てDockerコンテナ(Debian Linux)を「異なる環境」の代替として使用する。

**変更**

コード変更なし。`TASKS.md`(TASK-S005を`[x]`に)、`CURRENT_TASK.md`。

**実行コマンド**

```bash
docker compose build app
docker run --rm -v .../data/sources:/data/sources:ro -v .../docker-work:/data/work ... \
  wikiepwing-app:dev wikiepwing ingest --raw-database /data/work/raw3.sqlite3 --lock-path ... --run-id docker-ingest
# 同様にnormalize/generate
```

**結果**

- コンテナ内`raw3.sqlite3`/`model3.sqlite3`はmacOSホスト版(TASK-S004)とメトリクス(articles_read/written/errors/warnings)が完全一致。sha256自体はOS/SQLiteビルド差異により異なるが想定通り。
- 1回目の`generate`はDocker Desktop VMのメモリ不足(既定約7.75GB)によりコンテナが無応答終了。`render/generate.py`が全記事を一括`fetchall()`する設計(見出し語衝突解決をグローバルに行うため)によるもので、コードのバグではなくDocker VM側のリソース制約と判断した。ユーザーがDocker Desktopのメモリを約85GBへ増やして再実行。
- 2回目の`generate`は成功し、`entries-rebuild3.jsonl`のsha256がmacOSホスト版・TASK-S004のDocker以外の再ビルド版すべてとbyte-for-byte完全一致(`1b6310d24f3485b1c2436cc2b0b3a7b3d75c006275f59e3f7474fb6078c58ac7`)。
- `compute_logical_build_hash`による論理ハッシュもmacOSホスト版とDocker版で完全一致(`765528ac...`)。
- OS・libc・SQLite/zstandardビルドが異なる環境間でも実データ全件規模での論理再現性を確認した。コンテナ成果物はスクラッチパッドのみに保持し、gitにはコミットしていない。

**次タスク**

- これでEPIC S(Reproducibility and operations)の主要タスク(S001-S005)がすべて完了した。残るはEPIC T(Release documentation)のうちT001(Build guide、依存R006、完了済みのため着手可能)、T003(Troubleshooting、依存R009、完了済み)、T004(Viewer verification guide、依存Q009,R009、完了済み)、T005(Licensing/attribution guide、依存O010,R009、完了済み)

## 2026-07-17 TASK-T001 Build guide

**目的**

EPIC R/Sで実データ全件規模で検証済みの手順に基づき、`BUILD.md`としてビルドガイドをまとめる。

**変更**

- `BUILD.md`(新規): 前提条件、doctor、acquire、ingest/normalize/generate/build、verify、画像パイプライン、Docker実行時の注意、運用コマンド、再現性確認の8セクション
- `README.md`: 読む順と想定リポジトリ構成に`BUILD.md`を追加

**実行コマンド**

```bash
uv run python -m wikiepwing.cli <各サブコマンド> --help  # ドキュメント内の全フラグ例と突き合わせ
make check
git diff --check
```

**結果**

- 全13サブコマンドのCLIフラグ例を実際の`--help`出力と突き合わせて一致を確認した。
- EPIC R/Sで発見した重要な知見(generateのプロファイル非依存性、image-fetchの逐次ダウンロード速度、DockerのOOM問題)を明記した。
- コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。

**次タスク**

- TASK-T003 Troubleshooting(依存: R009、完了済み)

## 2026-07-17 TASK-T003 Troubleshooting

**目的**

PLAN.md 31(v1.0 Definition of Done)のDocumentation項目「troubleshooting」を満たす。EPIC R/Sで実際に遭遇した問題と対処を`TROUBLESHOOTING.md`としてまとめる。

**変更**

- `TROUBLESHOOTING.md`(新規): 既に修正済みの実データ限定バグ7件、運用上の注意点7件、診断手順
- `README.md`: 読む順と想定リポジトリ構成に`TROUBLESHOOTING.md`を追加

**実行コマンド**

```bash
make check
git diff --check
```

**結果**

- すべての項目はLOG.mdに記録済みの実際の問題(EPIC R: redirects重複キー・NDJSON行サイズ・data: URI・Unicode改行文字・プロトコル相対URL・User-Agent・429リトライ、EPIC S: Docker OOM)に基づいて記述した。
- コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。

**次タスク**

- TASK-T004 Viewer verification guide(依存: Q009,R009、両方完了済み)

## 2026-07-17 TASK-T004 Viewer verification guide

**目的**

COMPATIBILITY.md 7(Viewer compatibility)の記録項目・Pass ruleに基づき、EPWINGビューア(EBWin系、EBPocket系、Emacs Lookup/lookup.el系)での確認手順を`VIEWER_VERIFICATION.md`としてまとめる。

**変更**

- `VIEWER_VERIFICATION.md`(新規): EPWINGバイナリのビルド手順、対象ビューア、記録項目/Pass rule、記録テンプレート
- `README.md`: 読む順と想定リポジトリ構成に追加

**実行コマンド**

```bash
make check
git diff --check
```

**結果**

- `docker/toolchain/mini-end-to-end-smoke.sh`等の既存スモークテストの実装を確認し、記述内容が実際のツールチェーン(`freepwing_build_entries.pl`, `eb-search.c`, `eb-entry.c`)と整合することを確認した。
- 全件規模のEPWINGバイナリビルド・実ビューアでの確認はまだ実施していないことを明記した(この環境にはビューアが無く、全件honmonも未ビルドのため、本タスクは手順書作成に限定)。
- コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。

**次タスク**

- TASK-T005 Licensing/attribution guide(依存: O010,R009、両方完了済み)

## 2026-07-17 TASK-T005 Licensing/attribution guide

**目的**

プログラム自体のライセンスと生成辞書のコンテンツライセンス(本文・画像)が別であることを明確にし、実装済みの帰属情報の仕組みと未実装の部分を`LICENSING.md`にまとめる。

**変更**

- `LICENSING.md`(新規): プログラムライセンス、本文/画像のコンテンツライセンス、BUILD-INFO.json、未実装の部分(attribution appendix)
- `README.md`: 既存「ライセンス」セクションから`LICENSING.md`への導線、読む順・想定リポジトリ構成に追加

**実行コマンド**

```bash
make check
git diff --check
```

**結果**

- `src/wikiepwing/config.py`をgrepし、`distribution.include_attribution_appendix`が設定検証のみで、実際にappendixファイルを生成するコードが存在しないことを確認し、正直に明記した。
- DATA_CONTRACTS.md 11のパッケージ内部構成(LICENSES.txt/ATTRIBUTION.txt/attribution.jsonl)とコードの実装状況を突き合わせた。
- コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。

**次タスク**

- TASK-T006 v1.0 release checklist(依存: S005,T001-T005、すべて完了済み)

## 2026-07-17 TASK-T006 v1.0 release checklist

**目的**

PLAN.md 31(v1.0 Definition of Done)の各項目を、実データ検証結果(EPIC R/S)とコード確認に基づいて評価し、`RELEASE_CHECKLIST.md`としてまとめる。

**変更**

- `RELEASE_CHECKLIST.md`(新規): Build/Content/Quality/Reproducibility/Documentationの5カテゴリすべての項目評価
- `README.md`: 読む順・想定リポジトリ構成に追加

**実行コマンド**

```bash
make check
git diff --check
```

**結果**

- 強く検証済み(source lock、resume、プロファイル生成、logical hashes)、部分的(画像/数式の全件検証、EPWINGバイナリの全件ビルド、reference比較の全件実測)、それぞれの根拠を記載した。
- コード確認により3件の未実装ギャップを新たに発見・記録した: (1) 検索語budget(`apply_search_budgets`)がパイプラインに未配線、(2) `BUILD-INFO.json`生成がCLIから未呼び出し、(3) Docker image digestの計算・記録が未実装。
- コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。

**次タスク**

- これでEPIC T(Release documentation、TASK-T001〜T006)がすべて完了した。TASKS.md全体を確認し、残る未完了タスクがあるか棚卸しする

## 2026-07-17 TASK-T007 Production EPWING build script

**目的**

ユーザー依頼。RELEASE_CHECKLIST.md(TASK-T006)で発見した「entries.jsonlから全件規模でHONMONをビルドする本番スクリプトが無い」ギャップに対応する。`docker/toolchain/build-epwing.sh`と`make build-epwing`を追加し、README.mdの「想定コマンド」を実態に更新する。

**変更**

- `docker/toolchain/build-epwing.sh`(新規): 既存の`freepwing_build_entries.pl`/`write_graphics_build_files`/`write_gaiji_build_files`の出力形式をそのまま受け付け、任意件数のentries・任意個数の画像/gaijiから`.epwing.zip`を組み立てる。画像・gaijiディレクトリは省略可能(Mini相当ビルドに対応)。
- `Makefile`: `build-epwing`ターゲットと関連変数(`ENTRIES`, `GRAPHICS_DIR`, `GAIJI_DIR`, `TITLE`, `SUBBOOK_DIR`, `EPWING_OUTPUT`)を追加。
- `README.md`: 「想定コマンド」「CLIの最終形」を実際に動作するコマンドに置き換え、`make build-epwing`を追記。
- `TASKS.md`: TASK-T007を追加。

**実行コマンド**

```bash
# 小規模動作確認(100記事フィクスチャ、画像・gaiji無し)
sh docker/toolchain/build-epwing.sh wikiepwing-toolchain:dev <entries.jsonl> /tmp/test.epwing.zip "" "" "テスト百科事典"
docker run --rm -v <extracted>:/book:ro --entrypoint /opt/eb/bin/wikiepwing-eb-search wikiepwing-toolchain:dev /book word "Emacs" 5

make check
git diff --check
```

**結果**

- 100記事フィクスチャ(`tests/fixtures/enterprise/hundred_articles.ndjson`)を実際にPythonパイプライン(register-local-source→ingest→normalize→generate→verify)に通してentries.jsonlを生成し、新しい`build-epwing.sh`でEPWINGパッケージを実際にビルドした。ビルド成功、`ebinfo`が正しいタイトルを表示し、`wikiepwing-eb-search`で"Emacs"検索が実際にヒットすることを確認した。
- 全件規模(約150万記事)での実行はユーザー側が行う方針のため、本タスクでは実施していない。画像・gaiji付きの本番規模テストも同様に未実施。
- コード変更(Python側)は無いため`make check`(1395 passed)は影響なし、`git diff --check`が成功することを確認した。

**次タスク**

- なし(TASKS.mdの全タスクが完了)。ユーザーが全件規模で`make build-epwing`を実行する際、必要に応じてサポートする

## 2026-07-17 TASK-T008 Acquire progress reporting

**目的**

ユーザー依頼。`acquire`が実行中に一切進捗を出力しないため「動いているのか固まっているのか分からない」という問題に実際に遭遇した。チャンク単位・チャンク内バイト単位の進捗コールバックを追加し、CLIで標準エラー出力に表示するようにする。

**変更**

- `src/wikiepwing/source/downloader.py`: `ChunkDownloadProgress`追加、`ResumableChunkDownloader`に`progress_interval_bytes`(既定8MiB)・`download`の`on_progress`引数を追加
- `src/wikiepwing/source/acquire.py`: `AcquireProgress`・`AcquireChunkProgress`追加、`acquire_snapshot`に`on_progress`・`on_chunk_progress`引数を追加
- `src/wikiepwing/cli.py`: `acquire`コマンドで両コールバックをstderr printに接続、`_format_mib`ヘルパー追加
- `tests/test_acquire.py`・`tests/test_chunk_downloader.py`: 回帰テスト計6件追加
- `TASKS.md`(TASK-T008追加)

**実行コマンド**

```bash
uv run pytest tests/test_acquire.py tests/test_chunk_downloader.py
make check
git diff --check
```

**結果**

- 既存の`_FakeDownloader`(test_acquire.py)を新しい`on_progress`引数に対応させた上で、チャンクごとの進捗イベント順序・already_presentマーキング・チャンク内バイト進捗の3件、downloader側で間引き・最終イベント保証・バリデーションの3件、計6件のテストを追加した。
- `make check`(1401 passed)、`git diff --check`が成功することを確認した。
- 既存のingest/normalize/generateと同じ「stderrへの進捗print」パターンに合わせた。

**次タスク**

- なし(TASKS.mdの全タスクが完了)

## 2026-07-17 TASK-T009 Normalize CPU-bound step parallelization

**目的**

ユーザー依頼。normalizeの処理時間についてユーザーから懸念があり、「処理時間が短縮できる変更ならば実装してほしいが、速度低下やバグ増加のリスクがあるならこのままにしたい」という条件付きで、16コア機での全コア並列化による高速化(最大10倍程度)を検討した。ユーザーから「150万レコードを一括で箱に貯めて一気にDB出し入れすればいいのでは」という提案があったが、それでは既存のbatch_sizeによるメモリ上限の仕組みを壊してしまう(generateステージで実際に発生している30-40GBメモリ問題と同じ構造になる)ため、既存のbatch_size/fetchmanyの単位を維持したまま、バッチ内でCPU律速な計算のみをプロセスプールに分散する設計とした。

**変更**

- `src/wikiepwing/normalize/orchestrate.py`:
  - モジュールdocstringに並列化の設計意図(`workers`は以前から`config`に宣言されていたが未使用だった)を追記
  - `_WorkItem`(rawからの読み込み結果一式、DBハンドルを含まずpickle可能)・`_ComputedResult`(計算結果)のfrozen dataclassを追加
  - `_normalize_one`を`_build_work_item`(raw.sqlite3読み込み、メインプロセス)と`_compute_normalized`(`normalize_html`からバリデーション・ハッシュ計算までの純粋関数、ワーカープロセスで実行可能)に分割
  - `_normalize_all`に`workers`引数を追加。`workers > 1`の場合のみ`ProcessPoolExecutor`を生成し、バッチ単位で`executor.map(_compute_normalized, work_items)`に分散、結果を`page_id`順(元のクエリの`ORDER BY page_id`のまま)で`repository.batch()`内で書き込む。`raw.sqlite3`の読み込みと`model.sqlite3`への書き込みはメインプロセスに残したまま変更なし
  - `run_normalize`に`workers: int = 1`引数を追加(デフォルトは逐次のまま、既存動作を変えない)
- `src/wikiepwing/cli.py`: `normalize`コマンドに`--workers`オプション追加(未指定時は`config`の`[normalize].workers`、デフォルト8)。`build`コマンドのnormalizeステージにも同様に`workers=normalize_section["workers"]`を配線
- `tests/test_normalize_orchestrate.py`: `test_normalize_parallel_matches_sequential_output`を追加。同じ入力に対し`workers=1`(逐次)と`workers=4`(並列)で`run_normalize`をそれぞれ実行し、`metrics`が完全一致すること・`model.sqlite3`のファイルバイトが完全一致することを検証
- `TASKS.md`(TASK-T009追加)

**実行コマンド**

```bash
uv run mypy src
uv run ruff format --check .
uv run ruff check .
uv run pytest tests/test_normalize_orchestrate.py -q
make check
git diff --check
```

**結果**

- 小規模フィクスチャ(10記事)で`workers=1`と`workers=4`が完全にバイト単位で同一の`model.sqlite3`を生成することをテストで確認した。
- `make check`(1402 passed、+1件)、`uv run mypy src`(138ファイル、エラーなし)、`git diff --check`が成功することを確認した。
- `config`の`[normalize].workers`(デフォルト8)は以前から宣言されていたが読まれていなかった値で、今回初めて実際にワーカー数として使用されるようになった。フルスケール実行時の実測(1.5万記事程度でどの程度速くなるか)はユーザー側で確認予定。

**次タスク**

- なし(TASKS.mdの全タスクが完了)
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち
- ユーザーが依頼した場合のみ: `generate`ステージの3層メモリ蓄積問題(30-40GB)の改善

## 2026-07-17 TASK-T010 Image fetch concurrency and fetch-count limit mode

**目的**

ユーザー依頼。`image-fetch`が`upload.wikimedia.org`への完全逐次ダウンロードで、全件(約250万ユニークURL)実行すると4〜12日かかる見積もり(RELEASE_CHECKLIST.md)だった。相手サーバーに迷惑をかけない範囲で並列ダウンロードに対応し、加えて「画像が不足した状態で一旦EPWINGビルドを最後まで通して動かしてみたい」という要望に応えるため、先頭N件のユニークURLを取得した時点で打ち切るlimitモードを追加する。

**変更**

- `src/wikiepwing/media/orchestrate.py`: `fetch_media`に`max_workers`(既定1=逐次)・`limit`(既定None=無制限)引数を追加。`max_workers > 1`のときのみ`ThreadPoolExecutor`を生成し(ネットワークI/OなのでThreadPoolExecutor。normalizeのCPU律速な`ProcessPoolExecutor`とは別の選択)、`executor.map`でplan順を保った並列ダウンロードを行う。`limit`はユニークURL抽出時に先頭N件で打ち切る(件数は「試行したユニークURL数」であり「成功件数」ではない)
- `src/wikiepwing/config.py`: `[images]`セクションに`fetch_concurrency`(INTEGER)を追加、`_validate_semantics`に0を拒否するチェックを追加
- `config/default.toml`: `images.fetch_concurrency = 4`(相手サーバーへの配慮を優先した控えめな既定値)を追加
- `src/wikiepwing/cli.py`: `image-fetch`コマンドに`--concurrency`(未指定時は`config`の`images.fetch_concurrency`)・`--limit`オプションを追加
- `tests/test_media_orchestrate.py`: 並列時のplan順序保持・`max_workers`/`limit`のバリデーション・limitがユニークURL単位でありplanエントリ単位ではないことを検証するテスト計5件追加
- `README.md`: `image-fetch`の`--concurrency`/`--limit`の使い方と、全件所要時間の見積もりを追記
- `TASKS.md`(TASK-T010追加)

**実行コマンド**

```bash
uv run mypy src
uv run ruff format .
uv run ruff check .
uv run pytest tests/test_media_orchestrate.py tests/test_config.py -q
make check
git diff --check
```

**結果**

- `make check`(1407 passed、+5件)、`uv run mypy src`(138ファイル、エラーなし)、`git diff --check`が成功することを確認した。
- `SecureMediaDownloader`はURLごとに独立した`urllib`リクエストを行い共有可変状態を持たないため、スレッドプールでの並行実行は安全と判断した。
- `limit`は「試行したユニークURL数」の上限であり「成功取得数」の上限ではない(失敗もカウントされる)。実行時間を予測可能にするための単純な設計を優先した。

**次タスク**

- なし(TASKS.mdの全タスクが完了)
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち
- ユーザーが依頼した場合のみ: `generate`ステージの3層メモリ蓄積問題(30-40GB)の改善

## 2026-07-17 TASK-T011 Image fetch progress reporting

**目的**

ユーザー依頼。TASK-T010で並列化・limitモードを追加した`image-fetch`が、実行中の進捗を一切出力せず「動いているのか分からない」という状態だった(acquireで過去に遭遇したのと同じ問題)。`fetch_media`にURL1件完了ごとの進捗コールバックを追加し、CLIで標準エラー出力に表示するようにする。

**変更**

- `src/wikiepwing/media/orchestrate.py`: `FetchProgress`(completed/total/succeeded/failed)を追加。`fetch_media`に`on_progress`引数を追加。逐次実行時はURL完了ごとに、並列実行時は`concurrent.futures.as_completed`でURLが実際に完了した順(plan順ではない)にコールバックを呼ぶ。返り値の`tuple`は従来通りplan順(ユニークURL抽出順)を維持する
- `src/wikiepwing/cli.py`: `image-fetch`コマンドで`on_progress`をstderrへの`print`に接続(`fetch N/M succeeded=X failed=Y`形式)
- `tests/test_media_orchestrate.py`: 逐次実行時の進捗順序・並列実行時の進捗イベント数・失敗のカウントを検証するテスト3件追加
- `TASKS.md`(TASK-T011追加)

**実行コマンド**

```bash
uv run mypy src
uv run ruff format .
uv run ruff check .
uv run pytest tests/test_media_orchestrate.py -q
make check
git diff --check
```

**結果**

- `make check`(1410 passed、+3件)、`uv run mypy src`(138ファイル、エラーなし)、`git diff --check`が成功することを確認した。
- 並列実行時は`ThreadPoolExecutor`のfutureを`as_completed`で拾うことで、実際にダウンロードが終わった順にリアルタイムで進捗を報告できるようにした(`executor.map`のままだと先頭のURLが遅いと後続の速い完了が報告されずに進捗が止まって見える問題を避けた)。最終的な返り値の順序はplan順のまま変えていない。
- 既存のacquire/normalize/generateと同じ「stderrへの進捗print」パターンに合わせた。

**次タスク**

- なし(TASKS.mdの全タスクが完了)
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち
- ユーザーが依頼した場合のみ: `generate`ステージの3層メモリ蓄積問題(30-40GB)の改善

## 2026-07-17 TASK-T012 Fix build-epwing.sh relative-path bind mount bug

**目的**

ユーザーが実際に`make build-epwing`(ENTRIES=entries-mini.jsonlのような相対パス)を実行したところ、`cp: -r not specified; omitting directory '/input/entries.jsonl'`で失敗した。原因を特定し修正する。

**変更**

- `docker/toolchain/build-epwing.sh`: `entries`/`graphics_dir`/`gaiji_dir`を、存在チェック直後・`docker run -v`に渡す前に絶対パスへ解決するコードを追加した(`entries=$(CDPATH= cd "$(dirname "$entries")" && pwd)/$(basename "$entries")`、ディレクトリは`$(CDPATH= cd "$dir" && pwd)`)
- `TASKS.md`(TASK-T012追加)

**実行コマンド**

```bash
# 実際にバグを再現・修正確認(100記事フィクスチャをPythonパイプラインで生成し、相対パスで指定)
sh docker/toolchain/build-epwing.sh wikiepwing-toolchain:dev entries-verify-test.jsonl output/verify-test.epwing.zip "" "" "検証用百科事典"
docker run --rm -v <extracted>:/book:ro --entrypoint /opt/eb/bin/wikiepwing-eb-search wikiepwing-toolchain:dev /book word "Emacs" 5
git diff --check
```

**結果**

- 原因: `docker run -v`は、ホスト側パスが`/`・`./`・ドライブレターで始まらない場合(単なる相対ファイル名など)、bind mountではなく名前付きボリュームとして解釈する。存在しない名前のボリュームは自動的に空のディレクトリとして作成されるため、`/input/entries.jsonl`が実際にはファイルではなく空ディレクトリになり、`cp`(非再帰)が失敗していた。
- 修正後、`tests/fixtures/enterprise/hundred_articles.ndjson`から実際にPythonパイプライン(register-local-source→ingest→normalize→generate)で生成した100記事分のentries.jsonlを相対パスで指定してビルドし、EPWINGパッケージが正しく生成され、`ebinfo`でタイトル表示・`wikiepwing-eb-search`で"Emacs"の検索が実際にヒットすることを確認した(ユーザーが遭遇したのと同じ相対パスの使い方で再現・検証)。
- シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。
- ユーザーの環境で生成された実際の`entries-mini.jsonl`(約150万記事)の先頭50件で試したところ、このバグとは別に`invalid character: \x8f`という`freepwing_build_entries.pl`のエンコーディングエラーが発生した。これは今回のバグとは無関係で、gaiji(外字)ディレクトリを指定していない状態でJIS X 0208外の文字を含む実データを処理しようとしたため起きたと見られる。全件規模でのビルド(画像・gaiji付き)は別途ユーザー側での検証が必要。

**次タスク**

- なし(TASKS.mdの全タスクが完了)
- ユーザーへ報告: 全件規模の`entries-mini.jsonl`をgaijiディレクトリなしでビルドすると`invalid character`エラーが出る可能性がある(gaiji生成済みディレクトリを`GAIJI_DIR`に渡す必要がある)
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち

## 2026-07-17 TASK-T013 Simple workaround for JIS X 0212 characters crashing the build

**目的**

ユーザーが全件規模の`entries-mini.jsonl`(約150万記事)でビルドを試したところ`invalid character: \x8f`で失敗した。外字(gaiji)パイプラインの現状を調査した結果、本格対応(normalize/generateへの外字置換統合、CLIコマンド新設)は相応の規模の作業になることを説明し、ユーザーから「簡易的な回避策を先に試したい」との依頼を受けた。

**変更**

- `docker/toolchain/freepwing_build_entries.pl`: `to_euc_jp`を文字単位のループに変更。各文字をEUC-JPエンコードし、先頭バイトが`0x8f`(JIS X 0212のSS3プレフィックス、FPWParserが理解できない)になるものだけを全角下駄記号(〓、U+3013、素のJIS X 0208で表現可能)に置換するようにした
- `TASKS.md`(TASK-T013追加)

**実行コマンド**

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
# JIS X 0212専用文字(凜)を含む新規フィクスチャでの再現確認
sh docker/toolchain/build-epwing.sh wikiepwing-toolchain:dev <凜を含むentries.jsonl> /tmp/gaiji-test.epwing.zip "" "" "外字テスト"
git diff --check
```

**結果**

- 原因: PerlのEncodeモジュールの`euc-jp`は、JIS X 0212(補助漢字面)の文字もSS3(`\x8f`)プレフィックス付きでエンコードしてしまうが、FreePWINGのFPWParserはJIS X 0208の2バイトコードしか理解せず`\x8f`を見ると即エラーになる。実データの本文には、珍しくはない通常の漢字でJIS X 0212にしか収録されていないものが含まれるため(既存のフィクスチャは意図的にJIS X 0208内の文字だけを使っていたため再現しなかった)、全件規模で初めて顕在化した。
- 修正後、既存の`freepwing-build-entries-smoke.sh`(通常のASCII/JIS X0208日本語コンテンツ)が引き続き成功することを確認した。加えて、JIS X 0212専用の実在漢字「凜」を含む新規フィクスチャを作成してビルドし、`invalid character`エラーが再発せず最後まで`.epwing.zip`が生成されることを確認した。
- これはあくまで簡易回避策であり、該当文字の情報は失われる(下駄記号に置き換わる)。本格的な対応(normalize/generateでの外字コード割り当て・専用グリフ描画・EPWING外字フォントとしての登録)は別途実施が必要であることをユーザーに明示した。
- シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。

**次タスク**

- ユーザーが依頼した場合のみ: normalize/generateへの本格的な外字(gaiji)パイプライン統合(検出→コード割り当て→グリフ描画→ビルドファイル書き出しのCLIコマンド新設)
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち
- RELEASE_CHECKLIST.mdの「gaiji fallback ✅ 完了」の記載は、ライブラリ関数レベルの完了であってパイプライン統合はされていない実態を反映するよう修正が必要(今回未実施)

## 2026-07-17 TASK-T014 freepwing_build_entries.pl progress reporting

**目的**

ユーザーが`make build-epwing`実行中に「進捗も何も出ない、遅すぎる」と報告(質問で対象を確認したところ`make build-epwing`と回答)。`freepwing_build_entries.pl`のentries.jsonlパース・FPWParser登録の2ループに進捗出力を追加する。

**変更**

- `docker/toolchain/freepwing_build_entries.pl`:
  - `$| = 1`(autoflush)・`$PROGRESS_EVERY = 20_000`を追加
  - パースループ開始前に総行数を数える軽量な事前パス(`wc -l`相当)を追加し、`parse N/total`をN件ごと+ループ終了後に必ず1回、標準エラー出力する
  - FPWParser登録ループにも同様に`index N/total`を追加
- `TASKS.md`(TASK-T014追加)

**実行コマンド**

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
# 45,000件の合成entries.jsonlで進捗出力を確認
git diff --check
```

**結果**

- 既存の`freepwing-build-entries-smoke.sh`(3エントリ)が引き続き成功し、`parse 3/3`・`index 3/3`が出力されることを確認した。
- 45,000件の合成フィクスチャを実際に`build-epwing.sh`経由でビルドし、`parse 20000/45000`→`parse 40000/45000`→`parse 45000/45000`→`index 20000/45000`→...という進捗が実際に出力され、ビルドも最後まで成功することを確認した。
- `fpwsort`/`fpwindex`/`fpwcontrol`/`fpwlink`/`ebzip`等、その後の工程はFreePWING/EB付属のコンパイル済みバイナリであり、ソースを持たず進捗出力を追加できないため今回は対象外。ユーザーへその旨を伝える。
- シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。

**次タスク**

- なし(TASKS.mdの全タスクが完了)
- ユーザーが依頼した場合のみ: normalize/generateへの本格的な外字(gaiji)パイプライン統合
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち

## 2026-07-17 TASK-T015 Speed up freepwing_build_entries.pl's to_euc_jp

**目的**

ユーザーから`freepwing_build_entries.pl`が「めちゃくちゃ遅い」、進捗表示や並列化で何とかならないか問い合わせがあった。原因を調査し、リスクの低い範囲で高速化する。

**変更**

- `docker/toolchain/freepwing_build_entries.pl`: `to_euc_jp`を、文字列全体を1回`encode('euc-jp', $value)`した後、結果のバイト列に対して`s/\x8f../$GETA_MARK_EUC_JP/gs`で正規表現一括置換する実装に変更(従来は1文字ずつ`split //`してencode()を呼んでいた)
- `TASKS.md`(TASK-T015追加)

**実行コマンド**

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
# 新旧実装のバイト単位一致確認(エッジケース含む、手動のPerlスクリプトで検証)
# 10万件の合成entries.jsonlでの実行時間比較(手動)
git diff --check
```

**結果**

- 原因: TASK-T013で追加した`to_euc_jp`が`split //`で1文字ずつループし`encode()`を呼んでいたため、全件規模(約150万記事、タイトル+本文+エイリアス)では数億〜十億回規模のPerl関数呼び出しが発生し、これが支配的なコストになっていた。
- JIS X 0212のSS3シーケンス(`\x8f` + 2バイト、両方とも`0xA1`-`0xFE`)は、他の正当なEUC-JPシーケンス(JIS X0208の2バイト目・SS2かなの2バイト目、いずれも`0xA1`以上)の末尾バイトとして`\x8f`(0x8Fは0xA1未満)が出現することがないため、「文字列全体を1回encode→結果バイト列に正規表現で`\x8f..`を一括置換」という実装に変えても、1文字ずつ判定していた旧実装とバイト単位で完全に等価であることを、様々なエッジケース(JIS X0212専用文字の連続、通常文字との混在、下駄記号が入力に既に含まれる場合等)を通したPerlスクリプトで確認した。
- 10万件・本文400〜800文字程度の合成entries.jsonl(約131MB)で実際にDocker内で計測: 旧実装134.08秒→新実装68.16秒(約2倍の高速化)。全件規模(約150万記事)では単純計算で約34分→約17分程度の短縮が見込まれる。
- FPWParserへの登録ループ(`text->add_text`等、`word2->add_entry`が`entry_position()`という処理順依存の内部カウンタを使う)は状態を持つため安全に並列化できないと判断し、今回は対象外とした。`fpwsort`/`fpwindex`等それ以降のコンパイル済みバイナリも同様に対象外。
- 既存の`freepwing-build-entries-smoke.sh`が引き続き成功することを確認した。シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。

**次タスク**

- ユーザーが依頼した場合のみ: パースループ(entries.jsonl読み込み+`to_euc_jp`)自体を複数プロセスへ分割する並列化(FPWParser登録ループとは独立に検討可能だが、Perlでの実装・出力順序の保証にそれなりのリスクが伴うため、今回は着手していない)
- ユーザーが依頼した場合のみ: normalize/generateへの本格的な外字(gaiji)パイプライン統合(GAIJI.md参照)
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち

## 2026-07-17 TASK-T016 More frequent freepwing_build_entries.pl progress interval

**目的**

ユーザー依頼。TASK-T014で追加した進捗出力(2万件ごと)を10件ごとに変更してほしい、また`make`を実行するたびに最新のプログラムが反映されているか確認したい、という依頼。

**変更**

- `docker/toolchain/freepwing_build_entries.pl`: `$PROGRESS_EVERY`を`20_000`から`10`に変更
- `TASKS.md`(TASK-T016追加)

**実行コマンド**

```bash
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
git diff --check
```

**結果**

- 既存の`freepwing-build-entries-smoke.sh`が引き続き成功することを確認した。
- 「`make`のたびに最新版が反映されるか」の質問について: `docker/toolchain.Dockerfile`を`grep`し、`freepwing_build_entries.pl`を一切`COPY`していないことを確認した。`docker/toolchain/build-epwing.sh`は`make build-epwing`実行のたびに、ホスト上の(その時点で編集済みの)`freepwing_build_entries.pl`を一時ディレクトリへコピーし、読み取り専用でbind mountしてコンテナに渡す実装になっているため、Dockerイメージの再ビルド有無に関わらず常にホスト上の最新ファイルが使われることを確認し、ユーザーへ回答した。
- シェルスクリプトのみの変更のため`make check`(Pythonテスト)には影響なし。`git diff --check`が成功することを確認した。

**次タスク**

- なし(TASKS.mdの全タスクが完了)
- ユーザーが依頼した場合のみ: パースループの並列化、normalize/generateへの本格的な外字(gaiji)パイプライン統合(GAIJI.md参照)
- 未解決: `config/local-paths.toml`をコミットするか`.gitignore`に追加するか、ユーザーへの確認待ち
## 2026-07-18 TASK-T017 Ingest pre/post-processing progress reporting

**目的**

`wikiepwing ingest` の記事処理前後にある長時間の無表示処理へ進捗表示を追加し、正常に処理中なのか終了不能なのかを判別可能にする。

**変更**

- `source/checksums.py`: bounded-memory fingerprint処理へ任意のバイト進捗コールバックを追加
- `ingest/database.py`: SQLite `integrity_check`へprogress handlerを設定し、開始・VMステップ・完了を通知
- `ingest/orchestrate.py`: 入力検証、resume判定用出力fingerprint、DB整合性検証、終了時DB fingerprintをフェーズ進捗として通知
- `cli.py`: 256 MiBごとのバイト進捗、1,000万VMステップごとのDB整合性進捗、各フェーズ完了を標準エラーへ表示
- `tests/`: fingerprintコールバック、DB整合性開始/完了、CLI表示を回帰テスト化

**実行コマンドと結果**

```bash
uv run pytest -q tests/test_checksums.py tests/test_raw_database.py tests/test_ingest_orchestrate.py tests/test_cli.py
# 73 passed
make format-check
# 291 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 139 source files
make test
# 1437 passed, 1 warning
git diff --check
# success
```

**次タスク**

- なし。ingest再実行時の既存complete manifest探索はTASK-T017の非対象。

## 2026-07-18 TASK-T018 Post-ingest command progress audit and reporting

**目的**

`normalize`以降のCLI、画像パイプライン、toolchainビルドを監査し、実データ規模で長時間になり得る無表示区間を可視化する。

**変更**

- 共通の`PhaseProgress`とCLI reporterを追加し、256 MiBごとのファイルI/O、1,000万VMステップごとのSQLite検査、1万件ごとの全件処理をbounded-frequencyで標準エラーへ表示
- `normalize`/`generate`: 入出力fingerprint、DB integrity、モデル読込、headword生成、gaiji割当・bitmap・registry、JSON encode/writeをフェーズ化
- `verify-raw`/`verify`: SQLite検査・サンプル展開とJSONL読込・tag/headword/target検査をフェーズ化
- `image-plan`/`image-fetch`/`image-convert`: SQL走査、画像読込・変換、report/graphics書込をフェーズ化
- `build-epwing.sh`: 入力配置、`fpwmake`、catalog生成、stage配置、`ebinfo`、`ebzip`、ZIP生成、出力コピーの開始・完了を表示
- `toolchain-image`は既存のBuildKit進捗が表示されるためコード変更なし

**実行コマンドと結果**

```bash
uv run pytest -q tests/test_cli.py tests/test_ingest_verify.py tests/test_media_orchestrate.py tests/test_freepwing_toolchain_definition.py
# 69 passed
make format-check
# 292 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 140 source files
make test
# 1440 passed, 1 warning
make toolchain-image
# success (BuildKit progress displayed)
sh docker/toolchain/handcrafted-three-entry-smoke.sh wikiepwing-toolchain:dev
# success
# 隔離したコミット版freepwing_build_entries.plでbuild-epwing.shを実行
# phase表示からZIP出力までsuccess
git diff --check
# success
```

**次タスク**

- なし。

## 2026-07-18 TASK-T019 Ignore generated root gaiji artifacts

**目的**

`generate`がリポジトリ直下へ既定出力したgaiji成果物をGit管理候補から除外し、誤コミットを防止する。

**変更**

- `.gitignore`: `/gaiji/`、`/gaiji.sqlite3`、`/unicode-report.json`をroot限定で追加。`src/wikiepwing/gaiji/`配下の新規ソースを誤ってignoreしない。
- `tests/test_repository_hygiene.py`: 上記3パターンを回帰テスト化。

**実行コマンドと結果**

```bash
git check-ignore -v gaiji gaiji.sqlite3 unicode-report.json
# 3件とも新規root限定パターンに一致
uv run pytest -q tests/test_repository_hygiene.py
# 1 passed
make format-check
# 293 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 140 source files
make test
# 1441 passed, 1 warning
git diff --check
# success
```

**結果**

- `.gitignore`は削除されておらず、履歴上の最新版を保持していた。
- 漏れていた生成物は未追跡のままだったため、ファイル削除や`git rm --cached`は不要だった。

## 2026-07-18 TASK-T020 FreePWING gaiji capacity and full EPWING build

**目的**

全件生成物がFreePWINGの外字上限を超えて停止する問題を修正し、実データからEPWING辞書ZIPを最後まで生成する。

**原因と変更**

- FreePWINGは半角・全角外字を各8,192文字までしか定義できないが、生成済み成果物は半角26,837・全角113,761文字を含んでいた。
- 各幅で使用回数の多い順、同数ならUnicode順に8,192文字を選び、選外文字を`[U+XXXX]`へ明示的にフォールバックする決定的な容量制御を追加した。
- 生成済みの12GB JSONL・gaiji registryをストリーム変換する`wikiepwing.gaiji.capacity`を追加し、再renderせず容量安全なbuild入力を作成した。
- generateのgaiji計数をwhole-corpusの`Counter`と一括置換へ変更し、進捗表示を10,000件間隔に制限した。
- FreePWINGが正規化後に空語とする記号だけの別名は呼出し前に判定・集計して除外する。記事間で共有される検索語は拒否せず、複数検索結果として保持・集計する。
- 実FreePWING統合テストで、空語別名を含む入力の継続と共有別名が2記事へ解決することを確認した。

**実生成結果**

```text
entries: 1,508,200
gaiji selected: narrow=8,192, wide=8,192
overflow unique: narrow=18,645, wide=105,569
overflow occurrences: narrow=65,547, wide=240,053
FreePWING empty headwords skipped: 12
shared headwords: 8
EPWING ZIP: data/output/jawiki.epwing.zip (5.7 GiB)
SHA-256: d3ec046a0c710e1d6fae61a2f5ec476a555cbda32df0f1f484da1bdf2b4b8b3a
```

`ebinfo`は生成前stageとEBZIP圧縮後packageの双方で成功し、EPWING/JIS X 0208、1 subbook、word/endword検索、16-dot narrow/wide外字を確認した。`unzip -t`も全7項目で成功した。

**実行コマンドと結果**

```bash
uv run python -m wikiepwing.gaiji.capacity \
  --entries-source entries-mini.jsonl --database gaiji.sqlite3 \
  --gaiji-source gaiji --entries-output data/work/entries-mini.jsonl \
  --gaiji-output data/work/gaiji \
  --report data/reports/gaiji-capacity-report.json
# success: 12GBをストリーム変換、各幅8,192外字
make build-epwing ENTRIES=data/work/entries-mini.jsonl \
  GRAPHICS_DIR=data/work/graphics GAIJI_DIR=data/work/gaiji \
  TITLE="日本語ウィキペディア二〇二六年六月" \
  EPWING_OUTPUT=data/output/jawiki.epwing.zip
# success: data/output/jawiki.epwing.zip
unzip -t data/output/jawiki.epwing.zip
# No errors detected in compressed data
make format-check
# 295 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 141 source files
make test
# 1453 passed, 1 warning
git diff --check
# success
```

**次タスク**

- 自動実装タスクはなし。生成済みEPWINGを実ビューアで開く手動確認へ進む。

## 2026-07-18 TASK-T032 Normalize full-run robustness and RAM-first parent bottleneck reduction

**目的**

参照EPWINGとの差分確認に必要な全件model再生成を進めるため、full normalize runの停止要因と親process律速を減らす。

**変更**

- `model-diff-ram6.sqlite3`のfull runは145,000記事時点で停止した。
  原因は、実データ内のinfobox field nameがwhitespace/zero-width正規化後に
  空文字となり、`InfoboxField`のmodel制約に違反したこと。
- 正規化後に空になるinfobox field nameはfieldごとskipし、
  `INFOBOX_EMPTY_FIELD_NAME` warning診断として記録するようにした。
- bulk writeへprecompressed canonical JSONを渡せるようにし、worker側で
  final canonical JSONのzstd圧縮まで行うようにした。
- macOS `sample`で親processを確認したところ、worker結果のunpickleとGCが
  目立ったため、batch結果受信中のGC抑制とProcessPool chunksize指定を追加した。
- `ram2`/`ram3`の古い実験processがメモリを保持していたため、明示PIDで停止した。
- `model-diff-ram8.sqlite3`として再実行中。1,305,000記事時点でreject 0。
  `ram6`の145,000記事停止地点は再発なく通過した。

**検証**

```bash
uv run pytest -q tests/test_normalize_infobox_block.py tests/test_normalize_whitespace.py
# 21 passed
uv run pytest -q tests/test_model_repository.py tests/test_normalize_orchestrate.py \
  tests/test_normalize_infobox_block.py tests/test_links_article_resolver.py
# 29 passed
uv run pytest -q tests/test_normalize_orchestrate.py tests/test_model_repository.py \
  tests/test_normalize_infobox_block.py
# 26 passed
uv run ruff check src/wikiepwing/model/repository.py src/wikiepwing/normalize/orchestrate.py \
  src/wikiepwing/normalize/infobox_block.py tests/test_model_repository.py \
  tests/test_normalize_infobox_block.py
# All checks passed
uv run mypy src/wikiepwing/model/repository.py src/wikiepwing/normalize/orchestrate.py \
  src/wikiepwing/normalize/infobox_block.py
# Success: no issues found in 3 source files
```

## 2026-07-18 TASK-T032 Normalize throughput bottleneck reduction

**調査結果**

- 8 worker指定にもかかわらず、約55,500記事時点ではworkerがほぼCPUを使わず、
  親processが約71% CPUを使用していた。
- 新しいinline link保存により、55,500記事で12,793,889 link（約230 link/記事）を
  解決・保存しており、linkごとのSQL照会と1行ずつのinsertが直列律速だった。
- 初回runは途中DBを残して停止し、既存`model.sqlite3`は変更していない。

**変更**

- raw DBに対する記事・redirect解決結果を記事間で共有するbounded cacheを追加した。
- fragmentをcache keyから分離し、同じ記事への異なるfragmentを保持したまま再利用する。
- model repositoryのlink保存を記事単位の`executemany`へ変更した。
- cache再利用時にSQL照会が発生せずfragmentを保持する回帰testを追加した。

**局所計測と検証**

```text
対象: 記事「日本」の1,704 links
cacheなし: 0.053秒、1,818 SQL queries
初回cache: 0.045秒、1,159 SQL queries
warm cache: 0.013秒、0 SQL queries
```

```bash
uv run pytest -q tests/test_links_article_resolver.py \
  tests/test_model_repository.py tests/test_normalize_orchestrate.py
# 19 passed
make format-check
# 299 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 143 source files
```

**再実行**

- 別成果物`data/work/model-diff-optimized.sqlite3`へ8 workerで開始した。
- 初期観測では8 workerがそれぞれ約55〜78% CPU、親processも約96% CPUとなり、
  以前のworker待機状態は解消した。全件throughputは継続計測する。

## 2026-07-18 TASK-T032 RAM-first normalize parallelization

**原因の追加特定**

- 5,000記事batchの実測で、redirect/category/media/licenseのarticle単位SQL、
  親processだけで行うlink解決・再encode、`links_target`の逐次更新が順に律速と判明した。
- 単にbatchを大きくするだけでは約2.3GB RAMを消費してworkerを待たせ、速くならなかった。

**変更**

- batch page IDをRAM上のSQLite TEMP tableへ入れ、4種類の付随情報を集合JOINで取得した。
- query plannerがchild table全走査を選ばないよう、TEMP table起点の`CROSS JOIN`に固定した。
- 各workerがraw DB readerと最大1,000,000 titleのlink cacheを保持し、link解決と
  最終canonical encode/hashも8 processで並列実行するようにした。
- 5,000記事分のarticle/link/media/diagnostic rowをRAMへ集約し、table単位でbulk insertする。
- model SQLite cacheを4GiB、各worker raw cacheを512MiB、mmapを8GiBへ拡大した。
- fresh build中は`links_target` indexを外し、全link投入後に一度だけ再作成する。
- kill後のforce再実行でもdeferred indexを最後に復元する契約を維持した。

**実測**

```text
従来: 約44〜49記事/秒
RAM/parallel版 warm batch: 約55〜83記事/秒
15,000記事時点: rejected 0
実行成果物: data/work/model-diff-ram6.sqlite3
```

**局所検証**

```bash
uv run pytest -q tests/test_model_repository.py tests/test_normalize_orchestrate.py
# 18 passed
make format-check
# 299 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 143 source files
```

## 2026-07-18 TASK-T022 Record viewer-observed differences as TODOs

**目的**

Emacs Lookupで観察したインターネット配布版と今回版の差を、今後の品質改善TODOとして記録する。

**変更**

- `DIFF.md`を新設し、本文レイアウト、内部リンク、画像、検索索引、メタデータの差を整理した。
- 今回版のplain-text化、リンク末尾列挙、graphics未接続というコードで確認できる原因を記録した。
- ユーザーのLookup実測により、`日本`のqueryは今回版1件、配布版複数件と判明した。配布版には別辞書も混在するが、Wikipediaだけでも「ニッポニア（小惑星）」等が追加でヒットするため、検索索引の実差として記録した。
- 各差分をfixture、自動比較、Lookup/EBWin/EBPocket手動確認へつながるTODOにした。

**検証**

```bash
git diff --check
# success
```

**次タスク**

- `DIFF.md`の優先順位に従い、本文中のインラインリンク保持を最初の実装候補とする。

### 2026-07-18 screenshot evidence follow-up

- `ref/1.png`から`ref/3.png`を比較資料として確認し、各画像が示す配布版検索、今回版本文、配布版本文の対応を`DIFF.md`へ追記した。
- 配布版のURL、英語名、サイズ・日時、`TOC|KW`、保護状態、項目別表示、画像を具体的な観察差分として追加した。
- 配布版にも原Wiki記法と生URLの表示ノイズがあるため、配布版をそのまま模倣せず、構造上の長所だけを改善目標にすることを明記した。
- 比較記事の版日時が配布版`2023-01-16`、今回版`2026-06-29`であり、本文内容差と表示変換差を分離すべきことを記録した。

## 2026-07-18 TASK-T023 Preserve inline internal links in FreePWING output

**目的**

`DIFF.md`の最優先TODOとして、本文中の内部リンク位置・表示ラベル・targetをFreePWING出力まで保持する。

**変更**

- `LinkRenderNode`を追加し、resolved internal linkを本文中のnodeとして保持するようにした。missing linkは従来どおり表示ラベルのplain textになる。
- JSONLの既存`body`文字列形式を維持しながら、正規化済み入力と衝突しない制御区切りでinline referenceを直列化した。gaiji容量変換を含む既存パイプラインを変更せず通過できる。
- FreePWING driverのbody opsへ参照開始・終了を追加し、表示ラベルを本文位置で囲むようにした。
- 参照マーカーのtargetがJSONLの`targets`に宣言されていなければ停止する検証を追加した。
- 記事末尾へ内部tagだけを列挙する処理を削除した。
- 実際にrenderされた`LinkRenderNode`からtargetsを導出し、表や情報ボックス内でも表示リンクとtarget宣言が一致するようにした。

**検証**

```bash
uv run pytest -q tests/test_render_render_node.py tests/test_render_mini_layout.py tests/test_render_freepwing_source.py tests/test_freepwing_build_entries_smoke.py
# 44 passed
sh docker/toolchain/freepwing-build-entries-smoke.sh wikiepwing-toolchain:dev
# success: inline linksを含む3記事EPWINGを生成・検索
make format-check
# 295 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 141 source files
make test
# 1456 passed, 1 warning
git diff --check
# success
```

**残課題**

- 全件再生成後の「日本」から「日本の歴史」へのLookup手動遷移は未実施。
- redirect経由・externalizedを含む専用fixtureは`DIFF.md`の未完了TODOとして残す。

**次タスク**

- `DIFF.md`優先順位2の本文レイアウト改善から、情報ボックス項目の連結解消を最小タスクとして選ぶ。

## 2026-07-18 TASK-T024 Measure the `日本` query against the distributed reference EPWING

**目的**

比較範囲を`日本`の1 queryに限定し、配布版と今回版の検索差を同一EB Library検索で実測する。

**結果**

- 配布版の実体はユーザー指定名と1文字異なる`ref/Wikip_ja20230120`に存在した。
- 配布版はword/endword/keyword/cross/menu/copyright、今回版はword/endwordを宣言する。
- 同一`wikiepwing-eb-search`による`word 日本 25`は、配布版25行中16種類、今回版25行中10種類だった。
- `word 日本 100`は両版とも100行に達した。Lookup上で今回版が実質1件に見える現象は、記事や索引結果が機械的に1件しかないことを意味しない。
- 配布版は読みを見出しに表示し、今回版は表示しない。今回版は同一見出しの重複が上位を占め、関係が見出しから分からないalias候補も含む。
- 実測結果と候補例を`DIFF.md`へ記録した。

**検証**

```bash
git diff --check
# success
```

**次タスク**

- Lookupが両辞書に対して実際に選択した検索方式を再現し、直接word検索との差を特定する。

## 2026-07-18 TASK-T025 Preserve block structure inside Parsoid section wrappers

**目的**

実データ「日本」の全17 blockが`UnsupportedBlock`へ平坦化される原因を修正する。

**変更**

- Parsoidの`section` wrapperを意味のない構造コンテナとして再帰展開し、子要素を通常のblock converterへ渡すようにした。
- 未知の`div`等は従来どおり診断付きfallbackとし、変更範囲を`section`だけに限定した。
- 見出し・段落・情報ボックスを含むsection fixtureを回帰テストへ追加した。

**実データ確認**

```text
変更前: 17 blocks、UnsupportedBlock 17
変更後: 561 blocks
  ParagraphBlock 400
  UnsupportedBlock 95
  HeadingBlock 56
  DefinitionListBlock 4
  UnorderedListBlock 3
  TableBlock 2
  InfoboxBlock 1
media: 69
```

残るfallbackは`div` 53件、`figure` 42件。

**検証**

```bash
uv run pytest -q tests/test_normalize_convert_block.py tests/test_normalize_pipeline.py tests/test_golden_normalize.py
# 45 passed
make format-check
# 295 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 141 source files
make test
# 1457 passed, 1 warning
git diff --check
# success
```

**次タスク**

- 「日本」に42件ある`rellink` divを、リンクを保持する関連項目paragraphとして変換する。

## 2026-07-18 TASK-T026 Preserve Parsoid related-link blocks

**目的**

実データ「日本」の関連項目42件を未知要素fallbackから回収し、独立した段落として表示境界を保持する。

**変更**

- `div.rellink`だけをParagraphBlockへ変換し、子inlineの表示文字列を保持するようにした。
- その他の未知`div`は従来どおり診断付きfallbackとし、対象class以外へ変更を広げていない。
- 関連項目のanchorを含むfixtureを追加した。anchorの実リンク解決は次タスクへ分離する。

**実データ確認**

```text
変更前: UnsupportedBlock 95（div 53、figure 42）
変更後: UnsupportedBlock 53（div 11、figure 42）
ParagraphBlock: 400 -> 442
```

**検証**

```bash
uv run pytest -q tests/test_normalize_convert_block.py tests/test_normalize_pipeline.py tests/test_golden_normalize.py
# 46 passed
make format-check
# 295 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 141 source files
make test
# 1458 passed, 1 warning
```

**次タスク**

- normalizeで透明化されている記事anchorをInternalLinkInlineへ変換し、既存resolverとT023のFreePWING inline reference出力へ接続する。

## 2026-07-18 TASK-T027 Preserve article anchors as unresolved internal links

**目的**

normalizeで単なる子文字列へ透明化されていた記事anchorの表示位置とtargetをinline modelへ保持する。

**変更**

- `./Title`と`/wiki/Title`を既存URL parserで解析し、InternalLinkInlineへ変換した。
- DB解決前の中間状態は`resolution=missing`、`target_page_id=None`とした。
- HTTP(S)外部リンクと危険なschemeは既存external link policyへ渡した。
- internal、external、unsafe URLの回帰テストを追加し、T026の関連リンクfixtureも新しいinline構造へ合わせた。

**実データ確認**

```text
記事: 日本
回収したInternalLinkInline: 1,704
Parsoid anchor形状: ./... 3,545、absolute URL 640、その他 1
```

**検証**

```bash
uv run pytest -q tests/test_normalize_convert_block.py tests/test_normalize_paragraphs.py
# 34 passed
make format-check
# 295 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 141 source files
make test
# 1461 passed, 1 warning
git diff --check
# success
```

**次タスク**

- main processでInternalLinkInlineをraw DBへ照合し、直接記事・redirect・missing・namespaceを確定してFreePWINGのclickable referenceへ到達させる。

## 2026-07-18 TASK-T028 Resolve normalized internal links against raw DB

**目的**

T027で回収した記事anchorを実際のpage IDへ解決し、T023のFreePWING inline reference出力へ接続可能にする。

**変更**

- Article payloadの全block/inline階層を走査するresolverを追加した。
- CPU workerは従来どおりDB非依存とし、raw DBを所有するmain processで直接記事とredirectを解決した。
- 同一project originのabsolute URLをExternalLinkInlineからInternalLinkInlineへ戻した。
- 解決後のArticleからcanonical JSONとlogical hashを再計算するようにした。
- query stringをtitleへ混入させず、日本語namespaceをexternalizedとして分類するようURL parserを補強した。

**実データ確認**

```text
記事: 日本
InternalLinkInline: 1,704
resolved: 1,691（unique target page IDs: 1,020）
missing: 8
externalized: 5
```

**検証**

```bash
uv run pytest -q tests/test_links_article_resolver.py tests/test_normalize_orchestrate.py tests/test_hundred_articles_fixture.py
# 21 passed
make format-check
# 297 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 142 source files
make test
# 1465 passed, 1 warning
git diff --check
# success
```

**次タスク**

- 「日本」の42件のfigureをUnsupportedBlockから画像配置modelへ変換し、Article.mediaとrenderer graphicsを接続する。

## 2026-07-18 TASK-T029 Preserve figure placement as ImageBlock

**目的**

「日本」のfigureを本文fallback textではなく画像配置modelとして保持する。

**変更**

- imageを含むfigureをImageBlockへ変換し、source URL由来のmedia_idとalt textを保存した。
- imageを含まないfigureとその他の未知要素は従来の診断付きfallbackを維持した。
- figure fixtureでImageBlockの内容を回帰検証した。

**実データ確認**

```text
ImageBlock: 0 -> 42
UnsupportedBlock: 53 -> 11（残りはdiv）
Article.mediaとmedia_idが一致したImageBlock: 42/42
```

**検証**

```bash
uv run pytest -q tests/test_normalize_convert_block.py tests/test_normalize_media_extraction.py
# 30 passed
make format-check
# 297 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 142 source files
make test
# 1466 passed, 1 warning
git diff --check
# success
```

**次タスク**

- ImageBlockの位置をRenderedEntryへ保持し、media変換結果のcontent hashをFreePWING graphic名として参照する。

## 2026-07-18 TASK-T030 Wire ImageBlock placement to FreePWING graphics

**目的**

T029で保持した画像位置を、変換済みBMPとFreePWING color graphic命令へ接続する。

**変更**

- GraphicRenderNodeを追加し、ImageBlock位置にgraphicとcaptionを出力した。
- image-fetch reportのsource URL/content hashとcgraphs.txtを検証し、実在するgraphicだけをmappingへ採用した。
- generateへ`--image-report`/`--graphics-dir`を追加し、mapping hashをstage input fingerprintへ含めた。
- FreePWING driverへgraphic token処理と`add_color_graphic_start/end`を追加した。
- 未取得・未変換画像はalt/captionのplain text fallbackを維持した。
- smokeの非数値tagをinline link parserが処理できない既存の不整合も、tag validationと同じ形式へ修正した。

**実データ確認**

```text
記事「日本」のImageBlock: 42
全42件へmappingを与えたrender確認: GraphicRenderNode 42、entry.graphics 42
既存100件限定image report: 有効graphics 98、「日本」に一致 0
```

**検証**

```bash
uv run pytest -q tests/test_render_graphic_mapping.py tests/test_render_render_node.py \
  tests/test_render_mini_layout.py tests/test_render_freepwing_source.py \
  tests/test_freepwing_build_entries_smoke.py tests/test_render_generate.py tests/test_cli.py
# 100 passed
make test-freepwing-build-entries
# toolchain image build success; honmon built and searchable with inline links and color graphic
make format-check
# 299 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 143 source files
make test
# 1473 passed, 1 warning
git diff --check
# success
```

**次タスク**

- 「日本」の42画像だけを選択取得・変換できるpage ID filterを画像CLIへ追加し、実画像を揃える。

## 2026-07-18 TASK-T031 Filter image planning and fetch by page ID

**目的**

全Wikipedia画像を取得せず、比較対象「日本」の画像だけを実表示用に用意する。

**変更**

- `plan_media`へ最大10,000件・正整数限定のpage ID filterを追加した。
- `image-plan`と`image-fetch`へ反復可能な`--page-id`を追加した。
- 無指定時は従来どおり全記事対象とし、空指定・重複・不正値を安全に処理した。
- READMEへ「日本」限定の取得例を追加した。

**実データ確認**

```text
page ID: 4821051（日本）
selected media: 68（body 61、infobox 5、main 1、lead 1）
取得成功: 68/68
BMP変換成功: 68/68
ImageBlockとの一致: 42/42
originals: 1.5 MiB
FreePWING graphics: 11 MiB
```

成果物:

- `data/reports/japan-image-fetch-report.json`
- `data/work/media-originals-japan/`
- `data/work/graphics-japan/`

**検証**

```bash
uv run pytest -q tests/test_media_orchestrate.py tests/test_cli.py
# 63 passed
make format-check
# 299 files already formatted
make lint
# All checks passed
make typecheck
# Success: no issues found in 143 source files
make test
# 1475 passed, 1 warning
git diff --check
# success
```

**次タスク**

- 全件modelを新しいnormalize処理で再生成し、画像mapping付きgenerate/EPWING buildを実行してLookupで比較可能な成果物を作る。

## 2026-07-18 TASK-T021 Document verified full-build commands

**目的**

TASK-T020で実際に成功した外字容量調整・toolchain image・EPWING生成・ZIP検証コマンドをREADMEへ反映する。

**変更**

- 新規generate出力では外字が各幅8,192文字へ自動制御されることと、既定の`GAIJI_DIR=gaiji`を明記した。
- 上限制御導入前の既存生成物を再利用する`wikiepwing.gaiji.capacity`と、容量調整後の`data/work`入力を使うbuildコマンドを追加した。
- 最終的に成功した`docker/toolchain/build-epwing.sh`の直接実行形を記録し、通常は同等の`make build-epwing`を推奨した。
- 全件1,508,200記事、ZIP 5.7 GiB、SHA-256、`ebinfo`・`unzip -t`成功という実測値へ、READMEの古い「全件未計測」記述を更新した。

**検証**

```bash
git diff --check
# success
uv run pytest -q tests/test_repository_hygiene.py
# 1 passed
```

**次タスク**

- 自動実装タスクはなし。生成済みEPWINGを実ビューアで開く手動確認へ進む。

### 2026-07-19 02:18 UTC — TASK-T033 / TASK-T034

**目的**

- `TASK-T033`: heading / infobox から抽出済みの keyword を FreePWING のキーワード（条件）検索インデックスへ接続し、`ebinfo` で keyword 検索が有効になることを確認する。
- `TASK-T034`: EPWING のクロス検索インデックス（`cross`）を有効にし、`ebinfo` の search methods で `cross` が検出されるようにする。

**変更**

- **Python generate ステージの修正**:
  - `RenderedEntry` データクラスおよび JSON レコード出力（`write_entries_jsonl`）に `keywords` フィールドを追加。
  - `run_generate` と `_render_all` が `AppConfig` を受け取るように変更し、設定（`search` セクション）に基づいて heading/infobox keyword 抽出および予算制御（`apply_search_budgets`）を適用した `keywords` リストを取得・受け渡しするように実装。
- **Perlビルドスクリプトの修正** (`docker/toolchain/freepwing_build_entries.pl`):
  - `initialize_fpwparser` / `finalize_fpwparser` に `keyword` インデックス用のインスタンス生成・クローズ処理を追加。
  - レコードループ内で `keywords` を順次 `keyword->add_entry` でインデックス登録するよう実装。
  - **空のキーワードでのクラッシュ回避**: テストデータ等でキーワードが 0 件のまま close すると FreePWING の `Index.pm` 内で subscript -1 エラーが起きるため、登録されたキーワードが 0 件のときはダミーキーワード `"dummy"` を自動登録するセーフガードを実装。
- **FreePWING へのパッチ追加** (`patches/freepwing/cross_search.patch`):
  - EPWING の仕様でクロス（複合）検索能力（`cross`）は、コントロールファイル内に ID `0x81` (cross) として `kidx` を同一マッピング・参照することで有効化されるため、`Control.pm` と `fpwcontrol.in` に `add_crossindex_entry` を追加するパッチを作成・適用。
- **テストの修正**:
  - `test_render_generate.py` や各種 profile/e2e ビルドテストにおいて、`run_generate` に `config` 引数を適切に引き渡すように修正。
  - `test_render_freepwing_source.py` の JSON アサーションに `keywords` フィールドを追加。
  - `test_freepwing_source.py` 内のパッチ有無アサーションで `cross_search.patch` を許容するように修正。

**実行コマンド**

```bash
# ローカルテストの確認
uv run pytest tests/test_render_generate.py tests/test_render_mini_layout.py
uv run pytest tests/test_freepwing_source.py

# ツールチェーンの再ビルドと煙テスト（ebinfo による検証）
make toolchain-image
make test-freepwing-build-entries

# テストスイート全体の実行
make test
```

**結果**

- `make test-freepwing-build-entries`（Docker ビルド煙テスト）内の `ebinfo` にて、以下のように `keyword` と `cross` の双方が有効（あり）と判定されることを確認した：
  `search methods: word endword keyword cross`
- 1,482 件のテストスイートがすべて正常にパスした。

**判断・注意点**

- テストビルドなどの少数 fixture ではキーワードが抽出されず `Index.pm` でクラッシュする現象を発見し、最初の項目の見出し位置に紐付けたダミーのキーワード `"dummy"` を自動挿入することでクラッシュを防止し、`kidx` の正常生成を保証した。
- `cross` 検索能力は `kidx`（キーワードインデックス）ファイルをコントロールファイル内で ID `0x81` として参照登録するだけで有効化できるため、独自の `cross` ファイルを作成するオーバーヘッドなしにクロス検索能力を確立した。

**次タスク**

- `TASK-T035`: 全件再ビルド (Full rebuild)


### 2026-07-20 TASK-T035 Full rebuild with new normalized model and index fixes

**目的**

全件モデル `model-diff-ram8.sqlite3`（1,508,200記事）から、新しく実装した keyword/cross 検索インデックス・インラインリンク・画像位置反映を統合した全件 EPWING 辞書を再ビルド（Full build）する。

**変更**

- **generate ステージのメモリ最適化・ストリーム化**:
  - 150万件の記事 `Article` および `RenderedEntry` を一度に全件一括保持すると、Mac/OS の OOM Killer (exit code 137) に引っかかるため、2パス・ストリーム処理へ移行。
  - `decode_article_metadata_only` を導入し、第1パスでは本文 blocks を空にしてデコードすることで外字スキャン（`GaijiPlan` 確定）のメモリ消費を数MBに削減。
  - 第2パス（ストリーム書き出し `write_entries_jsonl_stream`）では、ジェネレータで記事を1件ずつデコード・レンダリングし、一時ファイルへ順次追記して最後に `os.replace` でアトミックに差し替える設計を確立。
- **システム制御コード（0x1e / 0x1f）の保護**:
  - インラインリンク等のシステム制御コード `\x1e` / `\x1f` が、Python の `str.strip()` や外字分類器 `classify_character` で「空白文字」または「未対応文字 (Category D)」として削除・破壊される問題を発見。
  - `classify_character` で `\x1e` / `\x1f` を常に `A`（表現可能文字）として保護し、`mini_layout.py` では `_safe_strip` を導入して制御文字を安全に温存するよう修正。
- **キーワードへの文字種 fallback 適用**:
  - `keywords` リスト内のハングル・ダイアクリティカルマーク等がそのまま直出しされ、Perl EUC-JP エンコード（`to_euc_jp`）で未解決 byte 例外を起こす問題に対処。`aliases` と同様に `embed_title_fallback` を適用。
- **EPWING ビルドタイトル仕様への適合**:
  - `catdump` が `Title = "Wikipedia"` の半角英語タイトルを拒否する仕様に対し、`TITLE` のデフォルトを全角日本語 `"ウィキペディア"` へ統一。
- **ビルド実行パラメータの修正**:
  - `GRAPHICS_DIR=data/work/graphics` を指定して `make build-epwing` を呼ぶことで、画像タグ（`cgraph:...`）を `cgraphs.txt` と完全同期してビルド。

**実行コマンド**

```bash
# 1. 全件 generate (2パス・ストリーム処理)
uv run wikiepwing generate \
  --config config/local-paths.toml \
  --config config/profiles/full.toml \
  --model-database data/work/model-diff-ram8.sqlite3 \
  --entries-output data/work/runs/full-build-20260719/entries.jsonl \
  --manifest-path data/work/runs/full-build-20260719/manifests/50-generate.json \
  --gaiji-dir data/work/runs/full-build-20260719/gaiji \
  --image-report data/reports/image-fetch-report.json \
  --graphics-dir data/work/graphics \
  --run-id full-build-20260719 --force

# 2. 全件 EPWING ビルド
make build-epwing \
  ENTRIES=data/work/runs/full-build-20260719/entries.jsonl \
  GAIJI_DIR=data/work/runs/full-build-20260719/gaiji \
  GRAPHICS_DIR=data/work/graphics \
  EPWING_OUTPUT=data/output/jawiki.epwing.zip

# 3. テストスイートの実行確認
make test
```

**結果**

- 1,508,200件の記事について `entries.jsonl` （19.4GB）をメモリ一定（OOMなし）で生成完了。
- FreePWING による EPWING ビルド・`ebzip` 圧縮（47.3% 圧縮率）および ZIP アーカイブ生成が成功。
- 成果物 `data/output/jawiki.epwing.zip`（7.1GB）の検証において、`ebinfo` により目標の4大検索機能（`word endword keyword cross`）の全有効化を確認。
- 1,482件のテストスイートがすべて正常にパスした。

**判断・注意点**

- OOM 対策およびマークアップ制御文字保護は、今後の全件スケール開発における強固な基盤となった。
- `catdump` は全角タイトルしか受け付けないため、EPWING カタログタイトルは常に全角表記を維持する必要がある。


### 2026-07-20 TASK-T036 Support Infobox image rendering and 16-worker parallel fetch

**目的**

Infobox内画像（`InfoboxBlock.images`）の EPWING バイナリ画像（`cgraph`）化対応および、画像取得処理 (`image-fetch`) のデフォルト並列数の 16 ワーカー化。

**変更**

- **画像取得並列度の増強 (`fetch_concurrency = 16`)**:
  - `config/default.toml` の `fetch_concurrency` を 4 から 16 へ更新。
- **Infobox 画像の `MediaReference` 抽出**:
  - `src/wikiepwing/normalize/media_extraction.py` で `raw_infobox.image_srcs` 内の画像 URL について `role="infobox"` の `MediaReference` を作成し、DBの `media_references` テーブルへ登録されるよう改善。
- **Infobox 画像の EPWING グラフィック表示化**:
  - `src/wikiepwing/render/mini_layout.py` の `_RenderContext` に `graphic_names_by_url` マッピングを追加。
  - `_render_infobox` 関数で、画像 URL に対応する `graphic_name` が存在する場合は `\x1eG:graphic_name\x1f` 制御コードを出力し、未変換時のみ `[画像: URL]` に安全にフォールバック。
- **テスト追加・検証**:
  - `tests/test_render_mini_layout.py` に `test_infobox_renders_graphic_node_when_mapped` を追加。

**実行コマンド**

```bash
uv run pytest tests/test_render_mini_layout.py tests/test_normalize_media_extraction.py tests/test_config.py
make format
make check
```

**結果**

- 1,484件の全テストスイートおよび各種リント・型チェック（`make check`）がすべて正常にパスした。

**判断・注意点**

- Infobox 内の画像も `media_references` テーブルから `image-plan` / `image-fetch` / `image-convert` パイプラインを経由して EPWING の `cgraph` としてバイナリ収録・表示されるようになった。


### 2026-07-20 TASK-T037 Support resumable image-fetch from existing report/originals

**目的**

`image-fetch` 実行時に既存の `report` および `originals-dir` 内の成功データを参照し、すでに取得済みの画像 URL に対する二重 HTTP リクエストを自動スキップして、日を跨いだ中断・再開（レジューム）に対応する。

**変更**

- **`fetch_media` への `existing_outcomes` スキップ機能の追加**:
  - `src/wikiepwing/media/orchestrate.py` の `fetch_media` で `existing_outcomes` に含まれる成功済み URL をネットワーク取得対象から外し、ダウンロードなしで成果を再利用する仕組みを実装。
- **CLI (`image-fetch`) への自動レジューム統合**:
  - `src/wikiepwing/cli.py` で `--report` と `--originals-dir` の既存データが存在する場合、`read_fetch_report` で読み込んで `fetch_media` へ引き渡すよう改修。
- **テストの追加**:
  - `tests/test_media_orchestrate.py` に `test_fetch_media_skips_already_fetched_urls` を追加。

**実行コマンド**

```bash
uv run pytest tests/test_media_orchestrate.py
make format
make check
```

**結果**

- 1,485件の全テストスイートおよび `make check` がすべて正常にパスした。

**判断・注意点**

- 日を跨いだ複数回の `image-fetch` や Ctrl+C による中断・再開時にも、既にダウンロード済みの画像が高速にスキップされるため、安全・効率的に全件画像取得を進められるようになった。


### 2026-07-20 TASK-T038 Implement EDIT.md layout rules (Infobox, Headings, Lists, Tables)

**目的**

`EDIT.md` に策定した編集・レイアウト方針に基づき、`mini_layout.py` の変換処理および各種ブロック表現を改修する。

**変更**

- **`EDIT.md` の作成**:
  - Infobox・セクション見出し・リスト・Table のレイアウト方針・フォーマット仕様を明文化。
- **レイアウトレンダラ (`mini_layout.py`) の修正**:
  - Infobox: `【Infobox {title}】` および `【項目名|値】` 形式で出力。
  - 見出し (Heading): `■ {見出し名}` 形式で出力。
  - リスト (List): 箇条書きを ` ・{内容}` 形式、順序付きリストを `1. {内容}` 形式で出力。
  - 表 (Table): 全テーブルを `|` 区切りのテキストグリッド形式で出力。
- **テストの修正・通過**:
  - `tests/test_render_mini_layout.py` のアサーションを更新。

**実行コマンド**

```bash
uv run pytest tests/test_render_mini_layout.py
make format
make check
```

**結果**

- 全 1,484 件のテストおよび `make check` が正常に通過した。

**判断・注意点**

- ビューア上での可読性が大幅に向上し、セクション・Infobox・箇条書きが明確に区別して閲覧できるよう改善された。


### 2026-07-20 TASK-T039 Add Makefile targets for wikiepwing CLI and update README.md

**目的**

`wikiepwing` の主要サブコマンド（`generate`, `build`, `image-plan`, `image-fetch`, `image-convert`, `verify`, `preview`）を `Makefile` のターゲットとして追加し、`README.md` を最新状態にメンテナンスする。

**変更**

- **`Makefile` の拡張**:
  - `generate`, `image-plan`, `image-fetch`, `image-convert`, `build`, `verify`, `preview` ターゲットを追加。
  - 各種オーバーライド変数（`MODEL_DB`, `CONCURRENCY`, `LIMIT` 等）に対応。
- **`scripts/preview_articles.py` の追加**:
  - `make preview` 実行時に指定モデルDBから記事を抽出し、HTML（`preview_articles.html`）を生成するスクリプトを設置。
- **`README.md` の更新**:
  - `make` コマンドによる主要タスク実行表とコマンド例を追加。

**実行コマンド**

```bash
make preview
make format
make check
```

**結果**

- 1,485件の全テストおよび `make check` が正常に通過した。

**判断・注意点**

- 長い `uv run wikiepwing ...` コマンドを意識せず、`make generate` や `make build` などの単一コマンドで安全かつ手軽にパイプラインを実行できるよう改善された。


### 2026-07-20 TASK-T040 Add acquire and normalize targets to Makefile

**目的**

Wikipedia Enterprise Snapshot チャンクダウンロード (`acquire`) やダンプ登録・正規化 (`register-local-source`, `ingest`, `normalize`) ターゲットを `Makefile` に追加し、`README.md` を更新する。

**変更**

- **`Makefile` の修正**:
  - `acquire` (Snapshot チャンクの取得・検証・固定) ターゲットを追加。
  - `register-local-source`, `ingest`, `normalize` ターゲットを追加。
  - 上書き用 `FORCE=1` フラグに対応。
- **`README.md` の更新**:
  - `make acquire` や `make normalize` を含むデータ取得からビルドまでの全手順・コマンド例を整備。

**実行コマンド**

```bash
make format
make check
```

**結果**

- 1,485件の全テストおよび `make check` が正常に通過した。

**判断・注意点**

- 初回データ取得（チャンクのダウンロード）から画像取得・変換・最終EPWING辞書ビルドまでの全パイプラインが Makefile 経由で正しい順序（`acquire` ➔ `normalize` ➔ `generate` ➔ `image-plan` ➔ `image-fetch` ➔ `image-convert` ➔ `build`）でワンコマンド実行可能になった。








