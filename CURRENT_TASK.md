# CURRENT_TASK.md

## Task ID

TASK-T009

## 目的

ユーザー依頼により追加。normalizeの処理時間についてユーザーから懸念があり、「処理時間が短縮できる変更ならば実装してほしいが、速度低下やバグ増加のリスクがあるならこのままにしたい」という条件付きで、16コア機での並列化による高速化を検討した。`normalize_html`によるDOM正規化からバリデーション・ハッシュ計算までの、記事1件ごとに副作用のないCPU律速な計算部分のみを`ProcessPoolExecutor`でプロセスプールに分散し、`raw.sqlite3`の読み込みと`model.sqlite3`への書き込みはこれまで通りメインプロセスで`page_id`順に逐次実行する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `_normalize_one`の中でCPU律速(副作用なし)な部分(`normalize_html`〜バリデーション〜ハッシュ計算)と、DBアクセスを伴う部分(raw読み込み・model書き込み)を分離できることを確認した
- [x] ユーザーの「150万レコードを箱に貯めて一気にDB出し入れ」提案について、それでは既存の`batch_size`によるメモリ上限の仕組みを壊す(generateステージの30-40GBメモリ問題と同じ構造になる)ことを説明し、既存のbatch_size/fetchmanyの単位を維持したままバッチ内で並列化する方針で合意した
- [x] `config`の`[normalize].workers`(デフォルト8)が以前から宣言されていたが未使用だったことを確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/orchestrate.py`(`_WorkItem`・`_ComputedResult`・`_build_work_item`・`_compute_normalized`追加、`_normalize_all`/`run_normalize`に`workers`引数追加)
- `src/wikiepwing/cli.py`(`normalize`コマンドに`--workers`追加、`build`コマンドのnormalizeステージに`workers`配線)
- `tests/test_normalize_orchestrate.py`(並列/逐次のバイト一致検証テスト追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run mypy src
uv run ruff format --check .
uv run ruff check .
uv run pytest tests/test_normalize_orchestrate.py -q
make check
git diff --check
```

## 完了条件

- [x] `_normalize_one`のCPU律速部分が`_compute_normalized`という純粋・pickle可能な関数として分離されている
- [x] `_normalize_all`が`workers > 1`の場合のみ`ProcessPoolExecutor`を使い、`workers=1`(既定)では従来通り逐次実行される
- [x] `config`の`[normalize].workers`が実際に`run_normalize`へ配線されている(CLIの`normalize`コマンド・`build`コマンド両方)
- [x] 小規模フィクスチャで`workers=1`と`workers=4`が完全にバイト単位で同一の`model.sqlite3`を生成することをテストで検証した
- [x] `make check`・`mypy`・`ruff`・`git diff --check`が成功する

## 非対象

- `generate`ステージの3層メモリ蓄積問題(30-40GB)の改善(ユーザーが今回は依頼していない、別途診断済みで説明した)
- フルスケール(150万記事)での実測・実行(ユーザー側で実施予定)

## 実施結果

`src/wikiepwing/normalize/orchestrate.py`に`_WorkItem`(rawからの読み込み結果一式、DBハンドルを含まずpickle可能)と`_ComputedResult`(計算結果)のfrozen dataclassを追加し、`_normalize_one`を`_build_work_item`(raw.sqlite3読み込み、メインプロセス)と`_compute_normalized`(`normalize_html`からバリデーション・ハッシュ計算までの純粋関数)に分割した。`_normalize_all`に`workers`引数を追加し、`workers > 1`の場合のみ`ProcessPoolExecutor`を生成、バッチ単位で`executor.map(_compute_normalized, work_items)`に分散し、結果を`page_id`順で`repository.batch()`内に書き込む。`raw.sqlite3`の読み込みと`model.sqlite3`への書き込みはメインプロセスのまま変更していない。

`run_normalize`に`workers: int = 1`引数を追加(既定は逐次のまま)。`src/wikiepwing/cli.py`の`normalize`コマンドに`--workers`オプションを追加し(未指定時は`config`の`[normalize].workers`)、`build`コマンドのnormalizeステージにも同様に配線した。

`tests/test_normalize_orchestrate.py`に`test_normalize_parallel_matches_sequential_output`を追加し、同一入力に対し`workers=1`と`workers=4`で`run_normalize`をそれぞれ実行、`metrics`の完全一致と`model.sqlite3`のファイルバイトの完全一致を検証した。

`make check`(1402 passed、+1件)、`uv run mypy src`(138ファイル、エラーなし)、`uv run ruff format --check .`・`uv run ruff check .`、`git diff --check`が成功することを確認した。
