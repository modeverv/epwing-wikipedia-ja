# GAIJI.md

外字(gaiji: EPWING/FreePWINGバックエンドで表現できない文字を、専用の bitmap
グリフとして埋め込む仕組み)の本格対応をスコープした設計メモです。別セッションで
実装することを前提に、現状分かっていること・見つかった問題・未決定事項をまとめて
います。

## 実装結果(2026-07-17、本メモに基づき本格対応を実施)

以下、本メモが要求していた本格対応(検出→分類→コード割り当て→グリフ描画→
ビルドファイル書き出し→本文への埋め込み)を実装した。§1〜§7は実装前の調査メモ
として残すが、いくつかの記載は実装によって古くなっている(該当箇所に注記した)。

- §3のバグを修正: `representability.py`の`is_backend_representable`が
  EUC-JPエンコード結果の先頭バイトが`0x8f`(JIS X 0212 SS3)になる文字も
  「表現可能」と誤判定していた。実際のPerl `Encode`/`FPWParser`の挙動
  (`v1/toolchain/records/build_records.pl`の`needs_gaiji`が既に正しく実装
  していた判定と同じ)に合わせ、SS3プレフィックスは「表現不可(C/D分類へ)」
  として扱うよう修正した。ベンダー拡張領域(0xF0〜0xFEの私用領域行)は
  未検証のまま「表現可能」扱いを維持している(§7参照、変更していない)。
- §2の統合ギャップを解消: 新規`src/wikiepwing/gaiji/embedding.py`が
  `plan_gaiji_codes`(全記事のtitle/alias/body文字列を1回スキャンし、
  `assign_gaiji_codes`で決定論的にコード割り当て)と`embed_gaiji_tokens`
  (本文: A分類はそのまま、C分類は`@@GAIJI:<code>@@`トークン、D分類は
  `[U+XXXX]`)、`embed_title_fallback`(title/alias: A分類以外は全て
  `[U+XXXX]`、gaijiトークンは絶対に生成しない)を提供する。
  `wikiepwing.render.freepwing_source.write_entries_jsonl`がこれを呼び出し、
  `wikiepwing.render.generate.run_generate`が`gaiji_dir`/
  `gaiji_database_path`/`unicode_report_path`が指定されればそれぞれ
  ビルドファイル(XBM+halfchars.txt/fullchars.txt)・レジストリ
  (`gaiji.sqlite3`、実行毎に作り直し)・レポートを書き出す。CLIの
  `generate`/`build`サブコマンドは`--entries-output`の隣に
  `gaiji/`・`gaiji.sqlite3`・`unicode-report.json`をデフォルトで出力する
  (`--gaiji-dir`等で上書き可)。
- **title/aliasにgaijiトークンを埋め込まない設計判断**: title/aliasは
  `word2->add_entry`の検索キーとしてそのまま使われるため、`@@GAIJI:...@@`
  という生トークン文字列が検索キーに混入すると絶対に検索できないentryが
  生まれてしまう。v1(`v1/src/wikiepwing/epwing/gaiji.py`)も同じ理由で
  titleは常に`[U+XXXX]`表記に倒しており、その前例に倣った(§4の
  「本文埋め込み構文」調査結果と合わせ、本文と検索キーで扱いを分けるのが
  正しいと判断)。
- §5の実機調査は完了: `tests/fixtures/handcrafted/build_fixture.pl`に
  実際のFreePWING API呼び出し例(`add_half_user_character`/
  `add_full_user_character`/`add_color_graphic_start`/
  `add_color_graphic_end`)がそのまま存在した。さらに`v1/toolchain/records/build_records.pl`
  に、本文中へのプレースホルダートークン埋め込み+Perl側での分割という、
  今回採用したのと同じ設計の実例(`@@GAIJI:...@@`/`@@CGRAPH:...@@`)が
  既にあった。`docker/toolchain/freepwing_build_entries.pl`に
  `add_text_with_gaiji`を追加し、`@@GAIJI:(narrow|wide)-NNNN@@`を
  `add_half_user_character`/`add_full_user_character`へ変換するようにした
  (コードの`narrow-`/`wide-`プレフィックスからwidth classをそのまま読める
  ため、Perl側に別途ルックアップテーブルは不要)。
- TASK-T013の暫定回避策(`to_euc_jp`の geta マーク置換)を撤去(§0/§6の
  想定通り)。修正後のパイプラインではtitle/alias/bodyのどの経路でも
  `\x8f`バイトが`to_euc_jp`に到達しない設計になっているため、万一到達したら
  黙って置換せず`die`する防御的チェックに変更した。
