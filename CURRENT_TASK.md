# CURRENT_TASK.md

## Task ID

TASK-T001

## 目的

`TASKS.md`のTASK-T001(Build guide、依存: R006完了済み)を実施する。実データ全件規模(EPIC R: R001〜R009、EPIC S: S001〜S005)で実際に検証済みの手順に基づき、`wikiepwing`でjawiki EPWING辞書をビルドする手順を`BUILD.md`としてまとめる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-T001(依存: R006、完了済み)を読んだ
- [x] 既存のトップレベルドキュメント(`README.md`, `CONFIG_REFERENCE.md`, `TESTING.md`等)に`BUILD.md`相当のものが無いことを確認した
- [x] EPIC R/Sで実際に実行し検証済みの実コマンド(acquire→ingest→normalize→generate→verify、image-plan/fetch/convert、doctor/preflight、disk-usage/clean/update)を土台にする方針にした
- [x] `CONFIG_REFERENCE.md`のsection 20(プロファイル別設定合成例)と内容が重複しないよう、`BUILD.md`はパイプライン全体の手順(何をどの順で実行するか)に集中し、設定ファイルの詳細は`CONFIG_REFERENCE.md`を参照する形にした

## 変更予定ファイル

- `BUILD.md`(新規)
- `README.md`(「人間が全体像を確認する場合」の読む順にBUILD.mdを追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
# ドキュメント内のコマンド例が実際のCLIヘルプと一致することを確認
uv run python -m wikiepwing.cli --help
uv run python -m wikiepwing.cli doctor --help
```

## 完了条件

- [x] `BUILD.md`に前提条件(認証情報、ディスク容量、Docker/ネイティブの選択肢)を記載した
- [x] `BUILD.md`にacquire→ingest→normalize→generate→verifyの手順を記載した(EPIC Rで実際に使ったコマンドと整合)
- [x] `BUILD.md`にLite/Full向けの画像パイプライン(image-plan/image-fetch/image-convert)手順を記載した
- [x] `BUILD.md`にfull build前ゲート(doctor/preflight)への言及を含めた
- [x] `BUILD.md`に運用コマンド(disk-usage/clean/update)への言及を含めた
- [x] ドキュメント内のCLIフラグ例が実際の`--help`出力と一致することを確認した(全13コマンドの`--help`出力と突き合わせ済み)
- [x] `README.md`から`BUILD.md`への導線を追加した

## 非対象

- Troubleshooting(TASK-T003)
- Viewer verification guide(TASK-T004)
- Licensing/attribution guide(TASK-T005)
- 実際のEPWINGバイナリ(honmon)ビルド手順の詳細(`docker/toolchain`側の話で、まだ全件規模では実施していないため概要のみ触れる)

## 実施結果

`BUILD.md`(新規)を作成した。前提条件(認証情報、ディスク容量、Docker/ネイティブ、ImageMagick)、実行前チェック(`doctor`)、Snapshot取得(`acquire`)、パイプライン本体(`ingest`→`normalize`→`generate`、または`build`でまとめて)、検証(`verify-raw`/`verify`)、Lite/Full向け画像パイプライン(`image-plan`/`image-fetch`/`image-convert`)、Docker実行時の注意(Docker Desktopのメモリ割り当て、TASK-S005で実際に踏んだ問題)、運用コマンド(`disk-usage`/`clean`/`update`)、再現性確認(`compute_logical_build_hash`)の8セクションで構成した。

すべての章はEPIC R(R001〜R009)・EPIC S(S001〜S005)で実際に実行・検証済みのコマンドと知見に基づいて書いた(推測での記述はしていない)。特に重要な実データ発見事項を明記した:
- `generate`コマンドはプロファイル設定を一切参照しないため、Mini/Lite/Fullで`entries.jsonl`の内容は同一になる(TASK-R008/R009)。プロファイル差は`normalize`時点のメディア選択にのみ表れる。
- `image-fetch`は逐次ダウンロードで、jawiki全件の約250万ユニークURLでは数日規模になる(TASK-R007)。
- Docker実行時、Docker Desktopの既定メモリ割り当て(約8GB)では全件`generate`がOOMする(TASK-S005)。

ドキュメント中の全13サブコマンド(`doctor`, `acquire`, `ingest`, `normalize`, `generate`, `build`, `verify-raw`, `verify`, `image-plan`, `image-fetch`, `image-convert`, `disk-usage`, `clean`, `update`)のCLIフラグ例を実際の`--help`出力と突き合わせて一致を確認した。`README.md`の「人間が全体像を確認する場合」の読む順と想定リポジトリ構成に`BUILD.md`を追加した。コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。
