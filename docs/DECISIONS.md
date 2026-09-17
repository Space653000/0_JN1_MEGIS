# 決策索引

> 文件治理
> - 目的：集中索引架構、流程與產品決策。
> - 目前內容：V3 採用 ADR 與既有工具鏈決策入口。
> - Owner：MEGIS Builder
> - 最後審查 commit：`6cc2ad78d237d2c2095d705910a242dcd2b6b2bc`

## 目的

集中列出 MEGIS 的架構、流程與產品決策，讓施工狀態、實作與證據可互相追溯。此索引不取代各 ADR 內容。

## 現有決策

- [ADR-0001：採用 MEGIS v3.0-claude-code 藍圖](decisions/ADR-0001-adopt-v3-blueprint.md) — accepted，V3C-BCR-001。
- [G0 工具鏈版本與平台決策](decisions/toolchain.md) — 既有 v2 基線；其內容會在 V3C-DEC-001 納入 D1–D9 決策架構。

## 維護責任

- Owner：施工 Agent。
- 新的技術基線、envelope、fingerprint、maturity、角色或驗收範圍變更必須建立新 ADR。
- 被取代的 ADR 保留並指向取代它的 ADR。
- 最後檢視基準：V3C-BCR-001（commit 於工作項完成時回填）。
