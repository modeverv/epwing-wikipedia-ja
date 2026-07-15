# CURRENT_TASK.md

## Task ID

TASK-P004

## 目的

`ARCHITECTURE.md` 21.3(「同じコードパスを使い、profile設定で差を作ります」)を実装する最初の一歩として、`[images]`の`enabled`設定を実際にnormalizeパイプラインへ配線する。AskUserQuestionで確認した方針に従い、`images.enabled=false`のとき記事の`media`が常に空になる(TASK-O001の本文画像抽出・Snapshotのmain image読み出しの両方をスキップする)という、明確で曖昧さのないtoggleのみを実装する。math/tables/search/referencesの他のconfig値は、既に現在の出力がMini相当(mathは常にtext)であるか、ARCHITECTURE.mdが「何を削るか」を仕様として明確にしていないため対象外とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-P004(依存: P002-P003)を読んだ
- [x] `ARCHITECTURE.md` 21.3を再確認した
- [x] AskUserQuestionで「images.enabledのみ配線」の方針を確認した
- [x] `NormalizeOptions`(`[normalize]`セクションのみ消費)・`normalize_html`(`classify_body_media`を常に呼ぶ)・`normalize/orchestrate.py`(`_read_media`+`body_media`を常に`select_media`で統合)の現状を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/pipeline.py`(`NormalizeOptions`に`images_enabled`追加、`normalize_html`が無効時は本文画像抽出をスキップ)
- `src/wikiepwing/normalize/orchestrate.py`(`images_enabled`が偽の場合main imageの読み出しもスキップし`media=()`にする)
- `src/wikiepwing/cli.py`(`normalize`/`build`サブコマンドの`NormalizeOptions`構築に`images_enabled`を追加)
- `tests/test_normalize_pipeline.py`/`tests/test_normalize_orchestrate.py`(追記)
- `tests/test_mini_profile_build.py`(Mini profileで実際に画像がゼロになることを確認するassertion追加)
- 既存の`NormalizeOptions(...)`呼び出し全箇所(`tests/test_golden_normalize.py`/`tests/test_mini_end_to_end_build.py`/`tests/test_lite_profile_build.py`)に新フィールドを追加
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_pipeline.py tests/test_normalize_orchestrate.py tests/test_mini_profile_build.py tests/test_lite_profile_build.py tests/test_golden_normalize.py tests/test_mini_end_to_end_build.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `NormalizeOptions.images_enabled=False`のとき、`normalize_html`が返す`body_media`は常に空タプルになる
- [x] `normalize/orchestrate.py`が`images_enabled=False`のとき、Snapshotのmain imageも含めて`Article.media`が常に空タプルになる
- [x] `images_enabled=True`(デフォルト)のときは既存の挙動(本文画像抽出+main image統合)が変わらない
- [x] `config/profiles/mini.toml`(`images.enabled=false`)を使った実際のend-to-end buildで、生成される記事の`media`が空になることを確認する
- [x] `make check`が成功する

## 非対象

- `math.render_graphics`/`tables.*`/`search.*`/`references.*`の配線(既に現状の出力がMini相当であるか、仕様上の判断が必要なため対象外)
- profile fileの自動選択(TASK-P001で対象外とした通り)

## 実施結果

- `normalize/pipeline.py`の`NormalizeOptions`に`images_enabled: bool = True`(デフォルトで既存の全呼び出し箇所と後方互換)を追加し、`normalize_html`が無効時は`classify_body_media`を呼ばず`body_media=()`にした。
- `normalize/orchestrate.py`の`_normalize_one`で、`images_enabled`が偽の場合はSnapshotのmain image読み出し(`_read_media`)も含めて`media=()`にする(本文画像だけでなく、main imageもスキップする)よう配線した。
- `cli.py`の`normalize`/`build`サブコマンドの`NormalizeOptions`構築に`images_enabled=config.section("images")["enabled"]`を追加した。
- `tests/test_normalize_pipeline.py`(2件追記: デフォルトで本文画像抽出/無効時のskip)、`tests/test_normalize_orchestrate.py`(2件追記: 実際のnormalize実行でmain image+本文画像ありなし双方を確認)、`tests/test_mini_profile_build.py`/`tests/test_lite_profile_build.py`(`images_enabled`をconfigから渡すよう修正し、Mini=0件・Lite=1件以上のmedia_referencesを確認するassertionを追加)。
- `make check`(format-check/lint/mypy/pytest 1236件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- 実際にend-to-end buildで確認した結果、Mini profile(`images.enabled=false`)は`media_references`テーブルが0件、Lite profile(`images.enabled=true`)は1件以上になることを確認した(ARCHITECTURE.md 21.1の「imageなし」を実際に満たす)。
- `math.render_graphics`/`tables.*`/`search.*`/`references.*`は対象外のまま(AskUserQuestionで確認した方針通り)。
