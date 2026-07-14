# CURRENT_TASK.md

## Task ID

TASK-J006

## 目的

`ARCHITECTURE.md` 14.2(衝突規則)を実装する: 同一`normalized_key`が複数の異なる記事(`target_page_id`)へ向く場合、(1)サイレントに上書きしない、(2)全候補を保持可能な方式を優先する、(3)単一候補しか持てない場合はpriorityと安定sort(TASK-J005の`sort_search_terms`)で選ぶ、(4)dropされた候補をレポートする。`rendered.sqlite3`(`DATA_CONTRACTS.md` 7、`search_terms`テーブル)の永続化層自体はまだ存在せず別タスクの対象であるため、本タスクは純粋な関数として衝突検出・解決・レポート生成を実装する(将来の永続化層はこれを呼び出すだけで良い設計にする)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-J006(依存: J005)を読んだ
- [x] `ARCHITECTURE.md` 14.2(衝突規則)を再確認した
- [x] `DATA_CONTRACTS.md` 7の`search_terms`テーブル(normalized_key毎に複数行を許容する設計、UNIQUE制約無し)を確認し、`rendered.sqlite3`自体の永続化層はまだ実装されていないことに気づいた

## 変更予定ファイル

- `src/wikiepwing/search/collision.py`(新規: `SearchTermCollision`, `find_collisions()`, `resolve_single_candidate_per_key()`)
- `tests/test_search_collision.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_search_collision.py
make check
git diff --check
```

## 完了条件

- [x] `find_collisions(terms)`が、同一`normalized_key`グループ内で`target_page_id`が複数種類存在する場合のみ衝突として報告し、winnerを`sort_search_terms`で選び、残りを`dropped`として保持する
- [x] 同一`normalized_key`でも`target_page_id`が全て同じ(例: titleとredirectが偶然同じ正規化キーになる)場合は衝突として報告しない
- [x] `resolve_single_candidate_per_key(terms)`が、正規化キー毎に1件(winner)だけを返す(単一候補しか持てないbackend向け)
- [x] `make check`が成功する

## 非対象

- `rendered.sqlite3`本体の永続化層(migrations/schemaの実装、将来タスク)
- backend search mapping(TASK-J007、実際にEPWING/FreePWINGへ書き出す配線)

## 実施結果

- `src/wikiepwing/search/collision.py`に`SearchTermCollision`・`find_collisions()`・`resolve_single_candidate_per_key()`を実装した。`normalized_key`でグルーピングし、`target_page_id`が複数種類存在するグループのみを衝突として報告(同一記事への複数候補は非衝突)、winnerは`sort_search_terms`(TASK-J005)で選ぶ。
- `tests/test_search_collision.py`(新規7件)で、非衝突(単一候補/同一記事への複数候補)・衝突検出・priorityによるwinner選択・normalized_key順でのレポート整列・単一候補への解決(衝突有り/無し双方)を確認した。
- `make check`(format-check/lint/mypy/pytest 831件)と`git diff --check`が成功した。
