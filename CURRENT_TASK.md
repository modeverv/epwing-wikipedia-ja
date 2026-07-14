# CURRENT_TASK.md

## Task ID

TASK-N002

## 目的

`ARCHITECTURE.md` 15.7の"2. TeX sourceがあればcache keyに使用"を実装する。TASK-N001の`RawMathNode`から、表記ゆれ(空白の差・Unicode正規化形式の違い)を吸収した正準形(canonical form)を作り、それをcache keyとして使えるハッシュへ変換する。TeX sourceが無い場合はテキスト代替(alttext)へフォールバックし、両方とも無い場合は安定したcache keyを作れないため`None`を返す(呼び出し側はcacheせずレンダリングする、TASK-N003-N004の対象)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-N002(依存: N001)を読んだ
- [x] `ARCHITECTURE.md` 15.7("2. TeX sourceがあればcache keyに使用")を再確認した
- [x] TASK-N001の`RawMathNode`(`tex_source`/`text_alternative`)を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/math_source.py`(新規: `canonicalize_math_source()`, `compute_math_cache_key()`)
- `tests/test_normalize_math_source.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_math_source.py
make check
git diff --check
```

## 完了条件

- [x] `canonicalize_math_source(text)`が、NFC正規化+空白run畳み込み+trimを行う
- [x] `compute_math_cache_key(node)`が、`tex_source`があればそれを優先し、無ければ`text_alternative`にフォールバックしてSHA-256ハッシュを返す
- [x] 表記ゆれのある同一の数式(空白の差等)が同じcache keyになる
- [x] `tex_source`/`text_alternative`が両方とも無い場合は`None`を返す
- [x] `make check`が成功する

## 非対象

- 実際のレンダリング・cache格納(TASK-N003-N004)

## 実施結果

- `src/wikiepwing/normalize/math_source.py`に`canonicalize_math_source()`・`compute_math_cache_key()`を実装した。NFC正規化+空白run畳み込み+trimでcanonical formを作り、`tex_source`優先・`text_alternative`フォールバックでSHA-256ハッシュを計算する。両方とも無い/canonical化後に空文字列になる場合は`None`を返す。
- `tests/test_normalize_math_source.py`(新規10件)で、空白畳み込み・trim・NFC正規化・tex_source優先・text_alternativeへのフォールバック・両方無い場合のNone・空白のみの場合のNone・表記ゆれのある同一数式での同一key・異なる数式での異なるkey・SHA-256 hex digest形式を確認した。
- `make check`(format-check/lint/mypy/pytest 1043件)と`git diff --check`が成功した。
