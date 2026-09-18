# MEGIS Project State

- Current gate: `G2 — Fixture Geometry Vertical Slice`
- Current work item: `V3C-ART-001 — Artifact 政策`
- Last green commit: `3afce2cef1f0dc8dca5013e9354568777c2c13e2`
- Control-plane schema: `1.1.0`
- Updated at: `2026-09-17T22:28:25+08:00`

## Accepted capabilities

- UI-0A：隔離的本機前端工具鏈
- UI-0B：證據驅動的施工進度中心
- UI-0C：引導式治具使用者體驗原型
- UI-0D：自動化驗證與使用者驗收
- G0-REP-001：正式施工控制面
- G0-ENV-001：可重現 Python、Node 與 CAD 工具鏈
- G0-CAD-001：CadQuery STEP／STL／DXF 輸出與重新載入可行性
- G0-DRW-001：FreeCAD headless projection 與固定模板 SVG fallback
- G0-SIM-001：COMSOL 本機可行性決策為 `out_of_scope`，不阻塞核心 Gate
- G0-CI-001：本機與 GitHub Actions baseline CI，含跨 checkout artifact hash 穩定性
- G1-IR-001：unit、coordinate、ID/reference、provenance 與 knowledge-state primitives
- G1-IR-002：完整 Engineering IR schema、語意參照完整性與負向契約測試
- G1-IR-003：Fixture、Acoustic、Robot golden inputs、deterministic round trip 與下游 consumer
- G1-MIG-001：V1→V2 deterministic migration、版本政策與可驗證 rollback
- G2-CAD-001：kernel-neutral geometry contract、capability negotiation 與 adapter seam
- G2-CAD-002：由 golden IR 驅動的 CadQuery fixture base、尺寸與拓樸驗證
- G2-CAD-003：cover、fasteners、USB-C cutout、PCB envelope 與組立間隙驗證
- V3C-BCR-001：V3 主藍圖指向、採用 ADR、74 項工作圖與必要 ID 防退化檢查
- V3C-CTL-001：向後相容 schema 1.1、單一 Builder claim、依賴無循環、done SHA 與 Gate 審查強制機制
- V3C-DOC-001：§5.1 必要文件、目錄與 28 份 Markdown 治理 metadata
- V3C-DEC-001：D1–D9 九份 accepted ADR、schema 驗證決策索引與誠實實作狀態
- V3C-DET-001：fingerprint policy 1.0.0、STEP/DXF 正規化、binary STL 與雙次 replay
- V3C-MAT-001：classification schema、全庫 manifest scanner、非 Design Run maturity 禁制與跨 process replay
- V3C-ART-001（實作與 E3 證據完成，待隔離交接）：artifact policy 1.0.0、Git 大小預算、五個既有重型製品精確白名單與新增禁制

UI-0 驗收只涵蓋使用者體驗原型；沒有工程生成能力或工程製品獲得驗收。

## Active scope

`V3C-ART-001` 實作與 E3 證據已完成：GitHub Actions run `35232682702` 驗證 commit `da4e61d`，run `35233187632` 驗證 README commit `3afce2c`，兩者全綠。控制面暫留 `in_progress`，因下一項 `V3C-REV-001` 明定必須由全新 session 執行，現施工 session 不得冒充隔離審查者。完整基線為 8 個 artifact policy 負向測試、103 個 Python tests、9 個前端 tests、13 筆 artifact smoke 與 1 份 manifest scanner 全綠。

## Next work item

由全新 session 接手 `V3C-REV-001`，對已 accepted Gate 與 V3C remediation 出具追溯審查；完成 `V3C-ACC-001` 後再回到 `G2-CAD-004`。目前不需要使用者重新驗收，但必須保留 reviewer 與 builder 的 session 隔離。

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- 本 Gate 不把 UI-0 合成展示資料視為工程資料。
