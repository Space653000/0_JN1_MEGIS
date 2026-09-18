# 維運手冊

> 文件治理
> - 目的：定義本機重建、健康檢查、備份、還原與故障處理的標準程序。
> - 目前內容：Windows local single-user 的可執行操作；secret scan 已納入 baseline CI。
> - Owner：MEGIS Maintainer；破壞性操作由使用者授權
> - 最後審查 commit：`4fa15e27011759b6b29df9a3d97fb095162e7c0c`

## 操作邊界

所有本機寫入留在 `C:\0_JN1_MEGIS`；本機服務只綁 `127.0.0.1`；遠端只同步至指定 GitHub repository。不得與 `C:\0_JN1_AERIS`、`C:\0_JN1_Offline-Local-Voice-Agent` 共用環境、cache、junction 或套件源。

## 重建程序（乾淨 checkout）

```powershell
git clone <repo> C:\0_JN1_MEGIS
cd C:\0_JN1_MEGIS
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --requirement requirements.lock
npm ci --prefix apps\web
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

版本鎖定：Python 3.11.9、Node.js 24.17.0、CadQuery 2.8.0、OpenCascade 7.9.3.1；`requirements.lock`、`apps/web/package-lock.json` 與 `environment/toolchain.lock.json` 為唯一真相。

## 健康檢查

`scripts/run-baseline-ci.ps1` 依序執行並任一步失敗即紅燈：

1. Control plane schema（74 work items、14 gates、claim、deferrals）
2. Secret scan（追蹤檔機密掃描）
3. Artifact policy 負向測試與儲存預算
4. pip check 與鎖定 CAD toolchain smoke
5. Python unit tests
6. Manifest maturity 掃描與 artifact hash smoke
7. 前端 lint／typecheck／unit／build

## 備份與還原

- 版本化內容：GitHub `main` 為異地副本；推送後比對本機與 `origin/main` SHA。
- 未版本化內容：`.runs/`、未列管重型 artifact、本機 `.venv` 與 cache 不受 Git 保護，需另行備份。
- 還原：clone 到核准工作區 → 依 lockfiles 重建 → 跑完整 baseline；不得從 JN1 其他專案共用環境。

## 故障處理

| 觸發 | 處置 |
|---|---|
| CI 紅 | 停在最後 green fixed point，讀失敗 job 修復；不降級測試 |
| claim／state 不一致 | 停止寫入，依 Git history 與重跑證據 reconcile，再續 claim |
| CAD adapter crash | adapter 回傳 structured error；不留看似成功的 artifact |
| Secret scan 命中 | 先輪換該密鑰，再移除來源；只有 intentional fixture 才允許進 allowlist；不得直接刪除 allowlist 規則 |
| 破壞性刪除／history rewrite／權限變更 | 一律先經使用者明確授權 |

## 密鑰衛生

`scripts/verify-secrets.mjs` 在每一次 CI push 掃描 `git ls-files` 追蹤內容，涵蓋 private key、AWS access key、GitHub／Slack／Google token 樣式；命中即紅燈。intentional fixture 必須走 allowlist 並註明用途；本機可另設 pre-commit 對照，repository 不自動安裝 hooks。

## Owner

MEGIS Maintainer；破壞性操作仍由使用者授權。

## 最後審查 commit

`4fa15e27011759b6b29df9a3d97fb095162e7c0c`
