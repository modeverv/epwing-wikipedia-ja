# CURRENT_TASK.md

## Task ID

TASK-L003

## 目的

`ARCHITECTURE.md` 12.2の"N100 Convert references"を完成させる。TASK-L002の`RawReferenceItem`から実際の`ReferencesBlock`(`items: tuple[tuple[Inline,...],...]`)を組み立て、`convert_block.py`のディスパッチへ配線し、Mini-profileでのレンダリングを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-L003(依存: L002,H007)を読んだ
- [x] `model/blocks.py`の`ReferencesBlock`(`items: tuple[tuple[Inline,...],...]`)を確認した
- [x] `reference_list.py`の`parse_reference_list`/`RawReferenceItem`を確認した
- [x] `build_references_block`は`convert_inline_nodes`のみで済み(`convert_document`不要)、`table_block.py`/`infobox_block.py`のような循環import回避が不要であることを確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/references_block.py`(新規: `build_references_block()`)
- `src/wikiepwing/normalize/convert_block.py`(`<ol class="references">`をディスパッチするよう配線)
- `src/wikiepwing/render/mini_layout.py`(ReferencesBlockの`_render_block`ケースを追加)
- `tests/test_normalize_references_block.py`(新規)
- `tests/test_normalize_convert_block.py`(配線の回帰テスト追加)
- `tests/test_render_mini_layout.py`(レンダリングの回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_references_block.py tests/test_normalize_convert_block.py tests/test_render_mini_layout.py
make check
git diff --check
```

## 完了条件

- [x] `build_references_block(node)`が、各`RawReferenceItem.content`を`convert_inline_nodes`でInlineへ変換し`ReferencesBlock`を組み立てる
- [x] `convert_block()`が`<ol class="references">`を`ReferencesBlock`へディスパッチする
- [x] Mini-profileが`ReferencesBlock`を、各項目を"[N] 引用文"の形式で番号付きレンダリングする
- [x] `make check`が成功する

## 非対象

- インラインマーカーとの実際のクロスリファレンス(番号の対応付けはDOM順による暗黙の対応のみ)

## 実施結果

- `src/wikiepwing/normalize/references_block.py`に`build_references_block()`を実装した。`parse_reference_list`(TASK-L002)の各`RawReferenceItem.content`を`convert_inline_nodes`でInlineへ変換し`ReferencesBlock`を組み立てる。
- `convert_block.py`に`is_reference_list`判定を追加した。参照リストも`<ol>`要素であるため、`is_ordered_list`より**前**にチェックする必要があることに気づき、その順序で配線した(誤って通常のOrderedListBlockへ変換されるのを防ぐ)。
- `render/mini_layout.py`に`ReferencesBlock`の`_render_block`ケース(`_render_references`)を追加した。各項目を"[N] 引用文"としてDOM順の番号付きでレンダリングする。
- `tests/test_normalize_references_block.py`(新規3件)・`tests/test_normalize_convert_block.py`への追加2件(参照リストの正しいディスパッチ、通常の`<ol>`が従来通りOrderedListBlockになること)・`tests/test_render_mini_layout.py`への追加2件を実装した。
- `make check`(format-check/lint/mypy/pytest 934件)と`git diff --check`が成功した。
