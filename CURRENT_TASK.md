# CURRENT_TASK.md

## Task ID

TASK-T047

## 目的

`mini_layout.py` の `ImageBlock` レンダリングにおいて、ローカルBMP埋め込み画像が存在しない場合のフォールバックとして `【画像|URL】` を出力するように改修し、Emacs Lookup (`lookup-image-url.el`) によるWebインライン画像の自動取得・表示に対応する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した

## 変更予定ファイル

- `src/wikiepwing/render/mini_layout.py`
- `tests/test_render_mini_layout.py`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
make generate MODEL_DB=data/work/model-diff-ram8.sqlite3 FORCE=1
make check
```

## 完了条件

- [x] `_RenderContext` に `urls_by_media_id` を保持させること
- [x] `ImageBlock` でローカルBMP変換画像が存在しない場合、画像URLがあれば `【画像|URL】` 形式のフォールバックを出力すること
- [x] 対応する単体テスト（`test_unavailable_image_falls_back_to_url_when_media_reference_exists`）を追加しパスすること
- [x] `make check`（全1,485テスト）がパスすること

## 結果

- `mini_layout.py` を改修し、未埋め込み画像について `【画像|URL】` 形式で出力する機能を追加。
- `lookup-image-url.el` のパターンに完全適合し、Lookup バッファ上でのインラインWeb画像自動描画に対応。

## 非対象

- 他のレンダラファイルの変更
