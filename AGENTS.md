# AGENTS.md

## 0. このファイルの目的

このリポジトリは、2026年時点の日本語Wikipediaから、Boookends 2023年版を参照実装とした高機能EPWING/JIS X 4081互換辞書を生成するためのものです。

このファイルはCodexなどの実装エージェント向けの最上位作業規約です。ほかのドキュメントと矛盾した場合は、次の優先順位で判断してください。

1. ユーザーが現在の会話で明示した指示
2. `AGENTS.md`
3. `CURRENT_TASK.md`
4. `ARCHITECTURE.md`
5. `PLAN.md`
6. `TASKS.md`
7. `TESTING.md`
8. `COMPATIBILITY.md`
9. `CONFIG_REFERENCE.md`
10. その他の文書・コメント

不明点があっても、広範囲を書き換えて推測で埋めてはいけません。小さな仮定を明記し、テスト可能な最小変更を行ってください。

---

## 1. 毎セッションの必須読書順

作業開始時は、必ず次の順で読みます。

1. `AGENTS.md`
2. `MEMORY.md`
3. `LOG.md` の末尾100行程度
4. `CURRENT_TASK.md`
5. `TASKS.md` の対象タスク
6. 対象タスクから参照される設計文書の節

毎回 `ARCHITECTURE.md` 全文を読み直す必要はありません。ただし、次の変更を行う場合は該当節だけでなく全文を確認してください。

- データベーススキーマの変更
- パイプラインのステージ追加・削除・順序変更
- 入力ソースの追加・変更
- EPWINGバックエンドの変更
- ビルド成果物の互換性変更
- 公開設定形式の変更
- 依存ライブラリの大幅変更

`CURRENT_TASK.md` が空、曖昧、または複数タスクを含む場合は、実装を始めず、`TASKS.md`から最小の未完了タスクを1つ選び、`CURRENT_TASK.md`を具体化します。

---

## 2. 絶対に守る開発原則

### 2.1 一度に1タスクだけ実装する

- `TASKS.md`の1つのタスクIDだけを対象とします。
- 同じ変更で別タスクまで「ついでに」実装しません。
- リファクタリングは、そのタスクを成立させる最小限に限定します。
- 変更ファイル数が予定より増えた場合は、いったん停止して理由を`LOG.md`へ記録します。

### 2.2 フルWikipediaビルドを早期に実行しない

次の条件をすべて満たすまで、完全版日本語Wikipediaの生成を開始してはいけません。

- 手作り3記事EPWINGが生成できる
- 小規模fixtureのend-to-endテストが通る
- 100記事fixtureが生成できる
- 中断・再開テストが通る
- 文字変換と外字フォールバックのテストが通る
- `wikiepwing verify` が機械的に成功判定できる
- `PLAN.md`のフルビルド前ゲートが完了している

### 2.3 入力データを直接信頼しない

以下はすべて外部入力です。

- Wikimedia Enterprise SnapshotのNDJSON
- Wikimedia公式XML/SQLダンプ
- Wikipedia HTML/Wikitext
- Wikimedia Commons画像
- 手元のBoookends 2023版EPWING
- 設定ファイル

必ずサイズ上限、文字列長、パス、URL、MIME、圧縮率、HTML構造を検証します。Wikitext、HTML、テンプレート、Lua、JavaScript、SVG内スクリプトを実行してはいけません。

### 2.4 秘密情報をリポジトリへ書かない

以下はコミット禁止です。

- Wikimedia Enterpriseのユーザー名・パスワード
- access token / refresh token / id token
- `.env`の実値
- API応答の認証ヘッダー
- ホスト側の個人パス

秘密情報は環境変数またはDocker secret相当で渡します。ログへ値を出してはいけません。

### 2.5 ホスト環境を汚さない

ホストにFreePWING、EB Library、Perlモジュール、ImageMagick設定などを直接インストールしません。通常の開発・テスト・生成はDocker内で完結させます。

許可されるホスト要件は次だけです。

- Docker / Docker Compose
- Git
- 任意のEPWINGビューアによる手動確認

### 2.6 失敗を隠さない

