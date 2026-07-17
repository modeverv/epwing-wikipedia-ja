# CURRENT_TASK.md

## Task ID

TASK-T019

## 目的

`generate`がリポジトリ直下へ出力するgaiji生成物をGit管理対象から除外し、誤コミットを防止する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `.gitignore`の現在内容とGit履歴を確認した

## 変更予定ファイル

- `.gitignore`
- `tests/test_repository_hygiene.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest -q tests/test_repository_hygiene.py
make format-check
make lint
make typecheck
make test
git diff --check
```

## 完了条件

- [x] `.gitignore`が削除・巻き戻されていないことを履歴から確認する
- [x] rootの`gaiji/`、`gaiji.sqlite3`、`unicode-report.json`をignoreする
- [x] 対応テストと標準検証が成功する

## 結果

- `.gitignore`は存在し、直近履歴の内容も保持されていた。
- 新たに生成された3種類のgaiji成果物だけがignore対象から漏れていた。
- 生成物本体は削除せず、Gitの追跡候補から除外する。

## 非対象

- 生成済み成果物の削除
- 既存コミットの履歴改変
- ソースコード配下の`src/wikiepwing/gaiji/`をignoreすること