- 実toolchainイメージ(`wikiepwing-toolchain:dev`)で実際に
  `fpwmake`を実行し、JIS X 0212のみの漢字(wide gaiji、例: 丂)と
  JIS X 0208に存在しない非日本語文字(narrow gaiji、例: タイ文字)を含む
  本文が、クラッシュせずビルド・検索(`wikiepwing-eb-search`)できることを
  確認した(`ebinfo`が`narrow font characters`/`wide font characters`を
  実際に報告)。
- 画像(色グラフィック、§4の類似問題)の本文埋め込み配線は今回のスコープ外
  とした(gaijiのみ先行、§7の選択肢のうち「gaijiだけ先に進める」を採用)。
  `freepwing_graphics.py`/`RenderedEntry.graphics`は引き続き未配線のまま。
- 未解決のまま残した項目(§7参照): ベンダー拡張領域(0xF0〜0xFEの私用領域行)
  の実ビューアでの表示確認、実データ全件(約150万記事)規模でのgaiji配線の
  実行・検証、`config.section("gaiji")`の`enabled`/`fallback_format`
  キーは宣言に沿って読み込む配線をしていない(`font_family`/
  `font_package_id`はレジストリの`font_identifier`列に反映済み)。

## 0. 背景(なぜこのメモがあるか)

2026-07-17、実データ全件(約150万記事)で`make build-epwing`を実行したところ
`freepwing_build_entries.pl`が`invalid character: \x8f`で失敗した(TASK-T013)。
調査の結果、以下が判明した:

- `RELEASE_CHECKLIST.md`は「gaiji fallback ✅ EPIC M実装済み(M001〜M009すべて
  完了)」と記載しているが、これは**個々のライブラリ関数が実装・単体テスト済み**
  という意味であり、**`normalize`/`generate`のどこからも呼ばれておらず、CLIコマ
  ンドとしても存在しない**(`grep`で確認、`write_gaiji_build_files`等は自分自身
  のテストからしか呼ばれていない)。この記載は実態とズレており、修正が必要。
- 応急処置として、`docker/toolchain/freepwing_build_entries.pl`の`to_euc_jp`に
  「EUC-JPエンコード結果の先頭バイトが`0x8f`(JIS X 0212のSS3プレフィックス)に
  なる文字を全角下駄記号(〓、U+3013)に置換する」という**簡易回避策**を入れて
  ビルドのクラッシュだけは止めた(TASK-T013、ユーザー明示の依頼)。これは**該当
  文字の情報が失われる**暫定対応であり、本格対応ではない。

このメモは、その本格対応(検出→分類→コード割り当て→グリフ描画→ビルドファイル
書き出し→本文への埋め込み)に何が必要かをまとめたもの。

## 1. 現状: 何が既にあるか(ライブラリレベル、実装・テスト済み)

`src/wikiepwing/gaiji/`配下に以下が存在し、それぞれ単体テストも通っている。

| モジュール | 役割 | 備考 |
|---|---|---|
| `representability.py` | `is_backend_representable(character)`: 1文字がEUC-JPエンコード可能か。`unrepresentable_characters(text)`: 文字列中の非対応文字を列挙 | **§3の問題を参照。Pythonの`codecs`の`euc-jp`実装を判定基準に使っているが、これは実際のツールチェイン(Perlの`Encode`モジュール)と食い違う** |
| `classifier.py` | `classify_character`: ARCHITECTURE.md 18.1のA/B/C/D分類 (A=そのまま表現可, B=設定済み置換, C=gaiji bitmap化, D=表現不能) | Bの置換テーブルは呼び出し側が渡す想定(まだ存在しない) |
| `unrepresentable.py` | D分類文字の`[U+XXXX]`表記フォールバックと、出現回数・記事例を集計する`UnrepresentableTracker` | |
| `code_assignment.py` | `assign_gaiji_codes`: `(sequence, width_class)`の集合から決定論的に`assigned_code`(`narrow-0001`/`wide-0001`形式)を割り当てる。Unicodeソート順ベースで処理順に依存しない | DATA_CONTRACTS.md 10の要件を満たす |
| `glyph_renderer.py` | `render_glyph_bitmap`: フォントから1文字をPNGとしてラスタライズ。`bitmap_hash` | Noto CJKフォント(`docker/toolchain.Dockerfile`にインストール済み)前提 |
| `freepwing_gaiji.py` | `write_gaiji_build_files`: `assigned_code`ごとにXBMファイルを書き出し、`halfchars.txt`/`fullchars.txt`(`"{assigned_code} {xbm_filename}"`形式)を生成。**`build-epwing.sh`の`GAIJI_DIR`が期待する形式そのもの** | TASK-H009のフィクスチャで実ツールチェイン相手に検証済み |
| `database.py` + `migrations/gaiji/001_initial.sql` | `gaiji.sqlite3`: `sequence`/`normalized_sequence`/`width_class`/`assigned_code`/`bitmap_path`/`bitmap_sha256`/`font_identifier`/`usage_count`を持つレジストリ。同じ文字列は一度だけbitmap生成(DATA_CONTRACTS.md 10) | `model.sqlite3`と同じマイグレーション機構を流用 |
| `report.py` | `build_unicode_report`/`write_unicode_report`: D分類文字の出現回数・頻出順・記事例をJSONレポート化 | |

