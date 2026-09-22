# MEGIS Project State

- Current gate: `G5 — 原型套件與可重現性`
- Current work item: `G5-REV-001 — G5 自我審查（in_progress）`
- Last green commit: `20c74d569434c05d49a4bbb9746a15872ba65eac`
- Control-plane schema: `1.1.0`
- Updated at: `2026-09-22T18:15:00+08:00`

## Active gate: G5

G2 已 closed（`SO-0003`，2026-09-21）。G3 已 accepted（`SO-0004`，2026-09-22，E4）。G4 已 accepted（`SO-0005`，2026-09-22，E4）。G5 — 原型套件與可重現性 現在為 active gate，下一個工項為 `G5-REV-001 — G5 自我審查`（in_progress）。

G5-REP-001 已閉合（2026-09-22）：clean-environment reproducibility test（`megis/package/repro.py`）把可重現契約定義為 semantic fingerprint（STEP→normalized text、STL→triangles、DXF→vectors、BOM CSV→utf8 text、drawing SVG→svg text）；`bom.csv`／`draft_drawing.svg`／`reference_case.stl` 還 byte-穩定（byte_sha256 一致），STEP/DXF 的 bytes 因 exporter 寫入 run metadata 允許跨 run 差異，但語意指紋固定；`contracts/g5/golden/repro-fingerprints.json`（corpusId `g5-repro-fingerprints@1.0.0`）+ `schemas/v3/repro-fingerprints.schema.json`；`tests/test_g5_rep_001.py` 6 tests；`scripts/verify_g5_rep_001.py` 以乾淨 clone（子程序）三方比對 source／clean／golden 的 `reportFingerprint`，全等且 g0-cad 三格式語意指紋對齊，semantic drift 0、無需 ADR；新錯誤碼 `MEGIS-REP-001`、ErrorDomain `REP`；baseline CI 498 Python + 9 Frontend 全綠（E3）。下一工項 `G5-REV-001`（in_progress）。

G5-DRW-001 已閉合（2026-09-22）：fixed-template draft drawing（`megis/package/drawing.py`）以 Engineering IR metadata 驅動、不從 STEP 猜 critical dimension，只允許固定 `fixture-a4-landscape@1.0.0` 模板，輸出不含時間戳的確定性 SVG（`svgSemanticFingerprint` 為其 SHA-256）；白名單維度只印與 IR nominal 一致的數值，永久標示 `DRAFT - ENGINEERING REVIEW REQUIRED` 與 `NOT FOR MANUFACTURING`，QA checklist 逐項記錄並可寫入 manifest；`schemas/v3/draft-drawing.schema.json` + `drawing-corpus.schema.json` + `contracts/g5/golden/drawing-corpus.json`（12 cases：5 positive／7 negative）、`tests/test_g5_drw_001.py` 21 tests、錯誤碼 `MEGIS-DRW-001/002`、ErrorDomain `DRW`；SVG 屬 draft，不含 release 宣告，也不生成工程/release artifact（E3）。baseline CI 492 Python + 9 Frontend 全綠。下一工項 `G5-REP-001`（in_progress）。

G5-BOM-001 已閉合（2026-09-22）：BOM exporter（`megis/package/bom.py`）把已驗證 IR 落成十二欄、item 升冪、UTF-8／LF 的確定性 CSV；數量一律讀 IR component quantity（現行 v2 schema 下為 1，不臆測），material／revision／provenance 全來自 IR，module 由 provenance marker 追溯；`schemas/v3/bom.schema.json` + `bom-corpus.schema.json` + `contracts/g5/golden/bom-corpus.json`（12 cases：5 positive／7 negative）、`tests/test_g5_bom_001.py` 25 tests、錯誤碼 `MEGIS-PKG-003／BOM-001／002`；baseline CI 471 Python + 9 Frontend 全綠（E3）。下一工項 `G5-REV-001`（in_progress）。

