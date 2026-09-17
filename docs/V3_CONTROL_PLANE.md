# V3 Control Plane 1.1

> 文件治理
> - 目的：說明 V3 control plane 與遷移期強制機制。
> - 目前內容：schema 1.1、claim、verifier、deferral 與負向測試。
> - Owner：MEGIS Builder
> - 最後審查 commit：`92e29c528bb9a635de83eb5ebedac60f9a11d5ae`

## 目的

說明 `V3C-CTL-001` 導入的向後相容 schema、單一 Builder claim，以及 v3 §5.13 控制面檢查如何在既有 repository 遷移期間生效。

## 目前內容

- `execution/schemas/work-queue.schema.json` 接受 `1.0.0` 舊資料與 `1.1.0`，並以選填欄位支援 owner、決策需求、證據等級、review、risk 與 blueprint traceability。
- `execution/AGENT_CLAIM.json` 及其 schema 將唯一在製項目、Builder、有效期間與起始 commit 綁定。
- verifier 檢查必要檔案、74 個必要 ID、唯一與無循環依賴、Gate／WIP／claim 一致、done 證據與 Git SHA、必要 review，以及 accepted Gate review／sign-off。
- `execution/V3_MIGRATION.json` 明列三項暫時延後：必要文件、既有 Gate 追溯審查及簽核。延後只在承接的 V3C 工作尚未完成時有效；承接項目一旦 done，缺件立即使 verifier 失敗。
- GitHub Actions 使用完整 history，讓 CI 能驗證每個 done `commitSha` 確實存在。

## 驗證與負向案例

`tests/test_v3_blueprint_adoption.py` 覆蓋 schema 1.0 相容、claim 不一致、依賴循環、缺少必要 ID、重開既有 done、延後到期、required review 缺失，以及 Git history 中 commit 不存在等控制面失敗模式。

## Owner

施工 Agent（目前為 Codex Builder）。

## 最後審查 commit

`bf152afefbd22e81655566fe5650d6c23d6b2992`（GitHub Actions run `35182065276` passed）。
