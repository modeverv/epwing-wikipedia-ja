# CURRENT_TASK.md

## Task ID

TASK-T020

## 目的

FreePWINGの半角・全角外字それぞれ8,192文字という上限をgenerate段階で守り、全件日本語Wikipediaから実際にEPWING辞書ZIPを生成する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] 実生成物が半角26,837・全角113,761外字を含み、FreePWINGが8,193文字目で停止することを確認した

## 変更予定ファイル

- `src/wikiepwing/gaiji/code_assignment.py`
- `src/wikiepwing/gaiji/embedding.py`
- 対応するgaiji/generateテスト
- `GAIJI.md`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest -q tests/test_gaiji_code_assignment.py tests/test_gaiji_embedding.py tests/test_render_generate.py
make format-check
make lint
make typecheck
make test
uv run python -m wikiepwing.gaiji.capacity \
  --entries-source entries-mini.jsonl --database gaiji.sqlite3 \
  --gaiji-source gaiji --entries-output data/work/entries-mini.jsonl \
  --gaiji-output data/work/gaiji \
  --report data/reports/gaiji-capacity-report.json
make build-epwing ENTRIES=data/work/entries-mini.jsonl \
  GRAPHICS_DIR=data/work/graphics GAIJI_DIR=data/work/gaiji \
  TITLE="日本語ウィキペディア二〇二六年六月" \
  EPWING_OUTPUT=data/output/jawiki.epwing.zip
unzip -t data/output/jawiki.epwing.zip
```

## 完了条件

- [x] narrow/wideそれぞれの外字数が8,192以下になる
- [x] 上限外文字が黙って消えず`[U+XXXX]`フォールバックとレポートへ入る
- [x] 選択・コード割当が入力順に依存せず決定的である
- [x] 対応テストと標準検証が成功する
- [x] `data/output/jawiki.epwing.zip`が実生成され、機械検証に成功する

## 結果

- 1,508,200記事からEPWING辞書ZIPを生成した。
- narrow/wide外字は各8,192文字。容量超過305,600出現を`[U+XXXX]`へ置換した。
- FreePWINGで空語となる検索別名12件を可視化して除外し、共有検索語8件は複数候補として保持した。
- ZIPは5.7 GiB、SHA-256は`d3ec046a0c710e1d6fae61a2f5ec476a555cbda32df0f1f484da1bdf2b4b8b3a`。

## 非対象

- EPWING規格・FreePWINGの8,192文字上限をパッチで拡張すること
- 複数subbookへの自動分割
- 入力Wikipediaデータの再取得・再normalize
