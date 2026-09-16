# MEGIS Project State

- Current gate: `G0 — Foundation & Feasibility`
- Current work item: `G0-REP-001 — 建立 repository 與狀態檔`
- Last green commit: `5baf870e254c799ee8421fb37fef14972e34505f`
- Control-plane schema: `1.0.0`
- Updated at: `2026-09-16T20:28:02+08:00`

## Accepted capabilities

- UI-0A：隔離的本機前端工具鏈
- UI-0B：證據驅動的施工進度中心
- UI-0C：引導式治具使用者體驗原型
- UI-0D：自動化驗證與使用者驗收

UI-0 驗收只涵蓋使用者體驗原型；沒有工程生成能力或工程製品獲得驗收。

## Active scope

目前只施工 `G0-REP-001`。目標是建立藍圖第 5 章正式控制面、將初始工作清單轉成具依賴與驗收條件的佇列，並讓進度網站改讀正式資料源。

## Next work item

`G0-ENV-001` 在 `G0-REP-001` 完成並同步後才可轉為 `ready`。

## Boundaries

- 所有本機寫入必須留在 `C:\0_JN1_MEGIS`。
- `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent` 不得變更、共用或依賴。
- 本機服務只綁定 `127.0.0.1`。
- 本 Gate 不把 UI-0 合成展示資料視為工程資料。
