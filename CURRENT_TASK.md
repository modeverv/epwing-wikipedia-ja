# CURRENT_TASK.md

## Task ID

TASK-F001

## 目的

`ARCHITECTURE.md` 11.7の意味論モデル層`Diagnostic`(`Article.diagnostics`に埋め込まれる自己完結的な診断record)を実装する。`DATA_CONTRACTS.md`のArticle JSON contractの`diagnostics`配列要素として往復可能なJSON codecを持つ。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F001を読んだ(依存: E001完了済み。詳細実装列は無く`ARCHITECTURE.md`/`DATA_CONTRACTS.md`が正本)
- [x] `ARCHITECTURE.md` 11.1(Article)・11.7(Diagnostic)を確認した
- [x] `DATA_CONTRACTS.md` 6節(Article JSON contract)の`diagnostics`配列を確認した
- [x] `src/wikiepwing/ingest/validate.py`の既存(ingest層専用)`Diagnostic`と役割が異なる(model層は自己完結、page_id/title/stageを内包)ことを確認した

## 変更予定ファイル

- `src/wikiepwing/model/__init__.py`
- `src/wikiepwing/model/diagnostics.py`
- `tests/test_model_diagnostics.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_diagnostics.py
make check
git diff --check
```

## 完了条件

- [x] `Diagnostic`が`ARCHITECTURE.md` 11.7のfield(code/severity/stage/page_id/title/message/source_path/source_excerpt/details)を持つ
- [x] 構築時にcode/severity/stage/messageの空文字・不正severityを拒否する
- [x] `payload()`と`parse_diagnostic()`が相互に往復可能である
- [x] 不正なJSON(objectでない、必須field欠落・型不一致)を明確なエラーで拒否する
- [x] `make check`が成功する

## 非対象

- ingest層`Diagnostic`(`wikiepwing.ingest.validate.Diagnostic`)からmodel層`Diagnostic`への変換(normalize統合時に別途対応)
- Inline/Block/Article本体のモデル化(TASK-F002以降)

## 実施結果

- `src/wikiepwing/model/diagnostics.py`に`Diagnostic`(`ARCHITECTURE.md` 11.7準拠、code/severity/stage/page_id/title/message/source_path/source_excerpt/details)、`parse_diagnostic`、`DiagnosticError`を実装した。
- 構築時にcode/severity/stage/messageの空文字・不正severityを`__post_init__`で拒否した。
- `payload()`/`parse_diagnostic()`が相互に往復可能であることを、optional fieldがNoneの場合を含めて確認した。
- `tests/test_model_diagnostics.py`に12件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート381件、`git diff --check`が成功した。

**判断・注意点**

- `wikiepwing.ingest.validate.Diagnostic`(ingest層、code/severity/message/detailsのみ)からmodel層`Diagnostic`への変換は、normalizeパイプライン統合時(Epic G以降)に別途実装する。両者は役割が異なるため統合・共有はしない。
