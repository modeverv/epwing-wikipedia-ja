# CURRENT_TASK.md

## Task ID

TASK-F006

## 目的

`PLAN.md` Phase 5の"JSON debug codec"/"schema version"/"canonical ordering"を実装する。Articleを`schema_version`封筒付きの決定的(key順ソート、区切り固定)なJSONバイト列にencode/decodeできるようにし、`DATA_CONTRACTS.md` 6節のArticle JSON例(`"schema_version": 1`)と整合させる。ハッシュ計算自体はTASK-F008の対象であり、本タスクは決定的なcanonical bytesの生成までを担う。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F006(依存: F004-F005)・F007(依存: F006)・F008(依存: F006、完了条件"order-independent sources yield deterministic canonical output")を読んだ
- [x] `ARCHITECTURE.md`にcanonical JSON serializationの詳細(key順/区切り/encoding)は明文化されていないことを確認した(未確定事項として自分でdocumented assumptionを置く)
- [x] `PLAN.md` Phase 5出口条件("canonical hash安定"は本タスクでは対象外、F008で扱う)を確認した
- [x] `DATA_CONTRACTS.md` 6節のArticle JSON例(`schema_version`はdataclass fieldではなくenvelope field)を確認した
- [x] 既存の`model/article.py`の`payload()`/`parse_article()`を確認した

## 変更予定ファイル

- `src/wikiepwing/model/canonical.py`
- `tests/test_model_canonical.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_canonical.py
make check
git diff --check
```

## 完了条件

- [x] `encode_article`/`decode_article`が相互に往復可能である
- [x] JSON出力が`sort_keys=True`・固定`separators`・`ensure_ascii=False`で決定的である(同一Articleから2回encodeしてbyte完全一致)
- [x] `schema_version`をtop-level envelope fieldとして埋め込み、`DATA_CONTRACTS.md`の例と一致する
- [x] 未対応の`schema_version`を明示的なcodec errorとして拒否する(黙って無視しない)
- [x] 不正なJSONバイト列・非object envelopeを拒否する
- [x] `make check`が成功する

## 非対象

- Canonical hash計算(TASK-F008)
- Compressed model DB schema(TASK-F007)
- 複数schema_versionの後方互換decoder(将来のtype追加時に対応)

## 実施結果

- `src/wikiepwing/model/canonical.py`に`encode_article`/`decode_article`/`CanonicalCodecError`を実装した。
- `tests/test_model_canonical.py`に10件のテストを追加。
- `uv run pytest tests/test_model_canonical.py`: 10 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート471件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(F006チェック)、`LOG.md`(新規エントリ)を更新した。
- canonical JSON serializationのkey順/区切り/encodingは仕様に明文化が無かったためdocumented assumption(`sort_keys=True`/`ensure_ascii=False`/`separators=(",", ":")`)を採用した。
- 次タスク: TASK-F007 Compressed model DB schema。
