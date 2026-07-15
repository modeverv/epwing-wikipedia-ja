# CURRENT_TASK.md

## Task ID

TASK-O009

## 目的

`ARCHITECTURE.md` 15.3の除外候補「duplicate hash」を、TASK-O003で採用した`source_url`重複という実用的な代替ではなく、TASK-O008で得られる実際のcontent hash(ダウンロード済みバイト列のsha256)で本来の意味通りに実装する。異なる`source_url`(例: 同じファイルの異なるサイズのサムネイルURL、複数箇所にミラーされたファイル)が実は同じバイト列である場合、最初の1件だけを残す。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O009(依存: O008)を読んだ
- [x] `ARCHITECTURE.md` 15.3(除外候補「duplicate hash」)を再確認した
- [x] TASK-O003の`select_media`が`source_url`重複を「実バイト未取得時点での実用的な代替」として採用していたことを確認し、本タスクはそれを置き換えるのではなく、実バイトが手に入った後段(ダウンロード後)で使う追加のdedupとして位置づけた
- [x] TASK-O008の`compute_content_hash`をそのまま再利用する

## 変更予定ファイル

- `src/wikiepwing/media/dedup.py`(新規: `HashedMedia`, `deduplicate_media`)
- `tests/test_media_dedup.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_dedup.py
make check
git diff --check
```

## 完了条件

- [x] 同じcontent_hashを持つ複数の`HashedMedia`(`source_url`が異なっていても)は最初の1件のみ残る
- [x] 異なるcontent_hashを持つ`HashedMedia`はすべて残る
- [x] 入力順序(最初に出現したもの)が保持される
- [x] 空入力は空タプルを返す
- [x] `make check`が成功する

## 非対象

- 実際のダウンロード・raster変換の実行フロー配線(TASK-O011/O012)
- TASK-O003の`select_media`の置き換え(役割が異なるため両方とも残す)

## 実施結果

- `src/wikiepwing/media/dedup.py`に`HashedMedia`(`MediaReference`+content hashの組)・`deduplicate_media`を実装した。同じcontent_hashを持つentryは(`source_url`が異なっていても)最初の1件のみ残し、入力順序を保持する。
- `tests/test_media_dedup.py`(新規5件)で、空入力・異なるhashの保持・同じhash異なるURLでの重複除去・入力順保持・3件重複での動作を確認した。
- `make check`(format-check/lint/mypy/pytest 1183件、ImageMagick依存3件はローカル環境でskip)と`git diff --check`が成功した。
- TASK-O003の`select_media`(source_url重複除去、実バイト未取得時点)は置き換えず、本タスクは実バイト取得後の追加dedupとして位置づけた。
