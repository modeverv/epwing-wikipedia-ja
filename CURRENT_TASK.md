# CURRENT_TASK.md

## Task ID

TASK-F005

## 目的

`ARCHITECTURE.md` 24.3(Model verification)と`PLAN.md` Phase 5出口条件(invalid nesting拒否、unknown typeを黙って無視しない)に基づき、既に構築済みの`Article`(F004)に対する意味的検証(dataclassの`__post_init__`だけでは検出できない不変条件)を行う`validate_article`を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F005を読んだ(依存: F004完了済み。詳細実装列は無し)
- [x] `ARCHITECTURE.md` 24.3(Model verification: block nesting/unique page IDs/title not empty/internal links validity/diagnostics consistency/serialization roundtrip)を確認した
- [x] `PLAN.md` Phase 5出口条件(roundtrip一致/invalid nesting拒否/canonical hash安定/unknown typeを黙って無視しない)を確認した
- [x] 既存の`ingest/validate.py`(config駆動limitsパターン)、`model/article.py`/`blocks.py`/`inline.py`/`diagnostics.py`の実装を確認した
- [x] `config/default.toml`・`src/wikiepwing/config.py`の`_SCHEMA`を確認した(model用セクションが存在しないため新設する)

## 変更予定ファイル

- `src/wikiepwing/model/validate.py`
- `tests/test_model_validate.py`
- `src/wikiepwing/config.py`(`_SCHEMA`に`[model]`セクション追加)
- `config/default.toml`(`[model]`セクション追加)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_validate.py tests/test_config.py
make check
git diff --check
```

## 完了条件

- [x] block/list/quote/table/infobox/definition-listのnesting深さが設定上限を超えた場合にdiagnosticを生成する(`ARCHITECTURE.md` 24.3 "block nesting")
- [x] `InternalLinkInline`の`resolution`と`target_page_id`の整合性を検証する(resolved⇔page_id有り、missing/externalized⇔page_id無し)(24.3 "internal links validity")
- [x] Articleに埋め込まれた`Diagnostic`の`page_id`/`title`がそのArticle自身と矛盾する場合にdiagnosticを生成する(24.3 "diagnostics consistency")
- [x] 妥当なArticleに対しては空のdiagnostics tupleを返す
- [x] `[model]`セクションを`config/default.toml`・`config.py`の`_SCHEMA`に追加し、`ModelValidationLimits.from_config`で読み込める
- [x] `make check`が成功する

## 非対象

- Canonical JSON codec/hash(TASK-F006)
- corpus全体でのpage_id一意性検証(単一Articleを対象とする本バリデータの範囲外。将来のcorpus組み立てstageで扱う)
- serialization roundtripの実行時チェック(既存のpayload/parse往復テストで担保済みのためvalidatorの責務としない)
- HTML由来の実データに対する検証(Epic G以降)

## 実施結果

- `src/wikiepwing/model/validate.py`に`ModelValidationLimits`/`validate_article`を実装した(nesting深さ、internal link resolution/target_page_id整合性、embedded Diagnostic整合性)。
- `src/wikiepwing/config.py`・`config/default.toml`に`[model]`セクション(`max_block_nesting_depth = 32`)を追加した。
- `tests/test_model_validate.py`に11件のテストを追加。
- `uv run pytest tests/test_model_validate.py tests/test_config.py`: 22 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート461件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(F005チェック)、`LOG.md`(新規エントリ)を更新した。
- corpus全体のpage_id一意性検証とserialization roundtripの実行時チェックは非対象として明示的にスコープ外とした。
- 次タスク: TASK-F006 Canonical JSON codec。
