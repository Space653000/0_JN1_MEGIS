# ADR-0003：COMSOL 維持 out_of_scope

> 文件治理
> - 目的：記錄 D2 的 COMSOL 授權、API 與核心 Gate 邊界。
> - 目前內容：已接受的 out_of_scope 決策及未來解鎖條件。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D2
- 決策者：既有 G0-SIM-001 可行性決策
- 相關工作項目：V3C-DEC-001、G0-SIM-001、G7-SOL-001

## 背景

本機盤點沒有 COMSOL 安裝、batch executable、API 或授權設定證據。把不可用的商業 solver 當作核心依賴，會使可重建性與後續 Gate 無法誠實驗收。

## 決策

COMSOL 決策為 `out_of_scope`，且不阻塞核心 Gate。不得宣稱已執行 COMSOL solve、API integration 或 license checkout。G7 至少必須提供不依賴 COMSOL 的 L0 路徑；L1 必須另有合法工具與量測比對。

## 考慮過的替代方案

1. 假設未來會有 license：不可驗證，拒絕。
2. 立刻購買或要求授權：未獲採購授權，且不屬於必要核心。
3. 明確 out_of_scope 並保留 adapter seam：可維持誠實邊界，因此採用。

## 後果

- COMSOL 不得出現在核心通過條件或 release 宣稱中。
- 未來只有在合法授權、支援版本、受控 adapter 與 reference smoke test 齊備後，才能以新 ADR 重新評估。
- 本決策不表示所有模擬都 out_of_scope，只限制 COMSOL 整合。

## 證據

- `environment/comsol.decision.json`
- `docs/G0_COMSOL_DECISION.md`
