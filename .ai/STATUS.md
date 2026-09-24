# 專案現況（已完成／施工中／未完成／阻塞）

> 文件治理
> - 目的：單一頁面回答「現在做到哪裡、卡在哪裡」，供每次工作開場快速定位。
> - 目前內容：2026-09-24 控制面與 GitHub 分支核對結果；後續提交以本段驗證紀錄為準。
> - Owner：Claude Code（研究／規劃／審查角色，見 [CLAUDE_REVIEWER.md](CLAUDE_REVIEWER.md)）
> - 資料來源：`execution/WORK_QUEUE.yaml`、`execution/PROJECT_STATE.md`、`docs/ACCEPTANCE.md`、`execution/BLOCKERS.yaml`、GitHub（`gh` CLI 查詢）。

## 0. 本次盤點最重要的發現：GitHub `main` 落後於實際進度

- 2026-09-24 開工快照：本地與遠端施工分支 **`codex/g1-req-001-research`** 同為 `c1f02e8`；GitHub **`main`** 停在 `2d74b37`，落後施工分支 **54 個 commit**。交付後須重新比對 SHA。
- 這些 commit 涵蓋 G4-MOD-002 之後的 G4、G5 全部、G6 UI／QST／AI／A11Y 準備段與 `.ai/` 治理入口。
- **沒有開啟中的 Pull Request**（`gh pr list` 為空），兩分支之間沒有合併計畫在途。
- 影響：只看 GitHub `main` 會看到 G4 中段的舊狀態，看不到 G5、G6 與 `.ai/` 治理入口。`.github/workflows/baseline-ci.yml` 的 push trigger 只包含 `main`；施工分支尚須經 PR 或 `main` CI 驗證。
- 本次同步以目前施工分支為目標；`main` 的整合方式待使用者另行指定。

## 1. 藍圖與治理文件

| 項目 | 狀態 |
|---|---|
| v3 藍圖（生效版本） | 存在、完整，`README.md` 與 `docs/DECISIONS.md` 皆指向它 |
| v1／v2 藍圖 | 封存保留，未刪除 |
| `.ai/BLUEPRINT.md`、`.ai/ACCEPTANCE.md`、`.ai/STATUS.md`、`.ai/CLAUDE_REVIEWER.md`、`.ai/CODEX_WORKER.md`、`AGENTS.md`、`CLAUDE.md` | 雙 Agent 角色與施工入口已建立／更新 |
| ADR 數量 | 11（`docs/decisions/ADR-0001`～`ADR-0011`） |
| 決策紀錄（sign-off） | 6（`SO-0001`～`SO-0006`），對應 UI-0／G0～G5 accepted |

## 2. Gate 層級狀態

| Gate | 狀態 | 備註 |
|---|---|---|
| UI-0A～D | ✅ accepted | 誠實 UX 原型，合成資料，已驗收 |
| G0 基礎建設與可行性 | ✅ accepted | 11 項全 done |
| G1 工程契約與黃金案例 | ✅ accepted | |
| G2 治具幾何垂直切片 | ✅ accepted | |
| G3 規則與驗證 | ✅ accepted | |
| G4 模組與限制條件組合 | ✅ accepted | |
| G5 原型套件與可重現性 | ✅ accepted | |
| **G6 引導式介面與 AI 輔助** | 🔧 **active，唯一未完成 Gate** | 見下方明細 |
| G7 聲學薄切片 | ⏳ planned | 依賴 G6 accepted |
| G8 機器人薄切片 | ⏳ planned | 依賴 G6 accepted |
| G9 強化與擴充 | ⏳ planned | 依賴 G7＋G8 |

## 3. 工作佇列統計（`execution/WORK_QUEUE.yaml`）

- 總計 **75** 個工作項目：**63 已完成 `done`**、**1 施工中 `in_progress`**、**11 規劃中 `planned`**（2026-09-24 直接解析 `execution/WORK_QUEUE.yaml`）。

### G6 明細（唯一有 in_progress／planned 混合的 Gate）

