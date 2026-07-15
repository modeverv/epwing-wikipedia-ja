# CURRENT_TASK.md

## Task ID

TASK-O006

## 目的

`ARCHITECTURE.md` 15.4の「SVG sanitize」「external entity禁止」を実装する。SVGはXMLであり、TASK-O005のmagic byte検証の対象外(別の脅威モデル)としたため、専用のsanitizerを実装する。DOCTYPE/ENTITY宣言(XXE・entity展開DoSの経路)を検出したら即座に拒否し、パース後のDOM木から`<script>`/`<foreignObject>`要素、`on*`イベントハンドラ属性、`javascript:` URIを持つ`href`/`xlink:href`属性を取り除いた安全なSVGバイト列を返す。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O006(依存: O005)を読んだ
- [x] `ARCHITECTURE.md` 15.4(「SVG sanitize」「external entity禁止」)を再確認した
- [x] 標準ライブラリの`xml.etree.ElementTree`(`expat`ベース)がDOCTYPE内のカスタムENTITY宣言によるXXE/entity展開DoSに晒されうることを確認し、パース前にDOCTYPE/ENTITY宣言を検出したら即座に拒否する(選択的除去ではなく)fail-closed方針にした
- [x] 新規外部依存(`defusedxml`等)を追加せず、標準ライブラリのみで実装できることを確認した

## 変更予定ファイル

- `src/wikiepwing/media/svg_sanitizer.py`(新規: `SvgSanitizeError`, `sanitize_svg`)
- `tests/test_media_svg_sanitizer.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_svg_sanitizer.py
make check
git diff --check
```

## 完了条件

- [x] `<!DOCTYPE ...>`または`<!ENTITY ...>`を含むSVGは(大文字小文字を問わず)拒否する
- [x] 整形式でないXMLは拒否する(クラッシュしない)
- [x] `<script>`要素は出力から除去される
- [x] `<foreignObject>`要素は出力から除去される
- [x] `on*`(`onload`/`onclick`等、大文字小文字問わず)属性は除去される
- [x] `javascript:`で始まる`href`/`xlink:href`属性は除去される
- [x] 安全な`<svg>`(`<rect>`/`<path>`等のみ)はほぼそのまま(内容が保持されて)出力される
- [x] `make check`が成功する

## 非対象

- SVGの完全なCSS/style属性内スクリプト解析(将来必要になれば別タスク)
- raster変換(TASK-O007)

## 実施結果

- `src/wikiepwing/media/svg_sanitizer.py`に`SvgSanitizeError`・`sanitize_svg`を実装した。生バイト列に(大文字小文字を問わず)`<!DOCTYPE`/`<!ENTITY`が含まれる場合はパース前にfail-closedで拒否する。`xml.etree.ElementTree`でパース後、`<script>`/`<foreignObject>`要素、`on*`イベントハンドラ属性、`javascript:` URIの`href`/`xlink:href`属性を木から除去してから再シリアライズする。ルート要素自体が危険なタグの場合も拒否する。`ElementTree.register_namespace`でSVG/xlink名前空間を登録し、`ns0:`のような自動生成prefixではなく通常の`xmlns=`形式で出力されるようにした。
- `tests/test_media_svg_sanitizer.py`(新規13件)で、安全なSVGの保持・DOCTYPE/ENTITY拒否(大文字小文字問わず)・整形式エラー拒否・script/foreignObject除去・onload/onclick除去(大文字小文字問わず)・javascript: href/xlink:href除去・安全なhrefの保持・危険なroot要素の拒否を確認した。
- `make check`(format-check/lint/mypy/pytest 1162件)と`git diff --check`が成功した。
- 新規外部依存は追加していない(標準ライブラリの`xml.etree.ElementTree`のみで実装)。
