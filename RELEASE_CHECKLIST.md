# RELEASE_CHECKLIST.md

PLAN.md 31(v1.0 Definition of Done)の各項目を、このプロジェクトの実際の実装状況・実データでの検証結果(EPIC R/S)に照らして評価したものです。「未実装/未検証」を隠さず記載することを優先しています。凡例: ✅ done / 🟡 partial / ❌ not done。

---

## Build

| 項目 | 状態 | 根拠 |
|---|---|---|
| clean clone + Dockerで生成可能 | 🟡 | `docker/app.Dockerfile`は実際にビルド・実行できる(TASK-S005で確認)。ただし実際にEPWINGバイナリまで作る`docker/toolchain.Dockerfile`は3記事・100記事フィクスチャでのみ検証済みで、全件規模のワンコマンド実行フローはまだ無い([VIEWER_VERIFICATION.md](VIEWER_VERIFICATION.md)参照) |
| hostへlegacy dependency不要 | ✅ | `wikiepwing`本体(ingest/normalize/generate)はPython+uvのみで完結し、TASK-S005でDockerコンテナ内実行を確認済み。FreePWING/EBはtoolchainイメージに閉じている |
| Mini/Lite/Full | ✅ | 実データ全件(約150万記事)で3プロファイルすべて生成・検証済み(TASK-R005/R008/R009) |
| resume | ✅ | 各ステージがmanifestベースでresume可能(TASK-I005系)。EPIC R/Sの複数回実行で実際に機能を確認 |
| source lock | ✅ | `source.lock.json`が全81チャンクの取得・検証・複数回の再利用で機能することを確認済み(TASK-R003、S004、S005) |

## Content

| 項目 | 状態 | 根拠 |
|---|---|---|
| title | ✅ | 実データ全件で正常に処理(TASK-R004/R005) |
| redirects | ✅ | 同上。実データでの重複キー問題を発見・修正済み(TASK-R003) |
| internal links | ✅ | EPIC H実装済み、小規模フィクスチャで検証済み |
| headings/lists | ✅ | EPIC G/H実装済み |
| tables | ✅ | EPIC K実装済み |
| infoboxes | ✅ | EPIC K実装済み。実データのinfobox画像抽出が`generate`の本文プレースホルダーに反映されることを確認(TASK-R008) |
| references | ✅ | EPIC L実装済み |
| gaiji fallback | ✅ | EPIC M実装済み(M001〜M009すべて完了) |
| images Lite/Full | 🟡 | パイプライン自体は実データで検証済み(TASK-R007、約2万件のサンプル取得・変換に成功)。ただし全件(約250万ユニークURL)での実行は逐次ダウンロードの所要時間(4〜12日)のためまだ行っていない |
| math Lite/Full | 🟡 | EPIC N実装済みで小規模フィクスチャでは検証済みだが、EPIC Rの実データ全件実行で数式コンテンツの有無・レンダリング結果を個別にスポットチェックしてはいない |

## Quality

| 項目 | 状態 | 根拠 |
|---|---|---|
| structured diagnostics | ✅ | 実データ全件で`diagnostics`テーブルに約892万件の`DOM_UNKNOWN_ELEMENT`警告等が正しく記録されることを確認(TASK-R004) |
| source/model/EPWING verify | 🟡 | `verify-raw`/`verify`(entries.jsonl)は実データ全件で検証済み(TASK-R003〜R009)。EPWINGバイナリ自体の検証(実ビューアでの確認)は小規模フィクスチャのみで、全件規模は未実施([VIEWER_VERIFICATION.md](VIEWER_VERIFICATION.md)) |
| fixed article regression | ✅ | TASK-H012(100記事fixture)ベースの回帰テストが存在 |
| reference comparison | 🟡 | TASK-Q007(Reference comparison engine)は実装・テスト済みだが、Boookends 2023参照実装との比較は小規模データでのみ実施(全件規模での比較は未実施) |
| compatibility thresholds | 🟡 | TASK-Q008で閾値ロジックは実装済みだが、全件規模データでの実測評価はまだ行っていない |
| **(発見事項)** 検索語budget(`search/search_term.py`の`apply_search_budgets`)がパイプラインに未配線 | ❌ | TASK-Q005で実装・単体テスト済みだが、`normalize`/`generate`のどこからも呼ばれていないことをgrepで確認(TASK-R008の実施結果に記録)。Mini/Lite/Fullの`search`セクション設定(`max_terms_per_article`等)は現状、生成される`entries.jsonl`に一切反映されない |

