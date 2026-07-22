## Task ID

TASK-T049

## 目的

`日本`のLookup完全一致検索でも、括弧付き同名記事を記事固有の表示見出しで複数候補として返せるようにする。FreePWING登録直前にEUC-JP変換後の同一検索キー・同一本文位置を重複排除し、本文導入部から安全に抽出できる読みを表示見出しへ付与する。固定query (`日本`, `にほん`, `にっぽん`, `Japan`) について参照版との候補・順位比較を自動化し、Lookup.elのexact/prefix/keyword呼び分けを文書化・テストする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `ARCHITECTURE.md`全文と検索・RenderedEntry・FreePWING・reference節を確認した
- [x] Lookup.el/ndeb.elの実装と直近Lookup画面を確認した

## 変更予定ファイル

- `src/wikiepwing/search/search_term.py`
- `src/wikiepwing/search/reading.py`
- `src/wikiepwing/render/rendered_entry.py`
- `src/wikiepwing/render/mini_layout.py`
- `src/wikiepwing/render/freepwing_source.py`
- `docker/toolchain/freepwing_build_entries.pl`
- `docker/toolchain/eb-search.c`
- 対応する `tests/` とtoolchain fixture
- `ARCHITECTURE.md`
- `TESTING.md`
- `ref/DIFF.md`
- `CURRENT_TASK.md`
- `TASKS.md`
- `LOG.md`

## 実行予定コマンド

```bash
uv run pytest <対象テスト>
make test-freepwing-build-entries
make check
```

## 完了条件

- [x] 括弧付き同名記事が基底語をheadwordとして保持し、`日本`完全一致で複数の異なる本文位置を返す
- [x] EUC-JP変換後に同じ検索キー・同じ本文位置となるword2登録を除去する
- [x] 導入部から確実に抽出できる読みを `記事名〔よみ〕` の表示見出しへ付与し、抽出不能時は元タイトルを維持する
- [x] `日本`, `にほん`, `にっぽん`, `Japan` のexact/prefix/keyword比較テストが参照版と今回版の候補・順位を機械可読に記録する
- [x] Lookup.elが通常入力=exact、`語*`=prefix、`@語`=keyword/crossを呼ぶことをコード根拠と自動テストで固定する
- [x] 局所テスト、toolchain smoke、`make check` が成功する
- [x] 文書とログが現状に一致する

## 非対象

- Lookup.el本体の既定検索方式変更
- 全記事への形態素解析・辞書読み推定
- Bookends版とのバイナリ一致
- 既存の全件 `entries.jsonl` / EPWING ZIPの即時再生成

## 結果

- 6記事のFreePWING fixtureで `日本` 完全一致が3つの異なる本文位置を返し、読み付き見出しを確認した。
- `make check` は1,499件成功、toolchain smokeも成功した。
- 全件再生成は処理時間が数時間規模のため中断した。アトミック出力により、既存の
  `data/work/entries.jsonl`（2026-07-22 13:03、18GB）と `output/` は変更されていない。
