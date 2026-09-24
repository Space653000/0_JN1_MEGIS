# 驗收標準（本專案精簡入口）

> 文件治理
> - 目的：定義「什麼才算完成」的共通標準，並索引各 Gate 目前的驗收狀態。本檔不取代 `docs/ACCEPTANCE.md`（正式 Gate 驗收索引）或藍圖 §25，只做精簡入口與交叉核對。
> - 目前內容：證據等級定義、work item／Gate 完成定義、目前各 Gate 驗收狀態表、已知例外。
> - Owner：Claude Code（研究／規劃／審查角色，見 [CLAUDE_REVIEWER.md](CLAUDE_REVIEWER.md)）
> - 最後盤點日期：2026-09-24（對照 `docs/ACCEPTANCE.md` 最後審查 commit `d27d16e`）

## 1. 證據等級（藍圖 §5.12，不得跳級引用）

| 等級 | 定義 | 可否單獨作為驗收依據 |
|---|---|---|
| E0 | 只有敘述 | 否 |
| E1 | 產物存在 | 否 |
| E2 | 本機自動化檢查通過並記錄命令與結果 | 一般 work item `done` 的最低要求 |
| E3 | 獨立環境（乾淨 checkout／CI）重跑通過 | golden／envelope／rules／maturity／package 相關 work item、Gate 完成條件 |
| E4 | 決策紀錄（依 D6：施工者自我審查後記錄；`engineering_review` 類型限具名工程師） | Gate acceptance、規則來源核准、envelope 變更 |

## 2. Work item 完成定義（摘自藍圖 §25.2，重點項）

一個工作項目只有在以下全部成立才是 `done`：

1. 需求與驗收條件可追溯；修改前 baseline 已記錄。
2. 程式、schema、tests、文件同步更新；相關自動測試、golden／negative／boundary regression 通過。
3. 產出 artifact 已實際檢查內容，不只是確認檔案存在。
4. 沒有新增未記錄的假設或風險；migration／rollback 邊界明確。
5. `PROJECT_STATE.md` 與 `WORK_QUEUE.yaml` 已更新；evidence 可由另一個 Agent session 重跑。
6. 證據達到該項目要求的最低等級；需要自我審查者，審查報告為 `passed`。
7. 新產生的 manifest 符合 classification／maturity 規則（測試用製品不得帶成熟度）。
8. 未違反 artifact 大小預算；claim 已釋放、handoff 已寫。

## 3. Gate 完成定義（摘自藍圖 §25.3）

- 所有完成條件（Exit criteria）達到 E3 以上。
- `Gx-REV-001`：施工者以全新 session、乾淨 checkout 自我審查 passed，且 CI 對同一 commit 全綠。
- `Gx-ACC-001`：`gate_acceptance` 決策紀錄（E4），使用者可否決。
- `docs/ACCEPTANCE.md` 已登錄該 Gate、commit、review、決策紀錄。

## 4. 目前各 Gate 驗收狀態（詳細請以 `docs/ACCEPTANCE.md` 為準）

| Gate | 狀態 | 審查 | 決策紀錄 |
|---|---|---|---|
| UI-0A～D | accepted | `V3C-REV-001`（2026-09-18，passed） | `V3C-ACC-001`（2026-09-21） |
| G0 | accepted | `V3C-REV-001` | `SO-0001`（2026-09-19） |
| G1 | accepted | `G1-REV-001`（2026-09-21） | `SO-0002`（2026-09-21） |
| G2 | accepted | `G2-REV-001`（2026-09-21，乾淨 checkout 92 tests + 4 script） | `SO-0003`（2026-09-21，E4） |
| G3 | accepted | `G3-REV-001`（2026-09-22，159 tests + 6 script 95 checks） | `SO-0004`（2026-09-22，E4） |
| G4 | accepted | `G4-REV-001`（2026-09-22，115 tests + 3 script 90 checks） | `SO-0005`（2026-09-22，E4） |
| G5 | accepted | `G5-REV-001`（2026-09-22，77 tests，三方 fingerprint 全等） | `SO-0006`（2026-09-22，E4） |
| G6 | **active，尚未 accepted** | 尚未執行 `G6-REV-001`（依賴 `G6-A11Y-001`、`G6-USE-001`、`G6-E2E-001` 先完成） | 尚未執行 `G6-ACC-001` |
| G7／G8／G9 | planned | — | — |

## 5. 阻擋 G6 Gate acceptance 的已知缺口

1. **`G6-A11Y-001`（in_progress）**：自動化（axe、鍵盤／焦點契約、瀏覽器代理稽核、write-once 人工紀錄器）已完成，但藍圖要求的 **6 個鍵盤 + 6 個螢幕閱讀器「具名真人」抽查尚未簽錄**。這是唯一登記中的阻塞：`B-G6-A11Y-HUMAN-001`（`execution/BLOCKERS.yaml`），owner 為「實際無障礙抽查者（具名）」。**Agent 產生的證據不得取代真人簽錄**——這是刻意設計，不是遺漏。
2. **`G6-USE-001`（planned）**：需要 ≥ 5 位非 CAD 背景參與者的真人可用性測試，同樣不能由 Agent 代理完成。
3. **`G6-E2E-001`、`G6-REV-001`、`G6-ACC-001`（planned）**：依序依賴前兩項完成後才能開始。

**因此 G6 Gate acceptance 的唯一路徑，是取得具名真人的無障礙抽查與可用性測試證據；這是流程設計上的人工關卡，不是本次盤點發現的問題。**

## 6. 控制面一致性核對（2026-09-24）

- `execution/PROJECT_STATE.md` 標頭、`execution/WORK_QUEUE.yaml` 與 `execution/AGENT_CLAIM.json` 均指向 `G6-A11Y-001`；前版所述 `G6-UI-002` 不一致已不再存在。
- 修改前 baseline 發現 `AGENT_CLAIM.json` 期限已過；Codex 依藍圖 §5.5 記錄後續領，並重跑控制面與完整驗證。這不構成 `G6-A11Y-001` 的真人驗收證據。

## 7. 誰來判定「驗收通過」

依 D6 與本次新增角色（見 [CLAUDE_REVIEWER.md](CLAUDE_REVIEWER.md)）：施工者對自己完成的工作項目自我審查；Claude Code 在此專案額外擔任研究／規劃／審查／驗收角色，可對任一 Agent 的施工結果進行獨立核對，但最終 Gate acceptance 與否決權在使用者。
