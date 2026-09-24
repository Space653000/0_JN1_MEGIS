# 專案現況（已完成／施工中／未完成／阻塞）

> 文件治理
> - 目的：單一頁面回答「現在做到哪裡、卡在哪裡」，供每次工作開場快速定位。
> - 目前內容：2026-09-24 全面盤點（本地 repository ＋ GitHub）結果。
> - Owner：Claude Code（研究／規劃／審查角色，見 [CLAUDE_REVIEWER.md](CLAUDE_REVIEWER.md)）
> - 資料來源：`execution/WORK_QUEUE.yaml`、`execution/PROJECT_STATE.md`、`docs/ACCEPTANCE.md`、`execution/BLOCKERS.yaml`、GitHub（`gh` CLI 查詢）。

## 0. 本次盤點最重要的發現：GitHub `main` 落後於實際進度

- 本地與遠端目前檢出分支：**`codex/g1-req-001-research`**（本地與 `origin/codex/g1-req-001-research` 完全同步，commit `aeb2899`）。
- GitHub **`main`** 分支停在 commit `2d74b37`（`chore: close G4-GRF-001 and start G4-MOD-002`，2026-09-22），**落後 `codex/g1-req-001-research` 46 個 commit**。
- 這 46 個 commit 涵蓋：G4-MOD-002 之後全部內容 → G5 全部（PKG／BOM／DRW／REP／REV／ACC）→ G6 全部（UI-001／QST-001／AI-001～004／UI-002／A11Y-001 準備段）。
- **沒有開啟中的 Pull Request**（`gh pr list` 為空），兩分支之間沒有合併計畫在途。
- 影響：任何人只看 `https://github.com/Space653000/0_JN1_MEGIS/tree/main` 會看到**遠遠落後的舊狀態**（大約停在 G4 中段），看不到 G5、G6 的全部工作與本次新增的 `.ai/` 文件。GitHub Actions 的 `Baseline CI` 只在 push 到 `main` 時觸發，因此 `codex/g1-req-001-research` 上的 46 個 commit **沒有任何一次由 GitHub Actions 驗證過**（`.github/workflows` 的 `on.push.branches` 只列 `main`）。
- 本次盤點**不主動合併分支**（使用者要求「先不要施工」，合併／改變 main 屬於重大且不可逆的 repository 操作）。是否要把 `codex/g1-req-001-research` 合併／fast-forward 到 `main`，或改成用 PR 走一次 CI，需要使用者決定。

## 1. 藍圖與治理文件

| 項目 | 狀態 |
|---|---|
| v3 藍圖（生效版本） | 存在、完整，`README.md` 與 `docs/DECISIONS.md` 皆指向它 |
| v1／v2 藍圖 | 封存保留，未刪除 |
| `.ai/BLUEPRINT.md`、`.ai/ACCEPTANCE.md`、`.ai/STATUS.md`、`.ai/CLAUDE_REVIEWER.md`、`CLAUDE.md` | **本次盤點新增／改版** |
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

- 總計 **75** 個工作項目：**62 已完成 `done`**、**1 施工中 `in_progress`**、**12 規劃中 `planned`**。

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

## 5. 本次盤點發現、但刻意不修正的控制面小問題

（因使用者指示「現在先不要施工」，以下只記錄，不動手改）

1. `execution/PROJECT_STATE.md` 標頭仍寫「目前工項：`G6-UI-002`（in_progress）」，但實際已 `done`、真正 in_progress 是 `G6-A11Y-001`。
2. `execution/AGENT_CLAIM.json` 仍宣稱持有 `G6-UI-002` 的施工鎖（`claimed_at 2026-09-23T09:00`），該項目已完成，理論上應已釋放。
3. `.git` 倉庫大小 2.3 MB，屬合理範圍，無異常膨脹。

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
