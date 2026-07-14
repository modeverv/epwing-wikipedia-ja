# CURRENT_TASK.md

## Task ID

TASK-G008

## 目的

`ARCHITECTURE.md` 12.2のpass `N60`(Convert lists、definition listを含む)の一部として、`<dl>`要素を`DefinitionListBlock`(`entries: tuple[DefinitionEntry, ...]`)へ変換する。連続する`<dt>`を1つのentryのterms、続く連続する`<dd>`をそのentryのdefinitionsとしてグループ化し、次の`<dt>`が現れた時点(直前に`<dd>`があった場合)で新しいentryを開始する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G008(依存: G005)を読んだ
- [x] `model/blocks.py`の`DefinitionListBlock`/`DefinitionEntry`(`terms: tuple[tuple[Inline,...],...]`、`definitions: tuple[tuple[Block,...],...]`)を確認した
- [x] `normalize/lists.py`(G007)のモジュール構成パターンを踏襲する

## 変更予定ファイル

- `src/wikiepwing/normalize/definition_lists.py`
- `tests/test_normalize_definition_lists.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_definition_lists.py
make check
git diff --check
```

## 完了条件

- [x] `is_definition_list(node)`が`<dl>`要素を判定する
- [x] `convert_definition_list(node) -> (DefinitionListBlock, tuple[Diagnostic, ...])`が`<dt>`/`<dd>`をentryへグループ化する
- [x] 連続する複数`<dt>`が1つのentryの複数termsとして保持される
- [x] 連続する複数`<dd>`が1つのentryの複数definitionsとして保持される
- [x] `<dd>`の後に新しい`<dt>`が現れると新しいentryが開始される
- [x] `<dl>`以外の要素を渡すと`ValueError`を送出する
- [x] `make check`が成功する

## 非対象

- 引用/preformatted(TASK-G009)
- 任意のDOMノードをBlockへ振り分ける汎用dispatcher(TASK-G010/G012)

## 実施結果

- `src/wikiepwing/normalize/definition_lists.py`に`is_definition_list`/`convert_definition_list`を実装した。
- `tests/test_normalize_definition_lists.py`に8件のテストを追加。
- `uv run pytest tests/test_normalize_definition_lists.py`: 8 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート558件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G008チェック)、`LOG.md`(新規エントリ)を更新した。
- 次タスク: TASK-G009 Quote/preformatted。
