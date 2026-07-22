# COMPATIBILITY.md

## 1. 目的

この文書は「Boookends 2023版相当」「EPWING互換」という表現を曖昧に使わないための互換性定義です。

このプロジェクトはBoookendsのバイナリ互換・内部実装互換・商標互換を目標にしません。

目標は次の3層です。

1. EPWING reader compatibility
2. Dictionary feature compatibility
3. User-experience compatibility

---

## 2. 互換性レベル

### Level 0 — Generated

- toolchainがファイルを出力しただけ
- readerでの検証なし

開発途中であり、配布不可。

### Level 1 — Structurally readable

- CATALOGSを解析可能
- subbookを列挙可能
- entryを検索可能
- ebzip後も読み取り可能

### Level 2 — Core dictionary

- 日本語見出し語
- redirect
-本文
- 内部リンク
- 複数ビューアのうち少なくとも2つで確認

Miniの最低目標。

### Level 3 — Rich content

- table
- infobox
- math
- image
- gaiji
- references

Liteの目標。

### Level 4 — Boookends-class functional compatibility

- Level 3
- richer aliases
- cross/condition-like search
- category/metadata access
- fixed query比較threshold
- Full/Lite/Mini相当プロファイル

Fullの目標。

---

## 3. 非互換として許容する項目

- 同一検索順位
- 同一ファイル分割
- 同一サブブック名
- 同一画像選択
- 同一table layout
- 同一gaiji code assignment
- 同一圧縮率
- 同一archive size
- 同一記事更新日
- 同一条件検索語抽出

差がある場合、ユーザー利用上の理由を説明できることが必要です。

---

## 4. 機能マトリクス

| Feature | Mini | Lite | Full | Reference comparison |
|---|---:|---:|---:|---|
| Title search | Required | Required | Required | automated |
| Redirect search | Required | Required | Required | automated |
| Normalized title | Required | Required | Required | automated |
| Internal links | Required | Required | Required | automated/manual |
| Headings | Required | Required | Required | manual sample |
| Lists | Required | Required | Required | golden |
| Tables | fallback | Required | Required | sample |
| Infobox | compact text | Required | Required | sample |
| Main image | No | Required | Required | sample |
| Multiple images | No | Optional | Required | metrics |
| Math text | Required | Required | Required | sample |
| Math bitmap | No | Required | Required | manual |
| Gaiji | Required fallback | Required | Required | manual |
| References | compact | Required | Required | sample |
| Alias search | limited | Required | Required | automated |
| Kana variants | Optional | Required | Required | automated |
| Category index | No | Optional | Required | automated |
| Cross-like search | No | limited | Required | automated/manual |
| Condition-like keyword | No | limited | Required | automated/manual |
| Attribution appendix | text source | images used | complete target | audit |

---

## 5. 固定query比較

### 5.1 Query classes

- exact common title
- Japanese title
- ASCII title
- redirect
- alternate spelling
- punctuation variant
- kana variant
- compound term
- missing term

### 5.2 Metrics

#### Result presence

正解対象記事が上位Nに含まれるか。

#### Overlap@N

```text
|new_top_N ∩ reference_top_N| / |reference_top_N|
```

検索設計が異なるため、完全一致を要求しません。

候補集合が同じでも順位が異なる場合を区別するため、同じ順位に同じ見出しが現れる割合
`rank_agreement_at_N` も記録します。これは合否を直接決める値ではなく、Bookends版との差を
観測する診断値です。

#### Target coverage

固定queryで期待記事を見つけられる割合。

### 5.3 Initial thresholds

v1.0 Full候補:

- exact title target coverage: 100%
- redirect target coverage: 99%以上
- fixed common queries target coverage: 95%以上
- missing query returns false exact hit: 0
- internal link target success in fixture: 100%

Overlap@Nは観測値として開始し、参照データ取得後にthresholdを決定します。

---

## 6. 記事比較

### 6.1 Article feature vector

