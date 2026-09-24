# Codex 施工角色與執行順序

> Owner：使用者。Codex 負責施工、修改、測試與修正；Claude Code 負責藍圖、獨立 Review 與驗收整理，最終驗收由使用者決定。

## 每次開工

1. 依序讀完 [BLUEPRINT.md](BLUEPRINT.md)、[ACCEPTANCE.md](ACCEPTANCE.md)、[STATUS.md](STATUS.md)，再讀它們指向的本次相關藍圖章節與驗收條件。
2. 核對 `execution/PROJECT_STATE.md`、`execution/WORK_QUEUE.yaml`、`execution/BLOCKERS.yaml`、`execution/AGENT_CLAIM.json`、最近的 handoff／review、Git 狀態與遠端分支。佇列與證據優先於過期的狀態敘述。
3. 依藍圖 §5.2、§5.4 選一個依賴已滿足的工作項目，確認單一施工 claim 與 WIP=1。過期 claim 依 §5.5 記錄原因後恢復；其他 Agent 的有效 claim 須先完成交接。
4. 跑相關的修改前 baseline。若失敗，先定位並記錄阻塞，再修復基準；保持工作樹中既有未提交變更。

## 施工與交付

1. 以最小可驗證增量修改程式、schema、測試與文件；遵守 [AGENTS.md](../AGENTS.md) 的工作區與 UI-0 邊界。
2. 執行相關測試、控制面驗證及必要的完整 baseline，核對實際產物與證據。需要具名真人的抽查或可用性測試，只由實際執行者簽錄。
3. 更新 `execution/` 正式控制面及 [STATUS.md](STATUS.md)，清楚標記已完成、施工中、未完成、阻塞、驗證結果與 GitHub 分支狀態。驗收未滿足時保留原工項狀態。
4. 以英文 `type: summary` 訊息 commit 已驗證的一致變更，push 當前 GitHub 分支，重新抓取並比對遠端 SHA。`main` 的合併或推送由使用者另行指定。
5. 將交付證據交給 Claude Code 做獨立 Review 與驗收整理；依藍圖 D6，施工者所需的正式自我審查仍照原有流程執行。

## 目前施工入口

依 [STATUS.md](STATUS.md) 與正式佇列，`G6-A11Y-001` 是唯一在製項目。其完成需要具名真人鍵盤與螢幕閱讀器抽查；`G6-USE-001` 依賴它，不能提前宣稱開工或完成。
