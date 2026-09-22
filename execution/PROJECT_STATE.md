# MEGIS Project State

- Current gate: `G6 — 引導式介面工程整合`
- Current work item: `G6-A11Y-001 — 無障礙驗證（in_progress）`
- Last green commit: `1714669f8ce2c60d69211e338eaccb9368a61bbd`
- Control-plane schema: `1.1.0`
- Updated at: `2026-09-23T04:42:00+08:00`

## Active gate: G6

G2 已 closed（`SO-0003`，2026-09-21）。G3 已 accepted（`SO-0004`，2026-09-22，E4）。G4 已 accepted（`SO-0005`，2026-09-22，E4）。G5 已 accepted（`SO-0006`，2026-09-22，E4）。G6 — 引導式介面工程整合現在為 active gate；`G6-UI-001`、`G6-QST-001`、`G6-AI-001`～`G6-AI-004` 已閉合（2026-09-22，E3），下一個工項為 `G6-A11Y-001 — 無障礙驗證`（in_progress）。

G6-UI-001 已閉合（2026-09-22）：capability-driven guided flow（`megis/guides/`、`schemas/v3/capability-manifest.schema.json`、`contracts/g6/golden/capability-manifest.json`、`apps/web/src/adapters/capability-guide-adapter.ts`）。介面只呈現後端已證明的能力，guided flow 從封閉問題集建立 schema 合法 Engineering IR；UI-form 與直接 API 路徑產出 byte-identical IR；unsafe unknown／超出能力的輸入以 `MEGIS-UI-001`／`MEGIS-UI-002`／`MEGIS-ENV-001` 阻擋而不自行預設；`tests/test_g6_ui_001.py` 11 tests + `scripts/verify_g6_ui_001.py` E3 allChecksPassed（golden fingerprint `7bfc576a...`），前端 guided-flow 測試（`prototype-flow.test.tsx` 6 tests）驗證越界／未知阻擋與合成標籤；baseline 509 Python + 12 Frontend 全綠（E3）。下一工項 `G6-QST-001`（in_progress）。
G6-QST-001 已閉合（2026-09-22）：deterministic question ordering 與 abstention（`megis/guides/qst.py`、`schemas/v3/question-order-corpus.schema.json`、`contracts/g6/golden/question-order-corpus.json`）實現藍圖 §14 動態問題引擎 rules 1-8：unsafe_to_default 先問、impact 由架構到需求遞減、從已證實能力可推得的 connector／fastener／cover 永不追問、順序以凍結 golden corpus 固定為決定性；unsafe unknown（未提供尺寸或 PCB envelope 為 unknown）以 `MEGIS-UI-001` 阻擋生成並給出下一步，critical unknown 在 abstention 後仍留在 pending set；`tests/test_g6_qst_001.py` 14 tests + `scripts/verify_g6_qst_001.py` E3 allChecksPassed（12 checks、18 corpus cases：ordering／abstention／boundary／negative，8 blocked cases 皆 MEGIS-UI-001 且無 artifact）；本段驗證 baseline 523 Python + 12 Frontend + control-plane 全綠（E3）。實作 commit `9c1c671`。下一工項 `G6-AI-001`（in_progress）。
G6-AI-001 已閉合（2026-09-22）：新增 `megis/ai/` provider-neutral seam、預設關閉的 `config/ai/provider.json`、recorded local stub、timeout／呼叫／token／成本上限與 deterministic form fallback；provider 故障回 `MEGIS-AI-001`、超限回 `MEGIS-AI-003`，並保留 `MEGIS-AI-002` 給 schema-invalid output。Audit 只保存 provider／model／prompt／schema 版本與 input SHA-256，不保存 raw intent 或 exception；package manifest 補上 provider 與 schema version。`tests/test_g6_ai_001.py` 17 tests、`scripts/verify_g6_ai_001.py` 9 checks、baseline 540 Python + 12 Frontend 全綠（E3）；實作 commit `5d890be` 已同步 GitHub。下一工項 `G6-AI-002`（in_progress）。
G6-AI-002 已閉合（2026-09-22）：新增 schema-bound AI Requirement draft quarantine（`schemas/v3/ai-requirement-draft.schema.json`、`megis/ai/extraction.py`）。所有 proposal 固定為 `llm_proposed` 並綁定原文 SHA-256 與 exact `evidenceSpan`；數值必須在 span 中出現，尺寸必須明示 `mm`。JSON／schema／hash／span／單位錯誤一律 `MEGIS-AI-002` 拒收且不修補；confirmation ledger 只提升使用者逐欄確認值，未確認值不能覆寫表單或進入 confirmed IR。3 筆 recorded fixtures、18 tests、7 verifier checks 與 baseline 558 Python + 12 Frontend 全綠（E3）；實作 commit `6694507` 已同步 GitHub。下一工項 `G6-AI-003`（in_progress）。
G6-AI-003 已閉合（2026-09-22）：建立 54 筆、六類平衡 intent corpus（complete／missing information／contradiction／out of envelope／unit mixed／prompt injection），以 case-level report 計算 schema conformance、field precision／recall、hallucination、unsafe hallucination、abstention、out-of-envelope detection、unit error 與 injection resistance，並附 Wilson 95% CI。54/54 cases、9/9 verifier checks、unsafe hallucination 0/41、injection resistance 9/9；explanation grounding 明確標為 not applicable 並交由 G6-AI-004，未虛報 100%。baseline 570 Python + 12 Frontend 全綠（E3）；實作 commit `555d10c` 已同步 GitHub。下一工項 `G6-AI-004`（in_progress）。
G6-AI-004 已閉合（2026-09-22）：新增 grounded explanation schema 與 fail-closed verifier（`megis/ai/explanation.py`），AI 只能引用 Engineering IR、rule result、manifest；核心重算 canonical SHA-256，逐一比對解釋文字中的每次數值出現、citation token、JSON Pointer 與來源數值。漏引、多引、錯值、錯 pointer、非數值來源、來源竄改、偽造 hash 或非法來源均整份回 `MEGIS-AI-002`，不修補。15 tests、8 verifier checks、4/4 example numbers grounded，baseline 585 Python + 12 Frontend 全綠（E3）；實作 commit `d27d16e` 已同步 GitHub。下一工項 `G6-A11Y-001`（in_progress）。
G6-A11Y-001 自動化段已完成（2026-09-22，工項仍 in_progress）：加入 `axe-core 4.10.3`，五個主要路由以 WCAG 2.2 A／AA tags 掃描為 0 violations；8 組 palette 對比度、skip link、route focus、aria-current、行動選單 Escape／Tab wrap、aria-pressed 等共 9 tests 全綠。另以實際 Chrome（1536×729）完成 8 項代理自動化瀏覽器稽核，證據為 `artifacts/g6-a11y-001/browser-audit.json`。人工證據契約補上 Draft 2020-12 schema、12 個 canonical checks、版本化空白範本與 fail-closed verifier；空白範本格式通過但 `--require-complete` 以 exit code 1 拒絕，12 contract tests 與完整 baseline 597 Python + 21 Frontend 全綠。這些工具不冒充真人操作；真人鍵盤與螢幕閱讀器抽查仍 pending，`closureEligible: false`，不得移交 G6-USE-001。
2026-09-23 驗收引導網頁補強：`/progress` 的 disclosure 現在分區列出目前工項的支援證據與正式 `verificationCommands`，同時保留 pending acceptance、fail-closed 說明與 G6 未完成邊界。控制面驗證新增 in-progress preparation 規則，缺少支援證據或驗證指令即拒絕；完整 baseline 597 Python + 22 Frontend 全綠，done／in-progress／planned 計數不變。