```text
present
body_nonempty
heading_count
paragraph_count
list_count
table_count
infobox_field_count
reference_count
internal_link_count
image_count
gaiji_count
rendered_char_count
```

### 6.2 比較方法

本文全一致は要求しません。2023版と2026版では記事内容が異なるからです。

比較するもの:

- entryが存在する
- leadが読める
-主要sectionが存在する
- rich featureが欠落していない
- searchできる
- internal linkが動く

### 6.3 Golden article manual checklist

各記事について:

- [ ] title正常
- [ ] lead正常
- [ ] headings階層
- [ ] link選択可能
- [ ] table readable
- [ ] infobox compact
- [ ] math readable
- [ ] image readable
- [ ] rare chars recognizable
- [ ] references usable

---

## 7. Viewer compatibility

### 7.1 必須候補

- EBWin系
- EBPocket系
- Emacs Lookup/lookup.el系

### 7.2 記録項目

```text
viewer name
viewer version
OS/version
artifact profile
artifact hash
search mode
result
known issue
screenshot reference path (optional, not source-controlled if large)
verified date
```

### 7.3 Pass rule

Mini:

- 2 viewer familiesでtitle search/body/internal link

Lite:

- 2 viewer familiesでimage/gaiji/mathの主要sample

Full:

- 2 viewer families + Emacs Lookupでsearch matrix

---

## 8. Character compatibility

### 8.1 Pass categories

- standard text correctly visible
- gaiji visible
- safe textual fallback visible

### 8.2 Failure

- silent omission
- replacement characterだけで元code point不明
- article generation failure caused by one character
- gaiji mapping collision

### 8.3 Threshold

- silent omissions: 0
- unreported substitutions: 0
- fallback without code point: 0
- gaiji registry collisions: 0

---

## 9. Link compatibility

### Automated thresholds

- fixture internal links resolved: 100% excluding intentional broken links
- full build missing target rate: report and investigate; initial target <1%
- generated target entry missing: 0
- redirect alias points to existing entry: 100%

fragment navigationはviewer/backend能力により別評価にします。

---

## 10. Media compatibility

### Lite

- main/lead image available articlesのうち、policy選択された画像が正しく表示
- missing imageはarticle failureにしない

### Full

- selected image count and attribution record一致
- broken graphic reference 0

画像自体の選択は参照版と一致不要です。

---

## 11. Table compatibility

表の視覚一致ではなく情報保持を測定します。

simple table fixture:

- caption retention 100%
- header visible text retention 100%
- cell visible text retention 100%

wide/complex:

- readable fallback
- diagnostic
- silent row lossなし

設定上のtruncateは明示され、件数をレポートします。

---

## 12. Search feature naming

EPWING backendの実際の検索種別を確認するまで、UI/文書で次の表現を使います。

- title search
- redirect/alias search
- cross-like component search
- condition-like keyword search

Boookendsの用語と完全に同一の機能だと確認できた場合だけ、より具体的に表記します。

---

## 13. Compatibility report schema

```json
{
  "schema_version": 1,
  "reference": {
    "name": "local-reference-2023",
    "fingerprint": "sha256:..."
  },
  "candidate": {
    "profile": "full",
    "artifact_hash": "sha256:..."
  },
  "queries": {
    "total": 0,
    "target_coverage": 0.0,
    "redirect_coverage": 0.0,
    "overlap_at_10": 0.0,
    "rank_agreement_at_10": 0.0
  },
  "articles": {
    "sample_count": 0,
    "present": 0,
    "manual_pass": 0
  },
  "viewers": [],
  "thresholds": {},
  "status": "pass"
}
```

---

## 14. 公開表現

合格前:

- experimental EPWING builder
- Boookends 2023 reference-tested

Level 4合格後:

- Boookends-class functional feature set
- Boookends-compatible usage goals

避ける表現:

- official Boookends 2026
- Boookends successor（作者合意なし）
- perfect compatibility
- complete Wikipedia reproduction
