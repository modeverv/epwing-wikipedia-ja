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

- 実行中に実データで発見したバグの修正:
  - `src/wikiepwing/media/downloader.py`(`SecureMediaDownloader.download`が`https://`スキーム必須のURLしか許可しておらず、実データの`<img src>`の大多数(6,333,316件中5,481,961件)を占めるプロトコル相対URL(`//upload.wikimedia.org/...`)を全て拒否していたバグを修正。`_resolve_protocol_relative`でリクエスト直前に`https:`を補完する。`media_id`/`source_url`として保存済みの値自体は変更しない)
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

- [ ] 約20,000件のサンプル画像に対し`fetch_media`(ダウンロード・検証・SVGサニタイズ)が実行される
- [ ] `convert_media`(ラスタ変換・content-addressed cache・重複排除)が実行される
- [ ] FreePWING graphics build files(`*.bmp`, `cgraphs.txt`)が生成される
- [ ] 実行中に実データ固有のクラッシュ・バグが見つかった場合は原因を特定し、コード修正・テスト追加・commitしてから再実行する(TASK-R003〜R005で確立したパターンを踏襲)

## 非対象

- 全2,546,801件の画像取得(ユーザーの判断によりサンプルに縮小)
- Lite generate/verify(TASK-R008)
- 実データ・実画像を`git`にコミットすること

## 実施結果

(未着手)
