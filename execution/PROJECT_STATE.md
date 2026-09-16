# MEGIS Project State

- Current gate: `G0 — Foundation & Feasibility`
- Current work item: `G0-ENV-001 — 鎖定 Python、Node 與 CAD dependencies`
- Last green commit: `09f19ea3633189bdbb58e254d8e5798736950bfb`
- Control-plane schema: `1.0.0`
- Updated at: `2026-09-16T20:38:59+08:00`

## Accepted capabilities

- UI-0A：隔離的本機前端工具鏈
- UI-0B：證據驅動的施工進度中心
- UI-0C：引導式治具使用者體驗原型
- UI-0D：自動化驗證與使用者驗收

UI-0 驗收只涵蓋使用者體驗原型；沒有工程生成能力或工程製品獲得驗收。

## Active scope

`G0-REP-001` 已完成並由 commit `09f19ea` 固定。現在只施工 `G0-ENV-001`，目標是鎖定 Python、Node、CadQuery、OpenCascade 與 FreeCAD 的支援版本及可重現安裝邊界。

## Next work item

`G0-CAD-001`、`G0-DRW-001` 與 `G0-SIM-001` 只有在 `G0-ENV-001` 完成後才能轉為 `ready`；一次仍只施工一個工作單元。

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- 本 Gate 不把 UI-0 合成展示資料視為工程資料。
