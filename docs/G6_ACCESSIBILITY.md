# G6-A11Y-001 無障礙驗證計畫與紀錄

> 文件治理
> - 目的：保存 WCAG 2.2 AA 自動化結果與真人鍵盤、螢幕閱讀器抽查紀錄。
> - 目前內容：自動化範圍、已修正項目、人工抽查紀錄器、驗證步驟與未完成邊界。
> - Owner：MEGIS Builder；真人抽查者須具名，使用者保有否決權。
> - 最後審查 commit：`50b50df2e1a13f006326406b1a50c2d0e125db96`。

## 目前狀態

`G6-A11Y-001` 目前為 `in_progress`；依賴的 `G6-UI-002` 已完成。既有 schema、紀錄器與 verifier 保留，但舊 UI 的自動化與 Chrome 稽核只算歷史證據；必須針對新的真實 HTTP UI 重跑自動化、瀏覽器及真人鍵盤／螢幕閱讀器抽查。在完整新證據形成前不得標記完成，也不得解鎖 G6-USE-001。

## 自動化範圍

- `axe-core 4.10.3`：`wcag2a`、`wcag2aa`、`wcag21aa`、`wcag22aa` 規則。
- 路由：`/progress`、`/design`、`/review`、`/results`、`/roadmap`。
- jsdom 無實際 layout/canvas，`color-contrast` 規則在 axe run 中停用；另以 WCAG 公式驗證 8 組核心文字／狀態色，實際瀏覽器仍須人工複核。
- 鍵盤契約：skip link、SPA route focus、`aria-current`、行動導覽 Escape、Tab／Shift+Tab 焦點循環、choice `aria-pressed`。
- Pipeline：frontend tests、ESLint、TypeScript、production build。

## 本段修正

- 新增「跳至主要內容」skip link，以及路由切換後將焦點移到 `<main>`。
- 導覽目前頁加入 `aria-current="page"`；行動選單加入 `aria-expanded`／`aria-controls`。
- 行動選單開啟後聚焦關閉鍵，Escape 關閉並回到開啟鍵；Tab 在選單內循環。
- PCB／USB-C 選擇卡加入 `aria-pressed` 與具名 group。
- 工作佇列表格補齊 row／columnheader／cell roles。
- 模擬進度加入 `aria-live`、`aria-busy`，裝飾性動畫元素不重複朗讀。
- input、textarea、select 補齊可見 focus ring；reduced-motion 同時縮短 animation。

## 真人鍵盤抽查表（pending）

抽查者、日期、瀏覽器版本與實際結果不得由 Agent 代填。

人工紀錄必須由實際執行者使用 write-once 紀錄器填寫。紀錄器要求先輸入具名 reviewer、環境版本及逐字 `YES` 接受個人執行聲明，再逐項收集 6 個鍵盤與 6 個螢幕閱讀器結果；只接受 `passed`／`failed`，且 `failed` 必須附人工觀察。它不提供覆寫參數，也不會替人產生或簽署紀錄。

```powershell
.\.venv\Scripts\python.exe scripts\record_g6_a11y_manual.py --output artifacts\g6-a11y-001\manual-audit.json
```

若輸出已存在，紀錄器會 fail closed；需要重測時應保留舊紀錄並指定新的版本化檔名，不得覆蓋歷史證據。實際執行者完成紀錄後再執行：

```powershell
.\.venv\Scripts\python.exe scripts\verify_g6_a11y_manual.py --require-complete --input <倉庫內的真人紀錄.json> --output artifacts\g6-a11y-001\manual-audit-verification.json
```

驗證器要求 12 個固定檢查 ID、具名 reviewer、帶時區時間、瀏覽器／作業系統版本與個人執行聲明。重複／缺漏 ID、額外欄位、完成狀態含 pending、失敗卻無 notes、路徑超出工作區，全部 fail closed；驗證器不會補值或替人簽名。

紀錄器本身已有 10 項自動化測試，驗證 12 個 section-qualified check、成功與失敗狀態、失敗備註、非 canonical 結果、拒絕聲明、工作區邊界及禁止覆寫。這些測試只證明收集工具的契約，不是人工稽核結果。

`/progress` 的驗收 disclosure 會直接列出目前工項已備妥的支援證據與 `verificationCommands`。支援材料與 acceptance evidence 分區呈現：即使 schema、範本、測試與 verifier 均存在，只要人工紀錄仍 pending，頁面就必須顯示「待施工驗證」與「G6 尚未完成」，不得用檔案存在取代人工通過。

| 路徑／情境 | 驗證步驟 | 預期 | 結果 |
|---|---|---|---|
| 全站首個焦點 | 只用 Tab 進入頁面 | skip link 可見且 Enter 移至主要內容 | pending |
| 桌面導覽 | Tab／Shift+Tab 走訪導覽 | 次序合理、焦點清楚、目前頁可辨識 | pending |
| 行動導覽 | 開啟後 Tab、Shift+Tab、Escape | 焦點不逃出、Escape 返回開啟鍵 | pending |
| `/design` | 不用滑鼠修改尺寸、PCB、select、textarea | 全部控制項可操作且狀態可辨識 | pending |
| `/review` | 勾選確認、返回、執行 | 禁用／啟用狀態與焦點順序正確 | pending |
| `/progress` | 展開／收合驗收證據 | `aria-expanded` 與內容同步 | pending |

## 實際瀏覽器代理稽核（passed，非人工證據）

2026-09-22 以實際 Chrome、1536×729 viewport、`http://127.0.0.1:4173` 完成八項代理自動化稽核。`/progress` 最新控制面、landmarks、skip link target、目前頁 `aria-current`、驗收 disclosure，以及 `/design` 的 SPA route focus、choice semantics、桌面水平溢位均通過；結構化紀錄位於 `artifacts/g6-a11y-001/browser-audit.json`。

此紀錄只補強 jsdom 沒有真實瀏覽器 layout 的缺口，不代表真人從頭到尾的鍵盤操作，也沒有啟用 NVDA、JAWS、Narrator 或 VoiceOver。因此下方兩張真人抽查表及 `closureEligible: false` 均保持不變。

## 真人螢幕閱讀器抽查表（pending）

至少記錄 screen reader 名稱、版本、瀏覽器、作業系統、抽查者與日期。

| 路徑／情境 | 預期朗讀 | 結果 |
|---|---|---|
| 全站 landmarks | header、主要導覽、main、各頁 H1 可被定位 | pending |
| `/design` form | label、單位、選取狀態與阻擋原因可理解 | pending |
| `/review` | unknown／critical 與確認 checkbox 可理解 | pending |
| `/run` | busy 狀態與完成狀態適度公告、不重複朗讀動畫 | pending |
| `/results` | Synthetic demo data 與 No engineering artifact generated 被朗讀 | pending |
| `/progress` | 目前工項、狀態、表格欄位與展開內容可理解 | pending |

## 封板規則

只有下列條件同時成立才可把 G6-A11Y-001 設為 `done`：自動化維持全綠、真人鍵盤表完成、真人螢幕閱讀器表完成、人工紀錄通過 `--require-complete` 驗證、發現問題均修正或有具名 blocker。`artifacts/g6-a11y-001/verification.json` 的 `closureEligible` 在此之前必須保持 `false`。
