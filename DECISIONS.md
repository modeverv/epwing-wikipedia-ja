# DECISIONS.md

## ADRの書き方

各設計判断は次を持ちます。

```text
Status: Proposed / Accepted / Superseded / Rejected
Date
Context
Decision
Consequences
Alternatives
```

---

## ADR-001 — 通常Wikimedia Enterprise Snapshot HTMLを標準入力にする

**Status:** Accepted  
**Date:** 2026-07-13

### Context

現代WikipediaのWikitextはTemplate/Lua/extensionに強く依存し、古い`wikipedia-fpw`相当のparserでは高機能表示を安定して再現しにくい。通常Snapshotには解析向けHTMLとWikitextが含まれる。

### Decision

`article_body.html`を標準本文入力とする。Wikitext/XMLは欠落時fallback・検証・追加metadata用途とする。

### Consequences

- Template engine自作を避けられる
- API accountとsource acquisitionが必要
- HTML DOM変更への追従が必要
- sourceをローカル固定し再現性を確保する

### Alternatives

- Wikitext-only: rejected as standard
- live REST API per article: rejected due network/reproducibility
- local MediaWiki/Parsoid: future fallback only

---

## ADR-002 — Structured Contentsをjawiki必須経路にしない

**Status:** Accepted  
**Date:** 2026-07-13

### Context

2026年7月時点のStructured Contents Snapshot対象一覧にjawikiがない。

### Decision

通常HTML Snapshotからtable/infobox/list/image referenceを自前でsemantic modelへ変換する。

### Consequences

- jawiki対応を現在実装できる
- DOM parser品質が重要
- 将来adapter追加可能

---

## ADR-003 — ネットワーク取得を独立stageにする

**Status:** Accepted

### Decision

acquire完了後は全変換stageをofflineで動作させる。

### Consequences

- source.lock必須
- debug/rebuildが安定
- disk使用量増加

---

## ADR-004 — Semantic intermediate modelを導入する

**Status:** Accepted

### Decision

HTMLからFreePWING sourceへ直接変換しない。Article/Block/Inline/Media/Diagnostic modelを経由する。

### Consequences

- test可能
- alternative backend可能
- 初期実装量増加

---

## ADR-005 — SQLiteと明示SQLを使う

**Status:** Accepted

### Context

巨大処理でserver DBを運用したくない。ユーザーはORMよりSQL直書きを好む。

### Decision

stage別SQLite、明示migration SQL、ORMなし。

### Consequences

- artifactとして持ち運び可能
- schema/queryを明示できる
- writer concurrency設計が必要

---

## ADR-006 — Stage成果物を原則不変にする

**Status:** Accepted

### Decision

raw/model/rendered/index DBを分け、後続stageが前stage DBを更新しない。

### Consequences

- resume/debug容易
- disk消費増加
- cleanup機能が必要

---

## ADR-007 — FreePWINGをadapterへ隔離する

**Status:** Accepted

### Decision

EPWING toolchain固有処理は`src/wikiepwing/epwing/`とtoolchain imageに限定する。

### Consequences

- parser/rendererがlegacy syntaxに汚染されない
- backend interface設計が必要

---

## ADR-008 — 内部UTF-8、出力時文字分類

**Status:** Accepted

### Decision

内部modelはUnicodeを保持し、backend直前で標準文字、safe substitution、gaiji、codepoint fallbackへ分類する。

### Consequences

- 早期data loss防止
- gaiji registryが必要
- output stageが複雑

---

## ADR-009 — Docker named volumeへ中間I/Oを置く

**Status:** Accepted

### Context

macOS Docker Desktop bind mountは大量I/Oに不利。

### Decision

source/work/cacheをnamed volume、output/report/logのみ必要に応じbind mount。

### Consequences

- performance改善
- Docker volumeのbackup/cleanup commandが必要

---

## ADR-010 — profilesを設定駆動にする

**Status:** Accepted

### Decision

Mini/Lite/Fullは同じpipeline・rendererを使用し、policy/configで差を出す。

### Consequences

- divergence防止
- profile validation必要

---

## ADR-011 — Boookends互換はfunctional measurement

**Status:** Accepted

### Decision

binary/brand一致ではなく、fixed queries、article features、viewer matrixで評価する。

### Consequences

- 比較器とmanual checklistが必要
- 絶対的「完全互換」を主張しない

---

## ADR-012 — 画像をnormalization中にdownloadしない

**Status:** Accepted

### Decision

normalizeはMediaReferenceだけを作り、media stageが選択・取得・変換する。

### Consequences

- network separation維持
- image policy変更でnormalize再実行不要

---

## ADR-013 — 個人用と公開配布用policyを分ける

**Status:** Accepted

### Decision

`distribution.mode=personal|public`を持ち、publicでは画像license/attributionを厳格化する。

### Consequences

- 個人buildを先に成立可能
- public release前のauditが必要

---

## ADR-014 — Full text indexを初期実装しない

**Status:** Accepted

### Context

EPWING内の巨大全文索引は容量・生成時間・検索品質に影響し、弱いモデルの実装範囲を超えやすい。

### Decision

title/redirect/alias/heading/category/infobox/cross-like termを優先し、本文全単語索引は将来機能。

---

## ADR-015 — Full buildはGate後にのみ実行

**Status:** Accepted

### Decision

3、10、100、10,000記事の段階Gateを通過するまで全件を禁止する。

### Consequences

- 問題縮小が容易
- 初回成果まで段階を要するが全体失敗を避けられる
