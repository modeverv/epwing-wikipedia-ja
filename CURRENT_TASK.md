# CURRENT_TASK.md

## Task ID

TASK-R008

## 目的

`TASKS.md`のTASK-R008(Full Lite generate/verify、依存: R007完了済み)を実施する。TASK-R004の`model.sqlite3`(全1,508,200記事)からLiteプロファイル設定で`wikiepwing generate`を実行し、`entries-lite.jsonl`を生成、`wikiepwing verify`で検証する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-R008(依存: R007、完了済み)を読んだ
- [x] TASK-R005(Full Mini generate)と同じ手順をLiteプロファイル設定で実行する。`generate`は画像の実際の取得/変換(TASK-R007で別途実施済み)を行わず、テキストエントリ生成のみであることを確認した

## 変更予定ファイル

- なし(コード変更を伴わない実行タスク。スクラッチパッド内に`entries-lite.jsonl`を生成する)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python -m wikiepwing.cli generate \
  --config "$SCRATCH/full-ingest-override.toml" \
  --config config/profiles/lite.toml \
  --model-database "$SCRATCH/data/work/model.sqlite3" \
  --entries-output "$SCRATCH/data/output/entries-lite.jsonl" \
  --git-commit "$(git rev-parse HEAD)" \
  --run-id full-r008-lite

uv run python -m wikiepwing.cli verify --entries "$SCRATCH/data/output/entries-lite.jsonl"
```

## 完了条件

- [x] `entries-lite.jsonl`が生成され、generateステージのmanifestが`completed`状態で書かれる
- [x] `verify`が全件のJSONパースに成功する
- [x] 実行中に実データ固有のクラッシュ・バグが見つかった場合は原因を特定し、コード修正・テスト追加・commitしてから再実行する(TASK-R003〜R007で確立したパターンを踏襲。今回はバグではなく設計上の理解を1件記録した)

## 非対象

- Full profile generate/verify(TASK-R009)
- 実データを`git`にコミットすること

## 実施結果

`model.sqlite3`(1,508,200記事)に対してLiteプロファイル設定で`wikiepwing generate`を実行し、`entries-lite.jsonl`を生成した。generateステージmanifestは`status=complete`(articles_read=1,508,200, entries_written=1,508,200, articles_skipped=0)。

生成後、`entries-lite.jsonl`のsha256がTASK-R005の`entries-mini.jsonl`と完全に一致する(byte-for-byte同一)ことに気づき、調査した。原因は実装上の理解不足ではなくバグでもなく、現行実装の設計上の事実だった:

- `render/generate.py`は`AppConfig`/プロファイル設定を一切参照しない(`--config`はCLIの他コマンドとの一貫性のために受け取るが、`run_generate`自体は`model.sqlite3`の既存レコードをそのまま`RenderedEntry`へ変換するのみ)。
- プロファイル間で実際に差がつくのは`normalize`ステージの`images_enabled`(`NormalizeOptions`)であり、これは`article.media`(`media_references`テーブル、後続のimage-fetch/convertが使う)にのみ影響する。
- `entries.jsonl`本文中の`[画像: ...]`プレースホルダー行は`InfoboxBlock.images`由来で、これは`infobox_block.py`の無条件変換で設定されており、`images_enabled`の影響を受けない。
- 検索語budget(`search/search_term.py`の`apply_search_budgets`)は`normalize`/`generate`のどこからも呼ばれておらず(grep で未使用を確認)、現行パイプラインには一切wiringされていない(`render/generate.py`のdocstringが述べる「catalog/subbook設定・graphic/gaiji登録は後続タスク」と整合する、意図的に未実装の範囲)。

結論として、TASK-R004で1回だけ実行した`normalize`(`images_enabled=true`、`config/default.toml`の既定値がLiteの値と一致)から得た`model.sqlite3`に対して、Mini/Lite/Fullいずれのプロファイル設定を`--config`で渡して`generate`しても、現行実装では`entries.jsonl`の内容は変わらない。これはバグではなく、現行コードの「プロファイル差はnormalize時のメディア選択(実際の画像fetch/convertの対象範囲)にのみ表れ、entries.jsonlの本文テキスト自体はプロファイル非依存」という設計の帰結である。TASK-R007(Lite media run)がすでにこの軸(メディア選択・fetch/convert)を実データで検証済みであるため、本タスクの範囲では追加のコード修正は不要と判断した。

`verify`実行結果はTASK-R006と同一の5件の`DUPLICATE_HEADWORD`(内容が同一のため当然)で、これらはすでにTASK-R006で実データの正当な特性と判定済み。`entries-lite.jsonl`はスクラッチパッドのみに保持し、gitにはコミットしない。
