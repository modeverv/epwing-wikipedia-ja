# CURRENT_TASK.md

## Task ID

TASK-E007

## 目的

`raw.sqlite3`への実際の書込を行うrepositoryを実装する。transaction・prepared SQL・foreign keyを守り、accepted/rejected記事・重複記録・診断をprepared文で永続化する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-E007を読んだ(依存: E001,E002,E006、いずれも完了済み。E005はTASK-E008の依存であり本タスクの対象外)
- [x] `DATA_CONTRACTS.md` 4節(articles/redirects/categories/templates/licenses/article_licenses/main_images/ingest_duplicates/diagnostics)を確認した
- [x] `ARCHITECTURE.md` 10.5(重複処理)、10.6(入力上限、HTML超過はreject)を確認した
- [x] TASK-E001(`ingest/database.py`)、TASK-E002(`zstd_codec`)、TASK-E004(`RawArticle`)、TASK-E005(`Diagnostic`)、TASK-E006(`DuplicateRecord`/`ExistingArticleState`)を確認した

## 変更予定ファイル

- `src/wikiepwing/ingest/repository.py`
- `tests/test_repository.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_repository.py
make check
git diff --check
```

## 完了条件

- [x] `get_existing_accepted`がpage_idごとの既存accepted state(revision_id/source_hash/source_sequence)を取得する(TASK-E006の重複解決へ渡す入力)
- [x] `write_accepted_article`がarticles行をUPSERTし、redirects/categories/templates/article_licenses/main_imagesをFK順序を守って置換する(古いchild行を先に削除してから再挿入)
- [x] `write_rejected_article`がchild行を作らずarticles行のみ(html/wikitext blob無し)を記録する
- [x] `write_duplicate`/`write_diagnostic`が`ingest_duplicates`/`diagnostics`へ記録する
- [x] `batch()` context managerがtransactionを管理し、例外時はrollbackする
- [x] html/wikitextの永続化に`zstd_codec.compress`を使う
- [x] `PRAGMA foreign_keys = ON`下で全操作がforeign key制約を満たす
- [x] `make check`が成功する

## 非対象

- validate_article・resolve_duplicateの呼び出し(オーケストレーションはTASK-E008)
- Ingestコマンド自体(TASK-E008)

## 実施結果

- `src/wikiepwing/ingest/repository.py`に`RawRepository`、`normalize_title`、`RawRepositoryError`を実装した。
- `get_existing_accepted`は`ingest_status='accepted'`の行のみ対象にし、rejected行は既存stateとして扱わない(重複解決の基準を信頼できるacceptedデータのみに限定)設計にした。
- `write_accepted_article`は`INSERT ... ON CONFLICT(page_id) DO UPDATE`によるprepared UPSERT、html/wikitextを`zstd_codec.compress`で圧縮して保存、redirects/categories/templates/article_licenses/main_imagesをFK順序(親articles行upsert後に子行を削除→再挿入)で置換した。
- `write_rejected_article`はhtml_zstd/wikitext_zstd無し・child行無しでarticles行のみ記録した(oversizeがreject理由になりうる大きなblobを無駄に保持しない)。
- `write_duplicate`/`write_diagnostic`は`ingest_duplicates`/`diagnostics`へprepared文で記録した。
- `batch()`はcontext managerとして`BEGIN IMMEDIATE`→正常終了で`commit`、例外時は`rollback`して再raiseする。
- コンストラクタで`PRAGMA foreign_keys`が有効でない接続を拒否した。
- TASK-D010の10正常記事をすべて書込み、`PRAGMA integrity_check`/`foreign_key_check`が共に成功することを確認した。
- `tests/test_repository.py`に12件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート350件、`git diff --check`が成功した。

**判断・注意点**

- title正規化は最小限のNFKC+trimのみとし、実際の日本語索引正規化(かな variant等)はEPIC J(日本語検索)の対象として残した。
- `validate_article`/`resolve_duplicate`の呼び出しはこのrepositoryの責務外とし、TASK-E008(Ingestコマンド)がオーケストレーションする。
