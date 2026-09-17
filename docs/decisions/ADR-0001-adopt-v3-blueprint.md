# ADR-0001：採用 MEGIS v3.0-claude-code 藍圖

> 文件治理
> - 目的：記錄 V3 藍圖採用決策及後果。
> - 目前內容：已接受的 V3C 遷移策略與證據。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

- 狀態：accepted
- 日期：2026-09-17
- 決策者：使用者
- 相關工作項目：V3C-BCR-001

## 背景

Repository 已依 v2.0 完成 UX-0、G0、G1，以及 G2-CAD-001～003。使用者指定 `MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md` 為新的施工目標，並要求持續在 `C:\0_JN1_MEGIS` 內施工、逐段提交及同步 GitHub。

## 決策

自本決策起，v3.0-claude-code 是主要規範；v2.0 與 v1.0 僅保留為歷史基線。依 v3 §0.6：

- 已完成的 work item 與已 accepted Gate 不重開、不改寫歷史。
- 新增九個 `V3C-*` work item，掛在目前 active 的 G2。
- `V3C-ACC-001` 完成前不得接受 G2。
- 所有 v3 §26.3～§26.11 的必要 ID 納入機器可驗證清單；對既有 accepted Gate 的差距由 V3C lane 追溯、補強或建立承接項目。
- D6、D7、D8 依使用者已作成的決定記錄；其他 G0 決策在 `V3C-DEC-001` 補齊。

## 考慮過的替代方案

1. 重設 repository 並從 G0 重做：會破壞已驗證歷史，違反 v3 遷移規則。
2. 直接繼續 G2-CAD-004、延後導入：會讓新 Gate 證據繼續建立在舊控制面上。
3. 採 V3C 補強線：保留既有證據，同時阻擋 G2 過早接受，故採用。

## 後果

短期先完成 V3C 控制面、文件、決策、fingerprint、maturity、artifact policy 與追溯審查；其後才恢復 G2-CAD-004。`ENGINEERING_REVIEWED` 與 `RELEASED` 在沒有具名工程師前仍不可達。

## 證據

- `MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md`
- `execution/WORK_QUEUE.yaml`
- `execution/schemas/v3-required-work-items.json`
- `scripts/verify-control-plane.mjs`
