# CURRENT_TASK.md

## Task ID

TASK-M001

## 目的

`ARCHITECTURE.md` 18.1(文字分類: A. backend標準文字として表現可能)の基礎となる、EPWING/FreePWING backendが実際にネイティブ表現できる文字の判定機構を実装する。既存のFreePWING連携(TASK-H009)で確立した事実(EUC-JPエンコードがFPWParserへ到達する前の必須変換)により、backendが表現できる文字とは「EUC-JPへ損失無く符号化できる文字」と定義する。Pythonの標準`codecs`が持つEUC-JP実装を「backend representability table」の実体として利用し、独自の巨大なlookup tableを再実装しない。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M001(依存: B009)を読んだ。B009は完了済み。
- [x] `ARCHITECTURE.md` 18.1-18.5(外字設計)を再確認した
- [x] TASK-H009で確立した「EUC-JPエンコードがFPWParserへの必須前処理」という事実を確認した(この判断根拠として採用する)

## 変更予定ファイル

- `src/wikiepwing/gaiji/__init__.py`(新規パッケージ)
- `src/wikiepwing/gaiji/representability.py`(新規: `is_backend_representable()`, `unrepresentable_characters()`)
- `tests/test_gaiji_representability.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_representability.py
make check
git diff --check
```

## 完了条件

- [x] `is_backend_representable(character)`が、EUC-JPへ符号化可能な1文字に対して`True`を返す
- [x] EUC-JPで表現できない文字(絵文字等)に対して`False`を返す
- [x] `unrepresentable_characters(text)`が、文字列中の表現不能な文字を出現順に(重複除去せず)返す
- [x] `make check`が成功する

## 非対象

- Unicode分類器(A/B/C/D全体の判定、TASK-M002)
- 安全な置換(TASK-M003)・gaiji registry(TASK-M004以降)

## 実施結果

- 新規パッケージ`src/wikiepwing/gaiji/`を作成し、`representability.py`に`is_backend_representable()`・`unrepresentable_characters()`を実装した。EUC-JPへの符号化可否をbackend representabilityの判定基準として採用し、Pythonの標準`codecs`実装をそのまま利用した(独自lookup tableの再実装をしない判断)。
- `tests/test_gaiji_representability.py`(新規8件)で、ASCII・常用漢字・ひらがな・全角カタカナの表現可能性、絵文字・CJK拡張面文字の表現不能性、文字列中の表現不能文字の出現順抽出、全表現可能文字列での空タプルを確認した。
- `make check`(format-check/lint/mypy/pytest 947件)と`git diff --check`が成功した。
