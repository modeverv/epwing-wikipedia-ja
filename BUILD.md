# BUILD.md

日本語Wikipedia(jawiki)からEPWING辞書のFreePWINGビルド入力(`entries.jsonl`とgraphics)を生成するまでの手順です。ここに書く各コマンドは、EPIC R(TASK-R001〜R009、実データ全件・約150万記事規模)およびEPIC S(TASK-S001〜S005、同一ホスト・Docker上での再現性検証)で実際に実行・検証済みのものです。

設定ファイルの詳細(プロファイルの合成方法など)は[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)、特にsection 20を参照してください。本書はパイプライン全体を「何をどの順で実行するか」に絞って説明します。

実際にEBWin/EBPocketなどで開けるEPWINGバイナリ(honmon)を全件データからビルドする最後の一段(`docker/toolchain`のFreePWINGツールチェーン呼び出し)は、本書執筆時点では全件規模での実施はまだ行っておらず、小規模フィクスチャ(3記事手作り・100記事)でのみ検証済みです。本書がカバーするのは、その入力(`entries.jsonl`とgraphics)を実データ全件から正しく生成するところまでです。

---

## 1. 前提条件

- **認証情報**: `WME_USERNAME`/`WME_PASSWORD`(または`WME_ACCESS_TOKEN`/`WME_REFRESH_TOKEN`)をWikimedia Enterprise Snapshotの認証情報として環境変数に設定します。TOMLへは書きません。
- **ディスク容量**: jawiki全件では、Snapshot(約29GB)・`raw.sqlite3`(約27GB)・`model.sqlite3`(約12GB)・`entries.jsonl`(約13GB、プロファイルごと)を合わせて、1回のビルドで100GB超を見込んでください。
- **実行環境**: ネイティブホスト実行(`uv run python -m wikiepwing.cli ...`)か、Dockerコンテナ実行(`docker compose build app`でビルドした`wikiepwing-app:dev`イメージ)のいずれかを選べます。Dockerで大規模ビルドを行う場合、Docker Desktopのメモリ割り当てを標準の約8GBから増やす必要があります(後述)。
- **ImageMagick**: Lite/Full向けの画像変換(`image-convert`)には`magick`(ImageMagick 7)が必要です(`brew install imagemagick`等)。

---

## 2. 実行前チェック(`doctor`)

```bash
uv run python -m wikiepwing.cli doctor
uv run python -m wikiepwing.cli doctor --json  # スキーマ付きJSONレポート
```

環境変数・パス・ツール導線を検証します。PLAN.md 30の「Full build前ゲート一覧」に挙げられた項目(toolchain smoke、reference scan、各種fixtureビルド green、resume/gaiji/image securityテストgreenなど)は、`src/wikiepwing/preflight.py`の`run_full_build_preflight`がdoctorのチェックとテストスイート結果を組み合わせて評価しますが、これは現時点ではCLIサブコマンド化されておらず、プログラムから呼び出す形です(TASK-R002で実施)。

---

## 3. Snapshotの取得(`acquire`)

```bash
export WME_USERNAME=...
export WME_PASSWORD=...

uv run python -m wikiepwing.cli acquire \
  --namespace 0 \
  --snapshot-version latest \
  --git-commit "$(git rev-parse HEAD)"
```

`paths.sources/<project>/<version_identifier>/`に全チャンクと`source.lock.json`が書き出されます。一度取得すれば、以降のingestはこの`source.lock.json`を指すだけで再ダウンロードは不要です。

事前にダウンロード済みのファイルがある場合は`register-local-source`で登録できます。取得済みSnapshotの整合性は`inspect-source --lock-path <source.lock.json>`で再検証できます。

---

## 4. パイプライン本体(`ingest` → `normalize` → `generate`)

3ステージを個別に実行するか、`build`でまとめて実行できます。

### 4.1 個別実行

```bash
uv run python -m wikiepwing.cli ingest \
  --lock-path paths.sources/<project>/<version>/source.lock.json \
  --git-commit "$(git rev-parse HEAD)"

uv run python -m wikiepwing.cli normalize \
  --git-commit "$(git rev-parse HEAD)"

uv run python -m wikiepwing.cli generate \
  --config config/profiles/<mini|lite|full>.toml \
  --entries-output paths.output/entries-<profile>.jsonl \
  --git-commit "$(git rev-parse HEAD)"
```

`--config`は複数回指定でき、後勝ちで合成されます(CONFIG_REFERENCE.md section 20参照)。

**重要**: プロファイル設定(`config/profiles/*.toml`)が実際に効くのは`normalize`ステージだけです(`images.enabled`が`article.media`の選択に影響します)。`generate`コマンド自体は`AppConfig`を一切参照しないため、同じ`model.sqlite3`から`generate`する限り、どのプロファイル設定を渡しても`entries.jsonl`の内容は同一になります(TASK-R008/R009で実データ全件規模で確認済み)。Mini/Lite/Fullで異なるのは、`normalize`時点でのメディア選択(後続のimage-fetch/convertが対象にする画像の範囲)です。

### 4.2 まとめて実行(`build`)

