# CURRENT_TASK.md

## Task ID

TASK-T018

## 目的

ユーザーが列挙したnormalize以降の主要CLI・toolchainコマンドを監査し、実データ規模で長時間になり得る無表示区間へ進捗表示を追加する。

対象コマンド:

- `normalize`
- `generate`
- `verify-raw`
- `verify`
- `image-plan`
- `image-fetch`
- `image-convert`
- `make toolchain-image`
- `make build-epwing`

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] TASK-T017でingest前後の進捗表示がコミット済みであることを確認した

## 変更予定ファイル

- 対象CLI/orchestrator/toolchainのうち監査で無表示区間が確認されたファイル
- 対応するテスト
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest -q <変更箇所の局所テスト>
make format-check
make lint
make typecheck
make test
git diff --check
```

Docker/toolchainに変更がある場合は対応smoke testも実行する。

## 完了条件

- [x] 各対象コマンドの重い処理区間と既存進捗表示をコードから確認する
- [x] 長時間になり得る無表示区間へbounded-frequencyの進捗表示を追加する
- [x] 短時間処理でもフェーズ開始または完了が確認できる
- [x] 対応テストと標準検証が成功する
- [x] 対象変更だけをコミットする

## 結果

- Python CLI群は共通のフェーズ進捗型とCLI reporterを使い、ファイルfingerprint、SQLite検査、全件走査、JSON変換・書き込み、画像ファイルI/Oを可視化した。
- `toolchain-image`はBuildKit自身の進捗表示が継続していることを実行確認した。
- `build-epwing`はFreePWING/EBの各外部コマンド前後へフェーズ表示を追加し、隔離したコミット版パーサーによる実ビルドでZIP出力まで確認した。
- 作業中に別途現れた`docker/toolchain/freepwing_build_entries.pl`等の未コミット変更と生成物は、本タスクのコミットから除外する。

## 非対象

- 各処理のアルゴリズム・出力形式・並列度の変更
- ingest再実行スキップ仕様の変更
- フルWikipediaデータを使った破壊的な再生成