- `except Exception: pass` を禁止します。
- 記事単位で回復可能な失敗は構造化診断として保存します。
- ステージ全体の整合性を壊す失敗は即座に停止します。
- スキップした記事・画像・表・数式は必ず件数を集計します。
- 「たぶん動く」を完了条件にしません。

### 2.7 互換性は測定する

Boookends互換とは、バイナリ一致やブランドの再現ではありません。`COMPATIBILITY.md`の測定項目で比較します。

以下を根拠なしに主張してはいけません。

- Boookendsと完全互換
- すべてのEPWINGビューアで動く
- すべての記事を完全に再現
- すべてのUnicode文字を表示可能
- 画像ライセンス処理が完全

---

## 3. 実装の技術的境界

### 3.1 正規の入力経路

v2の標準入力は、Wikimedia Enterpriseの通常Snapshotに含まれるレンダリング済みHTMLです。標準Snapshotには記事HTML、Wikitext、redirects、categories、licenseなどの項目が含まれます。

ただし、APIやネットワークへ依存したまま後続処理を動かしてはいけません。

正しい流れは次です。

1. `acquire` ステージでSnapshotをローカルへ固定
2. SHA-256、識別子、版、取得日時を`source.lock.json`へ記録
3. 以後のステージはローカルファイルのみを読む
4. 必要に応じて通常のWikimedia XML/SQLダンプを検証・フォールバック用に追加

Structured Contents Snapshotは2026年7月時点で日本語Wikipediaを対象としていないため、必須経路にしてはいけません。

### 3.2 内部文字コード

- 内部表現はUTF-8 Unicodeです。
- Unicodeを早い段階でJISへ丸めません。
- EPWING出力直前のbackend adapterで、標準文字・置換・外字へ分類します。
- 文字損失は件数と文字集合をレポートします。

### 3.3 FreePWING境界

FreePWING、EB Library、`ebzip`固有処理は、次の配下から外へ漏らしてはいけません。

```text
src/wikiepwing/epwing/
docker/toolchain/
patches/freepwing/
patches/eb/
```

記事パーサーや検索語抽出器がFreePWING用タグを直接生成してはいけません。必ず中間モデルを通します。

### 3.4 データベース境界

- SQLiteを使用します。
- SQLAlchemyなどのORMは導入しません。
- スキーマは明示SQLで管理します。
- マイグレーションは番号付きSQLで管理します。
- ステージごとのDBを原則として不変成果物にします。
- 大量BLOBはzstd圧縮して保存します。

### 3.5 Dockerボリューム

大量I/Oを伴う中間データをmacOS bind mountへ置いてはいけません。

- ダンプ: named volume
- 作業DB: named volume
- 画像・数式キャッシュ: named volume
- 最終ZIP、レポート、ログ: bind mount可能
- 小規模fixture: リポジトリ内でよい

---

## 4. コーディング規約

### 4.1 Python

- Python 3.12系を固定します。
- パッケージ管理は`uv`を使用します。
- `uv.lock`をコミットします。
- public関数・クラスには型注釈を付けます。
- `mypy`または`pyright`の設定に従います。
- `ruff`をformatter/linterとして使用します。
- `pathlib.Path`を使用します。
- subprocessは引数配列で呼び、`shell=True`を使いません。
- 時刻はUTCのtimezone-aware datetimeで保存します。
- JSONは安定したキー順を必要とする場面では明示的にソートします。

### 4.2 SQL

- `SELECT *`を永続コードで使いません。
- 大量挿入はtransactionとbatchを使います。
- 外部キー制約を有効にします。
- `busy_timeout`を設定します。
- DBスキーマの変更にはmigrationとschema testを追加します。
- 大規模な`ALTER TABLE`を安易に実施せず、新DB生成ステージを優先します。

### 4.3 ログ

ログは人間可読形式とJSON Lines形式の両方を生成できるようにします。

必須フィールド:

```text
timestamp
level
stage
run_id
event
page_id     # 記事に関係する場合
title       # 記事に関係する場合
diagnostic_code
message
```

トークン、パスワード、Authorizationヘッダーをログに出してはいけません。

### 4.4 コメント

コメントには「何をしているか」より「なぜその制約が必要か」を書きます。ドキュメントで説明済みの内容を大量にコードへ複製しません。

