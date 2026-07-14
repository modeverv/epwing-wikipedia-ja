# CURRENT_TASK.md

## Task ID

TASK-F008

## 目的

`TASKS.md`のTASK-F008完了条件("order-independent sources yield deterministic canonical output where contract permits")を満たす、Articleの論理hash(logical hash)計算を実装する。TASK-F006のcanonical JSON codecの上に構築し、抽出順序が非決定的なcollection(aliases/categories/media/diagnostics/source_license_ids)を安定した順序に正規化してからhashすることで、意味的に同じ内容なら抽出順序に関わらず同一hashになるようにする。block配列(本文の出現順序)は意味を持つため並べ替えない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F008(依存: F006、完了条件: order-independent sources yield deterministic canonical output where contract permits)を読んだ
- [x] `ARCHITECTURE.md` 26.1(physical SHA-256 vs logical hashの区別、ただしEPWINGパッケージ出力の文脈)を確認し、Article/model層でのlogical hashの算出方法自体は明文化されていないことを確認した(documented assumptionとして設計する)
- [x] `src/wikiepwing/model/canonical.py`(`encode_article`のkey順ソート済みJSON出力)を確認した

## 変更予定ファイル

- `src/wikiepwing/model/logical_hash.py`
- `tests/test_model_logical_hash.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_logical_hash.py
make check
git diff --check
```

## 完了条件

- [x] `compute_logical_hash(article) -> str`が64文字16進のsha256 hex digestを返す
- [x] `aliases`/`categories`/`media`/`diagnostics`/`source_license_ids`のtuple順序を入れ替えても同一Articleに対して同一hashを返す(order-independent)
- [x] `blocks`の順序を入れ替えると異なるhashになる(本文順序は意味を持つため正規化しない)
- [x] 内容が異なるArticleは異なるhashになる
- [x] 同一入力に対して複数回呼び出しても同一hashを返す(決定的)
- [x] `make check`が成功する

## 非対象

- EPWINGパッケージ出力のphysical/logical hash(`ARCHITECTURE.md` 26.1、別epic)
- model DBへのhash書き込み(TASK-G012)

## 実施結果

- `src/wikiepwing/model/logical_hash.py`に`compute_logical_hash`を実装した。
- `tests/test_model_logical_hash.py`に9件のテストを追加。
- `uv run pytest tests/test_model_logical_hash.py`: 9 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート487件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(F008チェック)、`LOG.md`(新規エントリ)を更新した。
- "order-independent"とみなすcollectionの選定(aliases/categories/media/diagnostics/source_license_idsのみ、blocksは対象外)はdocumented assumption。
- Epic F(Model)完了。次はEpic G(HTML normalization baseline)。
