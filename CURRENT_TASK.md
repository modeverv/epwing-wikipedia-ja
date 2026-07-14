# CURRENT_TASK.md

## Task ID

TASK-M002

## 目的

`ARCHITECTURE.md` 18.1(文字分類: A backend標準文字/B 設定済み文字列へ置換可能/C gaiji bitmapとして表現/D 表現不能)を実装する。TASK-M001の`is_backend_representable`をA分類の判定に使う。B分類(安全な置換)の実際の対応表はTASK-M003で構築されるため、本タスクの分類器は置換表を呼び出し側から注入できる引数として受け取る(未指定時は何も置換しない)。C/Dの境界は、Unicodeの一般カテゴリ(`unicodedata.category`)がCc(制御)/Cf(書式)/Cs(サロゲート)/Co(私用)/Cn(未割り当て)であれば「意味のあるグリフを持たずgaiji化しても無意味」としてD、それ以外の実際に印字可能な文字はCとする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-M002(依存: M001)を読んだ
- [x] `ARCHITECTURE.md` 18.1(文字分類)・18.2(置換例)・18.5(D分類のfallback)を再確認した
- [x] TASK-M003(安全な置換)がTASK-M002に依存する関係(置換表はまだ存在しない)であることを確認し、分類器が置換表を引数として受け取る設計にする根拠とした
- [x] TASK-M001の`is_backend_representable`を確認した

## 変更予定ファイル

- `src/wikiepwing/gaiji/classifier.py`(新規: `CharacterClass`, `classify_character()`)
- `tests/test_gaiji_classifier.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_gaiji_classifier.py
make check
git diff --check
```

## 完了条件

- [x] backend表現可能な文字は`"A"`に分類される
- [x] 置換表に登録されている文字は(backend表現不可の場合)`"B"`に分類される
- [x] 印字可能だがbackend表現不可・置換表未登録の文字は`"C"`に分類される
- [x] 制御文字・書式文字・サロゲート・私用領域・未割り当てコードポイントは`"D"`に分類される(ただしASCII C0制御文字はEUC-JPがそのまま通すため実際には"A"になる、実装中に発見・テストで明記)
- [x] `make check`が成功する

## 非対象

- 実際の置換表の構築(TASK-M003)
- gaiji registry・bitmap生成(TASK-M004以降)

## 実施結果

- `src/wikiepwing/gaiji/classifier.py`に`CharacterClass`・`classify_character()`を実装した。判定順序: `is_backend_representable`→A、置換表に登録済み→B、Unicode一般カテゴリがCc/Cf/Cs/Co/Cnのいずれか→D、それ以外→C。
- 実装中に気づいた点: ASCII C0制御文字(`\x01`等)はEUC-JPがそのままバイト通過させるため、意味の無い文字であっても`is_backend_representable`が`True`を返し"A"に分類される。これは`ARCHITECTURE.md` 18.1がAを「エンコード可能性」のみで定義しており「意味のあるグリフ」を要求していないため、仕様上正しい挙動と判断した。当初の誤ったテスト期待値(C0制御文字を"D"と想定)を発見・修正し、代わりにC1制御文字(EUC-JPで実際に符号化不可)でD分類の実際の経路を検証するテストに差し替えた。
- `tests/test_gaiji_classifier.py`(新規11件)で、A/B/C/D各分類の境界(置換表の有無、backend表現可能性が置換表より優先されること、C1制御文字・書式文字・未割り当て・私用領域のD分類)を確認した。
- `make check`(format-check/lint/mypy/pytest 958件)と`git diff --check`が成功した。
