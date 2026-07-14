# CURRENT_TASK.md

## Task ID

TASK-H003

## 目的

`ARCHITECTURE.md` 12.5の最終行"外部サイトへのリンクはplain URLまたは注記として残します"を実装する。`TASK-H001`で内部linkでは無い(`parse_internal_url`が`None`を返した)と判定されたURLに対し、安全なスキーム(`http`/`https`)のみを`ExternalLinkInline`として許可し、それ以外のスキーム(`javascript:`/`data:`等)は情報を落とさずlabelのみを保持する形にfallbackさせる。`config/default.toml`の`[references] external_urls = "plain-text"`と整合するpolicy値のみ受け付ける。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-H003(依存: H001)を読んだ
- [x] `ARCHITECTURE.md` 12.5最終行を確認した。具体的なpolicy値の列挙は無く、`config/default.toml`の`[references] external_urls = "plain-text"`が唯一の既存configであることを確認した
- [x] `model/inline.py`の`ExternalLinkInline`(`label`/`url`)を確認した

## 変更予定ファイル

- `src/wikiepwing/links/external_policy.py`
- `tests/test_links_external_policy.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_links_external_policy.py
make check
git diff --check
```

## 完了条件

- [x] `apply_external_link_policy(label, url, policy) -> Inline`が`http`/`https`スキームのURLを`policy="plain-text"`の場合`ExternalLinkInline`として返す
- [x] `javascript:`/`data:`等の安全でないスキームは`ExternalLinkInline`を作らず、labelのみ(透過的なinline群)を返す(情報を失わない)
- [x] 未知の`policy`値は明示的なエラーとして拒否する(黙って無視しない)
- [x] スキームの無い相対URLやprotocol-relative URL(`//example.org/...`)の扱いを妥当に決定する
- [x] `make check`が成功する

## 非対象

- Redirect alias抽出(TASK-H004)
- References/footnote sectionでの実際のrendering(Epic L)

## 実施結果

- `src/wikiepwing/links/external_policy.py`に`apply_external_link_policy`/`ExternalLinkPolicyError`を実装した。
- `tests/test_links_external_policy.py`に8件のテストを追加。
- `uv run pytest tests/test_links_external_policy.py`: 8 passed。
- `make check`: format-check/ruff lint/mypy strict/pytest(標準スイート646件)すべて成功。
- `git diff --check`: 問題なし。
- `TASKS.md`(H003チェック)、`LOG.md`(新規エントリ)を更新した。
- `policy`は現状`"plain-text"`のみ受け付ける(configに他の値の定義が無いため)。
- 次タスク: TASK-H004 Redirect alias extraction。