`config/default.toml`の`[gaiji]`(`enabled`/`font_family`/`font_package_id`/
`fallback_format`)も宣言済みだが、`config.section("gaiji")`はコードのどこからも
呼ばれていない(これも「宣言はあるが未配線」)。

## 2. 現状: 何が無いか(統合ギャップ)

1. **CLIコマンドが無い**。`image-plan`/`image-fetch`/`image-convert`に相当する
   `gaiji-*`コマンド、あるいは`normalize`/`generate`内での自動処理が一切無い。
2. **本文中の文字置換が行われていない**。`normalize`/`generate`のどちらも
   `is_backend_representable`/`unrepresentable_fallback`等を呼んでいない。
   つまり`entries.jsonl`には生のUnicode文字がそのまま入っており、
   `GAIJI_DIR`を`build-epwing.sh`に渡しても**それだけでは`invalid character`は
   解消しない**(渡したグリフファイルを本文が一切参照していないため)。
3. **「名前付きビルド資産を本文中の特定位置から参照する」仕組みが無い**。
   §4で詳述するが、これは画像パイプラインにも共通する未解決の穴で、gaiji対応の
   本丸はここにある。
4. **`gaiji.sqlite3`をどのステージで・いつ更新するか未設計**。`normalize`実行時
   (記事ごとに逐次)か、`generate`実行時(全記事を見てグローバルに決定)か、
   専用の`gaiji-plan`/`gaiji-build`ステージを新設するか、要検討(§6)。

## 3. 重要な発見: `is_backend_representable`の判定基準が実際のツールチェインとズレている

`representability.py`は Python 標準ライブラリの`str.encode("euc-jp")`が成功する
かどうかで「バックエンドで表現可能」を判定している。しかし実際にFreePWINGの
`FPWParser`へ渡す前の変換は`docker/toolchain/freepwing_build_entries.pl`が行って
おり、そこでは**Perlの`Encode`モジュール**を使っている。この2つの実装は**同じ
"euc-jp"という名前でも変換できる文字集合が異なる**:

```
文字   Python codecs "euc-jp"        Perl Encode "euc-jp"
凜    → f4a5 (成功。JIS拡張/私用領域行) → f4a5 (同じ)
丂    → 8fb0a1 (成功。JIS X 0212 SS3)   → 8fb0a1 (同じ)
㐂    → UnicodeEncodeError(失敗)        → ??? (未検証)
髙    → UnicodeEncodeError(失敗)        → ??? (未検証)
```

実際に確認した通り、**Perlの`Encode`はJIS X 0212(SS3、`\x8f`プレフィックス)を
「エンコードできる」と判定するが、それを受け取るFPWParser自身はSS3を理解せず
`invalid character`で落ちる**(TASK-T013で発見・回避した問題そのもの)。つまり:

- `is_backend_representable("丂")`は現状**`True`を返すが、実際にはビルドを壊す**。
  これは`classifier.py`の分類Aの境界そのものが誤っている、ということ。
- 逆に「凜」のような、JIS拡張の私用領域(0xF0〜0xFE行)にPython/Perl双方の実装が
  便宜的にマッピングしている文字が、実際のEPWINGビューアで正しく表示されるかは
  未検証(ベンダー拡張領域はビューア実装によって対応がまちまちな可能性がある)。

**本格対応に着手する前に、まず「バックエンドが本当に安全に表現できる文字集合」
の正確な定義を作り直す必要がある。** 選択肢:

- FPWParserが実際に受け付ける文字を、Dockerツールチェイン内でPerlを使って
  総当たり検証するスクリプトを書き、その結果を「正」とする。
- あるいはJIS X 0208の規格上の範囲(行1-94、私用領域0xF0-0xFEを除く)だけを
  安全とみなす、より保守的な独自実装に置き換える(SS3を含め、ベンダー拡張領域は
  最初から「表現不可」として全部gaiji行きにする)。

