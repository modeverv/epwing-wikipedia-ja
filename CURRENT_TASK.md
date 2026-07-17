# CURRENT_TASK.md

## Task ID

TASK-T010

## 目的

ユーザー依頼により追加。`image-fetch`が`upload.wikimedia.org`への完全逐次ダウンロードで、全件(約250万ユニークURL)実行すると4〜12日かかる見積もり([RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md))だった。相手サーバーに迷惑をかけない範囲で並列ダウンロードに対応し、加えて「画像が不足した状態で一旦EPWINGビルドを最後まで通して動かしてみたい」という要望に応えるため、先頭N件のユニークURLを取得した時点で打ち切るlimitモードを追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `fetch_media`が現状完全に逐次(`for entry in plan`)であり、`SecureMediaDownloader.download`自体は独立したURLごとのリクエストで共有可変状態を持たないためスレッドプールでの並列化が安全であることを確認した
- [x] normalizeの並列化(TASK-T009)がCPU律速な`ProcessPoolExecutor`だったのに対し、`image-fetch`はネットワークI/O律速なので`ThreadPoolExecutor`が適切であることを確認した
- [x] `SecureMediaDownloader`自体がすでに429(レート制限)へのbackoff/retryを実装済みであることを確認し、並列度自体は既定を控えめ(4)にすることで相手サーバーへの配慮とする方針にした

## 変更予定ファイル

- `src/wikiepwing/media/orchestrate.py`(`fetch_media`に`max_workers`・`limit`引数追加)
- `src/wikiepwing/config.py`(`[images].fetch_concurrency`追加)
- `config/default.toml`(`images.fetch_concurrency = 4`追加)
- `src/wikiepwing/cli.py`(`image-fetch`に`--concurrency`・`--limit`追加)
- `tests/test_media_orchestrate.py`
- `README.md`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run mypy src
uv run ruff format .
uv run ruff check .
uv run pytest tests/test_media_orchestrate.py tests/test_config.py -q
make check
git diff --check
```

## 完了条件

- [x] `fetch_media`が`max_workers > 1`のとき`ThreadPoolExecutor`で並列ダウンロードし、plan順(unique URL順)で結果を返す
- [x] `max_workers`が1以下の非正値の場合に`ValueError`を送出する
- [x] `limit`を指定すると先頭N件のユニークURLで打ち切り、負値の場合は`ValueError`を送出する
- [x] `config`の`[images].fetch_concurrency`(既定4)がCLIの`--concurrency`未指定時に使われる
- [x] `README.md`に`--concurrency`/`--limit`の使い方と全件所要時間の見積もりを追記した
- [x] `make check`・`mypy`・`ruff`・`git diff --check`が成功する

## 非対象

- `SecureMediaDownloader`自体のレート制限・backoffロジックの変更(既存のまま)
- ホストごとの動的な並列度調整(常に固定の`max_workers`)

## 実施結果

`src/wikiepwing/media/orchestrate.py`の`fetch_media`に`max_workers: int = 1`(既定は逐次)・`limit: int | None = None`(既定は無制限)を追加した。`max_workers > 1`のときのみ`ThreadPoolExecutor`を生成し、`executor.map`でplan順(ユニークURL抽出順)を保ったまま並列ダウンロードする。`limit`はユニークURL抽出時に先頭N件で打ち切る実装とした(「試行したユニークURL数」の上限であり、「成功取得数」の上限ではない点に注意)。

`config`の`[images]`に`fetch_concurrency`(既定4、相手サーバーへの配慮を優先した控えめな値)を追加し、`cli.py`の`image-fetch`コマンドに`--concurrency`(未指定時は`config`値)・`--limit`オプションを追加した。

`tests/test_media_orchestrate.py`に5件のテスト(並列時のplan順序保持、`max_workers`/`limit`の非正値バリデーション、`limit`がユニークURL単位でありplanエントリ単位ではないことの検証)を追加した。`README.md`に`--concurrency`/`--limit`の使用例と、全件実行の所要時間見積もり(4〜12日)・limitモードの使いどころを追記した。

`make check`(1407 passed、+5件)、`uv run mypy src`(138ファイル、エラーなし)、`uv run ruff format .`・`uv run ruff check .`、`git diff --check`が成功することを確認した。
