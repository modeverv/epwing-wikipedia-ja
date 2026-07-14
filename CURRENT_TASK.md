# CURRENT_TASK.md

## Task ID

TASK-K009

## 目的

`ARCHITECTURE.md` 11.6(InfoboxBlock)の実際のモデル組み立てとMini-profileでのレンダリングを実装する。TASK-K008の`RawInfobox`から、各fieldの値をBlockへ変換して実際の`InfoboxBlock`/`InfoboxField`を組み立てる`build_infobox_block()`と、それを`mini_layout.py`の`_render_block`ディスパッチへ接続してテキストレンダリングする処理を実装する。title・fields・imagesが全て空の場合は`INFOBOX_EMPTY`Diagnostic(`ARCHITECTURE.md` 11.7の例に既に列挙されているcode)を記録する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-K009(依存: K008,H007)を読んだ
- [x] `ARCHITECTURE.md` 11.6(InfoboxField/InfoboxBlock)・11.7(`INFOBOX_EMPTY`が既存の例コードであることを確認)
- [x] TASK-K008の`RawInfobox`/`parse_infobox_dom`を確認した
- [x] TASK-K004の`build_table_block`(同様のパターン: parse→convert_document→model組み立て)を参考にした

## 変更予定ファイル

- `src/wikiepwing/normalize/infobox_block.py`(新規: `build_infobox_block()`)
- `src/wikiepwing/render/mini_layout.py`(InfoboxBlockの`_render_block`ケースを追加)
- `tests/test_normalize_infobox_block.py`(新規)
- `tests/test_render_mini_layout.py`(InfoboxBlockレンダリングの回帰テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_infobox_block.py tests/test_render_mini_layout.py
make check
git diff --check
```

## 完了条件

- [x] `build_infobox_block(table_element)`が、`RawInfobox`の各fieldの値をBlockへ変換し、`InfoboxBlock`/`InfoboxField`を組み立てる
- [x] title/fields/imagesが全て空の場合、`INFOBOX_EMPTY`のDiagnosticを記録する
- [x] Mini-profileが`InfoboxBlock`を、title(あれば)+各fieldの「name: value」+画像参照のプレースホルダ行としてレンダリングする
- [x] `make check`が成功する

## 非対象

- 画像の実ダウンロード・MediaReference化(別epic)
- Table/Infobox golden set(TASK-K010)

## 実施結果

- `src/wikiepwing/normalize/infobox_block.py`に`build_infobox_block()`を実装した。TASK-K008の`parse_infobox_dom`を使い、各fieldの値ノードを`convert_document`でBlockへ変換して`InfoboxBlock`/`InfoboxField`を組み立てる。title/fields/imagesが全て空の場合は`INFOBOX_EMPTY`(既存の例コード)を記録する。
- `render/mini_layout.py`に`InfoboxBlock`の`_render_block`ケースを追加した。title(あれば)+各fieldの「name: value」(値を`_render_block`で再帰的にフラット化)+各画像srcの`[画像: ...]`プレースホルダ行としてレンダリングする。モジュールdocstringの古い記述(TableBlock wide/complexが未実装のプレースホルダのままという記述、TASK-K005で既に実装済みだったのを直し忘れていた)も併せて修正した。
- `tests/test_normalize_infobox_block.py`(新規6件)・`tests/test_render_mini_layout.py`への追加2件を実装した。
- `make check`(format-check/lint/mypy/pytest 904件)と`git diff --check`が成功した。mypyで`diagnostics`変数の型再代入エラー(`tuple`→`list`)を検出し、別名の変数へ分離して修正した。
