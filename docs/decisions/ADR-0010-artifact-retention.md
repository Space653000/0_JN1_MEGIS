# ADR-0010：Design Run 保留 90 天、golden 永久保留

> 文件治理
> - 目的：記錄 D9 的製品保留週期與例外。
> - 目前內容：已接受 retention policy；自動清理尚未實作。
> - Owner：MEGIS Maintainer
> - 最後審查 commit：`7ab1cad43dadaa2db53e4dfab62c7cfc67096e03`

- 狀態：accepted
- 日期：2026-09-17
- 決策 ID：D9
- 決策者：V3 藍圖預設，並由本機資料管理邊界確認
- 相關工作項目：V3C-DEC-001、V3C-ART-001、G5-PKG-001

## 背景

Design Run 可能包含 STEP、STL、drawing、BOM、manifest 與 log，若無期限保留會造成磁碟與備份膨脹。Golden case 則是 regression oracle，刪除會破壞可重現性與歷史比較。

## 決策

本機 Design Run artifact 自完成時間起保留 90 天；受調查、waiver、sign-off 或使用者明確保留標記約束者暫停到期處理。Golden inputs、預期值、schema、測試 fixture、fingerprint oracle 與其 provenance 永久版本化保留。

自動清理尚未實作。在 V3C-ART-001 與 G5-PKG-001 建立 manifest、分類、dry-run、保留標記與可恢復處置前，不得依本 ADR 直接批次刪除現有資料。

## 考慮過的替代方案

1. 所有 artifact 永久保留：磁碟與 Git 膨脹不可控。
2. 所有 artifact 90 天刪除：會破壞 golden 與稽核證據。
3. Design Run 90 天、golden 永久、例外可 hold：兼顧營運與可重現性，因此採用。

## 後果

- Manifest 必須記錄 classification、建立時間、retention class 與 hold 狀態。
- 清理機制必須預設 dry-run、限制在 repository-local run storage，並產生稽核紀錄。
- Git-tracked golden 不受 Design Run 90 天規則影響。

## 證據

- `docs/OPERATIONS.md`
- `MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md`
