# CURRENT_TASK.md

## Task ID

TASK-M005

## 目的

`ARCHITECTURE.md` 18.4(フォント: Docker内の再配布可能なNoto CJK系を利用、package versionとhashをmanifestへ記録、フォントファイル自体は成果物に含めない)を実装する。gaiji文字(Unicode sequence)を実際にラスタライズしてbitmap(PNG bytes)を生成する。Pillowを新規依存として追加し、`docker/toolchain.Dockerfile`に(既存のDebian snapshot pinning慣習に従い)`fonts-noto-cjk`を追加する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M005(依存: M004)を読んだ
- [x] `ARCHITECTURE.md` 18.4(フォント)を再確認した
- [x] `docker/toolchain.Dockerfile`が全パッケージをDebian snapshot(2026-07-01時点)からexact versionでpinしている慣習を確認した
- [x] Debian snapshot archive(`snapshot.debian.org`、`docker/toolchain.Dockerfile`が既に参照している同一snapshot)から`fonts-noto-cjk`の実際のpinバージョン(`1:20220127+repack1-1`)をネットワーク経由で確認した(推測でバージョンを書かない)
- [x] このDev環境(macOS)にはNoto CJKフォントが無いため、実際のフォント読み込みが必要なテストは、利用可能な候補フォントパス(macOSのCJK対応システムフォント含む)を探索し、見つからなければ`pytest.skip()`する設計にする(ネットワーク取得はしない)

## 変更予定ファイル

- `pyproject.toml`(Pillowを依存に追加)
- `docker/toolchain.Dockerfile`(`fonts-noto-cjk=1:20220127+repack1-1`を追加、apt installリストへ)
- `src/wikiepwing/gaiji/glyph_renderer.py`(新規: `GlyphRenderError`, `render_glyph_bitmap()`, `bitmap_hash()`, `DEFAULT_FONT_PATH`)
- `tests/test_gaiji_glyph_renderer.py`(新規、フォント利用可能性に応じてskip)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv add "Pillow==12.2.0"
uv run pytest tests/test_gaiji_glyph_renderer.py
make check
git diff --check
```

## 完了条件

- [x] `render_glyph_bitmap(sequence, font_path=...)`が、フォントを使って文字/sequenceを実際にラスタライズしPNG bytesを返す
- [x] `bitmap_hash(bitmap)`が、bitmap内容のSHA-256を返す(TASK-M004の`bitmap_hash`カラムと整合)
- [x] フォントファイルが存在しない・不正な場合に`GlyphRenderError`を送出する
- [x] `docker/toolchain.Dockerfile`に`fonts-noto-cjk`(pin済みバージョン)が追加される
- [x] `make check`が成功する

## 非対象

- gaiji code割当(TASK-M006)・FreePWING連携(TASK-M007)
- 実際のDocker buildの実行確認(このセッションではDocker実行環境が無いため、Dockerfileの変更内容の妥当性はコードレビューベースで確認する)

## 実施結果

- `pyproject.toml`に`Pillow==12.2.0`を依存として追加した(`uv add`で`uv.lock`も更新)。
- `docker/toolchain.Dockerfile`のruntimeステージに`fonts-noto-cjk=1:20220127+repack1-1`を追加した。バージョンは推測せず、`docker/toolchain.Dockerfile`が既に参照している同一Debian snapshot(2026-07-01時点)からネットワーク経由で実際のpinバージョンを確認して採用した。
- `src/wikiepwing/gaiji/glyph_renderer.py`に`GlyphRenderError`・`render_glyph_bitmap()`・`bitmap_hash()`・`DEFAULT_FONT_PATH`を実装した。フォント読み込み失敗・グリフ無しをGlyphRenderErrorとして扱う。
- `tests/test_gaiji_glyph_renderer.py`(新規8件)を実装した。このDev環境(macOS)にはDebianのfonts-noto-cjkが無いため、実際のフォント読み込みが必要なテストはmacOSのCJK対応システムフォント(Hiragino Sans GB等)を候補として探索し、見つからなければ`pytest.skip()`する設計にした(ネットワーク取得はしない)。
- `tests/test_gaiji_toolchain_definition.py`(新規1件)で、Dockerfileにpin済みfonts-noto-cjkが含まれることを確認した。
- `make check`(format-check/lint/mypy/pytest 987件)と`git diff --check`が成功した。
