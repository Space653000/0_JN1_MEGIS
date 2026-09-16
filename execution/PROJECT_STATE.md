# MEGIS Project State

- Current gate: `G1 — Engineering Contracts & Golden Cases`
- Current work item: `G1-IR-001 — 定義 unit、coordinate、ID 與 provenance primitives`
- Last green commit: `86b9b67513822538e8bd3147d403f24521bb0815`
- Control-plane schema: `1.0.0`
- Updated at: `2026-09-17T01:10:55+08:00`

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

UI-0 驗收只涵蓋使用者體驗原型；沒有工程生成能力或工程製品獲得驗收。

## Active scope

G0 六個工作項目皆已完成；GitHub Actions run `35126277676` 對 commit `86b9b67` 全綠。現在只施工 `G1-IR-001`，目標是以正反向 schema tests 固定 unit、coordinate、ID 與 provenance primitives。

## Next work item

`G1-IR-001` 完成後依相依關係處理 `G1-IR-002`；一次仍只施工一個工作單元。

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- 本 Gate 不把 UI-0 合成展示資料視為工程資料。