G5-PKG-001 已閉合（2026-09-22）：package manifest（`schemas/v3/package-manifest.schema.json`）提供六種 fingerprint kind（byte_sha256／normalized_text_sha256／gltf_sha256／step_sha256／dxf_sha256／csv_sha256），`megis/package/manifest.py` 逐檔算 byte SHA-256、`megis/package/verify.py` 可重建與核對；`schemas/v3/manifest-corpus.schema.json` + `contracts/g5/golden/manifest-corpus.json`（18 cases：7 positive／11 negative，PKG-001×5、PKG-002×6）；`tests/test_g5_pkg_001.py` 25 tests；`megis/errors/registry.py` 新增 `MEGIS-PKG-001/002`；baseline CI 446 Python + 9 Frontend 全綠（E3）。下一工項 `G5-BOM-001`（in_progress）。

G4-MOD-001 已閉合（2026-09-22）：四級 capability 閉集合（metadata_only／layout_capable／geometry_capable／validated）與 §12 policy 表；`megis/module`、`schemas/v3/module.schema.json`、18 cases；28 tests + `verify_g4_mod_001.py` allChecksPassed（E3）。

G4-GRF-001 已閉合（2026-09-22）：Relationship vocabulary 八型別閉集合（contains／mounts_to／fastens／opens_through／clears／aligns／covers／removable_along），每型別語意與必要驗證、參數不變量；`megis/relationship`、`schemas/v3/relationship.schema.json`、20 cases（8 positive／12 negative）；26 tests + `verify_g4_grf_001.py` allChecksPassed（E3）。

G4-MOD-002 已閉合（2026-09-22）：Module composition（`megis/composition`）把 Module＋Relationship 落到 Fixture golden IR，只衍生 proven 的 mount／fastener／opening／clearance constraints；移除會清除或明確標示 dependent constraints、缺值絕不補虛構數字（`unsafeToDefault` unknown＋blocked kind）、Module 版本固定（idempotent／upgrade_blocked／allow_upgrade）。`schemas/v3/module-composition-corpus.schema.json`、20 cases；29 tests + `verify_g4_mod_002.py` allChecksPassed（E3）；baseline CI 389 Python + 9 Frontend 全綠。G4-IMP-001 接續 in_progress 並完成 AGENT_CLAIM 交接。

G4-IMP-001 已閉合（2026-09-22）：safe STEP／DXF metadata extraction（`megis/importing`）。untrusted 檔案只在隔離 subprocess（`python -m megis.importing.worker`）內解析，父程序只回收單一 JSON；guard 在解析前攔截副檔名／magic／大小（`MEGIS-IMP-001/002`），worker 做結構完整性檢查並以可注入的 `max_entities` 與 `WORKER_TIMEOUT_SECONDS` 封頂（`MEGIS-IMP-003/004`）。只抽取 bounding box、solid/shell 計數、candidate holes／planar sections、file unit（含 inch）與 parser warnings；報告標示 `derivedFromImport` 且不提升 capability。`schemas/v3/import-report.schema.json`（`additionalProperties: false`）、`contracts/g4/golden/import-corpus.json`（16 cases）；`tests/test_g4_imp_001.py` 32 tests（public API、unit、corpus-driven、schema contract）；baseline CI 421 Python + 9 Frontend 全綠。下一工項 `G4-REV-001`（in_progress）。
G4-REV-001 已閉合（2026-09-22）：G4 自我審查於工作區內 `.runs/g4-rev-001-clean` 乾淨 clone 固定 commit `eef0afc` 重跑 G4 全部驗證（115 tests、3 支驗證腳本 90 checks、control-plane verifier），審查報告 passed、無 blocking finding。`execution/reviews/2026-09-22-G4-REV-001-review.md` + `artifacts/g4-rev-001/verification.json`（E3）。下一工項 `G4-ACC-001`（in_progress）。
G4-ACC-001 已閉合（2026-09-22）：G4 gate acceptance 決策紀錄（E4，`execution/signoffs/SO-0005.yaml` + `artifacts/g4-acc-001/verification.json`），可追溯至 G4 審查與 CI；G4 gate 標為 accepted，G5 gate 轉 active，`G5-PKG-001` 施工開始。