## 4. もう一つの重要な発見: 「名前付き資産を本文中から参照する」仕組みが画像パイプラインにも無い

`write_gaiji_build_files`は`halfchars.txt`/`fullchars.txt`+XBMファイルという
**ビルド資材**を作るだけで、「本文中のこの位置にこの外字を置く」という**参照**
は別の話。FreePWINGの規約では、Perlの`FPWUtils::FPWParser`が
`add_reference_start`/`add_reference_end`(内部リンク用、`freepwing_build_entries.pl`
に実装済み)のような「特殊な埋め込み呼び出し」を通じて本文中に特殊要素を挿入する
形になっているはずで、外字用にも同様の(`add_*`)呼び出しが必要と推測されるが、
**現状の`freepwing_build_entries.pl`にはそのような呼び出しが一切無い**。

これは画像(gaiji以外の色グラフィック)でも**全く同じ状況**だと分かった:
`src/wikiepwing/media/freepwing_graphics.py`のdocstringに次の記載がある:

> Wiring an entry's actual `RenderedEntry.graphics` and generating the matching
> `add_color_graphic_start`/`add_color_graphic_end` calls in the FreePWING
> intermediate JSON/Perl build script is a separate step

つまり`RenderedEntry.graphics`フィールドは存在するが常に空(`render/mini_layout.py`
で`graphics=()`固定)で、画像もgaiji同様「ビルド資材は作れるが本文からの参照は
未実装」という同じ穴を抱えている。**この「名前付き資材への参照」を解決する仕組み
は、gaijiと画像の両方に共通するので、どちらか一方だけを直すのではなく、共通の
設計にした方がよい**(実装は別々でも、参照構文の考え方は揃えるべき)。

`freepwing_build_entries.pl`が読み込む`entries.jsonl`のレコード形式
(`wikiepwing.render.freepwing_source.write_entries_jsonl`が書く`tag`/`title`/
`aliases`/`body`/`targets`)には、現状「本文中の特定位置に外字/画像を挿入する」
ためのフィールドが無い。本文の`body`は単なる文字列であり、`RenderedEntry.body`
(`render_node.py`のノード木)からこの文字列へ平坦化する際に位置情報が失われて
いる可能性が高い(要調査: `write_entries_jsonl`/`RenderedEntry`→`body`文字列
変換の実装を読むこと)。

## 5. FreePWINGの実際の埋め込み構文を先に調べる必要がある

本格対応を設計する前に、次を実機(toolchainイメージ)で確認すべき:

- `FreePWING::FPWUtils::FPWParser`のPerl APIに、外字(gaiji)を本文中の1文字と
  して埋め込むメソッドが存在するか(`add_gaiji`のような名前を推測)。
  `perldoc`やモジュールのソース(`/opt/freepwing/`配下、toolchainイメージ内)を
  実際に読むこと。
- 同様に色グラフィックの埋め込みメソッド(`add_color_graphic_start`/
  `add_color_graphic_end`は`freepwing_graphics.py`のdocstringに名前だけ出てくる
  が、実際に呼び出しているコードは無い)。
- `tests/fixtures/handcrafted/build_fixture.pl`(既存の手作りフィクスチャ)に、
  これらの呼び出しの実例がある可能性が高い(docstringが
  `add_color_graphic_start("wiki-mark")`を実例として挙げている)。**まずこの
  フィクスチャを読むこと。**

## 6. 実装スコープ案(段階的に)

以下は一案。実際に着手する際は、まず§5の実機調査を先に行い、判明した構文に
合わせて調整すること。

### Step 1: representability判定の作り直し(§3の修正)

- Docker toolchainイメージ内でPerlの`Encode`を使い、「実際にFPWParserが受け付ける
  文字集合」を総当たり検証するスクリプトを書く(または保守的にJIS X0208規格範囲
  だけを許可する実装に絞る)。
- `representability.py`をこの正しい判定に置き換える。既存の`classifier.py`等の
  単体テストへの影響を確認。

### Step 2: 検出・分類・コード割り当てを`normalize`または`generate`に配線

- `normalize`(記事ごとに1回処理される)か`generate`(全記事を見て
  グローバルにコード割り当てできる)か検討。`code_assignment.py`の
  「処理順に依存しない決定論的割り当て」という制約から、**全記事のgaiji候補が
  出揃ってから一括でコード割り当てする方が自然**(`generate`側、または
  `generate`の前に独立した`gaiji-plan`ステージを新設)。
