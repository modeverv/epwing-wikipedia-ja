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

## 想定コマンド

```bash
make image
make doctor
make test

# 入力の取得
make acquire PROJECT=jawiki SNAPSHOT=latest

# 小規模fixtureの生成
make fixture-build PROFILE=mini

# 固定済み入力から生成
make build PROJECT=jawiki PROFILE=full

# 成果物検証
make verify
```

CLIの最終形:

```bash
wikiepwing doctor
wikiepwing source acquire --project jawiki --snapshot latest
wikiepwing source inspect
wikiepwing reference scan /reference/boookends-2023
wikiepwing build --profile mini
wikiepwing build --profile lite
wikiepwing build --profile full
wikiepwing verify
wikiepwing compare-reference
wikiepwing report
```

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

公開配布を行う前に、画像帰属情報と再配布条件を確認してください。
