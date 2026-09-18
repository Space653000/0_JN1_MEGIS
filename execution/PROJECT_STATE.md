# MEGIS Project State

- Current gate: `G2 — Fixture Geometry Vertical Slice`
- Current work item: `V3C-REV-001 — 已 accepted Gate 追溯審查`
- Last green commit: `af963561a8d8b4e377c5020ced609714c9e47eec`
- Control-plane schema: `1.1.0`
- Updated at: `2026-09-19T01:25:30+08:00`

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
- G0-DOC-001：v3 §5.1 必要文件 24 項全部存在、41 份 docs/*.md 治理 metadata 全通過，secret scan 整合進 baseline
- G0-DEC-001：D1–D9 所有 G0 使用者決策有 accepted ADR 與可追溯證據（E4），誠實標記 enforced／partially_enforced／policy_only
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
- V3C-REV-001（進行中，fresh-session reviewer 接棒）：對 UI-0、G0、G1 已 accepted Gate 與 V3C remediation 的追溯審查，差距皆有承接項目

UI-0 驗收只涵蓋使用者體驗原型；沒有工程生成能力或工程製品獲得驗收。

## Active scope

`V3C-REV-001` 追溯審查報告已產出，10 項結構差距全部對應既有承接 ID，掌控面規則要求 G0/G1 承接項全 done 後才能將 REV/ACC 標 done，故維持 `in_progress` 傘型。本段完成 `G0-DEC-001`：以既有 `V3C-DEC-001` 決策補記為來源，D1–D9 全部有 accepted ADR 與可追溯證據（E4），新增 `tests/test_g0_dec_001.py` 與 `artifacts/g0-dec-001/verification.json`；本機完整 baseline 全綠（106 Python、23 decision tests、219 secret-scan 檔、221 artifact-policy 檔）。
## Next work item

下一步完成 `G0-DET-001`（Determinism 與 fingerprint 原型：兩次重跑 semantic fingerprint 一致、header 正規化與 maturity 掃描生效），再依序 `G0-REV-001` → `G0-ACC-001`，接著 G1 承接項（`G1-ERR-001` → `G1-ENV-001` → `G1-REQ-001` → `G1-REV-001` → `G1-ACC-001`）；全部 done 後才能將 `V3C-REV-001` 與 `V3C-ACC-001` 標 done，再回到 `G2-CAD-004`。不需要使用者重新驗收，但必須保留 reviewer 與 builder 的 session 隔離。

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- 本 Gate 不把 UI-0 合成展示資料視為工程資料。
