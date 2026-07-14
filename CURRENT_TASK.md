# CURRENT_TASK.md

## Task ID

TASK-F002

## 目的

`ARCHITECTURE.md` 11.3/11.4のInline unionのうち、`PLAN.md` Phase 6が「最初に対応する」と定めた種別(text、bold/italic、internal/external link、code、line break)を実装し、それ以外は`UnsupportedInline`へ落とすJSON codecを持つ。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-F002を読んだ(依存: F001完了済み。詳細実装列は無く`ARCHITECTURE.md`/`PLAN.md`が正本)
- [x] `ARCHITECTURE.md` 11.3(Inline union)・11.4(InternalLinkInline)を確認した
- [x] `DATA_CONTRACTS.md` 6節のInline JSON例(text/internal_link)を確認した
- [x] `PLAN.md` Phase 6「初期対応」(headings、paragraphs、bold/italic、internal/external links、...)を確認し、ruby/math inlineは対象外(将来epicへ委譲)とした
- [x] TASK-F001の`model/diagnostics.py`の実装スタイル(frozen dataclass、`__post_init__`検証、`payload`/`parse_*`往復)を踏襲する

## 変更予定ファイル

- `src/wikiepwing/model/inline.py`
- `tests/test_model_inline.py`
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_model_inline.py
make check
git diff --check
```

## 完了条件

- [x] `TextInline`/`StrongInline`/`EmphasisInline`/`CodeInline`/`LineBreakInline`/`InternalLinkInline`/`ExternalLinkInline`/`UnsupportedInline`を実装する
- [x] `InternalLinkInline`が`ARCHITECTURE.md` 11.4のfield(label/target_title/target_normalized_title/target_fragment/target_page_id/resolution)を持つ
- [x] `payload()`/`parse_inline()`が全種別で相互に往復可能である(strong/emphasis/linkのlabelなどnested inlineを含む)
- [x] 未知の`type`をcodec errorとして拒否する(`DATA_CONTRACTS.md`の規定通り)
- [x] `resolution`が`resolved`/`missing`/`externalized`以外を拒否する
- [x] `make check`が成功する

## 非対象

- Block model(TASK-F003)
- HTMLからInlineへの実際の変換(Epic G)
- math/ruby inline(将来epic)

## 実施結果

- `src/wikiepwing/model/inline.py`に`TextInline`/`StrongInline`/`EmphasisInline`/`CodeInline`/`LineBreakInline`/`InternalLinkInline`/`ExternalLinkInline`/`UnsupportedInline`と`Inline` union型、`inline_payload`/`parse_inline`を実装した。
- `InternalLinkInline`は`ARCHITECTURE.md` 11.4通りのfield(label/target_title/target_normalized_title/target_fragment/target_page_id/resolution)を持ち、`resolution`は`resolved`/`missing`/`externalized`以外を拒否する。
- 全種別で`payload()`/`parse_inline()`が相互に往復可能であることを、strong内emphasis等のnestingを含め確認した。
- 未知の`type`は`InlineError`として拒否した(`DATA_CONTRACTS.md`の規定通り)。
- `tests/test_model_inline.py`に18件のテストを追加した。
- format-check、ruff lint、mypy strict、標準スイート399件、`git diff --check`が成功した。

**判断・注意点**

- `PLAN.md` Phase 6の初期対応範囲に無いmath/ruby inlineは対象外とし、将来該当epicで追加する(それまでは`UnsupportedInline`が受け皿になる)。
