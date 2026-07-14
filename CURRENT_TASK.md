# CURRENT_TASK.md

## Task ID

TASK-E006

## 目的

同一page_idの重複記事を、`ARCHITECTURE.md` 10.5の重複処理rule(revision ID優先、同revision同hashは無視、同revision異hashはfatal診断候補)に従って解決する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E006を読んだ(依存: E004完了済み)
- [x] `ARCHITECTURE.md` 10.5(重複処理)を確認した
- [x] `DATA_CONTRACTS.md`の`ingest_duplicates`table列(page_id/kept_revision_id/dropped_revision_id/kept_hash/dropped_hash/reason/source_sequence)を確認した
- [x] TASK-E004の`RawArticle`、TASK-E005の`Diagnostic`を確認した
- [x] TASK-D010のedge case(同page ID別revision、同revision同hash重複、同revision異hash)を確認した

## 変更予定ファイル

- `src/wikiepwing/ingest/deduplicate.py`
- `tests/test_deduplicate.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_deduplicate.py
make check
git diff --check
```

## 完了条件

- [x] 既存recordが無ければ新規採用(`first_seen`)
- [x] revision IDが大きい方を採用する(到着順に関わらず、新方が大きければ置換、小さければ既存を維持)
- [x] 同revision・同hashは重複として無視しつつ`ingest_duplicates`へ記録する
- [x] 同revision・異hashはconflictとして診断(`Diagnostic`, severity=error)を伴い、既存を維持したまま安全側に倒す
- [x] すべての決定が`ingest_duplicates`table列にそのまま対応する`DuplicateRecord`を返す
- [x] TASK-D010の3つのedge case(同page ID別revision、同revision同hash重複、同revision異hash)が期待通りに解決されることを確認する
- [x] `make check`が成功する

## 非対象

- 実際のDBへの読み書き(既存stateの取得・`ingest_duplicates`への書込はTASK-E007)
- titleによる同一性判定(`ARCHITECTURE.md`が明示的に禁止)

## 実施結果

- `src/wikiepwing/ingest/deduplicate.py`に`ResolutionAction`(enum)、`ExistingArticleState`、`DuplicateRecord`(`ingest_duplicates`table列に対応)、`Resolution`、`resolve_duplicate`を実装した。
- `ARCHITECTURE.md` 10.5の規則通り: 既存recordが無ければ`FIRST_SEEN`、revision IDが大きい方を`REPLACED_BY_NEWER_REVISION`/`KEPT_EXISTING_NEWER_REVISION`として採用(到着順に依存しない)、同revision同hashは`IGNORED_IDENTICAL_DUPLICATE`として無視しつつ記録、同revision異hashは`CONFLICT_KEPT_EXISTING`として既存を維持しつつ`REC_REVISION_HASH_CONFLICT`診断(severity=error)を伴わせた。
- titleによる同一性判定は一切行わない(`ARCHITECTURE.md`の明示的禁止に従う)。
- TASK-D010の3つのedge case(同page ID別revision、同revision同hash重複、同revision異hash)すべてを実際に解決し、期待通りの`action`/`duplicate_record`/`diagnostic`になることを確認した。
- `tests/test_deduplicate.py`に6件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート338件、`git diff --check`が成功した。

**判断・注意点**

- 実際のDBからの既存state取得・`ingest_duplicates`への書込はTASK-E007(Batch repository writer)の責務とし、本タスクは純粋な決定ロジックのみを提供した(page_idごとにDB row 1件を都度SELECTすることで、bounded memoryのまま重複解決を行える設計を想定)。
