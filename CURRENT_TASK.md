# CURRENT_TASK.md

## Task ID

TASK-G004

## 目的

`ARCHITECTURE.md` 12.2のpass `N30 Normalize headings and section anchors`を実装する。`<h1>`〜`<h6>`要素を`HeadingBlock`(`level`/`anchor`/`inlines`)へ変換する。`TASKS.md`の依存グラフ上、G004はG003のみに依存しG005(paragraph/text conversion)には依存しないため、見出し内のinline変換は本タスクでは単純なテキスト平坦化(`TextInline`一つ)に留め、太字/斜体/リンク等の豊かなinline変換はG005/G006以降が担う。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G004(依存: G003)とG005(依存: G003)・G006(依存: G005)の依存関係を確認し、G004がG005より前にinline変換全体を実装する必要が無いことを確認した
- [x] `ARCHITECTURE.md` 12.2(pass `N30`)を確認した。具体的なanchor生成アルゴリズムの明文化は無いため、MediaWikiの一般的な慣行(`id`属性またはネストした`span`の`id`、無ければテキストから生成するslug)をdocumented assumptionとして採用する
- [x] `model/blocks.py`の`HeadingBlock`(`level`は1-6、`anchor`は非空文字列必須)を確認した

## 変更予定ファイル

- `src/wikiepwing/normalize/headings.py`
- `tests/test_normalize_headings.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_headings.py
make check
git diff --check
```

## 完了条件

- [x] `is_heading(node)`が`h1`〜`h6`要素を判定する
- [x] `convert_heading(node) -> (HeadingBlock, tuple[Diagnostic, ...])`が要素タグからlevelを抽出する
- [x] 要素自身の`id`属性を優先してanchorとする
- [x] 自身に`id`が無い場合、最初にネストした子孫要素の`id`属性を使う(`<span class="mw-headline" id="...">`慣行に対応)
- [x] どちらも無い場合、平坦化したテキストからslug(空白を`_`に置換)を生成してanchorとする
- [x] テキストも`id`も全く無い空見出しの場合、fallback anchorを使いdiagnosticを記録する
- [x] 見出しが空文字列の場合もdiagnosticを記録する
- [x] 見出し以外の要素を渡すと`ValueError`を送出する
- [x] `make check`が成功する

## 非対象

- 見出し内の太字/斜体/リンク等の豊かなinline変換(TASK-G005/G006以降)
- 文書全体でのanchor一意性保証(将来必要になれば別タスクで対応)

## 実施結果

- `src/wikiepwing/normalize/headings.py`に`is_heading`/`convert_heading`を実装した。
- `tests/test_normalize_headings.py`に8件のテストを追加。
- `uv run pytest tests/test_normalize_headings.py`: 8 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート523件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G004チェック)、`LOG.md`(新規エントリ)を更新した。
- anchor生成規則(own id/nested mw-headline id/slug fallback)はdocumented assumption。
- 次タスク: TASK-G005 Paragraph and text conversion。
