# CURRENT_TASK.md

## Task ID

TASK-O011

## 目的

`ARCHITECTURE.md` 17.2(FreePWING adapterの責務「graphic/gaiji登録」)を実装する。TASK-M007の`write_gaiji_build_files`(gaiji向けXBMビルドファイル書き出し)と全く同じパターンで、TASK-O007がBMP化した画像を`fpwmake`が読むビルド入力(`*.bmp`ファイル+`cgraphs.txt`)として書き出す。`tests/fixtures/handcrafted/cgraphs.txt`(`wiki-mark bitmap.bmp`)・`tests/fixtures/handcrafted/build_fixture.pl`の`add_color_graphic_start("wiki-mark")`/`add_color_graphic_end()`呼び出し(実toolchainで検証済み)を、本モジュールが生成すべき出力形式の一次情報源とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O011(依存: O007,H009)を読んだ
- [x] `ARCHITECTURE.md` 17.2(「graphic/gaiji登録」)を再確認した
- [x] `tests/fixtures/handcrafted/cgraphs.txt`(`名前 ファイル名`形式、gaijiのhalfchars.txt/fullchars.txtと同じ形式)・`build_fixture.pl`の`add_color_graphic_start`/`add_color_graphic_end`呼び出しを確認した
- [x] `src/wikiepwing/gaiji/freepwing_gaiji.py`の`write_gaiji_build_files`(TASK-M007)のパターン(ビルドファイルをdestination_dirへ書き出し、リスト形式のカタログファイルを併せて生成)をそのまま踏襲する方針にした
- [x] `RenderedEntry.graphics`フィールドへの実際の配線・本文中への`add_color_graphic_start`/`add_color_graphic_end`呼び出しの生成(intermediate JSON/`freepwing_build_entries.pl`の拡張)は、TASK-M006/M007がgaijiの割り当てとビルドファイル書き出しを本文への実配線から分離したのと同じ理由で、本タスクの対象外とし、ビルドファイル書き出しのみを実装する

## 変更予定ファイル

- `src/wikiepwing/media/freepwing_graphics.py`(新規: `GraphicBuildEntry`, `FreePwingGraphicsError`, `write_graphics_build_files`)
- `tests/test_media_freepwing_graphics.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_freepwing_graphics.py
make check
git diff --check
```

## 完了条件

- [x] `write_graphics_build_files`が各entryのBMPバイト列を`{name}.bmp`として書き出す
- [x] `cgraphs.txt`に`{name} {name}.bmp`形式の行が(`tests/fixtures/handcrafted/cgraphs.txt`と同じ形式で)書き出される
- [x] 複数entryが与えられた場合、`cgraphs.txt`の行順が入力順を保つ
- [x] destination_dirが存在しない場合は自動作成される
- [x] 不正な`name`(空文字列・空白/改行を含む等、cgraphs.txtの行形式を壊すもの)は`FreePwingGraphicsError`を送出する
- [x] `make check`が成功する

## 非対象

- `RenderedEntry.graphics`への実際のデータ設定・本文中への`add_color_graphic_start`/`add_color_graphic_end`呼び出し生成(intermediate JSON/`freepwing_build_entries.pl`の拡張)
- Image plan/fetch/convert commands(TASK-O012)

## 実施結果

- `src/wikiepwing/media/freepwing_graphics.py`に`GraphicBuildEntry`(name/bmp_bytesの検証付き)・`FreePwingGraphicsError`・`write_graphics_build_files`を実装した。TASK-M007の`write_gaiji_build_files`と同じパターンで、各entryのBMPを`{name}.bmp`として書き出し、`cgraphs.txt`(`tests/fixtures/handcrafted/cgraphs.txt`と同じ`名前 ファイル名`形式)を入力順で生成する。
- `tests/test_media_freepwing_graphics.py`(新規8件)で、BMP/catalog書き出し・空入力での空catalog・ディレクトリ自動作成・入力順保持・不正なname(空文字列/空白/改行)・空bmp_bytesの拒否を確認した。
- `make check`(format-check/lint/mypy/pytest 1199件、ImageMagick依存3件はローカル環境でskip)と`git diff --check`が成功した。
- `RenderedEntry.graphics`への実際のデータ設定・本文中への`add_color_graphic_start`/`add_color_graphic_end`呼び出し生成(intermediate JSON/Perlスクリプトの拡張)は対象外(TASK-M006/M007がgaijiの割り当てとビルドファイル書き出しを本文への実配線から分離したのと同じ理由)。
