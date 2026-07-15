# CURRENT_TASK.md

## Task ID

TASK-O005

## 目的

`ARCHITECTURE.md` 15.4のダウンロード安全性要件のうち「実デコード後pixel上限」「MIMEとmagic byte検証」を実装する。TASK-O004がダウンロードした生バイト列を、(1) magic byteから実際のフォーマットを判定し、(2) 宣言された`Content-Type`と矛盾しないか確認し、(3) Pillowで実際にデコードして得られる幅・高さの積が上限を超えないか検証する、という3段階のバリデーションを行う。SVGはXML(magic byteでの判定になじまない、外部entity等の懸念もある)ため対象外とし、TASK-O006(SVG sanitizer)に委ねる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O005(依存: O004)を読んだ
- [x] `ARCHITECTURE.md` 15.4(「実デコード後pixel上限」「MIMEとmagic byte検証」)を再確認した
- [x] TASK-M005で追加済みのPillow依存を再利用する(新規依存なし)
- [x] `MediaDownloadResult.content_type`(TASK-O004、`Content-Type`ヘッダから取得、`None`もありうる)を確認した

## 変更予定ファイル

- `src/wikiepwing/media/validation.py`(新規: `MediaValidationError`, `MediaValidationResult`, `validate_media_bytes`)
- `tests/test_media_validation.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_validation.py
make check
git diff --check
```

## 完了条件

- [x] PNG/JPEG/GIF/WEBPの実際のmagic byteを正しく認識する
- [x] magic byteから判定できない(不正/未対応)フォーマットは拒否する
- [x] 宣言された`Content-Type`(与えられた場合)が実際に検出したフォーマットと矛盾する場合は拒否する。`None`の場合はスキップする
- [x] Pillowでのデコードが失敗する場合は拒否する(クラッシュしない)
- [x] 幅×高さが`max_pixels`を超える場合は拒否する
- [x] 検証成功時は検出フォーマット・幅・高さを返す
- [x] `make check`が成功する

## 非対象

- SVG(XMLベースで別の脅威モデル、TASK-O006のSVG sanitizerの対象)
- raster変換(TASK-O007)

## 実施結果

- `src/wikiepwing/media/validation.py`に`MediaValidationError`・`MediaValidationResult`・`validate_media_bytes`を実装した。magic byte(PNG/JPEG/GIF/WEBPの既知シグネチャ)でフォーマットを判定し、`declared_content_type`(与えられた場合)がそのフォーマットと矛盾しないか確認したうえで、Pillowで実際にデコードして幅・高さを取得し、`max_pixels`を超えないか検証する。
- `tests/test_media_validation.py`(新規13件)で、PNG/JPEG/GIF/WEBP各magic byteの認識・未対応フォーマットの拒否・Content-Type一致/不一致/未知値/未指定・デコード失敗・pixel上限超過/境界値・`max_pixels`のバリデーションを確認した。
- `make check`(format-check/lint/mypy/pytest 1149件)と`git diff --check`が成功した。
- SVGは対象外(TASK-O006のSVG sanitizerが別の脅威モデルで対応)。
