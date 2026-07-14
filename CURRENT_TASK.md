# CURRENT_TASK.md

## Task ID

TASK-G012

## 目的

`TASKS.md` TASK-G012(依存: F007-F008,G011)を実装する。raw.sqlite3の`accepted`記事を読み出し、既存のHTML正規化パイプライン(G001-G011)を通して`Article`を組み立て、`model/validate.py`で検証し、`model/canonical.py`+`model/logical_hash.py`でcanonical JSON化・ハッシュ計算した上でzstd圧縮し、`model.sqlite3`(TASK-F007のschema)へ書き込む。`ingest/orchestrate.py`(TASK-E008/E010)と同じmanifest lifecycle(running/complete/failed、`--force`)パターンに従う。`wikiepwing normalize` CLIコマンドも追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G012を読んだ
- [x] `ingest/orchestrate.py`(`run_ingest`/`IngestManifest`/manifest lifecycle)、`ingest/repository.py`(`RawRepository`のbatch/replace-children pattern)、`ingest/zstd_codec.py`、`cli.py`の`ingest`サブコマンド配線を確認した
- [x] `migrations/raw/001_initial.sql`(`articles`/`redirects`/`categories`/`article_licenses`+`licenses`/`main_images`)と`migrations/model/001_initial.sql`(`articles`/`links`/`media_references`/`diagnostics`)を確認した
- [x] `Article`の各fieldとraw.sqlite3データのmapping方針を決定した(下記「判断」参照)

## 変更予定ファイル

- `src/wikiepwing/normalize/pipeline.py`(HTML文字列→`tuple[Block,...]`+diagnosticsの1関数化)
- `src/wikiepwing/model/repository.py`(`ModelRepository`: batch書き込み)
- `src/wikiepwing/normalize/orchestrate.py`(`run_normalize`とmanifest lifecycle)
- `src/wikiepwing/cli.py`(`normalize`サブコマンド追加)
- `tests/test_normalize_pipeline.py`
- `tests/test_model_repository.py`
- `tests/test_normalize_orchestrate.py`
- `tests/test_cli.py`(normalizeサブコマンドのparse確認を追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_pipeline.py tests/test_model_repository.py tests/test_normalize_orchestrate.py tests/test_cli.py
make check
git diff --check
```

## 完了条件

- [x] `normalize_html(html, *, max_dom_depth, html_recover, remove_edit_ui, remove_navboxes, remove_authority_control) -> (tuple[Block,...], tuple[Diagnostic,...])`がparse→root selection→unsafe node除去→document変換→whitespace正規化を一貫して行う
- [x] `ModelRepository`がarticles行のUPSERT+`links`/`media_references`/`diagnostics`子行の置換をbatchトランザクションで行う
- [x] `run_normalize`がraw.sqlite3の`accepted`記事を読み、Article組み立て→validate→canonical encode+logical hash→zstd圧縮→書き込みを行う
- [x] `normalize_status`を`complete`/`fallback`(UnsupportedBlockを含む)/`rejected`(validate_articleがerror/fatalを検出)の3値で判定する
- [x] manifestのrunning/complete/failed lifecycleと`--force`挙動が`ingest/orchestrate.py`と同様に動作する
- [x] `wikiepwing normalize`サブコマンドが動作する(`--raw-database`/`--model-database`/`--run-id`/`--manifest-path`/`--force`等)
- [x] `make check`が成功する

## 非対象

- 内部/外部リンクの実HTML変換(`<a>`要素の変換自体、Epic H)。`links`テーブルへの書き込みロジックは実装するが、現時点で`InternalLinkInline`を生成する変換器が無いため実質空になる
- 画像の実HTML変換(`<img>`要素、Epic O)。`media`はraw.sqlite3の`main_images`由来のみとする
- Table/Infobox/Math/Referencesの実変換(Epic K/L/N)

## 判断(Article field ⇔ raw.sqlite3 mapping)

- `page_id`/`revision_id`/`title`: raw articlesの同名列から直接
- `normalized_title`: raw articlesの`normalized_title`列から直接
- `source_url`: raw articlesの`url`列から
- `source_date_modified`: raw articlesの`date_modified`(ISO文字列、tz-aware)を`datetime.fromisoformat`で復元
- `abstract`: 正規化後の最初の`ParagraphBlock`をflattenしたテキスト(存在しなければ`None`)
- `blocks`: `normalize_html`の出力
- `aliases`: raw `redirects`子テーブルの各行を`source="redirect"`、`confidence=1.0`として`Alias`化
- `categories`: raw `categories`子テーブルの`category_name`列
- `media`: raw `main_images`(存在すれば`role="main"`の`MediaReference`1件)
- `diagnostics`: normalize pipelineのdiagnostics + `validate_article`のdiagnostics(page_id/titleをこの記事の値でスタンプ)
- `source_license_ids`: raw `licenses.identifier`(`article_licenses`経由)

## 実施結果

- `src/wikiepwing/normalize/pipeline.py`(`NormalizeOptions`/`normalize_html`)、`src/wikiepwing/model/repository.py`(`ModelRepository`)、`src/wikiepwing/normalize/orchestrate.py`(`run_normalize`他)を実装し、`src/wikiepwing/cli.py`に`normalize`サブコマンドを追加した。
- `tests/test_normalize_pipeline.py`(6)、`tests/test_model_repository.py`(3)、`tests/test_normalize_orchestrate.py`(5)、`tests/test_cli.py`への追加(2)で合計30件近いテストを追加。
- `uv run pytest tests/test_normalize_pipeline.py tests/test_model_repository.py tests/test_normalize_orchestrate.py tests/test_cli.py`: 30 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート609件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G012チェック)、`LOG.md`(新規エントリ)を更新した。
- 静的レビュー中に`ReferencesBlock.items`/`UnorderedListBlock.items`のfield名衝突バグを発見・修正し、回帰テストを追加した。
- 作業中にBash実行環境が長時間一時利用不可になったが、静的レビューで対応し復旧後にテスト実行を完了した。
- 次タスク: TASK-G013 Baseline golden snapshots。
