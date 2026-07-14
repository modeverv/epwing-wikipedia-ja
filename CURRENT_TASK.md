# CURRENT_TASK.md

## Task ID

TASK-E002

## 目的

raw/model BLOB圧縮用のzstd codecを実装する。決定的設定(同じ入力+levelで同じbytes)、roundtrip、入出力サイズ上限を持つ。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E002を読んだ(依存: E001完了済み)
- [x] `CONFIG_REFERENCE.md` 8節(`ingest.zstd_level`: 「再現性が保たれる固定設定を使用」)を確認した
- [x] `DATA_CONTRACTS.md`の`html_zstd`/`wikitext_zstd`/`article_json_zstd`/`body_json_zstd`列を確認した
- [x] zstd Python bindingが未導入だったため`zstandard`を確認し、`pyproject.toml`の依存へ追加した

## 変更予定ファイル

- `pyproject.toml`
- `uv.lock`
- `src/wikiepwing/ingest/zstd_codec.py`
- `tests/test_zstd_codec.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_zstd_codec.py
make check
git diff --check
```

## 完了条件

- [x] `compress`/`decompress`のroundtripが元のbytesと一致する
- [x] 同じ入力・levelでの`compress`が毎回同じbytesを返す(決定的、マルチスレッド無効)
- [x] 入力・出力それぞれにbyte上限を持ち、超過を拒否する
- [x] decompress前にframeの`content_size`を検査し、宣言サイズが上限超過なら実際の展開を行わずに拒否する
- [x] 不正な圧縮データ・levelの範囲外指定を拒否する
- [x] `make check`が成功する

## 非対象

- NDJSON parsing・record抽出(TASK-E004)
- 実際のarticles/model tableへの書込(TASK-E007)

## 実施結果

- `pyproject.toml`へ`zstandard==0.25.0`を実行時依存として追加し、`uv sync`で`uv.lock`を更新した(プロジェクトの初めての実行時依存)。
- `src/wikiepwing/ingest/zstd_codec.py`に`compress`/`decompress`/`ZstdCodecError`を実装した。`ZstdCompressor(threads=0)`で単一スレッド圧縮とし、同じ入力・levelで決定的なbytesを保証した。
- level範囲(1〜22)、`max_input_bytes`/`max_output_bytes`の非正値・超過を拒否した。
- decompress前に`get_frame_parameters`でframeの`content_size`を検査し、`ZSTD_CONTENTSIZE_UNKNOWN`/`ZSTD_CONTENTSIZE_ERROR`のsentinel値を除いた宣言サイズが上限を超える場合は実際の展開を行わずに拒否した。content_size未知のstreaming frameは`decompress(..., max_output_size=...)`自体の上限で保護した。
- `tests/test_zstd_codec.py`に12件のテスト(roundtrip、決定性、level境界、入出力サイズ上限、不正frame、宣言サイズ超過、content_size未知frameの境界)を追加した。
- format-check、ruff lint、mypy strict、標準スイート286件、`git diff --check`が成功した。
- `docker/app.Dockerfile`は`uv sync --frozen`で`pyproject.toml`/`uv.lock`から依存を解決するため、Dockerfile自体の変更は不要だった。

**判断・注意点**

- `zstandard`ライブラリのAPIで`content_size`が「未知」を表す際は`None`ではなく`ZSTD_CONTENTSIZE_UNKNOWN`(2^64-1相当)のsentinel整数を返すことが分かった(実装時に発見、テストで固定した)。