2026-09-23 人工稽核紀錄器補強：新增 `scripts/record_g6_a11y_manual.py`，由實際抽查者輸入具名 reviewer、瀏覽器／作業系統／輔助技術版本、明確 attestation，以及 12 個 section-qualified `passed`／`failed` 結果。紀錄器限制輸出於工作區、拒絕覆寫、失敗結果強制備註，並在寫入前呼叫既有 fail-closed verifier；10 recorder tests 全綠。Agent 未產生任何真人紀錄，鍵盤與螢幕閱讀器仍 pending，工項與 62／1／11 計數不變。

G5-ACC-001 已閉合（2026-09-22）：G5 gate acceptance 決策紀錄（E4，`execution/signoffs/SO-0006.yaml` + `artifacts/g5-acc-001/verification.json`），可追溯至 G5 審查與 CI；G5 gate 標為 accepted，G6 gate 轉 active，`G6-UI-001` 施工開始。

G5-REV-001 已閉合（2026-09-22）：G5 自我審查於工作區內 `.runs/g5-rev-001-clean` 乾淨 clone 固定 commit `51259f6` 重跑 G5 全部驗證（77 tests、`verify_g5_rep_001.py` allChecksPassed 三方 reportFingerprint 全等、control-plane verifier），審查報告 passed、無 blocking finding；`execution/reviews/2026-09-22-G5-REV-001-review.md` + `artifacts/g5-rev-001/verification.json`（E3）。下一工項 `G5-ACC-001`（in_progress）。

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
| G5-REV-001 | done | execution/reviews/2026-09-22-G5-REV-001-review.md、artifacts/g5-rev-001/verification.json；乾淨 clone 重跑 77 tests + verify_g5_rep_001.py allChecksPassed + control-plane verifier 全綠（E3） |
| G5-ACC-001 | done | execution/signoffs/SO-0006.yaml、artifacts/g5-acc-001/verification.json；G5 gate accepted（E4，可追溯至 G5 審查與 CI） |

## G6 work items

| ID | Status | Evidence |
|---|---|---|
| G6-UI-001 | done | schemas/v3/capability-manifest.schema.json、contracts/g6/golden/capability-manifest.json、megis/guides/、apps/web/src/adapters/capability-guide-adapter.ts、tests/test_g6_ui_001.py（11 tests）、scripts/verify_g6_ui_001.py（E3 allChecksPassed）、artifacts/g6-ui-001/verification.json；baseline 509 Python + 12 Frontend 全綠 |
| G6-QST-001 | done | megis/guides/qst.py、schemas/v3/question-order-corpus.schema.json、contracts/g6/golden/question-order-corpus.json（18 cases）、tests/test_g6_qst_001.py（14 tests）、scripts/verify_g6_qst_001.py（E3 allChecksPassed 12 checks）、artifacts/g6-qst-001/verification.json；baseline 523 Python + 12 Frontend 全綠；實作 commit 9c1c671 |

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- UI-0 合成展示資料不視為工程資料。
