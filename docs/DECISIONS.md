# 決策索引

> 文件治理
> - 目的：集中索引架構、流程與產品決策。
> - 目前內容：V3 採用、D1–D9、重型 artifact 白名單、既有工具鏈決策入口；G0-DEC-001 已以 D1–D9 ADR 收斂。
> - Owner：MEGIS Builder
> - 最後審查 commit：`4358333b5e9f8c7a218a773f6cee0e8012a2f634`

## 目的

集中列出 MEGIS 的架構、流程與產品決策，讓施工狀態、實作與證據可互相追溯。此索引不取代各 ADR 內容。

## 現有決策

- [ADR-0001：採用 MEGIS v3.0-claude-code 藍圖](decisions/ADR-0001-adopt-v3-blueprint.md) — accepted，V3C-BCR-001。
- [ADR-0011：既有 G0 重型製品精確白名單](decisions/ADR-0011-legacy-heavy-artifact-allowlist.md) — accepted，V3C-ART-001。
- [G0 工具鏈版本與平台決策](decisions/toolchain.md) — 既有 v2 基線。

## V3 §8.1 決策

| ID | 決策 | ADR | 實作狀態 |
|---|---|---|---|
| D1 | 本機 single-user | [ADR-0002](decisions/ADR-0002-local-single-user-deployment.md) | enforced |
| D2 | COMSOL `out_of_scope` | [ADR-0003](decisions/ADR-0003-comsol-out-of-scope.md) | enforced |
| D3 | LLM adapter、G6 前無 provider、離線 fallback | [ADR-0004](decisions/ADR-0004-llm-adapter-offline-fallback.md) | partially_enforced |
| D4 | GitHub Actions Windows x64；驗證後可推 main；禁止 force | [ADR-0005](decisions/ADR-0005-windows-ci-and-main-push.md) | enforced |
| D5 | 客戶／公司工程資料不得入庫或外送 | [ADR-0006](decisions/ADR-0006-protect-customer-engineering-data.md) | partially_enforced |
| D6 | 施工者以全新 session 自我審查；無具名工程師 | [ADR-0007](decisions/ADR-0007-builder-self-review.md) | partially_enforced |
| D7 | 同時只有一個 Builder claim；同 Agent 分離審查 | [ADR-0008](decisions/ADR-0008-single-builder-agent-claim.md) | enforced |
| D8 | 施工者以公開可查證來源研究 unknown | [ADR-0009](decisions/ADR-0009-research-reference-unknowns.md) | policy_only |
| D9 | Design Run 90 天；golden 永久 | [ADR-0010](decisions/ADR-0010-artifact-retention.md) | policy_only |

機器可讀索引：`execution/decisions/g0-decisions.json`。`implementationStatus` 明確區分「決策已接受」與「執行機制已完成」，不得以 ADR 取代後續 work item。

`G0-DEC-001`（G0 主線）已於 2026-09-19 以本索引的 D1–D9 ADR 與既有決策證據閉合，記錄見 `artifacts/g0-dec-001/verification.json`；決策已接受不取代各 follow-up work item。

## 維護責任

- Owner：施工 Agent。
- 新的技術基線、envelope、fingerprint、maturity、角色或驗收範圍變更必須建立新 ADR。
- 被取代的 ADR 保留並指向取代它的 ADR。
- 最後檢視基準：`4358333b5e9f8c7a218a773f6cee0e8012a2f634`。
