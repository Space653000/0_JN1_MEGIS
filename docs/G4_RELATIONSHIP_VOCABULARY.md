# Relationship Vocabulary（G4-GRF-001）

> 文件治理
> - 目的：描述 `megis.relationship` 如何實作藍圖 §4.16 Relationship vocabulary（八型別封閉集合）與每型別語意／反例。
> - 目前內容：八型別詞彙、每型別語意與必要驗證、參數不變量、golden corpus 與驗證證據。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：G4-GRF-001 實作 commit（完工報告列出 SHA）

## 目的

Relationship 描述模組或介面之間的工程關係。`megis.relationship` 提供 §4.16 的封閉八型別詞彙，每個型別都有定義好的語意、要滿足的「必要驗證」條件與正反例測試。型別是封閉集合：新增型別需 schema MINOR 版本並增加語意測試。此模型也是 G4-MOD-002（PCB／USB-C／M3 composition）的組合基礎。

## 八型別閉集合（藍圖 §4.16）

| 類型 | 語意 | 必要驗證 |
|---|---|---|
| `contains` | A 的內腔容納 B | B 的 clearance envelope 完全在 A 內腔內 |
| `mounts_to` | B 以 fastener 固定於 A | 孔位對齊、boss 存在、嚙合長度 |
| `fastens` | fastener 連接 A 與 B | 螺絲長度、通孔、內螺紋 |
| `opens_through` | 介面 B 穿過 A 的壁面 | 開口存在、開口 ≥ 介面 envelope + 間隙 |
| `clears` | A 與 B 最小距離 ≥ d | 距離計算 |
| `aligns` | A 與 B 在指定軸對齊 | 軸向偏差 ≤ 容差 |
| `covers` | A 覆蓋 B 的開口 | 配合面與干涉檢查 |
| `removable_along` | A 可沿方向移除 | 掃掠干涉檢查 |

## 文件形狀與語意驗證

`schemas/v3/relationship.schema.json` 規定每個 Relationship 最少有 `schemaVersion`、`relationship_id`、`type`、`source`、`target`、`parameters`、`provenance`；型別由閉集合 enum 決定，每個型別再透過 `allOf` 分支要求各自的必要參數。

`megis/relationship/schema.py` 的 `validate_relationship` 合併 schema 與語意檢查，回傳確定的 JSON Pointer 錯誤清單：

- 參數分三類並各自强制不變量：參考參數（`envelope_ref`／`cavity_ref`／`boss_ref` 等）必須非空字串；長度／容差參數（`clearance_gap_mm`／`minimum_distance_mm`／`tolerance_mm` 等）必須為非負數字且工程值嚴格為正；文字參數（`axis`／`direction`）必須非空。
- Relationship 不得把某實體關聯到自己（`source == target` 被拒絕）。
- 每個參數項與 Relationship 本身都必須攜帶 `provenance`。

## Golden corpus 與驗證

`contracts/g4/golden/relationship-corpus.json` 提供 20 個 table-driven cases（8 positive、12 negative）：八型別各一個正例與一個各型別反例，另含未知型別、自關聯、缺頂層 provenance、參數缺 provenance 的通則反例。`scripts/verify_g4_grf_001.py` 全數驗證後寫入 `artifacts/g4-grf-001/verification.json`（E3），不產生工程製品。

```powershell
.venv/Scripts/python.exe -m pytest tests/test_g4_grf_001.py
.venv/Scripts/python.exe scripts/verify_g4_grf_001.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

## Owner

MEGIS Builder；使用者可否決某個 relationship 型別的語意或必要驗證要求。
