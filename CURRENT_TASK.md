# CURRENT_TASK.md

## Task ID

TASK-H004

## 目的

`ARCHITECTURE.md` 13.3(alias source: redirectsを候補の一つとし、"aliasにはsourceとconfidenceを付けます")を実装する、raw.sqlite3の`redirects`テーブルからの`Alias`抽出を独立した公開関数として切り出す。`TASK-G012`(`normalize/orchestrate.py`)実装時に同等ロジックを`_read_aliases`としてprivateに埋め込んでいたため、本タスクでEpic Hの正式な場所(`links`パッケージ)へ抽出し、テスト可能な公開APIとして再構成する。`normalize/orchestrate.py`はこの関数を再利用するようリファクタする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H004(依存: E008)を読んだ
- [x] `ARCHITECTURE.md` 13.3(alias source一覧、redirectsが候補の一つ)を確認した
- [x] `normalize/orchestrate.py`の既存`_read_aliases`実装(TASK-G012時点)を確認した。これを`links`パッケージへ移設する

## 変更予定ファイル

- `src/wikiepwing/links/redirect_aliases.py`
- `src/wikiepwing/normalize/orchestrate.py`(`_read_aliases`を削除し`extract_redirect_aliases`を利用)
- `tests/test_links_redirect_aliases.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_links_redirect_aliases.py tests/test_normalize_orchestrate.py
make check
git diff --check
```

## 完了条件

- [x] `extract_redirect_aliases(connection, page_id) -> tuple[Alias, ...]`がraw.sqlite3の`redirects`テーブルから`target_page_id`に一致する行を`ordinal`順に`Alias(source="redirect", confidence=1.0)`へ変換する
- [x] 該当するredirectが無い場合は空tupleを返す
- [x] `normalize/orchestrate.py`が`_read_aliases`を削除し、この関数を利用するようリファクタされている
- [x] `make check`が成功する

## 非対象

- redirect以外のalias source(title/normalized title variant/HTML display title/lead bold/Wikidata、将来のtaskで対応)
- Stable entry IDs(TASK-H005)

## 実施結果

- `src/wikiepwing/links/redirect_aliases.py`に`extract_redirect_aliases`を実装した。
- `src/wikiepwing/normalize/orchestrate.py`の`_read_aliases`を削除しこの関数を利用するようリファクタした。
- `tests/test_links_redirect_aliases.py`に2件のテストを追加。
- `uv run pytest tests/test_links_redirect_aliases.py tests/test_normalize_orchestrate.py`: 7 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート648件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H004チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-H005 Stable entry IDs。
