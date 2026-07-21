# CURRENT_TASK.md

## Task ID

TASK-T048

## 目的

FreePWING backend において記事を跨ぐ同一見出し語（同名タイトル・リダイレクト・曖昧さ回避）の削除・間引きを行わず、全記事に対して見出し語（aliases / word2）として登録するように `backend_mapping.py` を改修する。また `verify.py` で同名見出し語を不具合としていた `DUPLICATE_HEADWORD` エラー判定を調整・解除し、対応する自動テストを更新する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した

## 変更予定ファイル

- `src/wikiepwing/search/backend_mapping.py`
- `src/wikiepwing/render/verify.py`
- `tests/test_search_backend_mapping.py`
- `tests/test_render_verify.py`
- `CURRENT_TASK.md`
- `TASKS.md`
- `LOG.md`

## 実行予定コマンド

```bash
make check
```

## 完了条件

- [x] `headwords_for_articles` で複数記事が同じ見出し語/エイリアスを持っても削除されず、各記事の見出し語リスト（headwords）に保持されること
- [x] 同一記事内では見出し語の重複が正しくユニーク化（deduplicate）されること
- [x] `verify_entries_jsonl` で異なる記事が同じ見出し語を持つ場合に `DUPLICATE_HEADWORD` エラーとならないこと
- [x] 単体テスト（`test_search_backend_mapping.py`, `test_render_verify.py`）が改修仕様に合わせて更新・追加されパスすること
- [x] `make check` が全件パスすること

## 結果

- FreePWING 向けの見出し語マッピング (`headwords_for_articles`) から単一記事優先の競合排除処理を削除し、同名見出し語・エイリアスを持つ全記事が各見出し語インデックスを所有できるように改修。
- `verify.py` の `DUPLICATE_HEADWORD` エラーチェックを削除し、FreePWINGの重複見出し語登録機能と完全に統合。
- 1,487件の全単体テストおよび `make check` にパス。

## 非対象

- 他の検索モジュールの変更


