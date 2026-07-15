# CURRENT_TASK.md

## Task ID

TASK-O007

## 目的

`ARCHITECTURE.md` 15.4/17.3の「image conversion tools」「ImageMagick delegate制限」を実装する。TASK-O005が検証したラスター画像(PNG/JPEG/GIF/WEBP)とTASK-O006がsanitizeしたSVGを、EPWING toolchainが期待するBMP形式(`tests/fixtures/handcrafted/generate_bitmap.pl`と互換)へ変換する。ユーザーの選択(AskUserQuestion)に従い、ImageMagickをDocker toolchain imageへ追加し(SVGラスタライズのため`librsvg2-bin`も追加)、`policy.xml`でdelegateを制限したうえで、Pythonからは`convert`/`magick` CLIをsubprocess経由で呼び出す。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-O007(依存: O005-O006)を読んだ
- [x] `ARCHITECTURE.md` 15.4(「ImageMagick delegate制限」)・17.3(toolchain imageの固定コンポーネントに「image conversion tools」)を再確認した
- [x] AskUserQuestionでImageMagick方式(Recommended)を選択したことを確認した
- [x] snapshot.debian.orgの実際のPackages index(`dists/bookworm/main/binary-amd64/Packages`、pinされたsnapshot日時)から`imagemagick`(`8:6.9.11.60+dfsg-1.6+deb12u9`)・`librsvg2-bin`(`2.54.7+dfsg-1~deb12u1`)の正確なバージョンを確認した(poolディレクトリの一覧だけでなく、実際にそのsnapshot日時でaptが解決するバージョンを使う)
- [x] ImageMagickの`policy.xml`は、パッケージインストール後に上書きしないとdpkgの展開で標準policyに戻ってしまうため、apt-get installの後にCOPYする順序にした

## 変更予定ファイル

- `docker/toolchain.Dockerfile`(imagemagick/librsvg2-bin追加、policy.xml上書き)
- `docker/toolchain/imagemagick-policy.xml`(新規: 危険なcoder/delegateを無効化した制限policy)
- `src/wikiepwing/media/raster_converter.py`(新規: `RasterConversionError`, `convert_to_bmp`)
- `tests/test_media_raster_converter.py`(新規、ImageMagickバイナリ未検出時はskip)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_media_raster_converter.py
make check
git diff --check
```

## 完了条件

- [x] `convert_to_bmp(content, source_format="png")`がBMPバイト列(`BM`マジック始まり)を返す(ImageMagickバイナリがローカルにない場合はskip)
- [x] `source_format="svg"`のSVGバイト列もBMPへ変換できる(librsvg delegate経由)
- [x] 空バイト列は事前に拒否する
- [x] ImageMagickがエラー終了した場合(不正なバイト列等)は`RasterConversionError`を送出する(クラッシュしない)
- [x] timeoutが機能する
- [x] `make check`が成功する(ローカル環境ではImageMagick依存のテストはskipされることを許容する)

## 非対象

- content-addressed cache(TASK-O008)
- dedup(TASK-O009)
- 実際のEPWING graphics統合(TASK-O011)

## 実施結果

- `docker/toolchain.Dockerfile`のruntime stageに`imagemagick=8:6.9.11.60+dfsg-1.6+deb12u9`・`librsvg2-bin=2.54.7+dfsg-1~deb12u1`を追加した(バージョンはsnapshot.debian.orgの`dists/bookworm/main/binary-amd64/Packages`から実際にそのsnapshot日時でaptが解決する値を確認して採用、poolディレクトリの一覧に見える最新版とは異なった)。`docker/toolchain/imagemagick-policy.xml`(新規)で危険なcoder(MSL/URL/HTTPS/HTTP/FTP/EPHEMERAL/MVG/TEXT/SHOW/WIN/PLT/PS系/PDF/XPS)を無効化し、apt-get installの**後**に`COPY`で上書きする順序にした(先に置くとdpkgの展開でパッケージ既定のpolicy.xmlに戻ってしまうため)。
- `src/wikiepwing/media/raster_converter.py`に`RasterConversionError`・`convert_to_bmp`・`is_imagemagick_available`を実装した。`magick`(ImageMagick 7)または`convert`(ImageMagick 6)をsubprocess経由で呼び出し、`format:-`記法でstdin/stdoutを使いバイト列を一時ファイルなしでやり取りする。
- `tests/test_media_raster_converter.py`(新規8件、実変換系5件はImageMagick未検出時に`pytest.mark.skipif`でskip、エラー系3件は常時実行)、`tests/test_media_toolchain_definition.py`(新規5件、Dockerfile/policy.xmlの内容検証)。
- テスト中に発見した実バグ: `imagemagick-policy.xml`のコメント内に含まれるem-dash(`--`)がXMLコメントとして不正(XML仕様上コメント内に`--`は使えない)で、実際にパースエラーになることを`test_policy_file_is_well_formed_xml`で検出し修正した。修正しなければDocker build自体は通ってもpolicy.xmlがImageMagickに読み込まれず、制限が効かない状態になっていた可能性がある。
- `make check`(format-check/lint/mypy/pytest 1171件、ImageMagick依存3件はローカル環境でskip)と`git diff --check`が成功した。
- content-addressed cache・dedup・実際のEPWING graphics統合は対象外(TASK-O008-O011)。
