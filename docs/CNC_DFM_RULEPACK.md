# CNC DFM Rule Pack（v1.0.0）

> 文件治理
> - 目的：描述 `contracts/g3/golden/cnc-dfm-rulepack.json`（G3-VAL-002 第一批 24 條 CNC DFM 規則）的內容、Condition 語彙、來源映射與治理限制。
> - 目前內容：24 條規則、72 個 positive/negative/boundary fixtures、8 個來源登錄（5 個已附 URL＋取用日期）、0 條 approved。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：G3-VAL-002 實作 commit（完工報告列出 SHA）

## 目的

以 rule schema（`schemas/v3/rule.schema.json`）與來源登錄（`config/rule-sources/sources.yaml`）為基礎，建立可執行、可追溯的 CNC DFM 第一批規則。每條規則自帶 positive／negative／boundary fixtures，由 `megis/rules/packs.py` 的 table-driven condition 語彙執行；release 治理閘門（`guard_release_evaluation`）在來源未核准前一律拒絕放行。

## 目前內容

Pack envelope（schema：`schemas/v3/rule-pack.schema.json`）：

- `schemaVersion: 1.0.0`、`workItem: G3-VAL-002`、`pack_id: cnc-dfm-rulepack@1.0.0`
- 規則數：24（藍圖 §11.2 要求 20–30）
- 所有規則 `status: in_review`、`reviewed_by: null`（來源未核准前不宣稱 approved）

### 規則清單

| 規則 ID | 內容 | 嚴重度 | 來源 |
|---|---|---|---|
| CNC_MIN_WALL_001 | 最小壁厚 ≥ 0.8 mm | error | SRC-CNC-DFM-001 |
| CNC_TAP_BLIND_001 | 盲孔攻牙：鑽孔深度 ≥ 螺紋長＋餘量 | error | SRC-CNC-DFM-001 |
| CNC_HOLE_ASPECT_001 | 孔深／孔徑 ≤ 3 | error | SRC-CNC-DFM-001 |
| CNC_INT_RADIUS_001 | 內角半徑 ≥ 1.2 × 刀具半徑 | error | SRC-CNC-DFM-001 |
| CNC_DEPTH_RATIO_001 | 口袋深度 ≤ 4 × 刀徑 | warning | SRC-CNC-DFM-001 |
| CNC_TOOL_ACCESS_001 | 刀具進入開口 ≥ 1.1 × 刀徑 | error | SRC-CNC-DFM-001 |
| CNC_SETUP_COUNT_001 | 加工面方向數 ≤ 3 | error | SRC-INTERNAL-ME-001 |
| CNC_MIN_HOLE_DIA_001 | 最小鑽孔直徑 ≥ 0.5 mm | error | SRC-CNC-DFM-001 |
| CNC_UNDERCUT_001 | 3 軸製程不得有 internal undercut | error | SRC-CNC-DFM-001 |
| CNC_EDGE_DIST_001 | 孔邊至零件邊 ≥ 2.0 mm | warning | SRC-CNC-DFM-001 |
| FAS_ENGAGE_AL_001 | 鋁材螺紋嚙合 ≥ 2.0 D（提議值） | error | SRC-INTERNAL-ME-001 |
| FAS_BOSS_WALL_001 | 螺紋孔剩餘壁厚 ≥ 1.5 mm（提議值） | error | SRC-INTERNAL-ME-001 |
| FAS_CBORE_DEPTH_001 | 沉頭深度 ≥ 1.1 × 螺絲頭高 | warning | SRC-ISO-4762 |
| FAS_CLEAR_HOLE_001 | M3 通孔 ≥ 3.4 mm（過渡值，未 assert ISO 273） | error | SRC-INTERNAL-ME-001 |
| FAS_SCREW_PROTRUDE_001 | 螺絲不得突出盲孔底部 | error | SRC-INTERNAL-ME-001 |
| PCB_EDGE_CLEAR_001 | PCB 邊至內壁 ≥ 1.5 mm | error | SRC-INTERNAL-ME-001 |
| PCB_STANDOFF_001 | Standoff 高度 ≥ 需求高度 | error | SRC-INTERNAL-ME-001 |
| PCB_TOP_CLEAR_001 | 頂面零件至上蓋 ≥ 2.0 mm | error | SRC-INTERNAL-ME-001 |
| PCB_STANDOFF_SPACING_001 | Standoff 間距 ≤ 100 mm | warning | SRC-INTERNAL-ME-001 |
| CON_USBC_OPEN_001 | USB-C 齊平開口 ≥ 1.05 × 外殼寬 | error | SRC-USB-TYPEC |
| CON_USBC_RECESS_001 | USB-C 內縮開口 ≥ 1.05 × overmold | error | SRC-USB-TYPEC |
| ASM_COVER_REMOVE_001 | 上蓋沿 +Z 移除路徑無干涉 | error | SRC-INTERNAL-ME-001 |
| ASM_COLLISION_001 | 任兩 component 無干涉 | error | SRC-INTERNAL-ME-001 |
| TOL_GENERAL_001 | 未標註尺寸於一般公差偏差類內 | info | SRC-ISO-2768-1 |

## Condition 語彙

`megis/rules/packs.py::condition_holds` 支援：`gte`、`lte`、`ratio_gte`、`ratio_lte`、`within`、`sum_gte`、`zero`、`info`。數值比較以 `EPSILON = 1e-9` 吸收浮點表示誤差；`_limit` 同時接受 `limit_mm`（帶單位）或 `limit`（無量綱）兩種鍵名。

## 治理限制

- 所有規則維持 `in_review`：來源登錄中 0 個 `approved`，因此規則不可被 release 評估（`MEGIS-RUL-001`）。
- 5 個公開來源已驗證 URL 可達並記錄 `accessed_at: 2026-09-22`；`SRC-ISO-273`、`SRC-ISO-261-262` 仍無可直接引用之公開頁面；`SRC-INTERNAL-ME-001` 的過渡數值（如 M3 通孔 3.4 mm）已標明 unapproved，不得宣稱 ISO 273 已查證。
- 未登錄來源遭 `load_rule_pack` 拒絕（`MEGIS-RUL-004`）。
- `TOL_GENERAL_001` 為 info 級，但以 `within` condition 提供正／負／邊界 fixtures，保持三類覆蓋。

## 驗證

```powershell
.venv/Scripts/python.exe -m pytest tests/test_g3_val_002.py
.venv/Scripts/python.exe scripts/verify_g3_val_002.py
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

## Owner

MEGIS Builder；使用者可否決來源決策與數值核准。

## 最後審查 commit

G3-VAL-002 實作 commit（完工報告列出 SHA）。
