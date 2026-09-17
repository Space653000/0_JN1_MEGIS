# ADR-0007：施工者以全新 session 自我審查

> 文件治理
> - 目的：記錄 D6 的審查角色、隔離要求與成熟度上限。
> - 目前內容：無具名工程師、同一 Agent fresh-session review 的使用者決策。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D6
- 決策者：使用者
- 相關工作項目：V3C-DEC-001、V3C-REV-001、各 Gate `*-REV-001`

## 背景

目前沒有指定具名機構工程師。使用者決定由施工的 Codex 或 Claude Code 負責審查自己的工作，但藍圖要求將施工上下文與審查上下文隔離，以降低自我確認偏差。

## 決策

誰施工，誰負責在全新 session 進行自我審查。審查必須使用指定 commit 的乾淨 checkout，不讀施工 session 的對話或暫存輸出，重跑全部驗證，並新增至少一個施工時未使用的 negative 或 boundary case。審查報告必須記錄不同的 build/review session ID、checkout commit、環境、CI run 與結論。

目前不設具名工程師。因此自我審查最多只能支撐 `PROTOTYPE`；`ENGINEERING_REVIEWED` 與 `RELEASED` 不可達，任何輸出都必須標示未經具名工程師審查。

## 考慮過的替代方案

1. 無審查：不可接受。
2. 同 session 自評：上下文偏差過高，不符合 V3。
3. 同一 Agent、全新 session、乾淨 checkout、CI 外部證據：符合使用者決策，故採用。

## 後果

- 施工 session 不得自行偽造 fresh-session review。
- Gate acceptance 在 review 報告與 CI 同 SHA 通過前不得完成。
- 使用者可否決任何 review 或要求另一 Agent 抽查。

## 證據

- `docs/decisions/ADR-0001-adopt-v3-blueprint.md`
- `docs/RISKS.md`
- `MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md`
