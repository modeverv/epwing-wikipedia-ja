# CURRENT_TASK.md

## Task ID

TASK-G003

## 目的

`ARCHITECTURE.md` 12.2のpass `N20 Remove unsafe/non-content nodes`を実装する。12.1が要求する"script/style/template-like executable contentを除去する"を無条件の安全策として実装し、12.3の除外候補のうち`config/default.toml`の`[normalize]`に既存のconfigフラグ(`remove_edit_ui`/`remove_navboxes`/`remove_authority_control`)が既にscaffoldされている3種を実装する。それ以外の除外候補(coordinates UI重複表示/hidden metadata/maintenance category表示/portal box/language switch UI)は、`ARCHITECTURE.md` 12.3自身が"情報を落とす可能性があるclassは、fixtureで確認してからruleへ追加します"と明記しており、実データ・具体的なclass名の裏付けが無い現時点では対象外とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-G003(依存: G002、実装note無し)を読んだ
- [x] `ARCHITECTURE.md` 12.1(script/style除去は必須の安全策)・12.3(除外候補一覧、および"fixtureで確認してからrule追加"という明示的な留保)・12.4(DOM rule設定のTOML例、`.mw-editsection`という具体的selector)を確認した
- [x] `config/default.toml`の`[normalize]`セクション(`remove_edit_ui`/`remove_navboxes`/`remove_authority_control`)が既に存在することを確認した
- [x] `src/wikiepwing/normalize/root_selection.py`の`_has_class`相当ロジックを再利用可能な形にリファクタリングする

## 変更予定ファイル

- `src/wikiepwing/normalize/html_parser.py`(`has_class`ヘルパーを公開)
- `src/wikiepwing/normalize/root_selection.py`(`has_class`を再利用するようリファクタ)
- `src/wikiepwing/normalize/unsafe_nodes.py`
- `tests/test_normalize_unsafe_nodes.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_unsafe_nodes.py tests/test_normalize_root_selection.py
make check
git diff --check
```

## 完了条件

- [x] `<script>`/`<style>`要素を設定に関わらず常に除去し、diagnosticを記録する
- [x] `UnsafeNodeRemovalOptions.from_config`が`[normalize]`の3フラグを読み込む
- [x] `remove_edit_ui=True`時に`.mw-editsection`クラスを持つ要素を除去する
- [x] `remove_navboxes=True`時に`.navbox`クラスを持つ要素を除去する
- [x] `remove_authority_control=True`時に`.authority-control`クラスを持つ要素を除去する
- [x] 各フラグが`False`の場合は対応する要素を保持する
- [x] 除去対象がネストしていても(祖先要素ごと)正しく除去され、無関係な兄弟要素は保持される
- [x] `make check`が成功する

## 非対象

- coordinates UI重複表示/hidden metadata/maintenance category表示/portal box/language switch UIの除去(具体的なclass名の裏付けが無いため対象外。実データ確認後に追加)
- Block/Inlineへの実際の変換(TASK-G004以降)
- 12.4記載のTOML `[[remove]]`/`[[classify]]`形式による汎用ルールエンジン化(config schemaの大幅拡張を要するため、既存のbooleanフラグ方式のままとする)

## 実施結果

- `src/wikiepwing/normalize/html_parser.py`に`has_class`を公開し、`root_selection.py`から重複ロジックを削除して再利用した。
- `src/wikiepwing/normalize/unsafe_nodes.py`に`UnsafeNodeRemovalOptions`/`remove_unsafe_nodes`を実装した。
- `tests/test_normalize_unsafe_nodes.py`に8件のテストを追加。
- `uv run pytest tests/test_normalize_unsafe_nodes.py tests/test_normalize_root_selection.py`: 13 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート515件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(G003チェック)、`LOG.md`(新規エントリ)を更新した。
- coordinates UI重複表示/hidden metadata/maintenance category表示/portal box/language switch UIは具体的class名の裏付けが無いため非対象とした。
- 次タスク: TASK-G004 Heading conversion。
