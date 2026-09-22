# MEGIS Project State

- Current gate: `G3 — 規則與驗證`
- Current work item: `G3-ACC-001 — G3 acceptance 決策紀錄`
- Last green commit: `ccf7b8129782303b4e09eaa2636c7be25d0aa90f`
- Control-plane schema: `1.1.0`
- Updated at: `2026-09-22T14:00:00+08:00`

## Active gate: G3

G2 已 closed（`SO-0003`，2026-09-21）。G3 — 規則與驗證 現在為 active gate。

G3-RUL-001 已閉合（2026-09-21）：rule schema（`schemas/v3/rule.schema.json`）、waiver schema（`schemas/v3/waiver.schema.json`）、生命週期狀態機與 waiver 到期／不可豁免邏輯（`megis/rules/`）、golden corpus（`contracts/g3/golden/rule-governance.json`）；14 tests + `verify_g3_rul_001.py` 18/18 checks 全綠，新增 `MEGIS-RUL-002／003`。

G3-SRC-001 已閉合（2026-09-21）：規則來源登錄與核對流程（`schemas/v3/rule-source.schema.json`、`config/rule-sources/sources.yaml`、`megis/rules/sources.py`）；8 個來源登錄、0 approved（保守狀態），review_due 過期自動降為 `needs_review`、draft 規則不可支撐核准；13 tests + `verify_g3_src_001.py` 18/18 checks 全綠，新增 `MEGIS-RUL-004`。

G3-VAL-001 已閉合（2026-09-21）：geometry / collision / clearance validators（`schemas/v3/validation-result.schema.json`、`megis/validation/`、`contracts/g3/golden/validation-corpus.json`）；15 個已知 pass/fail cases + `verify_g3_val_001.py` 17/17 checks 全綠，新增 `MEGIS-VAL-002／003`。

G3-VAL-002 已閉合（2026-09-22）：CNC DFM rule pack（`contracts/g3/golden/cnc-dfm-rulepack.json`，24 條規則、72 個 positive/negative/boundary fixtures），以 rule schema 與來源登錄為基礎，全部 `in_review`、0 approved；release 治理閘門在來源未核准前拒絕放行（MEGIS-RUL-001）；68 tests + `verify_g3_val_002.py`（8/8 checks、72 fixtures、0 failure）全綠。

G3-MAT-001 已閉合（2026-09-22）：maturity evaluator（`megis/maturity/`）實作 §1.4 狀態表（DRAFT→CONCEPT→PROTOTYPE→ENGINEERING_REVIEWED→RELEASED）並為 Design Run `maturity` 唯一寫入者；含 D6／禁止類別上限、輸入變更與 waiver 到期重算、64 位輸入摘要；18 個 table-driven cases（每狀態 positive/negative ＋重算＋上限）、28 tests + `verify_g3_mat_001.py` 20/20 checks 全綠。

G3-BEN-001 已閉合（2026-09-22）：benchmark metrics（`megis/benchmark/`）實作偵測語意與 KPI（precision／recall／FP／false release／Wilson 95% CI）。dev corpus `contracts/g3/golden/benchmark-corpus.json`（40 cases：30 defect、10 clean）全數通過 oracle，recall 1.0、precision 1.0、FP 0、false release 0；holdout corpus（10 cases）SHA-256 仍為封存值 `73a25950...`（R-AGT-002），10/10 passed；12 tests + `verify_g3_ben_001.py` 13/13 checks 全綠，`artifacts/g3-ben-001/verification.json`（E3）。

G3-REV-001 已閉合（2026-09-22）：G3 自我審查於工作區內 `.runs/g3-rev-001-clean` 乾淨 clone 固定 commit `8303595` 重跑 G3 全部驗證（159 tests、6 支驗證腳本 95 checks、control-plane verifier），審查報告 passed、無 blocking finding；holdout §18.1 封存 SHA 重算一致。`execution/reviews/2026-09-22-G3-REV-001-review.md` + `artifacts/g3-rev-001/verification.json`（E3）。

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
| G3-VAL-001 | done | schemas/v3/validation-result.schema.json、megis/validation/、contracts/g3/golden/validation-corpus.json；15 cases + verify_g3_val_001.py 17/17 checks |
| G3-VAL-002 | done | contracts/g3/golden/cnc-dfm-rulepack.json、megis/rules/packs.py、tests/test_g3_val_002.py；24 rules、72 fixtures、68 tests + verify_g3_val_002.py allChecksPassed |
| G3-SRC-001 | done | schemas/v3/rule-source.schema.json、config/rule-sources/sources.yaml、megis/rules/sources.py；13 tests + verify_g3_src_001.py 18/18 checks |
| G3-MAT-001 | done | megis/maturity/evaluator.py、schemas/v3/maturity-evaluation.schema.json、contracts/g3/golden/maturity-corpus.json；18 cases、28 tests + verify_g3_mat_001.py allChecksPassed |
| G3-BEN-001 | done | megis/benchmark/、schemas/v3/benchmark-corpus.schema.json、schemas/v3/benchmark-report.schema.json、contracts/g3/golden/benchmark-corpus.json、contracts/g3/holdout/holdout-corpus.json；40 cases、12 tests + verify_g3_ben_001.py allChecksPassed |
| G3-REV-001 | done | execution/reviews/2026-09-22-G3-REV-001-review.md、artifacts/g3-rev-001/verification.json；乾淨 clone 重跑 159 tests + 6 支驗證腳本 95 checks 全綠 |
| G3-ACC-001 | in_progress | G3 gate acceptance 決策紀錄（見 `execution/AGENT_CLAIM.json`） |

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- UI-0 合成展示資料不視為工程資料。
