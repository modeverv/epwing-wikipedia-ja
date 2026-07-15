# CURRENT_TASK.md

## Task ID

TASK-P001

## 目的

`ARCHITECTURE.md` 21(Mini/Lite/Full profile定義)・`CONFIG_REFERENCE.md` 17(profile defaultsの正確なTOML内容)を実装する。`config/profiles/mini.toml`/`lite.toml`/`full.toml`を`CONFIG_REFERENCE.md`記載の内容通りに作成し、`AppConfig.profile`の値を`"mini"`/`"lite"`/`"full"`の3つに制限するschema検証を追加する。`CONFIG_REFERENCE.md` 1の読み込み順(1. default 2. project 3. profile 4. explicit `--config` 5. CLI override)が示す「layer 3」の自動選択・読み込みは、既存の`load_config`呼び出し全箇所(ingest/normalize/generate/image-fetch等)の実効設定値を一括で変える広範囲な挙動変更になるため、本タスクでは対象外とする(TASK-P004「Profile-driven renderer」がプロファイル駆動の実際の適用を担う設計と判断)。既存の`--config`オプションで`config/profiles/<profile>.toml`を明示的に渡すことで、今日すでにprofile overlayとして機能する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-P001(依存: A003)を読んだ
- [x] `ARCHITECTURE.md` 21(Mini/Lite/Full)・`CONFIG_REFERENCE.md` 17(mini.toml/lite.toml/full.tomlの正確な内容)を再確認した
- [x] `config.py`の`load_config`が現在`default_path`+明示的な`override_paths`のみをマージし、`config/profiles/<profile>.toml`の自動選択は行っていないことを確認した
- [x] `config/default.toml`の現在の`[search]`(`max_terms_per_article=64`等)が`lite.toml`の値(`max_terms_per_article=32`)と異なることを確認し、自動読み込みを実装すると既存の実効設定・テスト前提が広範囲に変わってしまうため、自動選択の配線はTASK-P004へ委ねる判断をした

## 変更予定ファイル

- `config/profiles/mini.toml`(新規)
- `config/profiles/lite.toml`(新規)
- `config/profiles/full.toml`(新規)
- `src/wikiepwing/config.py`(`profile`値のvalidation追加)
- `tests/test_config.py`(追記)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_config.py
make check
git diff --check
```

## 完了条件

- [x] `config/profiles/mini.toml`/`lite.toml`/`full.toml`が`CONFIG_REFERENCE.md` 17と一致する内容で存在する
- [x] 各profile fileを`load_config(DEFAULT_CONFIG, [profile_path])`のように明示的overrideとして渡すと、`ConfigurationError`を送出せず正しくマージされる
- [x] `profile`が`"mini"`/`"lite"`/`"full"`以外の値の場合は`ConfigurationError`を送出する
- [x] `make check`が成功する

## 非対象

- `config/profiles/<profile>.toml`の自動選択・読み込み配線(`load_config`の呼び出し全箇所の実効設定を変える広範囲な変更、TASK-P004の対象と判断)
- `config/projects/<project>.toml`(layer 2、別タスクの対象)

## 実施結果

- `config/profiles/mini.toml`/`lite.toml`/`full.toml`を`CONFIG_REFERENCE.md` 17の内容通りに作成した。
- `src/wikiepwing/config.py`に`_PROFILES = ("mini", "lite", "full")`を追加し、`load_config`が`profile`値をこの3つに制限するよう検証を追加した。
- `tests/test_config.py`に、各profile fileをoverrideとして読み込めること・各profileの主要な値(images.enabled、search.max_terms_per_article等)・不正なprofile値の拒否を確認する13件のテストを追加した。
- `make check`(format-check/lint/mypy/pytest 1230件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- `config/profiles/<profile>.toml`の自動選択・読み込み配線(既存の`load_config`呼び出し全箇所の実効設定を一括で変える広範囲な挙動変更になるため)、`config/projects/<project>.toml`(layer 2)は対象外とした。
