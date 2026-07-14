# CURRENT_TASK.md

## Task ID

TASK-M007

## 目的

`ARCHITECTURE.md` 17.2(FreePWING adapter)・18.3/18.4を完成させ、TASK-M005(bitmap生成)・TASK-M006(決定論的code割当)の出力を、実際の`fpwmake`が読み込むgaiji build入力(`halfchars.txt`/`fullchars.txt`+個別XBMファイル)へ変換する。`tests/fixtures/handcrafted/halfchars.txt`("half-mark half16.xbm")・`fullchars.txt`・`generate_gaiji.pl`(実際に`fpwmake`へ渡り動作確認済みのXBM生成スクリプト)をリファレンス実装として、同じXBMバイト形式(LSB-first、1=前景/黒)で出力する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M007(依存: M006,H009)を読んだ
- [x] `tests/fixtures/handcrafted/generate_gaiji.pl`の実際のXBM出力形式(`#define {name}_width`/`_height`、`static unsigned char {name}_bits[] = {...}`)を確認した
- [x] `halfchars.txt`/`fullchars.txt`の行形式(`<name> <xbmファイル名>`)を確認した
- [x] TASK-M005の`render_glyph_bitmap`(PNG出力)・TASK-M006の`assign_gaiji_codes`(narrow/wideの決定論的code)を確認した
- [x] EB Library/fpwmakeのnarrow/wide gaiji寸法が8x16/16x16であることを既存fixtureから確認した

## 変更予定ファイル

- `src/wikiepwing/gaiji/freepwing_gaiji.py`(新規: `xbm_bytes_from_image()`, `render_glyph_as_xbm()`, `write_gaiji_build_files()`)
- `tests/test_gaiji_freepwing_gaiji.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_freepwing_gaiji.py
make check
git diff --check
```

## 完了条件

- [x] `xbm_bytes_from_image(image, name)`が、PIL 1-bit imageから`generate_gaiji.pl`と同じテキスト形式(`#define`/`static unsigned char`)のXBM bytesを生成する(既知の小さな画像で厳密にバイト列を検証する)
- [x] `render_glyph_as_xbm(sequence, font_path=..., width_class=...)`が、narrow(8x16)/wide(16x16)の寸法でフォントからXBMを生成する
- [x] `write_gaiji_build_files(entries, destination_dir)`が、各gaijiのXBMファイルと`halfchars.txt`/`fullchars.txt`(`<name> <xbmファイル名>`形式)を書き出す
- [x] `make check`が成功する

## 非対象

- gaiji.sqlite3への実際の書き込み配線・normalize/renderパイプラインへの実配線(将来のタスク)
- 実際のDocker/`fpwmake`実行による統合確認(このセッションではDocker実行環境が無いため、既存fixtureとのバイト形式一致をコードレビュー・ユニットテストで確認する)

## 実施結果

- `src/wikiepwing/gaiji/freepwing_gaiji.py`に`FreePwingGaijiError`・`GaijiBuildEntry`・`xbm_bytes_from_image()`・`render_glyph_as_xbm()`・`write_gaiji_build_files()`を実装した。XBMのビット詰め順(LSB-first、bit=1が前景/黒)を、実際に動作確認済みの`tests/fixtures/handcrafted/generate_gaiji.pl`のバイト列を手動でデコードして確認した上で実装し、既知の小さな画像で厳密にバイト列が一致することをテストで検証した。
- `render_glyph_as_xbm`はnarrow(8x16)/wide(16x16)の寸法でフォントからラスタライズし、`write_gaiji_build_files`は各gaijiのXBMファイルと`halfchars.txt`/`fullchars.txt`(`<name> <xbmファイル名>`形式、実fixtureと同じ行形式)を書き出す。
- mypy strictで`Image.load()`の戻り値型(`PixelAccess | None`)に関するエラーを検出し、None チェックを追加して修正した。
- `tests/test_gaiji_freepwing_gaiji.py`(新規7件)で、実fixtureパターンとのバイト完全一致・非8倍数幅の拒否・全白画像でのゼロバイト・narrow/wideの寸法・build files書き出し(XBM+リストファイル)・空エントリでの空リストファイルを確認した。
- `make check`(format-check/lint/mypy/pytest 1003件)と`git diff --check`が成功した。
