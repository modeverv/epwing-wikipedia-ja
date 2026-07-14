# CURRENT_TASK.md

## Task ID

TASK-L002

## 目的

`ARCHITECTURE.md` 12.2の"N100 Convert references"の続きとして、記事末尾の参照リスト(MediaWiki Cite拡張が出力する`<ol class="references"><li id="cite_note-X">...</li>...</ol>`)を解析する。各`<li>`から、脚注番号に対応する`note_id`(`<sup>`側のtarget_idと同じ値、TASK-L001)と、実際の引用文content(`<span class="mw-cite-backlink">`の巻き戻しリンクを除いた`<span class="reference-text">`部分、または無ければbacklinkを除いた残り)を抽出する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-L002(依存: L001)を読んだ
- [x] MediaWiki Cite拡張の参照リスト実際のHTML出力形式(`<ol class="references">`、`<span class="mw-cite-backlink">`、`<span class="reference-text">`)を確認した(ドキュメントにアルゴリズムが無いため、この形式を判断根拠として採用する)
- [x] `model/blocks.py`の`ReferencesBlock`(`items: tuple[tuple[Inline,...],...]`、id情報を持たない設計)を確認した。本タスクの`note_id`はTASK-L003での実際のBlock組み立てには使わないが、将来のマーカー⇔リスト対応付けの布石として抽出しておく

## 変更予定ファイル

- `src/wikiepwing/normalize/reference_list.py`(新規: `RawReferenceItem`, `is_reference_list()`, `parse_reference_list()`)
- `tests/test_normalize_reference_list.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_reference_list.py
make check
git diff --check
```

## 完了条件

- [x] `is_reference_list(node)`が、`class`に`references`トークンを含む`<ol>`要素を検出する
- [x] `parse_reference_list(node)`が、各`<li>`の`id`属性を`note_id`として、`<span class="reference-text">`があればその子要素、無ければbacklink要素を除いた残りの子要素を`content`として抽出する
- [x] `make check`が成功する

## 非対象

- 実際の`ReferencesBlock`への変換・レンダリング(TASK-L003)
- インラインマーカーとの実際のクロスリファレンス機能(モデルにid情報を保持する設計が無いため対象外)

## 実施結果

- `src/wikiepwing/normalize/reference_list.py`に`RawReferenceItem`・`is_reference_list()`・`parse_reference_list()`を実装した。`<ol class="references">`を検出し、各`<li>`から`id`属性(`note_id`)と、`<span class="reference-text">`があればその子要素、無ければ`<span class="mw-cite-backlink">`を除いた残りの子要素を`content`として抽出する。
- `tests/test_normalize_reference_list.py`(新規8件)で、リスト検出・非検出・note_id+reference-text抽出・複数項目の順序保持・backlinkのみ除去のフォールバック・id欠落時のNone・非リストへの呼び出し時のエラー・非`<li>`子要素の無視を確認した。
- `make check`(format-check/lint/mypy/pytest 927件)と`git diff --check`が成功した。
