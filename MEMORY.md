# MEMORY.md

セッションをまたいで維持する、短く安定したプロジェクト記憶です。一時的な作業記録は`LOG.md`へ書きます。

## 固定された目的

- 2026年時点の日本語Wikipediaから高機能EPWING互換辞書を生成する。
- Boookends 2023年版は挙動比較の参照実装として扱う。
- Boookendsのバイナリ一致、内部実装復元、名称の流用は目的としない。
- Docker内で再現可能に生成する。
- Mini / Lite / Fullの3プロファイルを持つ。

## 固定された設計判断

- 標準入力はWikimedia Enterprise通常SnapshotのHTML。
- Structured Contentsは日本語版の必須経路にしない。
- Wikimedia公式XML/SQLダンプを補助・検証経路として利用する。
- 後続ステージはネットワークを使わず、取得済み入力だけを読む。
- Python 3.12、`uv`、SQLite、明示SQL、Docker named volumeを使う。
- FreePWING固有処理はEPWING adapter内へ隔離する。
- 内部文字列はUTF-8を維持し、出力時に標準文字・置換・外字へ分類する。
- フルビルドよりfixture vertical sliceを優先する。

## 品質原則

- unsupported内容を黙って捨てない。
- スキップ、変換失敗、欠落を構造化診断として集計する。
- 見た目の完全一致より、意味と検索可能性を優先する。
- 互換性は自動比較と複数ビューアの実測で判断する。

## 未決事項

- FreePWING toolchainの最終固定バージョンと必要パッチ
- Boookends 2023版が使用する外字方式の詳細
- EPWING backendが扱える画像形式・寸法の最適値
- Fullプロファイルの画像上限と最終容量
- 条件検索・クロス検索の具体的な索引設計
