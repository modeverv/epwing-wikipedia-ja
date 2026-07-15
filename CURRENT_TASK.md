# CURRENT_TASK.md

## Task ID

TASK-O001

## 目的

`ARCHITECTURE.md` 15.1(「Normalizationは画像参照だけを保存します。ダウンロードしません。」)・15.2(`MediaReference`のフィールド定義)を実装する。`<img>`(および`<figure>`+`<figcaption>`で包まれたもの)というDOM要素から、既存の`wikiepwing.model.article.MediaReference`を抽出する関数を実装する。`role`は本タスクでは常に`"unknown"`とし(role分類はTASK-O002)、`media_id`は既存の`normalize/orchestrate.py`の`_read_media`(Wikimedia Enterprise Snapshotのmain image由来)が採用している`media_id == source_url`という前例に合わせる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O001(依存: G001,F004)を読んだ
- [x] `ARCHITECTURE.md` 15.1/15.2を再確認した
- [x] `model/article.py`の既存`MediaReference`(`media_id`/`source_url`必須、`role`は`Literal["main","infobox","lead","body","icon","unknown"]`)を確認した
- [x] `normalize/orchestrate.py`の`_read_media`が`media_id=row["content_url"]`(=`source_url`と同じ値)を採用している前例を確認した
- [x] TASK-O002(role classification)・TASK-O010(attribution model)がともにTASK-O001に依存しており、本タスクの出力(`role="unknown"`のMediaReference)がそのまま入力になる設計であることを確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/media_node.py`(新規: `is_image_node`, `parse_image_node`, `is_figure_with_image`, `parse_figure_media`)
- `tests/test_normalize_media_node.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_media_node.py
make check
git diff --check
```

## 完了条件

- [x] `<img src="..." alt="..." width=".." height="..">`から`MediaReference(media_id=source_url, source_url=..., alt_text=..., role="unknown", source_width=.., source_height=..)`を抽出できる
- [x] `src`属性のURLパスから`source_name`(ファイル名部分、URLデコード済み)を導出する
- [x] `width`/`height`属性が欠落・不正な場合は`None`になる(クラッシュしない)
- [x] `<figure><img ...><figcaption>text</figcaption></figure>`から`caption`にfigcaptionのテキストが入る
- [x] `src`属性がない`<img>`はMediaReferenceを生成できない(`media_id`/`source_url`が空文字列を許さない既存contractのため、呼び出し側が判別できるようNoneを返すか例外にする)
- [x] `make check`が成功する

## 非対象

- role classification(TASK-O002)
- 実際のダウンロード・selection policy(TASK-O003-O012)
- `convert_block`/`ImageBlock`への配線(まだ`ImageBlock`は`media_id`のみのplaceholderであり、配線タイミングは後続タスクの範囲と判断)

## 実施結果

- `src/wikiepwing/normalize/media_node.py`に`is_image_node`/`parse_image_node`/`is_figure_with_image`/`parse_figure_media`を実装した。`parse_image_node`は`src`属性が無い`<img>`に対しては`None`を返す(既存の`MediaReference.__post_init__`が空文字列の`source_url`を許さないため)。`source_name`はURLパスの最後のセグメントをURLデコードして導出する。`width`/`height`は非負整数としてparseできない場合`None`にfallbackする。`parse_figure_media`は`<figure>`配下(ネスト含む)から最初の`<img>`と`<figcaption>`のテキストを見つけて`MediaReference`を構築する。
- `tests/test_normalize_media_node.py`(新規16件)で、属性抽出・URLデコード・width/height欠落/不正値のfallback・figcaptionからのcaption抽出・ネストしたimg探索・src欠落時のNone返却を確認した。
- `make check`(format-check/lint/mypy/pytest 1103件)と`git diff --check`が成功した。
- `role`は常に`"unknown"`(TASK-O002が分類する)。`convert_block`/`ImageBlock`への実際の配線・selection policyは対象外のまま(TASK-O002以降)。
