# CURRENT_TASK.md

## Task ID

TASK-T021

## 目的

全件ビルドで実際に成功した外字容量調整・toolchain・EPWING生成・検証コマンドをREADMEへ反映する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] TASK-T020の実行ログと最終成果物を確認した

## 変更予定ファイル

- `README.md`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
git diff --check
uv run pytest -q tests/test_repository_hygiene.py
```

## 完了条件

- [x] 新規generate出力からの標準ビルドコマンドが明記されている
- [x] 上限制御導入前の既存生成物を再利用する変換コマンドが明記されている
- [x] 実際に成功した最終コマンド、成果物サイズ、検証方法が明記されている
- [x] 文書差分と局所テストが成功する

## 結果

- READMEの標準ビルドを`make toolchain-image`、正しいgaiji path、実際のtitle/output pathへ更新した。
- 上限制御導入前の12GB生成物を再利用する`wikiepwing.gaiji.capacity`手順を追加した。
- 最後まで成功したtoolchain scriptの直接実行形、1,508,200記事・5.7 GiB・SHA-256・`unzip -t`検証結果を記録した。

## 非対象

- コード・設定形式の変更
- 全件generate/buildの再実行
