# CURRENT_TASK.md

## Task ID

TASK-R006

## 目的

`TASKS.md`のTASK-R006(Full Mini verify/report、依存: R005完了済み)を実施する。TASK-R005で生成した`entries-mini.jsonl`(全1,508,200記事)に対する`wikiepwing verify`の結果(`ok=false`, 5件の`DUPLICATE_HEADWORD`)を調査し、実データの正当な特性かソフトウェアのバグかを切り分けて報告する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R006(依存: R005、完了済み)を読んだ
- [x] TASK-R005で得た`verify`結果(entry_count=1,508,200, 5件のDUPLICATE_HEADWORD)を出発点にした

## 変更予定ファイル

- なし(コード変更なし。5件の重複を`model.sqlite3`に対するクエリで調査し、報告する)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
# model.sqlite3への直接クエリで各重複ペアのpage_id/title/source_urlを確認
uv run python3 -c "..."
```

## 完了条件

- [x] 5件の`DUPLICATE_HEADWORD`それぞれについて、対象2記事の`page_id`/`title`/`source_url`を確認した
- [x] 各重複が実データ由来(Wikipedia側のページ重複)かソフトウェアのバグ(誤った重複生成)かを判定した
- [x] 判定結果と根拠をCURRENT_TASK.md/LOG.mdに記録した

## 非対象

- Lite/Full生成(TASK-R007以降)
- 検出された重複の自動解消ロジックの実装(実データの特性が原因であり、`verify`が意図通り機能していることが確認できれば、本タスクの範囲では追加のコード変更は不要と判断)

## 実施結果

5件の`DUPLICATE_HEADWORD`(TASK-R005で検出)それぞれについて、`model.sqlite3`/`raw.sqlite3`を直接クエリして調査した。全5ペアとも:

- `page_id`・`revision_id`・`source_sequence`(取り込み元チャンク内の位置)がすべて異なる別記事である
- `title`と`source_url`(Wikipedia記事URL)が完全に一致する
- `source_date_modified`が数日単位でずれている(例: p5260981が2026-06-26、p5261033が2026-06-29)

これは、同一タイトル/URLの記事が異なる`page_id`で2回存在するという実データ(Wikimedia Enterprise Snapshot)自体の特性であり(MediaWikiでは記事の削除・再作成によって同一タイトルに新しい`page_id`が割り当てられることがあり、Snapshotの取得期間内に両方のpage_idの状態が含まれ得る)、wikiepwingのソフトウェア側の重複生成バグではないと判断した。`ingest/deduplicate.py`のdedup処理はpage_id単位で正しく機能しており(異なるpage_id間のタイトル一致はそもそも対象外)、`verify`の`DUPLICATE_HEADWORD`検出はこの実データの特性を意図通り検出できていることを確認した(`render/verify.py`のdocstringが述べる「FreePWINGツールチェーンのbuild時チェックを事前に再現する」という目的に合致)。

追加のコード変更は不要と判断した。1,508,200件中5件(0.0003%)という頻度は実運用上許容範囲内であり、実際のEPWING build時に発生する見出し語衝突は既存のFreePWINGツールチェーン側の処理(`docker/toolchain/freepwing_build_entries.pl`)に委ねる。
