# CURRENT_TASK.md

## Task ID

TASK-G001

## 目的

`TASKS.md` TASK-G001の実装要件("no network/entities、malformed recovery policy")を満たす、安全なHTMLパーサーを実装する。標準ライブラリの`html.parser.HTMLParser`を用い、外部ネットワークアクセスや外部entity解決を一切行わない(stdlibパーサー自体がI/Oを行わないためXXE相当のリスクが構造的に存在しない)最小限のDOM木を構築する。不正なHTML(未対応の閉じタグ、閉じられていないタグ、`max_dom_depth`超過)は`[normalize] html_recover`設定に従い、回復してdiagnosticを記録するか、明示的にエラーとするかを切り替える。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G001(依存: F004,D010、実装要件: no network/entities、malformed recovery policy)を読んだ
- [x] `config/default.toml`の`[normalize]`セクション(`html_recover`/`preserve_unknown_text`/`max_dom_depth`)を確認した
- [x] `tests/fixtures/enterprise/edge_case_articles.ndjson`(D010で作成済みの実データ由来fixture、HTML本文を含む)を確認した
- [x] `model/diagnostics.py`のDiagnostic型を確認し、DOM関連diagnostic codeの命名は`ARCHITECTURE.md` 11.7の例(`DOM_INVALID_NESTING`/`DOM_UNKNOWN_ELEMENT`)に倣う

## 変更予定ファイル

- `src/wikiepwing/normalize/__init__.py`
- `src/wikiepwing/normalize/html_parser.py`
- `tests/test_normalize_html_parser.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_html_parser.py
make check
git diff --check
```

## 完了条件

- [x] `parse_html(html, *, max_dom_depth, html_recover) -> HtmlParseResult`が正常なHTMLから`ElementNode`/`TextNode`のDOM木を構築する
- [x] コメント・processing instruction・DOCTYPE宣言を無視する
- [x] 名前付き/数値文字参照(entity)を安全にデコードする(外部DTD/ネットワーク参照なし)
- [x] 未対応の閉じタグ(開始タグが無い)を`html_recover=True`では無視してdiagnosticを記録し、`False`では`HtmlParseError`を送出する
- [x] EOF時に閉じられていないタグを自動クローズし、`html_recover=True`ではdiagnosticを記録、`False`では`HtmlParseError`を送出する
- [x] `max_dom_depth`超過時にそれ以上の子要素を追加しない(切り捨て)でdiagnosticを記録する
- [x] `make check`が成功する

## 非対象

- Root content選択(TASK-G002)
- Unsafe/UI node除去(TASK-G003)
- Block/Inlineへの実際の変換(TASK-G004以降)
- HTML entity以外のsanitization(script/style除去等はG003で扱う)

## 実施結果

- `src/wikiepwing/normalize/__init__.py`(新規パッケージ)、`src/wikiepwing/normalize/html_parser.py`に`parse_html`/`HtmlParseResult`/`ElementNode`/`TextNode`/`HtmlParseError`を実装した。
- `tests/test_normalize_html_parser.py`に15件のテストを追加。
- `uv run pytest tests/test_normalize_html_parser.py`: 15 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート502件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G001チェック)、`LOG.md`(新規エントリ)を更新した。
- 新規依存追加を避け標準ライブラリ`html.parser.HTMLParser`を採用(ネットワークI/O・外部entity解決なし)。
- 次タスク: TASK-G002 Root content selection。
