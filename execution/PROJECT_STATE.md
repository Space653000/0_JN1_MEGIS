# MEGIS Project State

- Current gate: `G0 — Foundation & Feasibility`
- Current work item: `G0-DRW-001 — FreeCAD TechDraw headless spike`
- Last green commit: `b8a0dddd2f3ab763cde4a466e851f3a733f3099a`
- Control-plane schema: `1.0.0`
- Updated at: `2026-09-17T00:27:22+08:00`

## Accepted capabilities

- UI-0A：隔離的本機前端工具鏈
- UI-0B：證據驅動的施工進度中心
- UI-0C：引導式治具使用者體驗原型
- UI-0D：自動化驗證與使用者驗收
- G0-REP-001：正式施工控制面
- G0-ENV-001：可重現 Python、Node 與 CAD 工具鏈
- G0-CAD-001：CadQuery STEP／STL／DXF 輸出與重新載入可行性

UI-0 驗收只涵蓋使用者體驗原型；沒有工程生成能力或工程製品獲得驗收。

## Active scope

`G0-CAD-001` 已完成並由 commit `b8a0ddd` 固定。現在只施工 `G0-DRW-001`，目標是驗證 FreeCAD 1.1.3 TechDraw headless 固定模板圖面路徑，並形成明確 `pass`、`fallback` 或 `out_of_scope` 決策。

## Next work item

`G0-DRW-001` 完成後依序處理 `G0-SIM-001` 與 `G0-CI-001`；一次仍只施工一個工作單元。

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- 本 Gate 不把 UI-0 合成展示資料視為工程資料。
