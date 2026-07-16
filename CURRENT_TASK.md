# CURRENT_TASK.md

## Task ID

TASK-S003

## 目的

`ARCHITECTURE.md` 26.2(決定論: 「archive timestamp固定」等)・`DATA_CONTRACTS.md` 12(build artifact contractのZIP配置)を実装する。EPWING辞書ディレクトリ(TASK-H010が生成したentries由来のbuild成果物一式)を、固定タイムスタンプ・固定ファイル順序・固定permission bitsでZIP化し、内容が同一であれば常にbyte-identicalなarchiveになる`build_deterministic_archive`を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S003(依存: H010)を読んだ
- [x] `ARCHITECTURE.md` 26.2(「archive timestamp固定」)・`CONFIG_REFERENCE.md`の`[epwing] archive_timestamp`(deterministic archive用に既にconfig schemaへ追加済み)・`DATA_CONTRACTS.md` 12(ZIP internal root構造)を再確認した
- [x] Python標準の`zipfile`モジュールの`ZipInfo(date_time=...)`でタイムスタンプを固定し、`external_attr`でpermission bitsを固定し、ファイルをsorted relative path順で追加することで決定論的なZIPが作れることを確認した

## 変更予定ファイル

- `src/wikiepwing/archive.py`(新規: `build_deterministic_archive`)
- `tests/test_archive.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_archive.py
make check
git diff --check
```

## 完了条件

- [x] `build_deterministic_archive`が`source_dir`配下の全ファイルを`root_directory_name/`prefix付きでZIPへ追加する
- [x] 全entryのタイムスタンプが`archive_timestamp`で固定される
- [x] 同一内容のsource_dirから2回buildして、生成されるZIPのバイト列が完全に一致する(byte-identical)
- [x] ファイル内容やファイル名が変わればZIPのバイト列も変わる
- [x] `archive_timestamp`がtimezone-awareでない場合は`ValueError`を送出する
- [x] `make check`が成功する

## 非対象

- Same-host/cross-host rebuild comparison(TASK-S004/S005)
- 実際のbuild pipelineへの統合配線(構築機能のみ)

## 実施結果

- `src/wikiepwing/archive.py`(新規)に`build_deterministic_archive`を実装した。固定`archive_timestamp`(全entry共通)・固定permission bits(0644)・sorted relative path順でのファイル追加により、内容が同一なら常にbyte-identicalなZIPになる。一時ファイル+`os.replace`で原子的に書き込む。
- `tests/test_archive.py`(新規9件)で、全ファイルのroot prefix付き格納・固定タイムスタンプ・2回buildでのbyte-identical・内容/root名変更での差異・naive timestampとempty root名の拒否・ディレクトリ自動作成・一時ファイルの残留なしを確認した。
- `make check`(format-check/lint/mypy/pytest 1344件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
