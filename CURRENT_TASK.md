# CURRENT_TASK.md

## Task ID

TASK-H005

## 目的

`ARCHITECTURE.md` 16.1(entry ID)を実装する。安定ID形式`p<page_id>`(例: `p12345`)を生成する関数を実装する。タイトル変更で内部参照が壊れないよう、page IDのみを基準とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H005(依存: F004)とH006(RenderedEntry model、依存: H005)を読んだ
- [x] `ARCHITECTURE.md` 16(RenderedEntry)・16.1(entry ID: `p<page_id>`)を確認した

## 変更予定ファイル

- `src/wikiepwing/render/__init__.py`
- `src/wikiepwing/render/entry_id.py`
- `tests/test_render_entry_id.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_entry_id.py
make check
git diff --check
```

## 完了条件

- [x] `compute_entry_id(page_id: int) -> str`が`p<page_id>`形式の文字列を返す(例: `compute_entry_id(12345) == "p12345"`)
- [x] page_idが正の整数でない場合はエラーを送出する
- [x] `make check`が成功する

## 非対象

- RenderedEntry model本体(TASK-H006)
- Mini layout renderer(TASK-H007)

## 実施結果

- `src/wikiepwing/render/__init__.py`(新規パッケージ)、`src/wikiepwing/render/entry_id.py`に`compute_entry_id`/`EntryIdError`を実装した。
- `tests/test_render_entry_id.py`に4件のテストを追加。
- `uv run pytest tests/test_render_entry_id.py`: 4 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート652件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H005チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-H006 RenderedEntry model。
