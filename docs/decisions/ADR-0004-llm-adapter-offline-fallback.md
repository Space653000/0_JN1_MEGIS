# ADR-0004：LLM 採 adapter 且預設離線

> 文件治理
> - 目的：記錄 D3 的 AI provider 邊界與 deterministic fallback。
> - 目前內容：G6 前無 provider、G6 後仍須可關閉的決策。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D3
- 決策者：V3 藍圖預設，並由現有無 provider 架構確認
- 相關工作項目：V3C-DEC-001、G6-AI-001～004

## 背景

MEGIS 的幾何、規則、成熟度與放行需要 deterministic contracts。LLM 輸出不可成為工程真相；目前也沒有外部 provider、憑證、資料傳輸或成本授權。

## 決策

LLM 必須位於可替換 adapter 後方，預設關閉；G6-AI-001 前不得呼叫真實 provider。無 provider、timeout、rate limit 或 provider failure 時，系統必須回到 deterministic 表單流程，且核心 UI→IR→package 能力不得依賴 LLM 才能工作。

LLM 只可產生 `llm_proposed` requirement、問題、候選方案與說明。未經確認的值不得進入 confirmed IR，也不得直接寫入 geometry、rules、maturity 或 sign-off。

## 考慮過的替代方案

1. 直接綁定單一 provider：造成供應商、網路與資料風險，拒絕。
2. 讓 AI 成為必要流程：破壞離線與可重現性，拒絕。
3. Adapter + 預設關閉 + 表單 fallback：保留 AI 輔助價值又不污染工程真相，因此採用。

## 後果

- 啟用 provider、上傳資料或產生費用仍需使用者明確授權。
- G6 必須建立 schema-bound output、grounding、abstention、KPI 與 prompt-injection 測試。
- AI 關閉模式與 AI 開啟模式都必須通過 E2E。

## 證據

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md`
