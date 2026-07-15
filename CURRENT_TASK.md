# CURRENT_TASK.md

## Task ID

TASK-N005

## 目的

`ARCHITECTURE.md` 15.7の数式変換パイプライン(1.テキスト代替 2.cache key 3.SVG/PNGレンダリング 4.**EPWING graphicへ変換** 5.失敗時fallback)のステップ4を実装する。TASK-N003の`render_math_to_image(..., image_format="png")`が返すPNGバイト列を、`tests/fixtures/handcrafted/generate_bitmap.pl`が示す実toolchain互換フォーマット(24bit color, `BM`マジック始まりの標準Windows BMP)に変換する。matplotlibのPNG出力は透過(RGBA)背景のため、EPWING側で表示される紙面色を想定した不透明な背景色に合成してからBMP化する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-N005(依存: N003)を読んだ
- [x] `ARCHITECTURE.md` 15.7(数式変換の優先順位、ステップ4「EPWING graphicへ変換」)を確認した
- [x] `tests/fixtures/handcrafted/generate_bitmap.pl`(実toolchainで検証済みのBMPフォーマット: `BM`マジック、24bit color、`BITMAPINFOHEADER`)を確認した
- [x] TASK-M005で追加済みのPillow依存を再利用する(新規依存なし)

## 変更予定ファイル

- `src/wikiepwing/normalize/math_raster.py`(新規: `MathRasterError`, `convert_png_to_bmp`, `render_math_to_bmp`)
- `tests/test_normalize_math_raster.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_math_raster.py
make check
git diff --check
```

## 完了条件

- [x] `convert_png_to_bmp(png_bytes, *, background=(255, 255, 255))`がPNGバイト列をデコードし、透過部分を`background`色で合成したうえで、`BM`マジックから始まる有効なBMPバイト列を返す
- [x] 透過のないPNG(不透明な数式レンダリング結果)を変換しても背景色の影響を受けない(不透明ピクセルはそのまま保持される)
- [x] `render_math_to_bmp(tex_source, *, font_size=16, background=(255, 255, 255))`がTASK-N003の`render_math_to_image(..., image_format="png")`を呼び出し、その結果を`convert_png_to_bmp`でBMP化して返す
- [x] 空/不正なPNGバイト列を渡すと`MathRasterError`を送出する(クラッシュしない)
- [x] `make check`が成功する

## 非対象

- inline/block layoutへの配線(TASK-N006)
- 実際のFreePWING graphic登録(`add_graphic`/EPIC O)
- gaijiのXBM変換(TASK-M007で対応済み、対象は独立したフルサイズ画像)

## 実施結果

- `src/wikiepwing/normalize/math_raster.py`に`MathRasterError`・`convert_png_to_bmp`・`render_math_to_bmp`を実装した。`convert_png_to_bmp`はPillowでPNGをデコードし、RGBAのalphaチャンネルをmaskとして`background`色の不透明キャンバスへ合成してからBMPとして書き出す(`tests/fixtures/handcrafted/generate_bitmap.pl`が示す`BM`マジック始まりの標準BMPと互換)。`render_math_to_bmp`はTASK-N003の`render_math_to_image(..., image_format="png")`をラップする。
- `tests/test_normalize_math_raster.py`(新規7件)で、BMPマジックの確認・透過ピクセルの背景合成・不透明ピクセルの保持・空/不正バイト列でのエラー・エンドツーエンドの決定論的レンダリングを確認した。
- `make check`(format-check/lint/mypy/pytest 1067件)と`git diff --check`が成功した。