## Reproducibility

| 項目 | 状態 | 根拠 |
|---|---|---|
| dependency lock | ✅ | `uv.lock`が存在し、CI/ビルドで`--frozen`運用 |
| toolchain source hashes | ✅ | `docker/toolchain/fetch-verified.sh`等でFreePWING/EBソースのフィンガープリント検証を実装済み |
| Docker digest | ❌ | `BUILD-INFO.json`の`software.app_image_digest`/`toolchain_image_digest`フィールドは定義されているが、実際にDockerイメージのdigestを計算してセットするコードがCLIのどこにも存在しない(grepで確認、常に`None`) |
| logical hashes | ✅ | TASK-S002(`compute_logical_build_hash`)を使い、同一ホスト再ビルド(TASK-S004)・Docker/macOSクロス環境(TASK-S005)の両方で実データ全件規模の一致を確認済み。最も強く検証されている項目 |
| BUILD-INFO | 🟡 | `build_build_info`/`write_build_info`(TASK-S001)はテスト済みのライブラリ関数として存在するが、CLIのどのコマンドからも呼ばれておらず、実際に`BUILD-INFO.json`ファイルを書き出す導線が無い(grepで確認) |

## Documentation

| 項目 | 状態 | 根拠 |
|---|---|---|
| README build instructions | ✅ | `README.md`に加え、詳細版として[BUILD.md](BUILD.md)を作成(TASK-T001) |
| config reference | ✅ | [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)(既存、TASK-T002でプロファイル合成例を追加) |
| troubleshooting | ✅ | [TROUBLESHOOTING.md](TROUBLESHOOTING.md)(TASK-T003)。EPIC R/Sで実際に遭遇した問題に基づく |
| license/attribution notes | 🟡 | [LICENSING.md](LICENSING.md)(TASK-T005)で現状を文書化したが、attribution appendixの自動生成自体は未実装(上記参照) |
| viewer verification notes | 🟡 | [VIEWER_VERIFICATION.md](VIEWER_VERIFICATION.md)(TASK-T004)で手順は文書化したが、実ビューアでの確認自体は小規模フィクスチャのみ |

---

## まとめ

- **強く検証済み**: Build(source lock/resume/プロファイル生成)、Content(テキスト系全般)、Reproducibility(logical hashes)は実データ全件規模で複数回・複数環境にわたって検証済みです。
- **部分的**: 画像・数式の全件規模での網羅的検証、EPWINGバイナリの全件規模ビルドと実ビューア確認、reference/compatibility比較の全件規模実測は、時間・外部サービス制約(rate limit等)により縮小スコープでの検証にとどまっています。
- **未実装のギャップ(v1.0前に対応が必要)**:
  1. 検索語budget(`apply_search_budgets`)がパイプラインに配線されていない — Mini/Lite/Fullの検索語仕様上の差別化が実質的に機能していない
  2. `BUILD-INFO.json`の生成がCLIのどこからも呼ばれていない
  3. Docker image digestの計算・記録が未実装
  4. attribution appendix(LICENSES.txt/ATTRIBUTION.txt/attribution.jsonl)の自動生成が未実装

これらのギャップは`TASKS.md`に新規タスクとして起票することを推奨します(本タスクの範囲は評価・記録のみで、実装は含みません)。
