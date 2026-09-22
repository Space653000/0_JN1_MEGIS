# G6-A11Y-001 無障礙驗證計畫與紀錄

> 文件治理
> - 目的：保存 WCAG 2.2 AA 自動化結果與真人鍵盤、螢幕閱讀器抽查紀錄。
> - 目前內容：自動化範圍、已修正項目、人工抽查步驟與未完成邊界。
> - Owner：MEGIS Builder；真人抽查者須具名，使用者保有否決權。
> - 最後審查 commit：`19685b6512cd693cfb098d42942d7bf50df99b6e`。

## 目前狀態

`G6-A11Y-001` 維持 `in_progress`。自動化檢查已通過，但藍圖明定還需要真人鍵盤與螢幕閱讀器抽查；在兩份真人證據完成前，不得標記工作項完成，也不得解鎖依賴它的 G6-USE-001。

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

| 路徑／情境 | 驗證步驟 | 預期 | 結果 |
|---|---|---|---|
| 全站首個焦點 | 只用 Tab 進入頁面 | skip link 可見且 Enter 移至主要內容 | pending |
| 桌面導覽 | Tab／Shift+Tab 走訪導覽 | 次序合理、焦點清楚、目前頁可辨識 | pending |
| 行動導覽 | 開啟後 Tab、Shift+Tab、Escape | 焦點不逃出、Escape 返回開啟鍵 | pending |
| `/design` | 不用滑鼠修改尺寸、PCB、select、textarea | 全部控制項可操作且狀態可辨識 | pending |
| `/review` | 勾選確認、返回、執行 | 禁用／啟用狀態與焦點順序正確 | pending |
| `/progress` | 展開／收合驗收證據 | `aria-expanded` 與內容同步 | pending |

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

只有下列條件同時成立才可把 G6-A11Y-001 設為 `done`：自動化維持全綠、真人鍵盤表完成、真人螢幕閱讀器表完成、發現問題均修正或有具名 blocker。`artifacts/g6-a11y-001/verification.json` 的 `closureEligible` 在此之前必須保持 `false`。
