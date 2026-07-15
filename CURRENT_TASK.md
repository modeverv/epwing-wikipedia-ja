# CURRENT_TASK.md

## Task ID

TASK-N006

## 目的

`convert_block.py`/`paragraphs.py`のdocstringに明記されている「images and math, whose real HTML conversion is deferred to later epics (N/O)」を数式について解消する。TASK-N001(`RawMathNode`抽出)・TASK-N002(`canonicalize_math_source`によるcanonical化)で得た情報を、block-level(`display="block"`)は`MathBlock`、inline(それ以外)は新設する`MathInline`として、実際のDOM変換パイプライン(`convert_block`/`convert_inline_nodes`)に配線する。あわせてMini layout renderer(TASK-H007)がこれらを人間可読なテキスト行として出力できるようにする。TASK-N003(レンダラ)・TASK-N004(cache)・TASK-N005(raster)が返すバイト列自体をgraphicsとして埋め込む配線はEPIC O(`GraphicAsset`/`add_graphic`)の責務であり、`ImageBlock`が同様にまだplaceholderであることに合わせ、対象外とする。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-N006(依存: N004-N005,H007)を読んだ
- [x] `convert_block.py`/`paragraphs.py`の現状(mathが未配線で、block-level mathはinline_bufferに混入、inline mathはtransparent wrapperとして子要素を再帰するだけで実質破棄される)を確認した
- [x] `model/blocks.py`の`MathBlock`(既存placeholder: `source`/`source_format`)、`ARCHITECTURE.md` 11.3の`MathInline`(未実装)を確認した
- [x] `mini_layout.py`が`ImageBlock`同様、graphics実体の埋め込みは行わずtextのみをrenderしている現状の設計方針を確認した

## 変更予定ファイル

- `src/wikiepwing/model/inline.py`(`MathInline`追加)
- `src/wikiepwing/normalize/math_content.py`(新規: `resolve_math_source`共有ヘルパー)
- `src/wikiepwing/normalize/convert_block.py`(block-level math配線)
- `src/wikiepwing/normalize/paragraphs.py`(inline math配線)
- `src/wikiepwing/render/mini_layout.py`(`MathBlock`/`MathInline`のtext render)
- `tests/test_normalize_math_content.py`(新規)
- `tests/test_normalize_convert_block.py`または既存math関連test(必要に応じて新規/追記)
- `tests/test_normalize_paragraphs.py`(追記)
- `tests/test_render_mini_layout.py`(追記)
- `tests/test_model_inline.py`(存在すれば追記、なければ確認のみ)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_math_content.py tests/test_normalize_paragraphs.py tests/test_render_mini_layout.py -q
make check
git diff --check
```

## 完了条件

- [x] `<math display="block">`(tex sourceまたはtext alternativeのいずれかがある場合)が`convert_block`経由で`MathBlock`になる
- [x] `<math>`(display="block"以外、tex sourceまたはtext alternativeのいずれかがある場合)が`convert_inline_nodes`経由で`MathInline`になる
- [x] tex sourceもtext alternativeも取れない`<math>`は診断コード付きの`UnsupportedBlock`/`UnsupportedInline`にfallbackする(クラッシュしない)
- [x] Mini layout rendererが`MathBlock`を独立した行として、`MathInline`を段落内テキストの一部としてrenderする
- [x] `make check`が成功する

## 非対象

- 実際のgraphic byte(TASK-N003-N005のレンダリング結果)をRenderedEntry.graphics/EPWING graphicへ埋め込む配線(EPIC O)
- MathML以外の数式表現(画像埋め込み数式等)への対応

## 実施結果

- `model/inline.py`に`MathInline`(`MathBlock`と同型: `source`/`source_format`)を追加し、`Inline` unionとpayload/parseへ配線した。
- `normalize/math_content.py`(新規)に`resolve_math_source(RawMathNode) -> tuple[str, str] | None`を実装した。TASK-N002の`compute_math_cache_key`と同じ優先順位(tex source優先、なければtext alternative、canonicalize後に空ならNone)で`(source, source_format)`を返す。
- `convert_block.py`: `is_math_node`を`_is_block_level`に追加(`display="block"`のときのみtrue)し、`convert_block`の dispatch に `_convert_math_block`(解決できれば`MathBlock`、できなければ`MATH_NO_SOURCE`診断付き`UnsupportedBlock`)を追加した。
- `paragraphs.py`: `convert_inline_nodes`の内部dispatchに`<math>`を追加し、`MathInline`または`MATH_NO_SOURCE`診断コード付き`UnsupportedInline`を返す`_convert_math_inline`を実装した。
- `whitespace.py`: `MathInline`を`_normalize_inline`の既存exhaustiveディスパッチに追加した(`MathBlock`同様、verbatim保持で`AssertionError`を回避)。
- `mini_layout.py`: `MathBlock`を独立行として、`MathInline`を段落内テキストの一部として(`_inline_text`)render するようにした。
- 新規テスト: `tests/test_normalize_math_content.py`(6件)、`tests/test_normalize_convert_block.py`/`tests/test_normalize_paragraphs.py`/`tests/test_render_mini_layout.py`/`tests/test_model_inline.py`への追記(計16件)。
- `make check`(format-check/lint/mypy/pytest 1083件)と`git diff --check`が成功した。
- 実際のgraphic byte(N003-N005)埋め込みはEPIC O待ちのため対象外のまま(`ImageBlock`と同じ既存方針)。
