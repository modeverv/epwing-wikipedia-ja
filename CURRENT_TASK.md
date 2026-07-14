# CURRENT_TASK.md

## Task ID

TASK-H001

## 目的

`ARCHITECTURE.md` 12.5(内部リンク解決)の手順1-4(URL decode/fragment分離/project base URL確認/namespace-title抽出)を実装する。page ID解決(手順6、TASK-H002)・redirect扱い(手順7)・EPWING entry ID変換(手順8)は対象外とする。`/wiki/Emacs`・`https://ja.wikipedia.org/wiki/Emacs`・`./Emacs`という3種の対象URL例に対応する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H001(依存: G006)を読んだ
- [x] `ARCHITECTURE.md` 12.5(対象URL例、処理手順1-8、"外部サイトへのリンクはplain URLまたは注記として残します")を確認した
- [x] MediaWikiの一般的なnamespace prefix(Category/Template/File/Talk/User/Wikipedia/Help/Portal/Module/MediaWiki/Special)とtitle中のunderscoreがspaceを表す慣行をdocumented assumptionとして採用する

## 変更予定ファイル

- `src/wikiepwing/links/__init__.py`
- `src/wikiepwing/links/url_parser.py`
- `tests/test_links_url_parser.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_links_url_parser.py
make check
git diff --check
```

## 完了条件

- [x] `parse_internal_url(url, *, project_base_urls) -> ParsedInternalUrl | None`が`/wiki/Title`形式(project base URLからの相対path)を解析する
- [x] 完全URL(`https://ja.wikipedia.org/wiki/Title`)が`project_base_urls`のいずれかと一致すれば内部linkとして解析する
- [x] 相対path(`./Title`、`../Title`)を解析する
- [x] fragment(`#section`)を分離する
- [x] percent-encodingをdecodeし、underscoreをspaceへ変換したtitleを返す
- [x] 既知のnamespace prefix(`Category:`等)を検出する。それ以外のcolonを含むtitleはnamespace無しとして扱う
- [x] `project_base_urls`のいずれにも一致しない・`/wiki/`形式でない場合は`None`(外部link)を返す
- [x] `make check`が成功する

## 非対象

- raw DBでのpage ID解決(TASK-H002)
- redirect targetの扱い(TASK-H002)
- EPWING entry IDへの変換(後続epic)

## 実施結果

- `src/wikiepwing/links/__init__.py`(新規パッケージ)、`src/wikiepwing/links/url_parser.py`に`parse_internal_url`/`ParsedInternalUrl`/`UrlParseError`を実装した。
- `tests/test_links_url_parser.py`に12件のテストを追加。
- `uv run pytest tests/test_links_url_parser.py`: 12 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート632件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H001チェック)、`LOG.md`(新規エントリ)を更新した。
- 既知namespace prefix一覧はMediaWikiの一般的な慣行に基づくdocumented assumption。
- 次タスク: TASK-H002 Internal target resolver。
