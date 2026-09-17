# ADR-0008：單一 Builder claim 與同 Agent 分離審查

> 文件治理
> - 目的：記錄 D7 的 Agent 角色與單一寫入鎖。
> - 目前內容：Codex／Claude Code 接手、claim 互斥與審查唯讀邊界。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D7
- 決策者：使用者
- 相關工作項目：V3C-DEC-001、V3C-CTL-001、V3C-REV-001

## 背景

Codex 與 Claude Code 都可能接手施工；若兩個 Agent 同時修改 `main` 或 `execution/`，work item、evidence 與 commit fixed point 會互相覆蓋。另一方面，D6 仍要求同一個施工 Agent 負責審查，但必須換新 session。

## 決策

同一時間只允許一個 Builder 持有有效 `execution/AGENT_CLAIM.json`。Claim 必須對應唯一 `in_progress` work item、具名 agent、base commit 與到期時間；過期或接手時先 reconcile Git 與控制狀態。

Codex 或 Claude Code 誰取得 work item 並施工，誰負責該項的 fresh-session review。Review session 是唯讀審查者，不得修改程式、schema、golden 或狀態檔；發現缺陷後回到新的 Builder 施工循環修正。

## 考慮過的替代方案

1. 多 Builder 平行寫 main：衝突與狀態漂移風險不可接受。
2. 只靠聊天協調：不可被 repository verifier 查驗。
3. Repository claim + WIP=1：簡單、可重跑且已具自動檢查，因此採用。

## 後果

- Agent 可平行做唯讀研究，但不能同時寫入。
- Claim 到期會使 baseline 失敗，必須合法續期或接手。
- 目前 verifier 已強制 work item/claim 一致；fresh-session review 證據由 V3C-REV-001 首次落實。

## 證據

- `execution/AGENT_CLAIM.json`
- `execution/schemas/agent-claim.schema.json`
- `scripts/verify-control-plane.mjs`
