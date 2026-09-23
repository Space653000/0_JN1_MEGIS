# G6-UI-002 真實 HTTP IR 介面整合補正

> 文件治理
> - 目的：修正 G6-UI-001 歷史證據未證明瀏覽器實際經 HTTP 使用 Python 工程核心的缺口。
> - 目前內容：maturity、本機 HTTP API、React adapter 與瀏覽器／direct HTTP byte-equivalence 均已完成並具 E3 證據。
> - Owner：MEGIS Builder；使用者保有否決權。
> - 回滾邊界：控制面、maturity、HTTP API、web adapter 各自獨立 commit。
> - 最後審查 commit：待本段控制面補正 commit。

## 為何新增補正項

`G6-UI-001` 的 Python 測試證明 `build_ir_via_ui()` 與 `build_ir_via_api()` 兩個同程序函式可產生等價 IR，但沒有證明 React 瀏覽器真的呼叫本機 HTTP API。現行前端仍載入硬編碼的 `synthetic-demo` capability adapter，Run 與 Results 也維持 UI-0 合成流程。

依藍圖「已 done 工作項不重開」原則，保留 `G6-UI-001` 歷史，新增 `G6-UI-002` superseding corrective item。`G6-A11Y-001` 已完成的自動化與人工證據工具仍保留，但在新 UI 固定前改回 planned，避免舊版 UI 的稽核證據被誤用於新介面。

## 固定施工範圍

1. 修正 guided IR 的 maturity 不變量；有 critical unknown 且未完成 package 證據時不得宣告 `PROTOTYPE`。
2. 建立只綁 `127.0.0.1` 的同步 HTTP seam，提供 health、capability、questions 與 canonical IR draft。
3. React 只透過真實 HTTP adapter 取得能力與 IR；API 離線時 fail closed，不退回合成 adapter。
4. 以實際 HTTP bytes 與瀏覽器 request 證明 UI／direct API 等價。

## 明確不在本工項

- 不建立 database、job queue 或 design-run lifecycle。
- 不生成 CAD、BOM、drawing 或 Prototype Package。
- 不提前執行 `G6-E2E-001`、G7 或 G8。
- 不把 IR draft 冒充工程製品或 release artifact。

SQLite／持久化會在完整 job lifecycle 的需求與 migration、backup、rollback acceptance 一起確立後再施工，避免建立半套資料層。

## 驗收次序

`control-plane reconciliation → maturity invariant → HTTP contract → React adapter → browser equivalence → baseline → review`。

## Maturity 補正結果

Guided IR 不再由 builder 直接寫死為 `PROTOTYPE`。`evaluate_guided_maturity()` 現在把實際已具備與尚未具備的證據交給共用 evaluator：requirements／IR schema 已通過，但 critical unknown、layout、geometry、rules、drawing QA 與 package reproducibility 尚未閉合，因此結果固定為 `DRAFT`。

Engineering IR schema 同步補回藍圖既有 maturity state `DRAFT`。測試驗證 reference-only 與 provided PCB 模式在未有執行證據前都不得升至 `PROTOTYPE`，且輸入改變會改變 evaluator digest。

## 本機 HTTP API contract

同步 API 使用 Python 標準函式庫，固定綁定 `127.0.0.1:4174`，不新增第三方 runtime dependency，也不建立 database／queue。端點如下：

| Method | Path | 內容 |
|---|---|---|
| GET | `/api/v1/health` | 服務 readiness |
| GET | `/api/v1/capabilities` | 直接由 `build_manifest()` 產生的完整 capability schema |
| GET | `/api/v1/questions` | 直接由 `guided_questions()` 產生的 11 個問題 |
| POST | `/api/v1/ir-drafts` | 直接由 Python guided flow 產生 canonical Engineering IR bytes |

安全邊界固定檢查 loopback bind、`Host`、`Origin`、JSON content type、64 KiB body 上限、5 秒 socket timeout 與 correlation ID。非信任 host／origin／route 使用 `MEGIS-SYS-002`，格式錯誤使用 `MEGIS-SCH-001`；所有錯誤均回傳結構化 error object。

## React 與瀏覽器等價結果

React production flow 已移除 `synthetic-demo` adapter，改由 `/api/v1/capabilities`、`/api/v1/questions` 與 `/api/v1/ir-drafts` 取得資料。Vite dev／preview 只把 `/api` 代理到 `127.0.0.1:4174`；API 離線、錯誤或逾時時停止建立 IR，不建立合成替代結果。

實際 Chrome 操作以 120 × 80 × 20 mm、2 片 PCB 的同一輸入取得 `DRAFT 2.0.0`、4 個 components、2 個 unsafe unknowns 與 correlation ID。API 在 canonical response bytes 上回傳 `X-Content-SHA256`；瀏覽器顯示值與獨立 direct HTTP 請求重算值同為 `71674fdfab545e3ec38b2b47203179b5403e8dc764412f64f1ca9171ccdda801`。證據見 `artifacts/g6-ui-002/browser-audit.json` 與 `verification.json`。
