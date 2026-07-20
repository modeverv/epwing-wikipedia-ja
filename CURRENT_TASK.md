# CURRENT_TASK.md

## Task ID

TASK-T038

## 目的

`EDIT.md` に定義した標準レイアウト方針に基づき、`mini_layout.py` における Infobox（`【項目|値】`）、見出し（`■ 見出し`）、リスト（`1. ` および ` ・`）、Table（テキストグリッド化）の表示フォーマットを改修する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `EDIT.md`が作成されていること

## 変更予定ファイル

- `EDIT.md`
- `src/wikiepwing/render/mini_layout.py`
- `tests/test_render_mini_layout.py`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_render_mini_layout.py
make check
```

## 完了条件

- [x] Infobox が `【Infobox {title}】` および `【項目名|値】` の形式で出力されること
- [x] セクション見出しが `■ 見出し名` の形式で出力されること
- [x] 箇条書きリストが ` ・` (インデント + 中黒)、順序付きリストが `1. ` 形式で出力されること
- [x] Table がテキストグリッド形式で出力されること
- [x] 関連するすべてのテストスイートが正常にパスすること

## 結果

- `EDIT.md` を作成し、標準レイアウト・編集方針（Infobox, 見出し, リスト, Table）を策定・明記。
- `src/wikiepwing/render/mini_layout.py` を改修し、以下の表示フォーマットを適用：
  - **Infobox**: `【Infobox {title}】` および `【項目名|値】` 形式
  - **セクション見出し**: `■ {見出し名}` 形式
  - **箇条書きリスト**: ` ・{内容}` 形式 / 順序付きリスト `1. {内容}` 形式
  - **表（Table）**: 全テーブルのテキストグリッド（`|` 区切り）形式化
- `tests/test_render_mini_layout.py` を新しい指定形式に合わせて修正し、1,485件の全テストおよび `make check` をクリア。

## 非対象

- HTML直出し等の非テキスト出力
