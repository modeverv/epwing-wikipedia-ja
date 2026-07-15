# CURRENT_TASK.md

## Task ID

TASK-N007

## 目的

`ARCHITECTURE.md` 15.7の数式変換優先順位の最後のステップ「5. 失敗時はTeX/plain textへフォールバック」を実装する。TASK-N003(レンダラ)・TASK-N004(cache)・TASK-N005(raster変換)を1つのパイプラインとして呼び出し、途中のどの段階で失敗しても(未対応のTeX構文、デコード失敗等)例外を外に漏らさず、TASK-N001が保存済みのplain text(text alternativeまたはTeX source)へフォールバックし、診断を1件記録する関数を実装する。1記事の数式1個の失敗が記事全体のbuildを止めないようにする(ARCHITECTURE.md 3.5の障害分離方針)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-N007(依存: N001)を読んだ
- [x] `ARCHITECTURE.md` 15.7(数式変換の優先順位、ステップ5「失敗時はTeX/plain textへフォールバック」)を再確認した
- [x] TASK-N003の`MathRenderError`・TASK-N005の`MathRasterError`(いずれも`ValueError`)を確認した
- [x] TASK-N004の`MathCache.get_or_render`(`render`callableが例外を送出した場合はそのまま伝播する、という既存契約)を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/math_fallback.py`(新規: `MathRenderOutcome`, `render_math_with_fallback`)
- `tests/test_normalize_math_fallback.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_math_fallback.py
make check
git diff --check
```

## 完了条件

- [x] `render_math_with_fallback`が、レンダリング・cache・raster変換すべて成功する場合はBMPバイト列を返す(`fallback_text`は`None`)
- [x] `MathRenderError`・`MathRasterError`いずれが発生しても例外を再送出せず、`fallback_text`に指定したplain textを設定し、`MATH_RENDER_FAILED`診断を1件返す
- [x] cache_keyが`None`でない場合、2回目の呼び出しでレンダラが再度呼ばれない(TASK-N004のcacheがそのまま機能する)
- [x] `make check`が成功する

## 非対象

- 実際のgraphic byteをRenderedEntry.graphics/EPWING graphicへ埋め込む配線(EPIC O)
- MathBlock/MathInlineへのfallback結果の再配線(既にTASK-N006でsource自体がplain textとして保存されているため、この関数は将来のEPIC O配線が使うレンダリング層のユーティリティ)

## 実施結果

- `src/wikiepwing/normalize/math_fallback.py`に`MathRenderOutcome`・`render_math_with_fallback`を実装した。TASK-N004の`MathCache.get_or_render`経由でTASK-N003の`render_math_to_image`(PNG)を呼び、TASK-N005の`convert_png_to_bmp`でBMP化する。`MathRenderError`/`MathRasterError`のいずれかが送出された場合は例外を再送出せず、呼び出し側が渡した`fallback_text`と`MATH_RENDER_FAILED`診断1件を返す。
- `tests/test_normalize_math_fallback.py`(新規4件)で、成功時のBMP返却・失敗時のtext fallback+診断・cache経由での2回目呼び出し省略・`None`cache_keyでの常時レンダリングを確認した。
- `make check`(format-check/lint/mypy/pytest 1087件)と`git diff --check`が成功した。
- これでEPIC N(数式)のTASK-N001からN007まで完了した。
