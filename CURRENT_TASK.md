# CURRENT_TASK.md

## Task ID

TASK-M003

## 目的

`ARCHITECTURE.md` 18.2(置換例: non-breaking space→normal space、typographic quote→configured quote、variation selector→base glyph + diagnostic、combining sequence→NFC化後に再判定)を実装する。「意味を変える置換は行いません」という制約の下、(1)nbsp・タイポグラフィ引用符は単純な文字→文字の置換表、(2)variation selectorは基底文字を残したまま除去してDiagnosticを記録、(3)結合文字列はNFC正規化を適用する、という3種類の処理を`apply_safe_substitutions()`にまとめる。TASK-M002の`classify_character`が受け取る`substitutions`引数の実データ(デフォルト置換表)もここで提供する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M003(依存: M002)を読んだ
- [x] `ARCHITECTURE.md` 18.2(置換例)を再確認した
- [x] TASK-M002の`classify_character`が`substitutions`引数(未提供時は何もしない)を受け取る設計であることを確認した。本タスクでその実データを提供する
- [x] variation selector(U+FE00-FE0F, U+E0100-E01EF)・NFC正規化がsingle-character置換とは異なる「シーケンスレベル」の処理であることに気づいた

## 変更予定ファイル

- `src/wikiepwing/gaiji/substitutions.py`(新規: `DEFAULT_SUBSTITUTIONS`, `is_variation_selector()`, `apply_safe_substitutions()`)
- `tests/test_gaiji_substitutions.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_substitutions.py
make check
git diff --check
```

## 完了条件

- [x] `DEFAULT_SUBSTITUTIONS`にnon-breaking space→space、タイポグラフィ引用符(左右single/double)→ASCII引用符が含まれる
- [x] `apply_safe_substitutions(text)`が、テキスト全体にNFC正規化を適用してから、variation selectorを除去(Diagnostic記録)し、置換表にある文字を置換する
- [x] variation selector除去後も直前の基底文字は保持される(基底文字ごと消えない)
- [x] `make check`が成功する

## 非対象

- gaiji registry・bitmap生成(TASK-M004以降)
- 実際のnormalizeパイプラインへの配線(本文全体への適用タイミングは別途検討)

## 実施結果

- `src/wikiepwing/gaiji/substitutions.py`に`DEFAULT_SUBSTITUTIONS`・`is_variation_selector()`・`apply_safe_substitutions()`を実装した。NFC正規化→variation selector除去(基底文字は保持、`CHAR_VARIATION_SELECTOR_DROPPED`Diagnosticを記録)→置換表適用、の順で処理する。
- `tests/test_gaiji_substitutions.py`(新規10件)で、nbsp→space・タイポグラフィ引用符→ASCII引用符・variation selector検出(標準/補助範囲)・variation selector除去時の基底文字保持とDiagnostic記録・結合文字列のNFC正規化・置換不要時の非変更・カスタム置換表・デフォルト置換表の内容を確認した。
- `make check`(format-check/lint/mypy/pytest 968件)と`git diff --check`が成功した。
