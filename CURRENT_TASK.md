# CURRENT_TASK.md

## Task ID

TASK-H012

## 目的

`TASK-D010`で作成した10記事の`normal_articles.ndjson`を拡張し、より大きな規模(100記事)でのend-to-end検証(TASK-H013 Mini end-to-end build)を可能にするfixtureを作成する。実データではなく、既存の10記事と同じWikimedia Enterprise NDJSONスキーマに従う決定的な合成データとする(D010の`normal_articles.ndjson`自体も合成データであり、同じ方針を踏襲する)。redirect数(0-2)・category数(1-2)・画像fieldの有無を変化させ、内部link(`article_body.html`内の`<a href="/wiki/...">`)で相互参照する記事群を含めることで、G012(normalize)・H002(link resolver)・H010(generate)・H011(verify)を100記事規模で実行できるようにする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H012(依存: D010)とH013(Mini end-to-end build、依存: H011-H012)を読んだ
- [x] `tests/fixtures/enterprise/normal_articles.ndjson`(D010、10記事)のスキーマ(identifier/name/url/namespace/in_language/is_part_of/date_modified/version/article_body/license/redirects/categories/templates/image)を確認した

## 変更予定ファイル

- `tests/fixtures/enterprise/generate_hundred_articles.py`(決定的生成スクリプト、再現性のため保持)
- `tests/fixtures/enterprise/hundred_articles.ndjson`(生成された100記事fixture)
- `tests/test_hundred_articles_fixture.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python3 tests/fixtures/enterprise/generate_hundred_articles.py
uv run pytest tests/test_hundred_articles_fixture.py
make check
git diff --check
```

## 完了条件

- [x] `hundred_articles.ndjson`が100行(記事)を持ち、既存のNDJSONスキーマ(D010と同型)に従う
- [x] 各記事の`identifier`(page_id相当)が一意である
- [x] 一部の記事が0-2件のredirectsを持つ
- [x] 一部の記事が`article_body.html`内に他記事への内部link(`/wiki/Title`形式)を持つ(G010以降のlink処理検証に使える)
- [x] 生成スクリプトが決定的(再実行しても同一出力)である
- [x] `make check`が成功する

## 非対象

- Mini end-to-end build自体の実行・検証(TASK-H013)
- 実Wikipediaデータの取得(引き続き合成データのまま)

## 実施結果

- `tests/fixtures/enterprise/generate_hundred_articles.py`(生成スクリプト)と`tests/fixtures/enterprise/hundred_articles.ndjson`(100記事)を追加した。
- `tests/test_hundred_articles_fixture.py`に6件のテストを追加。
- `uv run pytest tests/test_hundred_articles_fixture.py`: 6 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート713件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H012チェック)、`LOG.md`(新規エントリ)を更新した。
- identifier範囲(920001-920100)は既存fixtureとの衝突回避のため選定。
- 次タスク: TASK-H013 Mini end-to-end build。