---

## 5. テスト規約

### 5.1 変更には必ずテストを付ける

次のいずれかを必須とします。

- unit test
- snapshot test
- integration test
- end-to-end fixture test
- toolchain smoke test

テストなしで許可される変更は、誤字修正とコメント修正だけです。

### 5.2 ネットワークに依存しない

通常のテストスイートはネットワークへ接続しません。ネットワークを使うテストは`network` markerを付け、明示的に実行します。

### 5.3 ゴールデンデータ

ゴールデンデータ更新時は、差分を確認せず一括更新してはいけません。

更新手順:

1. 変更前テストを実行
2. 期待差分を説明
3. 対象fixtureだけ更新
4. 更新後差分を確認
5. `LOG.md`へ理由を記録

### 5.4 手動確認は自動テストの代替ではない

EBWin、EBPocket、Emacs Lookupなどでの確認は重要ですが、完了判定には自動検証も必要です。

---

## 6. 1タスクの標準作業フロー

### Step 1: 状態確認

```bash
git status --short
git branch --show-current
```

未コミット変更がある場合は、対象タスクと関係するか確認します。無関係な変更を勝手に戻してはいけません。

### Step 2: 対象タスク確認

`CURRENT_TASK.md`に次を記入します。

- Task ID
- 目的
- 変更予定ファイル
- 実行予定コマンド
- 完了条件
- 非対象

### Step 3: 失敗するテストを先に作る

可能な限り、要求を表す失敗テストまたはfixtureを先に追加します。

### Step 4: 最小実装

- 対象タスクだけを実装します。
- 将来のための抽象化を過剰に追加しません。
- ただし`ARCHITECTURE.md`で明示された境界は守ります。

### Step 5: 局所テスト

変更箇所に近いテストから実行します。

### Step 6: 標準検証

最低限、次を実行します。

```bash
make format-check
make lint
make typecheck
make test
```

Docker/ツールチェーンに関係するタスクでは、対応するsmoke testも実行します。

### Step 7: 文書更新

- `TASKS.md`の状態を更新
- `LOG.md`へ実施内容とコマンド結果を追記
- 長期的判断なら`MEMORY.md`へ追記
- 設計変更なら`DECISIONS.md`と`ARCHITECTURE.md`を更新

### Step 8: 完了報告

完了報告には次だけを簡潔に書きます。

- 何を変更したか
- 主要ファイル
- 実行したテストと結果
- 残課題
- 次に実行すべきTask ID

「完了」と書く前に、`CURRENT_TASK.md`の完了条件を1項目ずつ確認します。

---

## 7. 禁止事項

以下は禁止です。

- 一気に全機能を実装する
- 全ファイルを大規模に書き換える
- 既存テストを削除して通す
- failureをwarningへ落として通す
- 型エラーを大量の`Any`で隠す
- `# type: ignore`を理由なしに追加する
- 任意コード実行を伴うWikitext/Lua処理
- HTML中のJavaScript実行
- SVGをブラウザやImageMagickへ無検証で渡す
- URLから生成した文字列を保存パスへ直接使う
- 記事タイトルをシェルコマンドへ埋め込む
- 生成物や巨大ダンプをGitへ追加する
- Boookendsの名称・ロゴ・作者性を自作成果物へ流用する
- 出典・ライセンス記録を削除する
- フルビルド成功だけで品質合格とする

---

## 8. 迷ったときの判断規則

1. データを失わない方を選ぶ
2. 後から再実行できる方を選ぶ
3. ステージ境界を守る方を選ぶ
4. テスト可能な方を選ぶ
5. 読みやすい辞書出力を優先する
6. 見た目の完全再現より意味保存を優先する
7. 互換性を推測せず測定する
8. 小さいfixtureで確認してから大きくする

---

## 9. 完了定義

タスクは次をすべて満たすまで完了ではありません。

- コードまたは文書が要求を満たす
- 対応テストがある
- 標準検証が成功する
- 失敗・スキップが可視化される
- ドキュメントが現状と一致する
- `LOG.md`が更新される
- 次タスクが明確である

プロジェクト全体の完了条件は`PLAN.md`と`COMPATIBILITY.md`に従います。
