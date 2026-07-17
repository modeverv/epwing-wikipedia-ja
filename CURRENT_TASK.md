# CURRENT_TASK.md

## Task ID

TASK-T005

## 目的

`TASKS.md`のTASK-T005(Licensing/attribution guide、依存: O010,R009完了済み)を実施する。プログラム自体のライセンスと、生成辞書に含まれるWikipedia本文・画像のライセンスが別であることを明確にし、実装済みの帰属情報の仕組み(TASK-O010の`MediaAttribution`モデル、`licenses`/`article_licenses`テーブル、TASK-S001の`BUILD-INFO.json`)と、まだ実装されていない部分(`distribution.include_attribution_appendix`は設定検証のみで、実際のappendixファイル生成コードは無い)を正直に区別して`LICENSING.md`にまとめる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-T005(依存: O010,R009、両方完了済み)を読んだ
- [x] `src/wikiepwing/media/attribution.py`(TASK-O010)の`MediaAttribution`/`is_licensed`を確認した
- [x] `migrations/raw/001_initial.sql`の`licenses`/`article_licenses`テーブル(記事本文のライセンス情報)を確認した
- [x] `src/wikiepwing/config.py`で`distribution.include_attribution_appendix`が`mode=public`時の設定検証としてのみ存在し(`334行目`)、実際にappendixファイルを生成するコードがリポジトリ全体を検索しても存在しないことを確認した(grepで新規実装が無いことを確認)
- [x] README.mdの既存「ライセンス」セクション(プログラムライセンスと生成辞書のライセンスは別、という方針)と重複せず、その詳細版として位置づける

## 変更予定ファイル

- `LICENSING.md`(新規)
- `README.md`(読む順に追加、既存の「ライセンス」セクションから`LICENSING.md`への参照を追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

なし(ドキュメントのみ)

## 完了条件

- [x] `LICENSING.md`にプログラム自体のライセンス(MIT)と生成辞書のコンテンツライセンス(Wikipedia本文・画像)が別であることを明記した
- [x] `LICENSING.md`に実装済みの帰属情報の仕組み(`MediaAttribution`、`licenses`/`article_licenses`テーブル、`BUILD-INFO.json`)を記載した
- [x] `LICENSING.md`に未実装の部分(attribution appendixの自動生成)を正直に明記した
- [x] `README.md`の「ライセンス」セクションから`LICENSING.md`への導線を追加した

## 非対象

- `distribution.include_attribution_appendix`の実装自体(本タスクはドキュメントのみ)
- v1.0 release checklist(TASK-T006)

## 実施結果

`LICENSING.md`(新規)を作成した。プログラムのライセンス(MIT)、コンテンツライセンス(本文: Wikimedia Enterprise Snapshotの`license`フィールド→`licenses`/`article_licenses`テーブル→`model.sqlite3`の`source_license_ids`という実装済みの流れ、画像: TASK-O010の`MediaAttribution`モデルと`images.missing_license_action`設定)、`BUILD-INFO.json`(TASK-S001)の6セクションで構成した。

DATA_CONTRACTS.md 11のパッケージ内部構成(`LICENSES.txt`/`ATTRIBUTION.txt`/`attribution.jsonl`)と`config.py`のコードを突き合わせ、`distribution.include_attribution_appendix`が現状「`mode=public`時に`true`必須」という設定検証としてのみ存在し、実際にappendixファイルを生成するコードはリポジトリ全体に存在しないことを確認し、正直に明記した(推測ではなくgrepでの確認に基づく)。公開配布前にはこの未実装部分を先に実装するか手動でライセンス表示を作成する必要があることを明記した。

`README.md`の既存「ライセンス」セクションから`LICENSING.md`への導線を追加し、読む順・想定リポジトリ構成にも追加した。コード変更を伴わないドキュメントのみの変更のため、`make check`(1395 passed)と`git diff --check`が成功することを確認した。
