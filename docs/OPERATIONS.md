# 維運手冊

> 文件治理
> - 目的：定義本機重建、驗證、備份、還原與故障處理。
> - 目前內容：Windows local single-user 的可執行操作邊界。
> - Owner：MEGIS Maintainer
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 目的

所有操作留在 `C:\0_JN1_MEGIS`，服務只綁 `127.0.0.1`，遠端只同步指定 GitHub repository。

## 目前內容

重建依 `README.md`、`requirements.lock`、`apps/web/package-lock.json` 與 `environment/toolchain.lock.json`。完整健康檢查執行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-baseline-ci.ps1
```

施工前讀取 state／queue／blockers／claim；claim 過期時先記錄 handoff，再由新 Builder 以目前 green commit 接手。Git 同步前 fetch 並確認無分歧，推送後核對本機與 `origin/main` SHA。

## 備份與還原

版本化內容以 GitHub `main` 為異地副本；`.runs/` 與未版本化重型 artifact 不受 Git 保護，需由使用者另行備份。還原時先 clone 到核准工作區，依 lockfiles 重建，再跑 baseline；不得從另外兩個 JN1 專案共用環境或 cache。

## 故障處理

- CI 紅：保留綠色 fixed point，讀取失敗 job，不降低測試。
- claim／state 不一致：停止寫入，依 Git history 與重跑證據 reconcile。
- CAD adapter crash：轉為 structured error；不得留下看似成功 artifact。
- 破壞性刪除、history rewrite 或權限變更：先取得使用者明確授權。

## Owner

MEGIS Maintainer；破壞性操作仍由使用者授權。

## 最後審查 commit

`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`
