# Claude Code 入口

每次處理本專案任務前，依序讀完以下四份文件，再開始任何動作：

1. [`.ai/CLAUDE_REVIEWER.md`](.ai/CLAUDE_REVIEWER.md) — Claude Code 在本專案的角色：研究、規劃、審查、驗收；與藍圖既有「誰做誰審查」機制的關係。
2. [`.ai/BLUEPRINT.md`](.ai/BLUEPRINT.md) — 本專案唯一藍圖依據的索引（目前生效版本、章節導覽、與既有控制面文件的對照）。
3. [`.ai/ACCEPTANCE.md`](.ai/ACCEPTANCE.md) — 驗收標準：證據等級、work item／Gate 完成定義、目前各 Gate 驗收狀態。
4. [`.ai/STATUS.md`](.ai/STATUS.md) — 目前已完成／施工中／未完成／阻塞的最新現況（含 GitHub 分支狀態）。

再讀 [AGENTS.md](AGENTS.md)：語言、工作區邊界、Git 政策、UI-0 邊界與安全限制的單一真相來源，優先於本檔與上述四份文件中任何看似衝突的敘述。

## 涉及實際施工時

除以上五份文件外，額外讀取當下狀態：`execution/PROJECT_STATE.md`、`execution/WORK_QUEUE.yaml`、`execution/BLOCKERS.yaml`、`execution/AGENT_CLAIM.json`，以及最近的 handoff／review。使用 `README.md` 指向的 V3 藍圖（`.ai/BLUEPRINT.md` 已索引路徑）；較舊版本的藍圖只作封存基線，不作施工依據。

