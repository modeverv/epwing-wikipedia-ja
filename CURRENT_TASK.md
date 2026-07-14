# CURRENT_TASK.md

## Task ID

TASK-H002

## 目的

`ARCHITECTURE.md` 12.5(内部リンク解決)の手順5-7(normalized title生成/raw DBでpage ID解決/redirect targetの扱い)を実装する。`TASK-H001`の`ParsedInternalUrl`を受け取り、raw.sqlite3の`articles`/`redirects`テーブルに対してpage ID解決を行い、`InternalLinkInline`の`resolution`値(`resolved`/`missing`/`externalized`)を決定する。namespace 0(記事本文)以外(`Category:`等)は本プロジェクトの初期scope(`source.namespace=0`)がnamespace 0のみを取り込む前提のため、`externalized`として扱う。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H002(依存: H001,E008)を読んだ
- [x] `ARCHITECTURE.md` 12.5の手順5-7を確認した
- [x] `ingest/repository.py`の`normalize_title`(NFKC+strip)を再利用する
- [x] `migrations/raw/001_initial.sql`の`articles`(`normalized_title`列、`ingest_status`)・`redirects`(`normalized_redirect_title`、`target_page_id`)テーブルを確認した

## 変更予定ファイル

- `src/wikiepwing/links/resolver.py`
- `tests/test_links_resolver.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_links_resolver.py
make check
git diff --check
```

## 完了条件

- [x] `resolve_internal_link(parsed, connection, *, follow_redirects=True) -> ResolvedLink`が`articles.normalized_title`に直接一致する記事を`resolved`として解決する
- [x] `redirects.normalized_redirect_title`に一致するredirectを`follow_redirects=True`の場合に`resolved`(target_page_id)として解決する
- [x] `follow_redirects=False`の場合、redirect一致があっても`missing`とする
- [x] どちらにも一致しない場合`missing`とする
- [x] `parsed.namespace`がNoneでない場合(Category等)は`externalized`とする
- [x] `make check`が成功する

## 非対象

- EPWING entry IDへの変換(後続epic)
- External link policy(TASK-H003)

## 実施結果

- `src/wikiepwing/links/resolver.py`に`resolve_internal_link`/`ResolvedLink`を実装した。
- `tests/test_links_resolver.py`に6件のテストを追加。
- `uv run pytest tests/test_links_resolver.py`: 6 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート638件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H002チェック)、`LOG.md`(新規エントリ)を更新した。
- namespace付きlinkを`externalized`とする判断は、初期scope(namespace 0のみ取り込み)に基づくdocumented assumption。
- 次タスク: TASK-H003 External link policy。