```bash
uv run python -m wikiepwing.cli build \
  --lock-path paths.sources/<project>/<version>/source.lock.json \
  --git-commit "$(git rev-parse HEAD)"
```

各ステージのmanifest(`paths.work/runs/<run-id>/manifests/*.json`)が既に`complete`かつ入力が変わっていなければ、そのステージはスキップされます(`--from-stage`/`--force-stage`で制御可能)。

### 4.3 検証(`verify-raw`/`verify`)

```bash
uv run python -m wikiepwing.cli verify-raw --raw-database paths.work/raw.sqlite3
uv run python -m wikiepwing.cli verify --entries paths.output/entries-<profile>.jsonl
```

`verify`は空tag/title、重複tag、記事間の重複見出し語、未解決リンクターゲットを検出します。実データでは、ページの削除・再作成に伴う「同一タイトル・同一URLだが異なるpage_id」という組み合わせが稀に(TASK-R006では150万件中5件)見つかることがあります。これはWikimedia Enterprise Snapshot自体の特性であり、wikiepwing側のバグではありません。

---

## 5. 画像パイプライン(Lite/Full、`image-plan`/`image-fetch`/`image-convert`)

```bash
uv run python -m wikiepwing.cli image-plan --model-database paths.work/model.sqlite3 > image-plan.json

uv run python -m wikiepwing.cli image-fetch \
  --config config/profiles/<lite|full>.toml \
  --model-database paths.work/model.sqlite3 \
  --originals-dir paths.work/media-originals \
  --report paths.reports/image-fetch-report.json

uv run python -m wikiepwing.cli image-convert \
  --originals-dir paths.work/media-originals \
  --report paths.reports/image-fetch-report.json \
  --cache-dir paths.cache/media-bmp \
  --graphics-dir paths.work/graphics
```

`image-fetch`は逐次ダウンロード(並列化なし)です。実データでのjawiki全件では、ユニーク画像URLが約250万件あり(TASK-R007の実測)、全件を逐次取得すると数日規模になります。全件が必要でない検証目的では、`model_media_orchestrate.plan_media`が返す`MediaPlanEntry`のタプルを間引いてから`fetch_media`/`convert_media`を直接呼び出す(既存関数をそのまま使う、コード変更不要)ことで、系統サンプリングによる縮小検証ができます(TASK-R007で約2万件のサンプルを検証)。

Wikimedia Commons(`upload.wikimedia.org`)への実際のリクエストには、Wikimedia側のUser-Agentポリシーへの準拠と、HTTP 429(rate limit)へのリトライ・バックオフが必須です(いずれも`src/wikiepwing/media/downloader.py`に実装済み)。

---

## 6. Docker実行時の注意

```bash
docker compose build app
docker run --rm \
  -v <sources>:/data/sources:ro \
  -v <work>:/data/work \
  -v <cache>:/data/cache \
  -v <output>:/data/output \
  -v <reports>:/data/reports \
  -v <logs>:/data/logs \
  wikiepwing-app:dev \
  wikiepwing <subcommand> ...
```

イメージの`config/default.toml`は`/data/...`をデフォルトパスとして持つため、上記のマウント先と一致していれば`--config`での上書きは不要です。

`generate`は全記事(jawiki全件で約150万件)をメモリに保持してから見出し語衝突をグローバルに解決するため、ネイティブホストでは30〜40GB規模のメモリを使用します。Docker Desktopの既定メモリ割り当て(macOSで約8GB)では全件`generate`が無応答終了(OOM)します。全件をDocker上で実行する場合は、Docker Desktopの設定でメモリ割り当てを増やしてください(TASK-S005では約85GBに設定して解決)。

---

## 7. 運用コマンド

```bash
uv run python -m wikiepwing.cli disk-usage         # config.paths配下の各ディレクトリのサイズを表示
uv run python -m wikiepwing.cli clean --keep-runs 2 --dry-run  # 古いpaths.work/runsを整理(paths.outputは対象外)
uv run python -m wikiepwing.cli update              # 最新Snapshotを取得し、直前バージョンとの差分(update-report.json/release-notes.md)を生成
```

---

## 8. 再現性の確認(参考: TASK-S004/S005)

同一入力から独立に2回ビルドし、`src/wikiepwing.build_logical_hash.compute_logical_build_hash`(`entries.jsonl`とgaiji/graphicsディレクトリのcontent-hashを合成)で論理内容が一致するか比較できます。

```python
from pathlib import Path
from wikiepwing.build_logical_hash import compute_logical_build_hash

h1 = compute_logical_build_hash(entries_jsonl=Path("entries-build1.jsonl"))
h2 = compute_logical_build_hash(entries_jsonl=Path("entries-build2.jsonl"))
assert h1 == h2
```

`raw.sqlite3`/`model.sqlite3`自体のsha256は、OS/SQLiteライブラリのビルド差異により環境間で一致しないことがあります(ページ配置がバイナリレベルで異なるため)。これは想定内であり、論理ハッシュ(`entries.jsonl`ベース)こそが再現性検証の正しい比較対象です。