G3-RUL-001 已閉合（2026-09-21）：rule schema（`schemas/v3/rule.schema.json`）、waiver schema（`schemas/v3/waiver.schema.json`）、生命週期狀態機與 waiver 到期／不可豁免邏輯（`megis/rules/`）、golden corpus（`contracts/g3/golden/rule-governance.json`）；14 tests + `verify_g3_rul_001.py` 18/18 checks 全綠，新增 `MEGIS-RUL-002／003`。

G3-SRC-001 已閉合（2026-09-21）：規則來源登錄與核對流程（`schemas/v3/rule-source.schema.json`、`config/rule-sources/sources.yaml`、`megis/rules/sources.py`）；8 個來源登錄、0 approved（保守狀態），review_due 過期自動降為 `needs_review`、draft 規則不可支撐核准；13 tests + `verify_g3_src_001.py` 18/18 checks 全綠，新增 `MEGIS-RUL-004`。

G3-VAL-001 已閉合（2026-09-21）：geometry / collision / clearance validators（`schemas/v3/validation-result.schema.json`、`megis/validation/`、`contracts/g3/golden/validation-corpus.json`）；15 個已知 pass/fail cases + `verify_g3_val_001.py` 17/17 checks 全綠，新增 `MEGIS-VAL-002／003`。

G3-VAL-002 已閉合（2026-09-22）：CNC DFM rule pack（`contracts/g3/golden/cnc-dfm-rulepack.json`，24 條規則、72 個 positive/negative/boundary fixtures），以 rule schema 與來源登錄為基礎，全部 `in_review`、0 approved；release 治理閘門在來源未核准前拒絕放行（MEGIS-RUL-001）；68 tests + `verify_g3_val_002.py`（8/8 checks、72 fixtures、0 failure）全綠。

G3-MAT-001 已閉合（2026-09-22）：maturity evaluator（`megis/maturity/`）實作 §1.4 狀態表（DRAFT→CONCEPT→PROTOTYPE→ENGINEERING_REVIEWED→RELEASED）並為 Design Run `maturity` 唯一寫入者；含 D6／禁止類別上限、輸入變更與 waiver 到期重算、64 位輸入摘要；18 個 table-driven cases（每狀態 positive/negative ＋重算＋上限）、28 tests + `verify_g3_mat_001.py` 20/20 checks 全綠。

G3-BEN-001 已閉合（2026-09-22）：benchmark metrics（`megis/benchmark/`）實作偵測語意與 KPI（precision／recall／FP／false release／Wilson 95% CI）。dev corpus `contracts/g3/golden/benchmark-corpus.json`（40 cases：30 defect、10 clean）全數通過 oracle，recall 1.0、precision 1.0、FP 0、false release 0；holdout corpus（10 cases）SHA-256 仍為封存值 `73a25950...`（R-AGT-002），10/10 passed；12 tests + `verify_g3_ben_001.py` 13/13 checks 全綠，`artifacts/g3-ben-001/verification.json`（E3）。

G3-REV-001 已閉合（2026-09-22）：G3 自我審查於工作區內 `.runs/g3-rev-001-clean` 乾淨 clone 固定 commit `8303595` 重跑 G3 全部驗證（159 tests、6 支驗證腳本 95 checks、control-plane verifier），審查報告 passed、無 blocking finding；holdout §18.1 封存 SHA 重算一致。`execution/reviews/2026-09-22-G3-REV-001-review.md` + `artifacts/g3-rev-001/verification.json`（E3）。

