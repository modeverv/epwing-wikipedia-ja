# Wikipedia EPWING Builder v2

2026年時点の日本語Wikipediaを、Docker内で再現可能にEPWING/JIS X 4081互換辞書へ変換するプロジェクトです。

Boookends 2023年版を表示・検索品質の参照実装として利用しますが、Boookendsのソースやブランドを複製するものではありません。目標は、現行データから同等クラスの利用体験を持つ独立実装を作ることです。

## 目標

- 現行の日本語Wikipedia記事をオフライン検索できる
- 見出し語、リダイレクト、別名、内部リンクを利用できる
- 表、Infobox、数式、代表画像を読みやすく変換できる
- Mini / Lite / Fullの3プロファイルを生成できる
- Dockerだけで同じ入力から同じ論理内容を再生成できる
- 失敗記事や未対応構造を集計・追跡できる
- EBWin、EBPocket、Emacs Lookupなどで検証できる

## 入力方針

標準経路はWikimedia Enterprise通常Snapshotのレンダリング済みHTMLです。取得後はローカルへ固定し、後続処理をオフラインで実行します。

補助・検証経路として、Wikimedia公式のXML/SQLダンプを利用します。

Structured Contents Snapshotは日本語Wikipediaを対象としていないため、v2の必須入力にはしません。

## 最初に読む文書

実装エージェントは次の順で読みます。

1. `AGENTS.md`
2. `MEMORY.md`
3. `LOG.md`
4. `CURRENT_TASK.md`
5. `TASKS.md`の対象タスク

人間が全体像を確認する場合:

1. `ARCHITECTURE.md`
2. `COMPATIBILITY.md`
3. `PLAN.md`
4. `TESTING.md`
5. `CONFIG_REFERENCE.md`
6. `BUILD.md`(実際にビルドする手順)
7. `TROUBLESHOOTING.md`(実行時に遭遇しうる問題と対処)
8. `VIEWER_VERIFICATION.md`(ビューアでの確認手順)
9. `LICENSING.md`(ライセンス・帰属情報)
10. `RELEASE_CHECKLIST.md`(v1.0 Definition of Doneの評価)

## 想定リポジトリ構成

```text
wikipedia-epwing-v2/
├── AGENTS.md
├── ARCHITECTURE.md
├── PLAN.md
├── TASKS.md
├── TESTING.md
├── COMPATIBILITY.md
├── CONFIG_REFERENCE.md
├── BUILD.md
├── TROUBLESHOOTING.md
├── VIEWER_VERIFICATION.md
├── LICENSING.md
├── RELEASE_CHECKLIST.md
├── DECISIONS.md
├── CURRENT_TASK.md
├── LOG.md
├── MEMORY.md
├── README.md
├── Makefile
├── compose.yaml
├── pyproject.toml
├── uv.lock
├── config/
├── docker/
├── migrations/
├── patches/
├── src/wikiepwing/
├── tests/
├── scripts/
├── output/
└── reports/
```

## 実際のコマンド

以下は実際に動作するコマンドです(詳細は[BUILD.md](BUILD.md)を参照)。「想定」ではなく、実データ全件規模(EPIC R/S)で検証済みです。

### 0. 事前準備(初回のみ)

```bash
# 認証情報の読み込み(.envは自動読み込みされないため毎回明示的に行う)
set -a
source .env
set +a
```

`config/default.toml`の`[paths]`は`/data/...`をデフォルトにしており、これはDockerコンテナ内を前提としたパスです。**macOSホストでネイティブ実行する場合は、実在するディレクトリを指す`--config`上書きファイルが必須です。** 例えばリポジトリ直下の`data/`(`.gitignore`済み)を使う場合:

```toml
# config/local-paths.toml (例、各自のパスに合わせて用意する)
schema_version = 1
project = "jawiki"
profile = "lite"

[paths]
sources = "../data/sources"
reference = "../data/reference"
work = "../data/work"
cache = "../data/cache"
output = "../data/output"
reports = "../data/reports"
logs = "../data/logs"
```

（`[paths]`の相対パスは、このTOMLファイル自身のディレクトリ`config/`からの相対で解決されるため、リポジトリ直下の`data/`を指すには`../data/...`と書きます。）

以降のコマンドはすべて`--config config/local-paths.toml`(または自分で用意した上書きファイル)を付けて実行してください。

```bash
mkdir -p data/{sources,reference,work,cache,output,reports,logs}
uv run python -m wikiepwing.cli doctor --config config/local-paths.toml
```

### 1. パイプライン本体

