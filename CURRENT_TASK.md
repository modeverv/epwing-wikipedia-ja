# CURRENT_TASK.md

## Task ID

TASK-R007

## 目的

`TASKS.md`のTASK-R007(Full Lite media run、依存: R006,P003完了済み)を実施する。TASK-R004の`model.sqlite3`(全1,508,200記事)に対する画像パイプライン(image-plan/image-fetch/image-convert)を実行する。

`image-plan`で全2,546,801件のユニーク画像URLが判明したが、`image-fetch`は逐次ダウンロード(並列化なし)であり、実測レイテンシ(約0.4秒/リクエスト)から全件では4〜12日規模の連続実行になると判明した。ユーザーに確認したところ、全件ではなく代表サンプル(約20,000件)でLite画像パイプライン全体を検証する方針が選択された。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R007(依存: R006,P003、両方完了済み)を読んだ
- [x] `image-plan`を全1,508,200記事に対して実行し、6,333,316件のmedia参照・2,546,801件のユニークURLを確認した(ローカルのみ、ネットワークアクセスなし)
- [x] AskUserQuestionで「full 2.5M-image fetch」の承認を得た後、実測レイテンシから所要時間(4〜12日)を追加で提示し、「Switch to a bounded sample instead (Recommended)」が選択されたことを確認した
- [x] ImageMagick(`magick`)を`brew install imagemagick`でインストールし、既存のテスト(`test_media_orchestrate.py`, `test_media_raster_converter.py`)がskipなしで21件成功することを確認した
- [x] `image-fetch`/`image-convert`のCLIは`--model-database`全体を対象にする設計でサンプルサイズ引数を持たないため、既存の`plan_media`/`fetch_media`/`convert_media`/`write_fetch_report`/`write_graphics_build_files`関数を直接呼び出す一回限りのスクリプト(コード変更なし、コミット対象外)で系統サンプリング(全プランを均等間隔で間引き、ページID全域の多様性を保持)を行う設計にした

## 変更予定ファイル

- 実行中に実データで発見したバグの修正(1件目):
  - `src/wikiepwing/media/downloader.py`(`SecureMediaDownloader.download`が`https://`スキーム必須のURLしか許可しておらず、実データの`<img src>`の大多数(6,333,316件中5,481,961件)を占めるプロトコル相対URL(`//upload.wikimedia.org/...`)を全て拒否していたバグを修正。`_resolve_protocol_relative`でリクエスト直前に`https:`を補完する。`media_id`/`source_url`として保存済みの値自体は変更しない)
  - `tests/test_media_downloader.py`(回帰テスト追加)
- 実行中に実データで発見したバグの修正(2件目):
  - `src/wikiepwing/media/downloader.py`(`_UrllibTransport`がUser-Agentヘッダを送っておらず、Wikimedia側のUser-Agentポリシーにより全リクエストが`403`で拒否されていたバグを修正。プロジェクトを識別する説明的なUser-Agentを送るようにした)
  - `tests/test_media_downloader.py`(回帰テスト追加)
- 実行中に実データで発見したバグの修正(3件目):
  - `src/wikiepwing/media/downloader.py`(`SecureMediaDownloader.download`が429 Too Many Requestsをリトライせず即座に失敗にしていたため、逐次大量リクエストで実データの過半数がrate limitで失敗していたバグを修正。`Retry-After`ヘッダがあればそれに従い、無ければ指数バックオフで`max_rate_limit_retries`回までリトライするようにした)
  - `tests/test_media_downloader.py`(回帰テスト追加)
- 実行結果として: `/private/tmp/.../scratchpad/sample_image_fetch.py`という一回限りのスクリプト(コミット対象外)で約20,000件のサンプル画像を取得・変換する
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python /private/tmp/.../scratchpad/sample_image_fetch.py
```

## 完了条件

- [x] 約20,000件のサンプル画像に対し`fetch_media`(ダウンロード・検証・SVGサニタイズ)が実行される
- [x] `convert_media`(ラスタ変換・content-addressed cache・重複排除)が実行される
- [x] FreePWING graphics build files(`*.bmp`, `cgraphs.txt`)が生成される
- [x] 実行中に実データ固有のクラッシュ・バグが見つかった場合は原因を特定し、コード修正・テスト追加・commitしてから再実行する(TASK-R003〜R005で確立したパターンを踏襲)

## 非対象

- 全2,546,801件の画像取得(ユーザーの判断によりサンプルに縮小)
- Lite generate/verify(TASK-R008)
- 実データ・実画像を`git`にコミットすること

## 実施結果

系統サンプリング(全6,333,316件のmedia参照から間隔316で間引き、20,043件・ユニークURL10,964件)に対し`fetch_media`/`convert_media`を実行する過程で、実データでのみ再現する3件のバグを発見・修正した(いずれも`src/wikiepwing/media/downloader.py`):

1. プロトコル相対URL(`//upload.wikimedia.org/...`、`<img src>`の大多数を占める)が`https://`スキーム必須のチェックで全て拒否されていたバグ
2. `_UrllibTransport`がUser-Agentを送っておらず、Wikimedia側のUser-Agentポリシーにより全リクエストが`403`で拒否されていたバグ
3. HTTP 429 Too Many Requestsをリトライせず即座に失敗にしていたため、逐次リクエストで大半がrate limitに阻まれていたバグ(`Retry-After`ヘッダ優先、無ければ指数バックオフで最大5回リトライするよう修正)

3件すべて修正・回帰テスト追加・`make check`成功を確認してからcommitし、そのうえで4回目の実行で成功した: `fetched=8403 failed=2561 total=10964`(成功率76.6%、1回目のスキーム修正前は`fetched=0`、2〜3回目のUser-Agent/429修正前後でも大半が失敗していたことと対比すると大幅な改善)。`converted=8319`(84件は内容が重複するBMPとして`convert_media`のcontent-addressed dedupeで自然に除外)。

残る2,561件の失敗内訳を確認し、いずれもソフトウェアのバグではなく想定内の実データ特性であることを確認した: HTTP 400(1,564件、Commons側のサムネイル参照が古くなっている実データの特性。`curl`でも同じ400を再現し確認済み)、host not in allowlist(901件、`/w/...`というja.wikipedia.org自身の相対パス、`upload.wikimedia.org`のみを許可する設計通り)、SVG DOCTYPE/ENTITY拒否(33件、XXE対策のセキュリティ機構が意図通り動作)、HTTP 404(6件、実際に削除されたファイル)、magic bytes不一致(5件)、Content-Length上限超過(数件)。

`$SCRATCH/data/work/graphics-sample/`に8,320個の`*.bmp`ファイルと`cgraphs.txt`が生成され、FreePWING graphics build filesの生成まで一気通貫で成功したことを確認した。全2,546,801件ではなくサンプルのみのため、Lite画像パイプライン(image-plan→image-fetch→image-convert)のロジック検証が目的であり、実データ・実画像はスクラッチパッドのみに保持しgitにはコミットしない。