G3-ACC-001 已閉合（2026-09-22）：G3 gate acceptance 決策紀錄（E4，`execution/signoffs/SO-0004.yaml` + `artifacts/g3-acc-001/verification.json`），可追溯至 G3 審查與 CI；G3 gate 標為 accepted，G4 gate 轉 active。

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
| G3-ACC-001 | done | execution/signoffs/SO-0004.yaml、artifacts/g3-acc-001/verification.json；G3 gate accepted（E4） |

## G4 work items

| ID | Status | Evidence |
|---|---|---|
| G4-MOD-001 | done | schemas/v3/module.schema.json、megis/module/、contracts/g4/golden/module-corpus.json（18 cases）、tests/test_g4_mod_001.py（28 tests）、scripts/verify_g4_mod_001.py（E3）、artifacts/g4-mod-001/verification.json、docs/G4_MODULE_CAPABILITY.md |
| G4-MOD-002 | done | schemas/v3/module-composition-corpus.schema.json、megis/composition/、contracts/g4/golden/module-composition-corpus.json（20 cases）、tests/test_g4_mod_002.py（29 tests）、scripts/verify_g4_mod_002.py（E3）、docs/G4_MODULE_COMPOSITION.md |
| G4-IMP-001 | done | megis/importing/、schemas/v3/import-report.schema.json、schemas/v3/import-corpus.schema.json、contracts/g4/golden/import-corpus.json（16 cases）、tests/test_g4_imp_001.py（32 tests）、docs/G4_IMPORT_SAFETY.md |
| G4-GRF-001 | done | schemas/v3/relationship.schema.json、megis/relationship/、contracts/g4/golden/relationship-corpus.json（20 cases）、tests/test_g4_grf_001.py（26 tests）、scripts/verify_g4_grf_001.py（E3）、artifacts/g4-grf-001/verification.json、docs/G4_RELATIONSHIP_VOCABULARY.md |
| G4-REV-001 | done | execution/reviews/2026-09-22-G4-REV-001-review.md、artifacts/g4-rev-001/verification.json；乾淨 clone 重跑 115 tests + 3 支驗證腳本 90 checks 全綠 |
| G4-ACC-001 | done | execution/signoffs/SO-0005.yaml、artifacts/g4-acc-001/verification.json；G4 gate accepted（E4） |

## G5 work items

| ID | Status | Evidence |
|---|---|---|
| G5-PKG-001 | done | schemas/v3/package-manifest.schema.json、schemas/v3/manifest-corpus.schema.json、contracts/g5/golden/manifest-corpus.json（18 cases）、megis/package/、tests/test_g5_pkg_001.py（25 tests）、artifacts/g5-pkg-001/verification.json；baseline CI 446 Python + 9 Frontend 全綠（E3） |
| G5-BOM-001 | done | schemas/v3/bom.schema.json、schemas/v3/bom-corpus.schema.json、contracts/g5/golden/bom-corpus.json（12 cases）、megis/package/bom.py、tests/test_g5_bom_001.py（25 tests）、artifacts/g5-bom-001/verification.json；baseline CI 471 Python + 9 Frontend 全綠（E3） |
| G5-DRW-001 | done | schemas/v3/draft-drawing.schema.json、schemas/v3/drawing-corpus.schema.json、contracts/g5/golden/drawing-corpus.json（12 cases）、megis/package/drawing.py、tests/test_g5_drw_001.py（21 tests）、artifacts/g5-drw-001/verification.json；baseline CI 492 Python + 9 Frontend 全綠（E3） |
| G5-REP-001 | done | schemas/v3/repro-fingerprints.schema.json、contracts/g5/golden/repro-fingerprints.json、megis/package/repro.py、tests/test_g5_rep_001.py（6 tests）、scripts/verify_g5_rep_001.py、artifacts/g5-rep-001/verification.json；baseline CI 498 Python + 9 Frontend 全綠（E3） |
| G5-REV-001 | in_progress | G5 自我審查 |

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- UI-0 合成展示資料不視為工程資料。
