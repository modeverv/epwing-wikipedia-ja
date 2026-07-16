# CURRENT_TASK.md

## Task ID

TASK-S002

## 目的

`ARCHITECTURE.md` 26.1(「logical hash: entry/index/graphicのcanonical stream hash」)を実装する。ZIP timestampやfilesystem orderingに左右される物理SHA-256とは別に、entries.jsonl(TASK-H010)・gaiji build files(TASK-M007)・graphics build files(TASK-O011)という「canonical stream」の集合を、順序に依存しない安定した方法でhashする`compute_stream_set_hash`(汎用primitive)と、実際のbuild成果物ディレクトリから呼び出す`compute_logical_build_hash`を実装する。

## 事前条件

- [x] `AGENTS.md`を読んだ
- [x] `MEMORY.md`を読んだ
- [x] `LOG.md`末尾を読んだ
- [x] `CURRENT_TASK.md`を確認した
- [x] `TASKS.md`のTASK-S002(依存: H010,M007,O011)を読んだ
- [x] `ARCHITECTURE.md` 26.1(物理SHA-256とlogical hashの違い、logical hashはcanonical stream単位)を再確認した
- [x] EB indexの実バイナリ構築はDocker内`fpwmake`が担い、この段階のPythonコードは直接生成物を持たないため、本タスクでは「entry(entries.jsonl)」「gaiji build files」「graphics build files」の3つのcanonical streamを対象とし、「index」自体は対象外とする(スコープを誠実に限定する)方針にした

## 変更予定ファイル

- `src/wikiepwing/build_logical_hash.py`(新規: `compute_stream_set_hash`, `collect_build_streams`, `compute_logical_build_hash`)。`model/logical_hash.py`(TASK-F008、Article単位のhash)とは別の関心事であり、命名衝突を避けるためモジュール名・関数名を明確に分けた
- `tests/test_logical_hash.py`(新規)
- `TASKS.md`
- `LOG.md`
- `CURRENT_TASK.md`

## 実行予定コマンド

```bash
uv run pytest tests/test_logical_hash.py
make check
git diff --check
```

## 完了条件

- [x] `compute_stream_set_hash`が`(name, content)`のペアの集合から、入力順序に依存しない(name昇順でsortしてからhashする)安定したsha256 hex digestを返す
- [x] 異なるnameの組み合わせ(例: `"ab"`+`"c"` vs `"a"`+`"bc"`)が異なるhashになる(length-prefixed framingで曖昧さを排除する)
- [x] `collect_build_streams`がentries.jsonl・gaiji directory・graphics directory(いずれもoptional)から`(name, content)`ペアをファイル名昇順で収集する
- [x] `compute_logical_build_hash`が上記を組み合わせて1つのhex digestを返す
- [x] `make check`が成功する

## 非対象

- EB indexバイナリ自体のcanonical hash(Docker内`fpwmake`が生成するバイナリのため対象外)
- 実際のbuild pipelineへの統合配線(TASK-S001と同様、構築・計算機能のみ)

## 実施結果

- `src/wikiepwing/build_logical_hash.py`(新規)に`compute_stream_set_hash`(name昇順sort+length-prefixed framingで曖昧さを排除)・`collect_build_streams`(entries.jsonl+gaiji/graphics directoryを収集)・`compute_logical_build_hash`を実装した。
- テスト作成中、`collect_build_streams`内の`(prefix, directory)`のループ変数順序を取り違えるバグ(`"gaiji"`という文字列自体を`Path`として扱おうとして`AttributeError`)を実際にテストで検出・修正した。
- `tests/test_build_logical_hash.py`(新規11件)で、順序非依存性・決定性・内容差異での変化・境界曖昧さの排除・空入力・entries.jsonl/gaiji/graphics収集・再帰・欠落ディレクトリの無視を確認した。
- `make check`(format-check/lint/mypy/pytest 1335件、ImageMagick依存6件はローカル環境でskip)と`git diff --check`が成功した。
- EB indexバイナリ自体(Docker内`fpwmake`が生成)は対象外。
