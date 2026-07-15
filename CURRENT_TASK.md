# CURRENT_TASK.md

## Task ID

TASK-N004

## 目的

`ARCHITECTURE.md` 22.3(work配下の"math cache"ディレクトリ)・15.5(画像のCache key設計、`converter_version`を含める慣習)を数式向けに実装する。TASK-N002の`compute_math_cache_key`が返すcontent-basedなキーに、レンダラのバージョン(TASK-N003の`render_math_to_image`実装が変わった場合に既存cacheを安全に無効化するため)を組み合わせたファイルシステムベースのcacheを実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-N004(依存: N003)を読んだ
- [x] `ARCHITECTURE.md` 15.5(画像Cache keyが`converter_version`/`policy_version`を含める設計)・22.3("math cache"というwork配下のディレクトリ)を再確認した
- [x] TASK-N002の`compute_math_cache_key`(`None`の場合はcacheしない、という既存契約)を確認した
- [x] `wikiepwing.pipeline.atomic_write`(TASK-I004)を再利用してcacheファイルを原子的に書き込む

## 変更予定ファイル

- `src/wikiepwing/normalize/math_cache.py`(新規: `MathCache`, `MATH_CACHE_VERSION`）
- `tests/test_normalize_math_cache.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_math_cache.py
make check
git diff --check
```

## 完了条件

- [x] `MathCache.get_or_render(cache_key, image_format, render)`が、cache_keyが`None`の場合は常に`render()`を呼び(cacheしない)、`None`でない場合はhit時にファイルから読み込み、miss時は`render()`を呼んで原子的に保存する
- [x] `MATH_CACHE_VERSION`をキーの一部に含め、バージョンを変えると既存cacheが再利用されなくなる
- [x] 同じcache_key・同じimage_formatの2回目の呼び出しで`render()`が呼ばれない(実際にcache hitすることを確認する)
- [x] `make check`が成功する

## 非対象

- raster変換(TASK-N005)・inline/block layout配線(TASK-N006)
- cacheの自動的なexpire・容量上限(将来必要になれば別タスク)

## 実施結果

- `src/wikiepwing/normalize/math_cache.py`に`MathCache`・`MATH_CACHE_VERSION`を実装した。`get_or_render`はcache_keyが`None`なら常にレンダリングし、それ以外はcache_key+`MATH_CACHE_VERSION`+image_formatから決定論的なファイルパスを計算してhit/miss判定する。miss時はTASK-I004の`atomic_write_bytes`で原子的に保存する。
- `tests/test_normalize_math_cache.py`(新規7件)で、cache miss時のrender呼び出し・cache hit時のrender非呼び出し・`None`キーでの常時レンダリング・異なるキー/フォーマットの独立した格納・ディレクトリ自動作成・`MATH_CACHE_VERSION`変更による既存cacheの無効化を確認した。
- `make check`(format-check/lint/mypy/pytest 1060件)と`git diff --check`が成功した。
