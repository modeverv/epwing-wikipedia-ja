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