```bash
make test
make check          # format-check + lint + typecheck + test

# Snapshotの取得
uv run python -m wikiepwing.cli acquire --config config/local-paths.toml \
  --namespace 0 --snapshot-version latest --git-commit "$(git rev-parse HEAD)"

# 取り込み→正規化→生成(3ステージ個別、または build でまとめて)
uv run python -m wikiepwing.cli ingest --config config/local-paths.toml \
  --lock-path <source.lock.json> --git-commit "$(git rev-parse HEAD)"
uv run python -m wikiepwing.cli normalize --config config/local-paths.toml \
  --git-commit "$(git rev-parse HEAD)"
uv run python -m wikiepwing.cli generate --config config/local-paths.toml --config config/profiles/mini.toml \
  --entries-output entries-mini.jsonl --git-commit "$(git rev-parse HEAD)"

# 検証
uv run python -m wikiepwing.cli verify-raw --raw-database data/work/raw.sqlite3
uv run python -m wikiepwing.cli verify --entries entries-mini.jsonl

# Lite/Full向け画像パイプライン
uv run python -m wikiepwing.cli image-plan --model-database data/work/model.sqlite3
uv run python -m wikiepwing.cli image-fetch --config config/local-paths.toml --config config/profiles/lite.toml \
  --model-database data/work/model.sqlite3 --originals-dir <dir> --report <report.json>
# 並列度・件数上限を指定する場合(既定は images.fetch_concurrency=4、上限なし)
uv run python -m wikiepwing.cli image-fetch --config config/local-paths.toml --config config/profiles/lite.toml \
  --model-database data/work/model.sqlite3 --originals-dir <dir> --report <report.json> \
  --concurrency 4 --limit 1000
uv run python -m wikiepwing.cli image-convert --originals-dir <dir> --report <report.json> \
  --cache-dir <cache> --graphics-dir <graphics>

# 実際にEPWINGバイナリ(.epwing.zip)をビルドする
make build-epwing ENTRIES=entries-mini.jsonl TITLE="日本語Wikipedia" EPWING_OUTPUT=output/jawiki.epwing.zip
# 画像/gaijiがある場合: GRAPHICS_DIR=<graphics> GAIJI_DIR=<gaiji> も指定する

# 運用コマンド
uv run python -m wikiepwing.cli disk-usage --config config/local-paths.toml
uv run python -m wikiepwing.cli clean --config config/local-paths.toml --keep-runs 2
uv run python -m wikiepwing.cli update --config config/local-paths.toml
```

`--config`は複数回指定でき、後勝ちで合成されます。パス上書き(`config/local-paths.toml`)とプロファイル(`config/profiles/*.toml`)は別ファイルなので、両方必要なコマンドには両方渡してください。詳細は[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) section 20を参照してください。

CLIサブコマンド一覧は`uv run python -m wikiepwing.cli --help`で確認できます。`wikiepwing`は現時点でPythonパッケージのエントリポイント(`uv run python -m wikiepwing.cli` または`pip install`後は`wikiepwing`コマンド)として提供され、`make`のサブコマンド化(`make acquire`等)はまだ行っていません。

`make build-epwing`が呼ぶ`docker/toolchain/build-epwing.sh`は、`entries.jsonl`から実際にEPWING本体(HONMON)をビルドする本番用スクリプトです。小規模(3記事・100記事)フィクスチャでは動作確認済みですが、日本語Wikipedia全件規模での実行時間・成果物サイズはまだ計測していません([TROUBLESHOOTING.md](TROUBLESHOOTING.md)参照)。

`image-fetch`は`upload.wikimedia.org`への逐次ダウンロードだと約250万ユニークURL全件で4〜12日かかる想定です(詳細は[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)参照)。`--concurrency`(既定: `images.fetch_concurrency`、既定値4)で相手サーバーに配慮した範囲の並列ダウンロードができ、`--limit N`を指定すると先頭N件のユニークURLを取得した時点で打ち切れます。画像が一部しかない状態でも`image-convert`以降・EPWINGビルドまで一通り動作確認したい場合は`--limit`を使ってください。

## 開発順序の最重要ルール

最初からWikipedia全件を処理しません。

1. Docker内で3記事の手作りEPWINGを作る
2. Boookends 2023版を読み取る参照検査器を作る
3. 10記事fixtureをHTMLから中間モデルへ変換する
4. 100記事fixtureをMini EPWINGへ変換する
5. 表・Infobox・外字・画像・数式を段階的に追加する
6. 10,000記事試験を通す
7. 最後に全件ビルドを行う

## ライセンス

プログラムのライセンスと、生成辞書に含まれるWikipedia本文・画像のライセンスは別です。生成物には入力Snapshot、Wikipediaライセンス、画像帰属情報、ビルドツール情報を含めます。

公開配布を行う前に、画像帰属情報と再配布条件を確認してください。詳細は[LICENSING.md](LICENSING.md)を参照してください。
