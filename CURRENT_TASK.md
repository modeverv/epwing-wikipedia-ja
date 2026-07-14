# CURRENT_TASK.md

## Task ID

TASK-M009

## 目的

`ARCHITECTURE.md` 18.5("件数・頻出順・記事例をreportへ出す")を完成させ、Epic M(Unicode and gaiji)を締めくくる。TASK-M008の`UnrepresentableTracker`から、JSON形式のUnicode reportを組み立てて原子的に書き出す`build_unicode_report()`/`write_unicode_report()`を実装する。既存の`reference/report.py`(JSON+HTML+Markdownの本格的なreport生成)ほど大掛かりな成果物は要求されていないため、`ARCHITECTURE.md` 18.5が明示する3項目(件数・頻出順・記事例)を持つ単一のJSON reportに絞る。書き込みはTASK-I004の`atomic_write_text`を再利用する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M009(依存: M003-M008)を読んだ
- [x] `ARCHITECTURE.md` 18.5(件数・頻出順・記事例)を再確認した
- [x] TASK-M008の`UnrepresentableTracker`/`most_frequent()`を確認した
- [x] `wikiepwing.pipeline.atomic_write.atomic_write_text`(TASK-I004)を確認し、report書き込みに再利用する

## 変更予定ファイル

- `src/wikiepwing/gaiji/report.py`(新規: `UnicodeReport`, `build_unicode_report()`, `write_unicode_report()`)
- `tests/test_gaiji_report.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_report.py
make check
git diff --check
```

## 完了条件

- [x] `build_unicode_report(tracker)`が、総出現数・distinct文字数・頻出順にソートされた文字ごとの統計(件数・記事例)を持つ`UnicodeReport`を組み立てる
- [x] `write_unicode_report(report, destination)`が、JSON reportを原子的に書き出す
- [x] `make check`が成功する

## 非対象

- HTML/Markdown形式のreport(`reference/report.py`ほどの規模は要求されていないと判断)
- 実際のCLIコマンドへの配線(将来のタスク)

## 実施結果

- `src/wikiepwing/gaiji/report.py`に`UnicodeReport`・`build_unicode_report()`・`write_unicode_report()`を実装した。`UnrepresentableTracker.most_frequent()`から総出現数・distinct文字数・文字ごとの統計(character/code_point/count/examples)を組み立て、JSONとして原子的に書き出す(TASK-I004の`atomic_write_text`を再利用)。
- `tests/test_gaiji_report.py`(新規6件)で、report組み立て・頻出順ソート・code_point/examples含有・空trackerでの挙動・JSON書き込みの妥当性・親ディレクトリ自動作成を確認した。
- `make check`(format-check/lint/mypy/pytest 1022件)と`git diff --check`が成功した。これでEpic M(Unicode and gaiji、M001-M009)が完了した。
