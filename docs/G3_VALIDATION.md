# 驗證結果與 Validators（G3-VAL-001）

> 文件治理
> - 目的：定義 MEGIS 驗證結果欄位、geometry／collision／clearance validators 語意與已知 pass/fail 案例的來源。
> - 目前內容：G3-VAL-001 Validation Result schema、kernel-neutral AABB validators 與 golden corpus（2026-09-21）。
> - Owner：MEGIS Builder；使用者保有否決權
> - 最後審查 commit：`eac514c7339a2f280ccd2f12078bfb5fcc247263`

## 目的

G3-VAL-001 建立可追溯的驗證層：元件以軸對齊邊界盒（AABB）表示，驗證器輸出符合 `schemas/v3/validation-result.schema.json` 的結果，讓 layout collision／clearance 與規則後續可合併。驗證器刻意與 CAD kernel 無關，可接受 CAD 匯出的 AABB 而不依賴 CAD 工具。

## 目前內容

- Validation Result schema：`schemas/v3/validation-result.schema.json`。每個失敗檢查帶穩定 `MEGIS-VAL-*` 錯誤碼、`severity`、`entity_refs`、`user_message_zh_tw` 與 `engineer_detail`，結果可機器路由也可人工閱讀。
- Validators：`megis/validation/geometry.py`（`BoundingBox`、`ComponentBox`、`ClearanceRequirement`、`DesignValidationInput`、`validate_design`）。
- 語意：
  - geometry：盒體必須有限、非反轉且有正體積；違反回傳 `MEGIS-VAL-003`。任何元件幾何無效時，placement 檢查整體略過。
  - collision：兩盒體於三軸皆有正重疊量才算碰撞；面接觸（間隙 0）不算碰撞。違反回傳 `MEGIS-VAL-001`。
  - clearance：軸向間隙取最大正分離；全軸重疊時取最小重疊深度之負值。`gap >= min_gap_mm` 即通過（邊界含入）；違反回傳 `MEGIS-VAL-002`，可附 `rule_id`。
- Golden corpus：`contracts/g3/golden/validation-corpus.json`（15 個已知 pass/fail cases，含 fixture assembly pass、碰撞、嵌套、餘隙邊界與懸空參照）。
- 錯誤碼：`MEGIS-VAL-001`（碰撞或佈局衝突）、`MEGIS-VAL-002`（餘隙不足）、`MEGIS-VAL-003`（驗證輸入幾何無效）。

## Owner

MEGIS Builder；使用者保有否決權。

## 最後審查 commit

`eac514c7339a2f280ccd2f12078bfb5fcc247263`