- 検出した文字を`gaiji.sqlite3`に登録(初回のみbitmap生成、`usage_count`更新)。
- 本文中の該当文字位置を、後段(Step 3)で参照できる形で記録する必要がある
  (例: `RenderedEntry`の段階で、文字位置ごとに「ここはgaijiの`assigned_code`
  である」という注釈情報を持たせる新しいノード種別、あるいは`body`文字列に
  一時的なプレースホルダートークンを埋め込み、Perl側で置換する、など)。

### Step 3: 本文埋め込み構文の実装(§4・§5の調査結果次第)

- `freepwing_build_entries.pl`に、Step 2で埋め込んだプレースホルダーを検出し、
  `FPWParser`の外字埋め込みAPI(§5で判明したもの)を呼び出すコードを追加。
- 画像(色グラフィック)の埋め込みも同じタイミングで解決できるなら、
  一緒に実装する価値が高い(§4参照)。

### Step 4: ビルドファイル書き出しの配線

- `write_gaiji_build_files`(既存、変更不要なはず)を、`gaiji.sqlite3`の内容から
  呼び出すCLIコマンド(`gaiji-build`?)またはgenerateステージの一部として追加。
- `docker/toolchain/build-epwing.sh`の`GAIJI_DIR`にこの出力を渡す(既存の
  `Makefile`の`GAIJI_DIR`変数は既にある、TASK-T007)。

### Step 5: レポート・診断

- D分類(表現不能)文字は`UnrepresentableTracker`で集計し、`report.py`で
  レポート化(既存のまま使えるはず)。`generate`の既存`diagnostics`テーブルとの
  統合も検討(既存の`Diagnostic`型に載せるか、別ファイルのレポートのままにするか)。

### Step 6: `freepwing_build_entries.pl`の暫定対応を外す

- Step 1〜4が完了したら、TASK-T013で入れた「〓に置換する」フォールバックは、
  本来「D分類(表現不能)文字」専用のフォールバック(`unrepresentable_fallback`
  の`[U+XXXX]`表記、ARCHITECTURE.md 18.5)に置き換えるべき。ただし
  `[U+XXXX]`という表記そのものがASCII文字列なので、これはEUC-JPエンコードの
  心配がなく現状の`to_euc_jp`をそのまま通せる。

## 7. 決定が必要な事項(実装前に決めること)

- gaijiコード割り当てのタイミング: `normalize`単位(記事ごと、resumeと相性が
  良い)か、`generate`単位(全体最適、コード割り当ての決定論性を保ちやすい)か。
- `gaiji.sqlite3`のライフサイクル: 毎回作り直すか、複数回のビルドを跨いで
  永続化し`usage_count`を積み上げるか(再現性・reproducibility要件との整合性を
  要確認。TASK-S002の`compute_logical_build_hash`等、既存の再現性検証に
  影響しないか)。
- ベンダー拡張領域(0xF0〜0xFE行)の扱い: 「Python/Perlの実装が便宜的にサポート
  している」文字を安全とみなすか、実際のEPWINGビューアでの表示確認が取れるまで
  保守的にgaiji扱いにするか。
- 画像埋め込み(§4)を同じタイミングで解決するか、gaijiだけ先に進めるか。

## 8. 参考: 関連ファイル一覧

- `src/wikiepwing/gaiji/*.py`(既存ライブラリ、§1参照)
- `migrations/gaiji/001_initial.sql`(既存スキーマ)
- `config/default.toml`の`[gaiji]`セクション(既存、未配線)
- `src/wikiepwing/media/freepwing_graphics.py`(§4の類似問題)
- `src/wikiepwing/render/rendered_entry.py`(`RenderedEntry.graphics`フィールド)
- `src/wikiepwing/render/freepwing_source.py`(`write_entries_jsonl`、本文の
  文字列化がどこで位置情報を失っているか要調査)
- `docker/toolchain/freepwing_build_entries.pl`(TASK-T013の暫定回避策、
  `to_euc_jp`のコメントに詳細あり)
- `tests/fixtures/handcrafted/build_fixture.pl`(FreePWING APIの実例、§5で
  最初に読むべきファイル)
- `ARCHITECTURE.md`17.2(FreePWINGアダプタの責務として「graphic/gaiji登録」が
  明記されている)・18章(外字設計)
- `DATA_CONTRACTS.md`10章(gaiji registryのスキーマ・決定論的割り当て要件)
- `RELEASE_CHECKLIST.md`(「gaiji fallback ✅」の記載は実態とズレているため、
  本格対応が終わった段階で修正すること)
