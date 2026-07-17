# LICENSING.md

プログラム自体のライセンスと、生成する辞書に含まれるWikipedia本文・画像のライセンスは別です。公開配布を行う前に、本書の内容を確認してください。

---

## 1. プログラムのライセンス

`wikiepwing`本体(このリポジトリのソースコード)はMITライセンスです(`pyproject.toml`の`license`フィールド)。

## 2. コンテンツのライセンス(本文)

Wikipedia記事本文は、Wikimedia Enterprise Snapshotの各記事に付与された`license`フィールド(CC BY-SA 4.0であることが多い)に従います。取り込み時の扱いは以下の通りです:

- `ingest`が各記事の`license`配列を`licenses`テーブル(識別子・名称・URL)と`article_licenses`(記事ごとの紐付け)として`raw.sqlite3`に保存します(`src/wikiepwing/ingest/repository.py`)。
- `normalize`がこれを`Article.source_license_ids`として`model.sqlite3`に引き継ぎます(`src/wikiepwing/normalize/orchestrate.py`の`_read_license_ids`)。
- 現状、`generate`が書き出す`entries.jsonl`自体にはライセンス情報は含まれません(本文テキストのみ)。ライセンス表示は、後述の「未実装の部分」にある通り、パッケージング時に別途添付する設計です。

## 3. コンテンツのライセンス(画像)

画像1件ごとの帰属情報(attribution)は`src/wikiepwing/media/attribution.py`の`MediaAttribution`モデルとして実装済みです:

```python
MediaAttribution(
    source_page_url,      # 画像の出典ページURL
    author,                # 作者名
    license_identifier,     # ライセンス識別子(例: "CC-BY-SA-4.0")
    license_url,            # ライセンス本文へのURL
)
```

`is_licensed(attribution)`が「ライセンス識別子を持つか」を判定します。`config/default.toml`の`images.missing_license_action`(`warn`/`exclude`/`fail`)で、ライセンス不明画像の扱いを制御できます。`distribution.mode = "public"`の場合、`exclude`以上が強制されます(`src/wikiepwing/config.py`のバリデーション)。

この帰属情報はDATA_CONTRACTS.md 9(image cache contract)の`attribution`フィールドとしてmedia cacheのメタデータに保存されます(`src/wikiepwing/media/cache.py`が利用する形状)。

## 4. ビルド由来情報(BUILD-INFO.json)

`src/wikiepwing/build_info.py`(TASK-S001)の`build_build_info`が、以下を含む`BUILD-INFO.json`を生成します:

- 入力Snapshotの`project`/`snapshot_version`(`SourceLock`由来)
- ビルドツールの`software`ブロック(`git_commit`、`app_image_digest`、`toolchain_image_digest`)
- ビルド日時、プロファイル

これは「生成物に入力Snapshot・ビルドツール情報を含める」というREADME.mdの方針を実装した部分です。

## 5. 未実装の部分(正直な現状)

DATA_CONTRACTS.md 11は、公開パッケージの内部構成として以下を規定しています:

```text
output/
├── jawiki-<snapshot>-<profile>.epwing.zip
├── jawiki-<snapshot>-<profile>-BUILD-INFO.json
└── jawiki-<snapshot>-<profile>-attribution.jsonl

ZIP internal root:
  BUILD-INFO.json
  LICENSES.txt
  ATTRIBUTION.txt or attribution data
```

本書執筆時点で、以下は**設定の検証ロジックとしては存在するが、実際に生成するコードは存在しません**(リポジトリ全体をgrepして確認済み):

- `attribution.jsonl`サイドカーファイルを書き出す処理
- ZIP内に`LICENSES.txt`/`ATTRIBUTION.txt`を同梱する処理
- 上記フォーマットで最終的な`.epwing.zip`をパッケージングする処理そのもの(`src/wikiepwing/archive.py`のTASK-S003は汎用の決定的ZIP生成関数であり、このEPWING固有パッケージ構成を組み立てる処理ではありません)

`distribution.include_attribution_appendix`は現状、`config.py`の`_validate_semantics`が「`mode=public`のとき`true`でなければエラー」という設定値の検証のみを行っており、実際にappendixの中身を生成するコードには繋がっていません。

**公開配布を行う場合**は、上記の未実装部分を先に実装するか、`media_references`テーブル・`MediaAttribution`の情報を手動で集約してライセンス表示ファイルを作成してください。

---

## 6. 関連ドキュメント

- 画像帰属情報のデータ形状: [DATA_CONTRACTS.md](DATA_CONTRACTS.md) 9(image cache contract)、11(package contract)
- 設定項目: [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) 12(`[images]`)、16(`[distribution]`)
