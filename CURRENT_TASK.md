# CURRENT_TASK.md

## Task ID

TASK-L001

## 目的

`ARCHITECTURE.md` 12.2の"N100 Convert references"パスの最初の段階として、本文中の脚注マーカー(MediaWikiのCite拡張が出力する`<sup class="reference"><a href="#cite_note-X">[1]</a></sup>`)を解析する。可視ラベル(例: "[1]")と、対応する参照リスト項目へのフラグメントID(`cite_note-X`)を抽出する。EPWINGはハイパーリンクを持てないプレーンテキストであるため、実際のInline型としては可視ラベルをそのまま使う(既存の`convert_inline_nodes`の透過的wrapper fallbackで`<sup>`/`<a>`を再帰すれば同じテキストは既に得られる)が、TASK-L002(参照リスト解析)が脚注マーカーと参照リスト項目を対応付けるために`target_id`の抽出が必要となるため、本タスクで独立した解析関数として実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-L001(依存: G001)を読んだ
- [x] `ARCHITECTURE.md` 11.3(Inline union)にreference marker専用の型が無く、`UnsupportedInline`のような汎用型のみであることを確認した
- [x] MediaWiki Cite拡張の実際のHTML出力形式(`<sup id="cite_ref-..." class="reference"><a href="#cite_note-...">[1]</a></sup>`)を確認した(ドキュメントにアルゴリズムが無いため、この形式を判断根拠として採用する)
- [x] `model/blocks.py`の`ReferencesBlock`(`items: tuple[tuple[Inline,...],...]`)を確認した(TASK-L002-L003で使う)

## 変更予定ファイル

- `src/wikiepwing/normalize/reference_marker.py`(新規: `ReferenceMarker`, `is_reference_marker()`, `parse_reference_marker()`)
- `tests/test_normalize_reference_marker.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_reference_marker.py
make check
git diff --check
```

## 完了条件

- [x] `is_reference_marker(node)`が、`class`に`reference`トークンを含む`<sup>`要素を検出する
- [x] `parse_reference_marker(node)`が、可視ラベル(flattenされたテキスト)と、内部の`<a href="#...">`から抽出した`target_id`(`#`除去済み)を返す
- [x] 対応する`<a>`が無い、またはhrefがフラグメントでない場合は`target_id=None`
- [x] `make check`が成功する

## 非対象

- 参照リスト(`<ol class="references">`)の解析(TASK-L002)
- 実際のレンダリング(TASK-L003)
- 本文Inline変換パイプラインへの実配線(既存の透過的wrapper fallbackで可視テキストは既に得られるため、target_id活用はL002以降で行う)

## 実施結果

- `src/wikiepwing/normalize/reference_marker.py`に`ReferenceMarker`・`is_reference_marker()`・`parse_reference_marker()`を実装した。`<sup class="reference">`要素を検出し、可視ラベル(flattenテキスト)と内部`<a href="#...">`から抽出したフラグメントID(`#`除去済み)を返す。
- `tests/test_normalize_reference_marker.py`(新規7件)で、マーカー検出・非マーカー(素の`<sup>`・`<span>`)の非検出・label/target_id抽出・`<a>`欠落時/フラグメント以外のhref時の`target_id=None`・非マーカーへの`parse_reference_marker`呼び出し時のエラーを確認した。
- `make check`(format-check/lint/mypy/pytest 919件)と`git diff --check`が成功した。
