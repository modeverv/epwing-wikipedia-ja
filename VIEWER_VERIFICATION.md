# VIEWER_VERIFICATION.md

生成した`entries.jsonl`から実際にEPWINGバイナリ(honmon)をビルドし、代表的なビューアで確認するための手順です。COMPATIBILITY.md 7(Viewer compatibility)の記録項目・Pass ruleに対応します。

**現状**: 本書執筆時点で、実際にEPWINGバイナリまでビルド・ビューア確認済みなのは3記事の手作りフィクスチャと100記事フィクスチャのみです(`docker/toolchain/handcrafted-three-entry-smoke.sh`、`docker/toolchain/mini-end-to-end-smoke.sh`)。jawiki全件規模の`entries.jsonl`(TASK-R005/R008/R009で生成済み)からのEPWINGバイナリビルドと、実ビューアでの確認はまだ実施していません。本書は、それを行うための手順を示します。

---

## 1. EPWINGバイナリのビルド

### 1.1 ツールチェーンイメージの用意

```bash
docker build -f docker/toolchain.Dockerfile -t wikiepwing-toolchain:dev .
```

このイメージにはFreePWING(`docker/toolchain/build-freepwing.sh`でビルド)とEBライブラリ(`docker/toolchain/build-eb.sh`)が含まれます。

### 1.2 小規模フィクスチャでの実行例(既に検証済み)

```bash
docker/toolchain/handcrafted-three-entry-smoke.sh    # 3記事の手作りフィクスチャ
docker/toolchain/mini-end-to-end-smoke.sh            # 100記事フィクスチャ(register-local-source→ingest→normalize→generate→freepwing_build_entries.pl→wikiepwing-eb-search)
docker/toolchain/lite-100-article-smoke.sh           # Lite 100記事版
```

これらは`docker/toolchain/freepwing_build_entries.pl`(FreePWINGのソースビルドスクリプト)を使って`entries.jsonl`からhonmonを実際にビルドし、`wikiepwing-eb-search`/`wikiepwing-eb-entry`(`docker/toolchain/eb-search.c`/`eb-entry.c`)で検索・エントリ取得ができることまで確認します。

### 1.3 全件規模での実行(未実施、これから行う場合の手順)

上記スモークテストのスクリプトを参考に、`entries.jsonl`(BUILD.mdの手順で生成したもの、jawiki全件で約13GB)を入力として同じ`freepwing_build_entries.pl`呼び出しに置き換えます。Lite/Full向けにはgraphics(`image-convert`で生成した`*.bmp`+`cgraphs.txt`)も必要です。全件規模では、ビルド時間・ディスク容量(honmonファイル自体のサイズ)を事前に見積もってください。

---

## 2. 対象ビューア(COMPATIBILITY.md 7.1)

| ビューア系統 | 入手方法の例 | 備考 |
|---|---|---|
| EBWin系 | Windows用。EBWin4等 | GUIビューア。検索・本文表示・画像表示を確認 |
| EBPocket系 | Android/iOS用アプリ | モバイル環境での表示・検索を確認 |
| Emacs Lookup/lookup.el系 | `lookup.el`(Emacs Lisp package) + `eblook`または本プロジェクトの`wikiepwing-eb-search`アダプタ | テキストベースでの検索・本文表示を確認。CUI/Emacs環境での動作確認に向く |

いずれも本プロジェクトのCIやこのビルド環境には含まれていません。実機・別マシンでのインストールが必要です。

---

## 3. 確認項目とPass rule(COMPATIBILITY.md 7.2/7.3)

### 3.1 記録項目(ビューア・profileの組み合わせごとに記録)

```text
viewer name
viewer version
OS/version
artifact profile
artifact hash
search mode
result
known issue
screenshot reference path (optional, not source-controlled if large)
verified date
```

### 3.2 Pass rule

- **Mini**: 2つ以上のビューア系統で、title search / body / internal linkが確認できること
- **Lite**: 2つ以上のビューア系統で、image / gaiji / mathの主要sampleが確認できること
- **Full**: PLAN.md 27(Phase 23、全件Full candidate)の基準に従う

### 3.3 記録テンプレート例

```text
## Mini profile

- viewer: EBWin4 x.y.z / Windows 11
  artifact profile: mini
  artifact hash: <BUILD-INFO.jsonのentry logical hash>
  search mode: title exact
  result: pass/fail
  known issue: (あれば)
  verified date: YYYY-MM-DD

- viewer: lookup.el (Emacs xx.y) + wikiepwing-eb-search
  ...
```

実際の確認結果は、大きなスクリーンショット等をリポジトリにコミットせず、別途保存してパスだけ記録してください(COMPATIBILITY.md 7.2の「not source-controlled if large」に対応)。

---

## 4. 関連ドキュメント

- 成果物の生成手順: [BUILD.md](BUILD.md)
- 既知の問題と対処: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Viewer compatibilityの詳細な出口条件: [COMPATIBILITY.md](COMPATIBILITY.md) 7
