# CURRENT_TASK.md

## Task ID

TASK-O008

## 目的

`ARCHITECTURE.md` 15.5のcache key設計の考え方(`converter_version`を含めることで、変換ロジックが変わった場合に既存cacheを安全に無効化する)を、TASK-N004の`MathCache`と同じ形でmedia向けに実装する。TASK-O007のraster変換結果(BMPバイト列)を、ダウンロードした生バイト列自体のcontent hash(sha256)をキーとしてfilesystemにcacheする「content-addressed cache」を実装する。同じbyte列を持つ画像(同一ファイルが複数のURLから参照されている場合等)は同じcache entryを共有するため、これ自体がTASK-O009(Dedup)の基盤になる。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O008(依存: O007)を読んだ
- [x] `ARCHITECTURE.md` 15.5(cache keyに`converter_version`を含める設計)を再確認した
- [x] TASK-N004の`MathCache`(`get_or_render`, `MATH_CACHE_VERSION`)の設計をそのまま踏襲する方針にした
- [x] `wikiepwing.pipeline.atomic_write`(TASK-I004)を再利用してcacheファイルを原子的に書き込む
- [x] TASK-O009(Dedup)がTASK-O008に依存しており、本タスクの「同じcontent hashは同じcache entryを共有する」という性質がその基盤になることを確認した

## 変更予定ファイル

- `src/wikiepwing/media/cache.py`(新規: `MediaCache`, `MEDIA_CACHE_VERSION`, `compute_content_hash`)
- `tests/test_media_cache.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_cache.py
make check
git diff --check
```

## 完了条件

- [x] `compute_content_hash(content)`が生バイト列のsha256 hex digestを返す
- [x] `MediaCache.get_or_convert(content_hash, convert)`が、hit時はファイルから読み込み、miss時は`convert()`を呼んで原子的に保存する
- [x] 同じcontent_hashの2回目の呼び出しで`convert()`が呼ばれない(cache hit)
- [x] 異なるcontent_hash(=異なる生バイト列)は独立したcache entryを持つ
- [x] `MEDIA_CACHE_VERSION`をキーの一部に含め、バージョンを変えると既存cacheが再利用されなくなる
- [x] `make check`が成功する

## 非対象

- Dedup(異なるcontent_hashが実は同じ画像であるケースの検出等、TASK-O009)
- 実際のEPWING graphics統合(TASK-O011)

## 実施結果

- `src/wikiepwing/media/cache.py`に`compute_content_hash`(生バイト列のsha256 hex digest)・`MediaCache`(`MATH_CACHE_VERSION`と同じ設計の`MEDIA_CACHE_VERSION`)を実装した。`get_or_convert`はcontent_hash+`MEDIA_CACHE_VERSION`から決定論的なファイルパスを計算し、hit時はファイルから読み込み、miss時は`convert()`を呼んで`atomic_write_bytes`で保存する。
- `tests/test_media_cache.py`(新規7件)で、content hashの決定性・cache miss/hitでの`convert()`呼び出し回数・異なるhashの独立した格納・ディレクトリ自動作成・`MEDIA_CACHE_VERSION`変更による既存cacheの無効化を確認した。
- `make check`(format-check/lint/mypy/pytest 1178件、ImageMagick依存3件はローカル環境でskip)と`git diff --check`が成功した。
- 「同じcontent hashは同じcache entryを共有する」という性質がTASK-O009(Dedup)の基盤になる。
