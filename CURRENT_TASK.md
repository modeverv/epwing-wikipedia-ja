# CURRENT_TASK.md

## Task ID

TASK-O012

## 目的

`ARCHITECTURE.md`のEPIC O最終タスクとして、TASK-O003-O011で実装した各段階(選択・ダウンロード・検証・SVG sanitize・raster変換・cache・dedup・attribution・FreePWING graphics build file書き出し)を実際に連結する`image plan/fetch/convert`コマンドを実装する。前段(このタスクの一部として実施済み: TASK-O012 part 1)でTASK-O001の抽出をnormalizeパイプラインへ配線し、`model.sqlite3`の`media_references`テーブルに本文画像も含めて保存されるようにした。本タスクの残り(part 2)では、`model.sqlite3`から画像参照を読み出し(`plan`)、実際にダウンロード・検証・sanitizeし(`fetch`)、raster変換・cache・dedup・graphics build file書き出しを行う(`convert`)、3つのCLIサブコマンドを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O012(依存: O003-O011)を読んだ
- [x] AskUserQuestionでbody-image配線を含める方針を確認し、part 1として既に実施・commit済みであることを確認した
- [x] `migrations/model/*.sql`の`media_references`テーブル(page_id/ordinal/media_id/source_url/.../role)が既に存在し、normalize側で書き込み済みであることを確認した
- [x] `config.py`の`[images]`セクション(`enabled`/`max_per_article`/`max_download_bytes`/`max_pixels`/`allowed_hosts`/`allow_svg`/`allow_animated`)が既にスキーマ定義済みであることを確認した(新規スキーマ追加は不要)
- [x] `cli.py`の`acquire`/`register-local-source`/`inspect-source`(stage manifestを使わない軽量なユーティリティコマンド)のパターンを、`image-plan`/`image-fetch`/`image-convert`にも採用する方針にした(ingest/normalize/generateの重いstage manifest/resumeパターンは今回は対象外)

## 変更予定ファイル

- `src/wikiepwing/media/orchestrate.py`(新規: `MediaPlanEntry`, `plan_media`, `FetchOutcome`, `fetch_media`, `ConvertOutcome`, `convert_media`)
- `src/wikiepwing/cli.py`(`image-plan`/`image-fetch`/`image-convert`サブコマンド追加)
- `tests/test_media_orchestrate.py`(新規)
- `tests/test_cli.py`(追記)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_orchestrate.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `plan_media(model_database_path)`が`media_references`テーブルから(rejected記事を除く)全画像参照を`page_id`/`ordinal`順で読み出す
- [x] `fetch_media(plan, ...)`が各一意な`source_url`につき1回だけダウンロードし(`SecureMediaDownloader`経由)、SVGならsanitize、それ以外ならMIME/magic/pixel検証を行い、成功/失敗を`FetchOutcome`として返す
- [x] `convert_media(fetch_outcomes, ...)`が成功したfetch結果をBMPへ変換し(`MediaCache`経由)、content hashで重複除去したうえで`GraphicBuildEntry`相当のデータを返す
- [x] `wikiepwing image-plan`/`image-fetch`/`image-convert` CLIサブコマンドが実行でき、それぞれJSON形式のレポートを出力する
- [x] `make check`が成功する(ImageMagick依存部分はローカル環境でskipされることを許容する)

## 非対象

- ingest/normalize/generateと同じ重いstage manifest/resumeパターン(今回は軽量ユーティリティコマンドとして実装)
- 実際のFreePWING全体ビルドへのgraphics統合(catalog/subbook設定への反映、EPIC Q以降)
- distribution mode(personal/distributable)による画像除外ポリシーの実装(config skeletonは既存だが、実際の適用ロジックは別タスク)

## 実施結果

- **part 1**(commit 3bacdce): TASK-O001の`parse_image_node`/`parse_figure_media`をnormalizeパイプラインへ配線した(`normalize/media_extraction.py`新規)。`normalize_html`の戻り値を`(blocks, diagnostics)`から`(blocks, body_media, diagnostics)`へ拡張し、`normalize/orchestrate.py`でSnapshotのmain imageと本文画像を`select_media`で統合するようにした。
- **part 2**(本コミット): `src/wikiepwing/media/orchestrate.py`に`MediaPlanEntry`/`plan_media`(`model.sqlite3`の`media_references`テーブルから読み出し)・`FetchOutcome`/`fetch_media`(一意な`source_url`ごとに1回ダウンロード、SVGはsanitize、それ以外はMIME/magic/pixel検証)・`ConvertOutcome`/`convert_media`(BMP変換+content hash dedup)・`write_fetch_report`/`read_fetch_report`(fetchとconvertを別プロセス/別呼び出しに分離するための中間レポート)を実装した。
- `cli.py`に`image-plan`/`image-fetch`/`image-convert`の3サブコマンドを追加した。`image-fetch`は`[images]`config section(`allowed_hosts`/`max_download_bytes`/`max_pixels`/`allow_svg`)を消費する。`image-convert`はfetch reportを読み、`write_graphics_build_files`(TASK-O011)でFreePWING graphics build filesを書き出す。ingest/normalize/generateの重いstage manifest/resumeパターンは採用せず、`acquire`/`register-local-source`/`inspect-source`と同じ軽量なユーティリティコマンドパターンにした。
- `tests/test_media_orchestrate.py`(新規17件、実DBを使った`plan_media`のテストを含む、raster変換系4件はImageMagick未検出時にskip)、`tests/test_cli.py`(新規5件: help表示3件+実際の`model.sqlite3`を使った`image-plan`のend-to-endテスト2件)。
- `make check`(format-check/lint/mypy/pytest 1223件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- distribution mode(personal/distributable)による画像除外ポリシーの実際の適用、実際のFreePWING全体ビルドへのgraphics統合(catalog/subbook設定)は対象外のまま。
