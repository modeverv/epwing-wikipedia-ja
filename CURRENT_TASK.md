# CURRENT_TASK.md

## Task ID

TASK-O003

## 目的

`ARCHITECTURE.md` 15.3の選択ポリシーを実装する。TASK-O002がroleを割り当てた`MediaReference`の並びから、除外候補(icon)を取り除き、`source_url`の重複(この段階では実バイトを未取得のため、"duplicate hash"の代替として`source_url`の重複を採用する)を除いたうえで、優先順位(主画像 > Infobox主要画像 > lead figure > 本文画像)に従って並べ替える、`Article.media`向けの最終選択リストを作る。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O003(依存: O002)を読んだ
- [x] `ARCHITECTURE.md` 15.3(選択ポリシー優先順位・除外候補)を再確認した
- [x] 実際のバイトダウンロード(TASK-O004以降)が未実装であるため、"duplicate hash"は`source_url`の重複で代替する、という設計判断を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/media_selection.py`(新規: `select_media`)
- `tests/test_normalize_media_selection.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_media_selection.py
make check
git diff --check
```

## 完了条件

- [x] `role="icon"`の`MediaReference`は結果に含まれない
- [x] 同じ`source_url`を持つ複数の`MediaReference`は最初の1件のみ残る
- [x] 結果が`main` > `infobox` > `lead` > `body`(`unknown`は最後)の優先順位で並ぶ
- [x] 同じroleの複数要素は入力順(DOM順)を保つ(安定ソート)
- [x] 空入力は空タプルを返す
- [x] `make check`が成功する

## 非対象

- 実際のダウンロード・content hashによる本当の重複検出(TASK-O004以降)
- decorative flag/tracking image/blank placeholderの検出

## 実施結果

- `src/wikiepwing/normalize/media_selection.py`に`select_media`を実装した。`role="icon"`を除外し、`source_url`重複を最初の1件のみ残す形で除去したうえで、`main`(0) > `infobox`(1) > `lead`(2) > `body`(3) > `unknown`(4) > `icon`(5、実際には既に除外済み)の優先度で安定ソートする。
- `tests/test_normalize_media_selection.py`(新規7件)で、空入力・icon除外・重複除去・優先順位ソート・unknown role・同roleでのDOM順保持・複合ケースを確認した。
- `make check`(format-check/lint/mypy/pytest 1120件)と`git diff --check`が成功した。
- 実際のcontent hashによる重複検出・decorative flag/tracking image検出は対象外(TASK-O004以降)。
