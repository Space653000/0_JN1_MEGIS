# MEGIS Project State

- Current gate: `G3 — 規則與驗證`
- Current work item: `G3-SRC-001 — 規則來源登錄與核對流程`
- Last green commit: `162d09d95df517c5123e4f7916ff19a0e2cfb087`
- Control-plane schema: `1.1.0`
- Updated at: `2026-09-21T20:00:00+08:00`

## Active gate: G3

G2 已 closed（`SO-0003`，2026-09-21）。G3 — 規則與驗證 現在為 active gate。

G3-RUL-001 已閉合（2026-09-21）：rule schema（`schemas/v3/rule.schema.json`）、waiver schema（`schemas/v3/waiver.schema.json`）、生命週期狀態機與 waiver 到期／不可豁免邏輯（`megis/rules/`）、golden corpus（`contracts/g3/golden/rule-governance.json`）；14 tests + `verify_g3_rul_001.py` 18/18 checks 全綠，新增 `MEGIS-RUL-002／003`。

## G1 閉合摘要

- G1-REV-001：自我審查 passed（54 tests），報告 `execution/reviews/2026-09-21-G1-REV-001-review.md`
- G1-ACC-001：`SO-0002`（E4 gate_acceptance）
- V3C-REV-001 / V3C-ACC-001：V3C 追溯閉合
- G2-NEG-001：boundary 10/10、negative 14/14、silent success 0、越界不 clamp（MEGIS-ENV-001）
- G2-REV-001：乾淨 checkout 92 tests + 4 個 G2 驗證腳本全綠，報告 `execution/reviews/2026-09-21-G2-REV-001-review.md`
- G2-ACC-001：`SO-0003`（E4 gate_acceptance，2026-09-21）

## G2 work items

| ID | Status | Evidence |
|---|---|---|
| G2-CAD-001 | done | megis/geometry/contracts.py, tests/test_g2_geometry_contract.py |
| G2-CAD-002 | done | megis/adapters/cadquery_backend.py, scripts/verify_fixture_base.py |
| G2-CAD-003 | done | megis/adapters/cadquery_backend.py, tests/test_g2_fixture_assembly.py |
| G2-CAD-004 | done | megis/adapters/cadquery_backend.py、gltf.py、scripts/verify_g2_cad_004.py；33 項 reload/cross-check 全數 passed |
| G2-NEG-001 | done | contracts/g2/golden/geometry-corpus.json、scripts/verify_g2_neg_001.py；boundary 10/10 合格、negative 14/14 回傳預期錯誤碼、silent success 0、越界不 clamp（MEGIS-ENV-001） |
| G2-REV-001 | done | execution/reviews/2026-09-21-G2-REV-001-review.md、artifacts/g2-rev-001/verification.json；乾淨 checkout 92 tests + 4 個 G2 驗證腳本全綠 |
| G2-ACC-001 | done | execution/signoffs/SO-0003.yaml、artifacts/g2-acc-001/verification.json；G2 gate accepted（E4） |

## G3 work items

| ID | Status | Evidence |
|---|---|---|
| G3-RUL-001 | done | schemas/v3/rule.schema.json、schemas/v3/waiver.schema.json、megis/rules/、contracts/g3/golden/rule-governance.json；14 tests + verify_g3_rul_001.py 18/18 checks |
| G3-VAL-001 | planned | geometry / collision / clearance validators |
| G3-VAL-002 | planned | CNC DFM rule pack（20–30 條規則） |
| G3-SRC-001 | in_progress | 規則來源登錄與核對流程（`docs/RULE_SOURCES.md`，見 `execution/AGENT_CLAIM.json`） |
| G3-MAT-001 | planned | Maturity evaluator（§1.4 table-driven tests） |
| G3-BEN-001 | planned | benchmark metrics（defect ≥ 30、clean ≥ 10、precision/recall/FP/Wilson CI） |
| G3-REV-001 | planned | G3 自我審查（全新 session） |
| G3-ACC-001 | planned | G3 acceptance 決策紀錄 |

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- UI-0 合成展示資料不視為工程資料。
