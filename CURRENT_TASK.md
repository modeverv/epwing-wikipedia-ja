# CURRENT_TASK.md

## Task ID

TASK-O010

## 目的

`ARCHITECTURE.md` 28.2(画像の帰属情報: source file page/author/license identifier/license URL)・`DATA_CONTRACTS.md`の画像cacheメタデータJSON(`attribution`フィールド: `source_page_url`/`author`/`license_identifier`/`license_url`、全てnullable)を実装する。Commons/Fileページからの実際の取得(28.2「取得できない項目はmissingとして記録」)は別機能(将来のEPIC O後続タスクまたはEPIC Pのprofile方針)であり、本タスクはモデル(dataclass・JSON payload/parse)と、ライセンス情報の有無を判定する`is_licensed`述語のみを実装する。「distributable profileの方針に従う」という実際の採否判断は、profileという概念自体がまだ存在しない(EPIC P未着手)ため対象外とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O010(依存: O001)を読んだ
- [x] `ARCHITECTURE.md` 28.2(画像の帰属情報)を再確認した
- [x] `DATA_CONTRACTS.md`の画像cacheメタデータJSON(`attribution`: `source_page_url`/`author`/`license_identifier`/`license_url`)を再確認し、フィールド名をそのまま採用した
- [x] `model/blocks.py`/`model/inline.py`/`model/article.py`のpayload/parseパターン(dataclass + `payload()` + `parse_*`関数、無効値は専用Error型)を踏襲する方針にした
- [x] `build_profile`(personal/distributable)という概念がまだコードベースに存在しない(EPIC P未着手)ことを確認し、実際の採否ポリシーは対象外にした

## 変更予定ファイル

- `src/wikiepwing/media/attribution.py`(新規: `MediaAttribution`, `AttributionError`, `is_licensed`, `parse_media_attribution`)
- `tests/test_media_attribution.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_attribution.py
make check
git diff --check
```

## 完了条件

- [x] `MediaAttribution`の全フィールド(`source_page_url`/`author`/`license_identifier`/`license_url`)がoptional(`None`許容)である
- [x] `payload()`が`DATA_CONTRACTS.md`の`attribution`フィールドと同じキー名のJSON辞書を返す
- [x] `parse_media_attribution`が`payload()`の出力を再びパースしてround-tripする
- [x] `is_licensed`が`license_identifier`が`None`でない場合に`True`を返す
- [x] 不正なJSON(型不一致等)は`AttributionError`を送出する
- [x] `make check`が成功する

## 非対象

- Commons/Fileページからの実際の帰属情報取得(将来の別タスク)
- build profile(personal/distributable)による採否ポリシー(EPIC P未着手のため対象外)

## 実施結果

- `src/wikiepwing/media/attribution.py`に`MediaAttribution`(`source_page_url`/`author`/`license_identifier`/`license_url`、全てoptional)・`AttributionError`・`is_licensed`・`parse_media_attribution`を実装した。フィールド名は`DATA_CONTRACTS.md`の画像cacheメタデータJSONの`attribution`フィールドとそのまま一致させた。
- `tests/test_media_attribution.py`(新規8件)で、round-trip・payload()のキー名一致・全フィールドnull許容・`is_licensed`のtrue/false判定(license_identifier有無、attribution自体がNoneの場合)・不正なJSON(非object・非string値)でのエラーを確認した。
- `make check`(format-check/lint/mypy/pytest 1191件、ImageMagick依存3件はローカル環境でskip)と`git diff --check`が成功した。
- Commons/Fileページからの実際の取得、build profileによる採否ポリシーは対象外(`build_profile`という概念自体がまだ存在しないため)。
