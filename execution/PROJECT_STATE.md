# MEGIS Project State

- Current gate: `G2 — 治具幾何垂直切片`
- Current work item: `G2-CAD-004 — 輸出與重新載入 artifacts`
- Last green commit: `c6e39020852f2c5fca6d49d12ddb7798793c9c37`
- Control-plane schema: `1.1.0`
- Updated at: `2026-09-21T00:00:00+08:00`

## Active gate: G2

G1 已 closed（`SO-0002`，2026-09-21），V3C 追溯閉合。G2 現在為 active gate。

## G1 閉合摘要

- G1-REV-001：自我審查 passed（54 tests），報告 `execution/reviews/2026-09-21-G1-REV-001-review.md`
- G1-ACC-001：`SO-0002`（E4 gate_acceptance）
- V3C-REV-001 / V3C-ACC-001：V3C 追溯閉合

## G2 work items

| ID | Status | Evidence |
|---|---|---|
| G2-CAD-001 | done | megis/geometry/contracts.py, tests/test_g2_geometry_contract.py |
| G2-CAD-002 | done | megis/adapters/cadquery_backend.py, scripts/verify_fixture_base.py |
| G2-CAD-003 | done | megis/adapters/cadquery_backend.py, tests/test_g2_fixture_assembly.py |
| G2-CAD-004 | in_progress | 本段執行：輸出檔可重新載入且幾何不為空（STEP/STL/DXF artifacts + reload 驗證） |
| G2-NEG-001 | planned | Boundary 與 negative geometry corpus（依賴 G2-CAD-004） |
| G2-REV-001 | planned | G2 自我審查 |
| G2-ACC-001 | planned | G2 acceptance（SO-0003） |

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- UI-0 合成展示資料不視為工程資料。
