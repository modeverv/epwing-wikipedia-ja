# CURRENT_TASK.md

## Task ID

TASK-S005

## 目的

`TASKS.md`のTASK-S005(Cross-host comparison、依存: S004完了済み)を実施する。この実行環境には物理的に別ホストが存在しないため、ユーザーに確認のうえ、Docker(`docker/app.Dockerfile`、python:3.12.13-slim-bookworm、Debian Linux)コンテナ内でのビルドを「異なる環境」の代替として採用し、macOSホストネイティブ実行(TASK-S004)の成果物とbyte-for-byte比較する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S005(依存: S004、完了済み)を読んだ
- [x] AskUserQuestionで「Docker経由で同一マシン上で実施する」ことの承認を得た(PLAN.md 28の作業項目に「macOS Docker Desktop」「native Linux Docker」が含まれており、Dockerベースの環境差異検証は元々想定されていた手法であることを確認)
- [x] `docker compose build app`でイメージをビルド済み(`wikiepwing-app:dev`)
- [x] `docker/app.Dockerfile`はDebian slim(python:3.12.13-slim-bookworm)ベースで、macOSホスト(Darwin/uv管理Python)とはOS・libc・SQLite/zstandardのビルドが異なる、真の環境差異軸であることを確認した
- [x] `docker run`で`compose.yaml`の名前付きvolumeを使わず、スクラッチパッドの既存source.lock.json/チャンクを直接bind mountして再ダウンロードを回避する設計にした

## 変更予定ファイル

- なし(コード変更を伴わない実行タスク。スクラッチパッド内に3回目の`raw3.sqlite3`/`model3.sqlite3`/`entries-rebuild3.jsonl`をコンテナ経由で生成する)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
docker compose build app

docker run --rm \
  -v "$SCRATCH/data/sources:/data/sources:ro" \
  -v "$SCRATCH/docker-work:/data/work" \
  -v "$SCRATCH/docker-cache:/data/cache" \
  -v "$SCRATCH/config-override.toml:/data/config-override.toml:ro" \
  wikiepwing-app:dev \
  wikiepwing ingest --config /data/config-override.toml --raw-database /data/work/raw3.sqlite3 \
    --lock-path /data/sources/jawiki/.../source.lock.json --run-id docker-ingest

# 同様にnormalize/generateを実行し、macOSホスト版(TASK-S004)の成果物とsha256比較する
```

## 完了条件

- [x] Dockerコンテナ内でingest→normalize→generateがすべて`status=complete`で完了する
- [x] コンテナ内成果物とmacOSホスト成果物(TASK-S004)の`entries.jsonl`論理ハッシュを比較する
- [x] 一致しない場合は差異の原因を調査・報告する(PLAN.md出口条件「binary差異説明」)(今回は完全一致のため差異なし)
- [x] 実行中に実データ固有のクラッシュ・バグが見つかった場合は原因を特定し、コード修正・テスト追加・commitしてから再実行する(コードのバグではなく、Docker Desktopのメモリ割り当て不足という環境要因が原因のクラッシュが1件発生。ユーザーがDocker Desktopのメモリを約85GBへ増やして解決)

## 非対象

- 真に別の物理・仮想ホストでの検証(この環境では利用不可のためDockerで代替)
- 実データを`git`にコミットすること

## 実施結果

物理的に別ホストが無い制約に対し、ユーザーの承認を得てDockerコンテナ(`wikiepwing-app:dev`、Debian slim/python:3.12.13-slim-bookworm)を「異なる環境」として使い、macOSホスト(TASK-S004)と同一の`source.lock.json`から独立にingest→normalize→generateを実行した。

- コンテナ内`raw3.sqlite3`/`model3.sqlite3`は、articles_read/written/errors/warningsなどのメトリクスがmacOSホスト版と完全一致した(sha256自体はOS/SQLiteビルドの違いにより異なるが、これは想定通りで問題ではない)。
- 1回目の`generate`実行はDocker Desktop VMのメモリ割り当て不足(既定約7.75GB)によりコンテナが無応答終了(manifestが`status=running`のまま、0記事処理)した。原因調査の結果、`render/generate.py`の`_render_all`が全記事を一括で`fetchall()`しメモリ上に保持する設計(見出し語衝突解決を全記事横断でグローバルに行うため、ストリーミング化が容易ではない)によるもので、ソフトウェアのバグではなくDocker VM側のリソース制約と判断した。ユーザーに確認のうえ、Docker Desktopのメモリ割り当てを約85GBへ増やしてもらい再実行した。
- 2回目の`generate`実行は成功し、`entries-rebuild3.jsonl`のsha256が macOSホストの`entries-mini/lite/full.jsonl`・TASK-S004の`entries-rebuild2.jsonl`すべてとbyte-for-byte完全一致した(`1b6310d24f3485b1c2436cc2b0b3a7b3d75c006275f59e3f7474fb6078c58ac7`)。
- `build_logical_hash.compute_logical_build_hash`による論理ハッシュもmacOSホスト版とDocker版で完全一致した(`765528ac4926c5a37d6b527c1f140ca7b9a408be7bcaa8a774d2e9d947141c57`)。

PLAN.md 28(Phase 24 再現性試験)の出口条件「entry logical hash一致」を、OS・libc・SQLite/zstandardビルドが異なる環境間で実データ全件規模で確認した。差異が無かったため「binary差異説明」は不要。コンテナ成果物(`raw3.sqlite3`, `model3.sqlite3`, `entries-rebuild3.jsonl`)はスクラッチパッドのみに保持し、gitにはコミットしない。
