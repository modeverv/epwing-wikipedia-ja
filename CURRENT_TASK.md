# CURRENT_TASK.md

## Task ID

TASK-F004

## 目的

`ARCHITECTURE.md` 11.1のArticle dataclass、13.3のalias(source/confidence)、15.2のMediaReferenceを実装する。Article/Alias/MediaReferenceの型定義とJSON codec(payload/parse)のみを対象とし、HTMLからの実際の変換やvalidatorは対象外とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F004を読んだ(依存: F003完了済み。詳細実装列は無し)
- [x] `ARCHITECTURE.md` 11.1(Article)・13.3(alias source/confidence)・15.2(MediaReference)を確認した
- [x] `DATA_CONTRACTS.md` 6節のArticle JSON例を確認した(`schema_version`はcodec層のenvelope fieldでdataclass fieldではないと判断)
- [x] 既存の`model/diagnostics.py`/`model/inline.py`/`model/blocks.py`の実装スタイルを踏襲する

## 変更予定ファイル

- `src/wikiepwing/model/article.py`
- `tests/test_model_article.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_article.py
make check
git diff --check
```

## 完了条件

- [x] `Article`(page_id/revision_id/title/normalized_title/source_url/source_date_modified/abstract/blocks/aliases/categories/media/diagnostics/source_license_ids)を実装する
- [x] `Alias`(title/source/confidence、`ARCHITECTURE.md` 13.3)を実装する
- [x] `MediaReference`(`ARCHITECTURE.md` 15.2の全field)を実装する
- [x] `source_date_modified`をUTC ISO-8601(`...Z`)としてJSON往復できる
- [x] `payload()`/`parse_article()`が相互に往復可能である(blocks/aliases/media/diagnosticsのnested構造を含む)
- [x] 不正な値(空title、confidence範囲外、naive datetime等)をエラーとして拒否する
- [x] `make check`が成功する

## 非対象

- Model validator(TASK-F005)
- Canonical JSON codec/正規順序・hash(TASK-F006)
- HTMLからArticleへの実際の変換(Epic G以降)
- `SearchTerm`(Epic 14、別epic)

## 実施結果

- `src/wikiepwing/model/article.py`に`Article`/`Alias`/`MediaReference`と`payload()`/`parse_article`/`parse_alias`/`parse_media_reference`を実装した。
- `tests/test_model_article.py`に19件のテストを追加(roundtrip、非UTCタイムゾーン往復、バリデーション拒否)。
- `uv run pytest tests/test_model_article.py`: 19 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート450件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(F004チェック)、`LOG.md`(新規エントリ)を更新した。
- `Alias.source`の値集合はARCHITECTURE.md 13.3のalias候補一覧からのdocumented assumption。
- 次タスク: TASK-F005 Model validator。
