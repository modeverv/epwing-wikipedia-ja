# CURRENT_TASK.md

## Task ID

TASK-M008

## 目的

`ARCHITECTURE.md` 18.5(D分類の文字はreplacement markerだけで済ませず、コードポイント表記をfallbackにする。例: `[U+1Fxxx]`。件数・頻出順・記事例をreportへ出す)を実装する。(1)コードポイント表記fallback文字列を生成する関数、(2)出現をcharacterごとに集計し、頻出順・記事例(件数上限付き)を取得できる`UnrepresentableTracker`を実装する。実際のreport出力フォーマット自体はTASK-M009(依存: M003-M008)の対象とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M008(依存: M002)を読んだ
- [x] `ARCHITECTURE.md` 18.5(fallback例`[U+1Fxxx]`、件数・頻出順・記事例)を再確認した
- [x] `DATA_CONTRACTS.md` 11(Diagnostic details contract、詳細サイズに上限を設ける慣習)を確認し、記事例の保持数にも上限を設ける根拠とした

## 変更予定ファイル

- `src/wikiepwing/gaiji/unrepresentable.py`(新規: `unrepresentable_fallback()`, `UnrepresentableTracker`, `UnrepresentableStat`)
- `tests/test_gaiji_unrepresentable.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_unrepresentable.py
make check
git diff --check
```

## 完了条件

- [x] `unrepresentable_fallback(character)`が`"[U+XXXX]"`形式(大文字hex、4桁以上、上位面は桁数を拡張)を返す
- [x] `UnrepresentableTracker.record()`が文字ごとの出現回数を集計する
- [x] `UnrepresentableTracker.most_frequent()`が頻出順(降順、同数はコードポイント順で安定)にソートされた統計を返す
- [x] 記事例(page_id/title)の保持数に上限があり、上限を超えても件数カウント自体は正しく増え続ける
- [x] `make check`が成功する

## 非対象

- 実際のreportファイル出力・フォーマット(TASK-M009)

## 実施結果

- `src/wikiepwing/gaiji/unrepresentable.py`に`unrepresentable_fallback()`・`UnrepresentableExample`・`UnrepresentableStat`・`UnrepresentableTracker`を実装した。fallbackは`"[U+XXXX]"`(4桁以上、必要に応じ桁数拡張)。Trackerは文字ごとの出現回数を無制限にカウントしつつ、記事例(page_id/title)の保持数だけ上限(デフォルト5件)を設ける設計にした。
- mypy strictで`sorted()`が`list`を返しタプル型注釈と不一致になるエラーを検出し、`tuple()`で包んで修正した。
- `tests/test_gaiji_unrepresentable.py`(新規13件)で、fallback形式(BMP/補助面)・出現回数集計・頻出順ソート・同数時のコードポイント順tie-break・limit・記事例上限とカウントの独立性・page_id/titleの保持・総出現数・distinct文字一覧・不正なmax_examples・0件上限時の挙動を確認した。
- `make check`(format-check/lint/mypy/pytest 1016件)と`git diff --check`が成功した。
