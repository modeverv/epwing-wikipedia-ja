# CURRENT_TASK.md

## Task ID

TASK-N001

## 目的

`ARCHITECTURE.md` 15.7(数式: 1.テキスト代替を保存 2.TeX sourceがあればcache keyに使用...)の最初の段階として、記事HTML中の数式ノード(`<math>`要素、MathML)を検出し、TeX source・テキスト代替・block/inline区分を抽出する。MediaWikiのMath拡張は`<math>`要素にMathML標準の`alttext`属性(TeX風の代替テキスト)と`display`属性(`"block"`/`"inline"`)を付与し、`<annotation encoding="application/x-tex">`子要素に元のTeX sourceを保持するという安定した標準に基づく(MediaWiki固有のwrapper class名の詳細ではなく、MathML仕様自体の属性に依拠することで、確認できないHTML実例への依存を避ける)。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-N001(依存: G001)を読んだ
- [x] `ARCHITECTURE.md` 15.7(数式の優先順位)を再確認した
- [x] `model/blocks.py`の`MathBlock`(`source`/`source_format`)を確認した(HTML変換はTASK-N002以降)
- [x] MathML標準の`<math alttext="..." display="block|inline">`属性と`<annotation encoding="application/x-tex">`子要素という安定した規約を判断根拠として採用した(MediaWiki固有のwrapper HTML構造の詳細確認はできないため)

## 変更予定ファイル

- `src/wikiepwing/normalize/math_node.py`(新規: `RawMathNode`, `is_math_node()`, `parse_math_node()`)
- `tests/test_normalize_math_node.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_normalize_math_node.py
make check
git diff --check
```

## 完了条件

- [x] `is_math_node(node)`が`<math>`要素を検出する
- [x] `parse_math_node(node)`が、`<annotation encoding="application/x-tex">`からTeX sourceを、`alttext`属性からテキスト代替を、`display`属性からblock/inline区分を抽出する
- [x] TeX source・alttextが無い場合はNoneを返す(データを失わない、Noneのまま保持)
- [x] `make check`が成功する

## 非対象

- 実際の`MathBlock`/`MathInline`モデルへの変換(TASK-N002以降)
- レンダリング・cache・fallback(TASK-N003-N007)

## 実施結果

- `src/wikiepwing/normalize/math_node.py`に`RawMathNode`・`is_math_node()`・`parse_math_node()`を実装した。MathML標準の`alttext`/`display`属性と`<annotation encoding="application/x-tex">`子要素(ネストの深さに依らず再帰探索)からTeX source・テキスト代替・block/inline区分を抽出する。
- `tests/test_normalize_math_node.py`(新規11件)で、math要素の検出・非検出・TeX source抽出・alttext抽出・display=block/inline/欠落の判定・TeX source欠落時のNone・alttext欠落時のNone・異なるencodingのannotationの無視・深くネストしたannotationの探索・非math要素へのエラーを確認した。
- `make check`(format-check/lint/mypy/pytest 1033件)と`git diff --check`が成功した。
