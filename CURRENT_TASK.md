# CURRENT_TASK.md

## Task ID

TASK-F003

## 目的

`ARCHITECTURE.md` 11.2のBlock unionのうち、`PLAN.md` Phase 5/6が「最初に対応する」と定めた種別を実装する。Table/Infoboxは`ARCHITECTURE.md` 11.5/11.6の完全な型を今のうちに定義しつつ、HTML変換自体はEpic K以降まで行わない。Image/Math/Referencesは最小限のplaceholder型とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F003を読んだ(依存: F002完了済み。詳細実装列は無く`ARCHITECTURE.md`/`PLAN.md`/`DATA_CONTRACTS.md`が正本)
- [x] `ARCHITECTURE.md` 11.2(Block union一覧)・11.5(Table)・11.6(Infobox)を確認した
- [x] `DATA_CONTRACTS.md` 6節のBlock JSON例(paragraph/heading/unordered_list/table/unsupported)を確認した
- [x] `PLAN.md` Phase 5(最初に対応するblock: Heading/Paragraph/List/DefinitionList/Quote/Preformatted/各種placeholder/Unsupported)とPhase 6(pre/code、horizontal rule)を確認した
- [x] TASK-F002の`model/inline.py`の実装スタイルを踏襲する

## 変更予定ファイル

- `src/wikiepwing/model/blocks.py`
- `tests/test_model_blocks.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_blocks.py
make check
git diff --check
```

## 完了条件

- [x] `ParagraphBlock`/`HeadingBlock`/`UnorderedListBlock`/`OrderedListBlock`/`DefinitionListBlock`/`QuoteBlock`/`PreformattedBlock`/`CodeBlock`/`HorizontalRuleBlock`/`TableBlock`/`InfoboxBlock`/`ImageBlock`/`MathBlock`/`ReferencesBlock`/`UnsupportedBlock`を実装する
- [x] `TableBlock`/`TableCell`が`ARCHITECTURE.md` 11.5、`InfoboxBlock`/`InfoboxField`が11.6のfieldを持つ
- [x] `payload()`/`parse_block()`が全種別で相互に往復可能である(list/quoteのnested block、table cellのnested blockを含む)
- [x] 未知の`type`をcodec errorとして拒否する
- [x] `complexity`(table)が`simple`/`wide`/`complex`/`unsupported`以外を拒否する
- [x] `make check`が成功する

## 非対象

- Article model(TASK-F004)
- HTMLからBlockへの実際の変換(Epic G/K/L/N/O)
- `NoticeBlock`(PLAN初期scopeに無いため今回は対象外、将来追加時もunion拡張のみで済む設計)

## 実施結果

- `src/wikiepwing/model/blocks.py`に15種のBlock型と補助型(`ListItem`/`DefinitionEntry`/`TableCell`/`InfoboxField`)、`Block` union、`block_payload`/`parse_block`を実装した。
- `tests/test_model_blocks.py`に32件のテストを追加(全種別roundtrip、nested block/inline、バリデーション、未知type拒否)。
- `uv run pytest tests/test_model_blocks.py`: 32 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート431件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(F003チェック)、`LOG.md`(新規エントリ)を更新した。
- `NoticeBlock`は`PLAN.md`初期scope外のため未実装。`ImageBlock`/`MathBlock`/`ReferencesBlock`は仕様未確定のためplaceholder形状とした。
- 次タスク: TASK-F004 Article model。
