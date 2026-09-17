# ADR-0006：禁止客戶與公司工程資料入庫或外送

> 文件治理
> - 目的：記錄 D5 的資料、IP 與外部服務邊界。
> - 目前內容：只允許自建或公開 golden 資料的決策。
> - Owner：MEGIS Builder
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D5
- 決策者：V3 藍圖預設，並由 repository 安全政策確認
- 相關工作項目：V3C-DEC-001、G4-IMP-001、G6-AI-001

## 背景

CAD、datasheet、標準原文與設計參數可能含營業秘密、個資、出口限制或著作權內容。Repository 與未來 AI provider 都不能被當作預設安全的資料接收端。

## 決策

客戶或公司 CAD、drawing、datasheet、BOM、識別資訊與非公開參數不得加入 repository，也不得送往外部服務。Golden、benchmark 與測試 corpus 只使用自建資料、明確可再散布資料，或公開來源的最小必要機械參數與原創摘要。

公開 datasheet 只記錄 URL、料號、版次、取用日期、必要參數與原創摘要；不得為方便而複製完整受保護文件。任何例外需要資料擁有者授權、範圍化 ADR 與 sign-off。

## 考慮過的替代方案

1. 先收資料再人工清理：容易把敏感內容寫入 Git history，拒絕。
2. 私有 repository 即可任意存放：私有性不等於授權與合規，拒絕。
3. 預設禁止，只用自建或公開最小資料：風險最低且足以施工，故採用。

## 後果

- Import 與 AI adapter 必須在未來加入隔離、大小、格式與外送控制。
- 規則來源只保存可合法保存的摘要與 reference metadata。
- 發現疑似敏感資料時停止處理並登記 blocker，不自行上傳或發布。

## 證據

- `AGENTS.md`
- `docs/PRODUCT.md`
- `docs/RULE_SOURCES.md`
