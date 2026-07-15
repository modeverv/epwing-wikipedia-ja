# CURRENT_TASK.md

## Task ID

TASK-N003

## 目的

`ARCHITECTURE.md` 15.7の"3. SVG/PNGへ安全にレンダリング"を実装する。ユーザーと相談の上、Node.js/外部LaTeXツールチェーンを新規導入するのではなく、matplotlibの組み込みmathtext機能(プロセス内、TeXマクロの完全なサブセットではなく実用的な部分集合をサポート)を使う方針を採用した。`matplotlib.mathtext.math_to_image`でTeX風の数式をSVG/PNGへレンダリングする。「Isolated」の意味は、外部プロセスのサンドボックスではなく、レンダリング失敗(構文エラー等)を1つの数式ごとに隔離し、他の数式・記事全体のビルドを止めないという意味で実装する(ARCHITECTURE.md 3.5"機能不足は劣化表示し、データ損失を記録する"の原則に従う)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-N003(依存: N002)を読んだ
- [x] `ARCHITECTURE.md` 15.7("3. SVG/PNGへ安全にレンダリング")を再確認した
- [x] ユーザーに新規依存導入の方針を確認し、matplotlib mathtext(プロセス内、新規外部ツールチェーン無し)を採用する承認を得た
- [x] `matplotlib.mathtext.math_to_image`のAPI(TeX風文字列を`$...$`で囲んで渡す、`format`引数でsvg/png切替)を確認した

## 変更予定ファイル

- `pyproject.toml`(matplotlibを依存に追加、`uv add`で実施済み)
- `src/wikiepwing/normalize/math_renderer.py`(新規: `MathRenderError`, `render_math_to_image()`)
- `tests/test_normalize_math_renderer.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv add "matplotlib==3.11.0"
uv run pytest tests/test_normalize_math_renderer.py
make check
git diff --check
```

## 完了条件

- [x] `render_math_to_image(tex_source, *, image_format="svg")`が、TeX風の数式文字列を実際にSVG/PNG bytesへレンダリングする
- [x] 構文エラーのある数式(mathtextがパースできない)に対して、記事全体を止めずに`MathRenderError`を送出する(呼び出し側が1つの数式単位でcatchしてfallbackできる設計)
- [x] svg/png両方のフォーマットに対応する
- [x] `make check`が成功する

## 非対象

- 実際のcache格納(TASK-N004)・raster変換(TASK-N005)・inline/block layout配線(TASK-N006)
- MediaWikiのtexvcが許す完全なTeXマクロ集合のサポート(matplotlib mathtextのサブセットに制限されることをdocstringに明記する)

## 実施結果

- `pyproject.toml`に`matplotlib==3.11.0`を新規依存として追加した(`uv add`)。
- `src/wikiepwing/normalize/math_renderer.py`に`MathRenderError`・`render_math_to_image()`を実装した。`matplotlib.mathtext.math_to_image`をプロセス内で呼び出し、失敗を`MathRenderError`として1数式単位で隔離する。
- 実装中に発見した問題: matplotlibのSVG出力は、壁時計タイムスタンプ(`<dc:date>`)とプロセスごとにランダムなglyph-idソルト(`svg.hashsalt`未設定時)を埋め込むため、同じ数式でも実行のたびに異なるバイト列になっていた。本プロジェクトの再現可能ビルドという目標(pinされたDocker snapshot等の既存方針)と相容れないため、`svg.hashsalt`を固定値へ設定し、出力後に`<dc:date>`要素を正規表現で除去することで決定論的な出力にした。
- `tests/test_normalize_math_renderer.py`(新規10件)で、SVG/PNGレンダリング・デフォルトフォーマット・異なる数式での異なる出力・SVG/PNG双方の決定性(タイムスタンプ/ソルト問題の回帰テスト)・空/空白のみのsourceでのエラー・未対応マクロでのエラー・失敗後も後続のレンダリングが正常に動作することを確認した。
- `make check`(format-check/lint/mypy/pytest 1053件)と`git diff --check`が成功した。
