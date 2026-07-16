# CURRENT_TASK.md

## Task ID

TASK-T002

## 目的

`TASKS.md`のTASK-T002(Configuration examples、依存: P003 Lite profile, Q006 Full profile。両方完了済み)を実装する。`CONFIG_REFERENCE.md`にはすでに各プロファイル(mini/lite/full)のTOML差分(section 17)が実装済みの`config/profiles/*.toml`と一致した状態で存在するため、本タスクでは「設定ファイルをどう合成してどのCLIコマンドに渡すか」という実行可能な例を追加する。TASK-T001(Build guide、依存: R006未完了)のような全パイプラインのウォークスルーは対象外とし、設定合成(config layering)に絞る。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-T002(依存: P003,Q006。両方完了済み)を読んだ
- [x] `CONFIG_REFERENCE.md`のsection 17(Profile defaults)が`config/profiles/{mini,lite,full}.toml`の実際の内容と一致していることを確認した(差異なし)
- [x] `config/projects/<project>.toml`は現状実装されていない(`config/`配下は`default.toml`と`profiles/*.toml`のみ)ため、`README.md`/`CONFIG_REFERENCE.md`の読み込み順1〜5のうち実在するのは1・3・4・5であることを確認した。本タスクでは実在するファイルのみを例に使い、存在しない`config/projects/`を実行例に含めない
- [x] `src/wikiepwing/config.py`の`load_config`が`default_path`+`override_paths`を順にdeep-mergeすることを確認し、CLIの`--config`(複数指定可、後勝ち)がこれに対応することを確認した
- [x] TASK-T001(Build guide、依存: R006、未完了)と役割が重複しないよう、本タスクは設定合成の実行可能な例に限定し、全パイプラインの解説は含めない

## 変更予定ファイル

- `CONFIG_REFERENCE.md`(section追記: プロファイル別の設定合成・CLI呼び出し例)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run python -m wikiepwing.cli ingest --help
uv run python -m wikiepwing.cli build --help
make check
git diff --check
```

## 完了条件

- [x] `CONFIG_REFERENCE.md`にmini/lite/full各プロファイルの設定合成例(`--config config/profiles/<profile>.toml`)を含むセクションを追加した
- [x] 例で参照するCLIフラグ(`--config`, `--lock-path`など)が実際の`cli.py`の実装と一致することを確認した(`--help`出力と突き合わせ済み)
- [x] TASK-T001(全パイプラインガイド)と重複する内容(ingest/normalize/generateの詳細な逐次実行手順全体)を書かない
- [x] `make check`が成功する(ドキュメントのみの変更のためテスト内容は変わらないが、既存スイートが壊れていないことを確認した)

## 非対象

- 全パイプラインの実行手順(TASK-T001 Build guideの対象)
- Troubleshooting(TASK-T003)
- Viewer検証手順(TASK-T004)
- ライセンス/帰属表示ガイド(TASK-T005)

## 実施結果

`CONFIG_REFERENCE.md`に「20. プロファイル別の設定合成例」を追加し、`load_config`のdeep-merge挙動(`default_path`+`override_paths`、後勝ち)を踏まえて、mini/lite/full各プロファイルを`--config config/profiles/<profile>.toml`で`ingest`/`normalize`/`generate`または`build`に渡す実行可能な例、および複数`--config`(プロファイル+ローカルpaths override)を合成する例を示した。`config/projects/<project>.toml`が未実装であることをsection 1の注記として明示した。例で使用した`--config`/`--lock-path`/`--from-stage`等のフラグは`uv run python -m wikiepwing.cli {ingest,build,normalize,generate} --help`の実出力と突き合わせて確認した。TASK-T001(Build guide)と役割が重複しないよう、全パイプラインの逐次実行解説やimage処理・full build前ゲートには触れなかった。ドキュメントのみの変更のため、`make check`(1378 passed, 6 skipped)と`git diff --check`が成功することを確認した。