| 工作項目 | 狀態 | 說明 |
|---|---|---|
| G6-UI-001 | ✅ done | capability-driven guided flow |
| G6-QST-001 | ✅ done | deterministic question ordering／abstention |
| G6-AI-001～004 | ✅ done | provider adapter、Requirement 萃取、評估語料、grounded explanation |
| G6-UI-002 | ✅ done | 補正真實 HTTP IR 介面整合（修正 G6-UI-001 的合成 adapter 問題） |
| **G6-A11Y-001** | 🔧 **in_progress** | 自動化（axe、鍵盤契約、瀏覽器代理稽核、write-once 紀錄器）已完成；**具名真人的 6 項鍵盤 + 6 項螢幕閱讀器抽查尚未簽錄** |
| G6-USE-001 | ⏳ planned | 需要 ≥5 位非 CAD 背景真人可用性測試 |
| G6-E2E-001 | ⏳ planned | 依賴 G6-A11Y-001、G6-USE-001 |
| G6-REV-001 | ⏳ planned | G6 自我審查（乾淨 checkout） |
| G6-ACC-001 | ⏳ planned | G6 Gate acceptance 決策紀錄 |

其餘 planned 項目為 G7（`G7-ACO-001`、`G7-SOL-001`、`G7-REV-001`、`G7-ACC-001`）與 G8（`G8-ROB-001`、`G8-REV-001`、`G8-ACC-001`），皆依賴 G6 accepted 才能開始。

## 4. 唯一登記中的阻塞（`execution/BLOCKERS.yaml`）

| ID | 內容 | Owner | 解除方式 |
|---|---|---|---|
| `B-G6-A11Y-HUMAN-001` | 具名真人完成 6 項鍵盤＋6 項螢幕閱讀器抽查 | 實際無障礙抽查者（具名，尚未指定） | 由真人使用 write-once 紀錄器（`scripts/record_g6_a11y_manual.py`）完成並簽錄；Agent 證據不得取代 |

**這是目前整條施工鏈唯一的真正阻塞**：G6-A11Y-001 → G6-USE-001 → G6-E2E-001 → G6-REV-001 → G6-ACC-001 → G7／G8 全部依序卡在「需要具名真人參與」這一點上。

## 5. 控制面核對與基準

1. `execution/PROJECT_STATE.md` 標頭與 `execution/WORK_QUEUE.yaml` 均指向 `G6-A11Y-001`；前版快照所述 `G6-UI-002` 標頭問題已不再存在。`PROJECT_STATE.md` 歷史段落仍保留當時的施工過程。
2. `execution/AGENT_CLAIM.json` 已指向 `G6-A11Y-001`，但 2026-09-24 14:15 (+08:00) 修改前 baseline 發現 claim 期限已過，`verify-control-plane.mjs` 因而拒絕執行。Codex 依藍圖 §5.5 續領該項 claim；不改變工項完成狀態。
3. 本地另有 7 個未追蹤的 `G6-USE-001` 協定、schema、工具與測試檔；它們屬前置材料，尚未納入本次提交，也不是 ≥5 位真人測試證據。
4. 續領 claim 後執行 `scripts/run-baseline-ci.ps1`：控制面、secret scan（516 tracked files／0 potential secrets）、artifact policy、工具鏈、629 個 Python tests（含未追蹤檔中的 12 個測試）、25 個前端測試、lint、typecheck、maturity、13 筆 artifact smoke 與 production build 均通過。此結果證明目前程式與文件修改未破壞基準，不代表真人驗收完成。

## 6. 本機工作目錄快照（Python／前端套件結構，供定位用）

```text
megis/            核心程式（adapters, ai, api, benchmark, composition, contracts,
                   determinism, envelope, errors, geometry, governance, guides,
                   importing, maturity, module, package, relationship, rules, validation）
tests/            50 個測試檔
schemas/          41 個 JSON Schema
contracts/        G1～G6 golden／holdout／template 語料
scripts/          34 個驗證／工具腳本
docs/             40+ 份 Gate 施工文件、決策、政策文件
docs/decisions/   11 個 ADR
execution/        狀態檔、審查報告、決策紀錄
outputs/          49 份逐日完工／盤點進度報告（2026-09-17～2026-09-23）
apps/web/         UI-0 前端（React + TypeScript + Vite）
MEGIS_Blueprint/  v1／v2／v3 藍圖（v3 為生效版本）
```

## 7. 下一步（依藍圖依賴順序，僅供參考，本次盤點不執行）

1. 指定具名真人完成無障礙抽查（`B-G6-A11Y-HUMAN-001`）與可用性測試（`G6-USE-001`）——**這是目前推進 G6 唯一需要使用者或其指定人員介入的環節**。
2. 完成 `G6-E2E-001`、`G6-REV-001`、`G6-ACC-001`，G6 Gate 正式 accepted。
3. 決定 `codex/g1-req-001-research` 與 `main` 的分歧如何處理（合併／PR／改變預設分支），見第 0 節。
4. G6 accepted 後依序進入 G7（聲學）、G8（機器人）、G9（強化）。
