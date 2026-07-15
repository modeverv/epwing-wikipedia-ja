# CURRENT_TASK.md

## Task ID

TASK-O002

## 目的

`ARCHITECTURE.md` 15.2の`MediaReference.role`(`Literal["main","infobox","lead","body","icon","unknown"]`)を実際に分類するロジックを実装する。TASK-O001が抽出する`MediaReference`(常に`role="unknown"`)と、TASK-K008の`RawInfobox.image_srcs`(infobox内で見つかった画像src集合)を入力に、15.3の選択ポリシー優先順位・除外候補リストの一部(サイズの小さいicon)を反映してroleを決定する。`main`(Wikimedia Enterprise Snapshotのmain image由来、既に`normalize/orchestrate.py`の`_read_media`が設定済み)はこのタスクでは上書きしない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O002(依存: O001,K008)を読んだ
- [x] `ARCHITECTURE.md` 15.3(選択ポリシー優先順位・除外候補: 16pxなどのicon等)を再確認した
- [x] TASK-K008の`RawInfobox.image_srcs`(infobox行から見つかったimg srcの生文字列集合)を確認した
- [x] TASK-O001の`MediaReference`(常に`role="unknown"`で返る)を確認した
- [x] `_read_media`が`role="main"`を既に設定している箇所を確認し、本タスクではそれを上書きしない設計にした

## 変更予定ファイル

- `src/wikiepwing/normalize/media_role.py`(新規: `classify_media_role`, `with_classified_role`)
- `tests/test_normalize_media_role.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_media_role.py
make check
git diff --check
```

## 完了条件

- [x] `role="main"`の`MediaReference`はそのまま(上書きされない)
- [x] `source_width`/`source_height`が両方とも閾値以下(icon相当のサイズ)であれば`role="icon"`になる
- [x] `source_url`が`infobox_source_urls`集合に含まれる場合は`role="infobox"`になる(iconサイズでない場合)
- [x] `is_lead=True`の場合は`role="lead"`になる(icon/infoboxのいずれでもない場合)
- [x] それ以外は`role="body"`になる
- [x] `with_classified_role`が新しい`MediaReference`(role以外のフィールドは元のまま)を返す
- [x] `make check`が成功する

## 非対象

- selection policy(重複除外・優先順位付けによる最終的な採用画像の決定、TASK-O003)
- decorative flag/tracking image/blank placeholderの検出(将来必要になれば別タスク、現時点ではサイズによるicon判定のみ実装)

## 実施結果

- `src/wikiepwing/normalize/media_role.py`に`classify_media_role`(優先順位: `main`維持 > iconサイズ判定 > infobox src集合一致 > lead flag > デフォルト`body`)と、それを適用した新しい`MediaReference`を返す`with_classified_role`(`dataclasses.replace`)を実装した。iconサイズ判定は`source_width`/`source_height`が両方とも20px以下の場合のみ真になり、片方だけ既知/両方不明な場合は`body`側にfallする。
- `tests/test_normalize_media_role.py`(新規10件)で、`main`維持・icon判定(単独・infoboxより優先)・infobox判定(leadより優先)・lead判定・デフォルトbody・次元不明/部分的既知でのicon非該当・`with_classified_role`のフィールド保持を確認した。
- `make check`(format-check/lint/mypy/pytest 1113件)と`git diff --check`が成功した。
- 重複除外・最終的な採用画像決定(selection policy)はTASK-O003の対象。decorative flag/tracking image検出は対象外のまま。
