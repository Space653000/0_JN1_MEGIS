# MEGIS

**Mechanical Engineering Generative Intelligence System（機械工程生成式智慧系統）**

MEGIS 的目標，是將機械、聲學與製造工程師的判斷轉化為可追溯、可驗證、可重現的引導式生成工程流程。系統以確定性工程資料、規則、受限幾何與驗證證據為核心；LLM 只協助整理設計意圖、提出問題與解釋結果，不取代幾何核心、物理求解器或工程簽核。

## V3.0 可執行藍圖

專案唯一主要施工依據為：

- [MEGIS Mechanical Engineering Generative Intelligence System — v3.0 Claude Code](<MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v3.0-claude-code.md>)
- [V2.0 可執行藍圖（封存基線）](<MEGIS_Blueprint/MEGIS_Mechanical Engineering Generative Intelligence System — v2.0 Codex.md>)
- [V1.0 原始藍圖（封存參考）](<MEGIS_Blueprint/OLD/Generative Mechanical Design Factory — Master Blueprint & Detailed Implementation Plan.md>)

V3.0 採 Gate-driven construction，不以日期或推測百分比宣稱完成。它保留 V2.0 已完成工作與 Gate，透過 V3 Conformance（`V3C-*`）補足 control plane、決策、fingerprint、classification、artifact 與隔離審查要求；每個 Gate 必須具備可重跑證據，下一 Gate 才能接受。

## 目前施工狀態

**G0～G5 已完成 Gate acceptance，G6 為 active Gate**。V3 必要工作圖共有 74 項，目前控制面為 **62 done、1 in progress、11 planned**；唯一在製項目是 `G6-A11Y-001 — 無障礙驗證`。

最近閉合的 G6 能力：

- `G6-UI-001`：capability-driven guided flow，只呈現已驗證能力；UI 與 API 產生等價 Engineering IR。
- `G6-QST-001`：deterministic question ordering 與 abstention；unsafe unknown 阻擋生成且不會消失。
- `G6-AI-001`：provider-neutral adapter、AI 預設關閉、recorded local stub、timeout／呼叫／token／成本上限；故障或超限時帶 `MEGIS-AI-*` 錯誤退回表單。
- `G6-AI-002`：schema-bound Requirement draft、exact evidence span、`llm_proposed` quarantine 與逐欄 confirmation；未確認值不得進入 confirmed IR。
- `G6-AI-003`：54 筆六類 intent corpus 與 case-level KPI；unsafe hallucination 0、injection resistance 100%，並附 Wilson 95% CI。
- `G6-AI-004`：白話解釋的每次數值出現都必須以 hash-bound source＋JSON Pointer 追溯至 IR、rule result 或 manifest。
- `G6-A11Y-001`（施工中）：axe WCAG 2.2 A／AA 五路由 0 violations，鍵盤／焦點契約自動化已通過；實際 Chrome 的 8 項代理自動化瀏覽器稽核亦通過。真人鍵盤與螢幕閱讀器抽查尚待完成，人工紀錄已具備 12 項固定檢查、具名 attestation 與 fail-closed verifier；進度頁會分開顯示已備妥材料、驗證指令及仍 pending 的 acceptance。
- 最新完整 baseline：597 個 Python tests、22 個 frontend tests，以及 control-plane、secret、artifact、toolchain、maturity、lint、typecheck、build 全綠。

UI-0 是本機端使用者體驗原型，用來先確認施工進度中心與治具／電子外殼引導流程。它使用有版本的 `PrototypeViewModel` 展示資料，不是藍圖中的 G6 工程能力，也不會產生 STEP、工程圖面、BOM、Prototype Package 或可供製造的工程製品。

目前已完成：

- UI-0A：最小可行基礎
- UI-0B：施工進度中心
- UI-0C：引導式使用者體驗原型
- UI-0D：自動化、瀏覽器與使用者驗收皆已通過

UI-0 已完成驗收，但其展示結果仍是合成資料。正式工程核心已完成至 G5：Engineering IR、支援 envelope、治具幾何、規則與驗證、maturity、Module composition、safe import、BOM、draft drawing、Prototype Package 與 clean-environment reproducibility 均有可重跑證據。G6 正把這些能力接入正式引導介面；尚未通過 G6 Gate acceptance 的能力不會提前宣稱完成。

## 待完成清單（依序）

1. `G6-A11Y-001`：WCAG 2.2 AA 自動化與人工抽查。
2. `G6-USE-001`：至少 5 位非 CAD 參與者的 usability test；需要真實人工證據。
3. `G6-E2E-001`、`G6-REV-001`、`G6-ACC-001`：端到端、乾淨 checkout 審查與 Gate acceptance。
4. G6 accepted 後依 Gate 依賴進入 G7 聲學、G8 機器人與 G9 強化。

## 為什麼目前網站沒有更多產品或功能？

`http://127.0.0.1:4173/progress` 直接讀取 `execution/WORK_QUEUE.yaml`，呈現正式控制面，而不是另外維護一份推測進度。設計、執行與結果頁仍保留 UI-0 的永久標示 `Synthetic demo data` 與 `No engineering artifact generated`；直到 G6 E2E、review 與 acceptance 完成前，不把前端畫面宣稱為完整工程產品。

| 使用入口／能力 | 現況 | 誠實邊界 |
|---|---|---|
| `/` 引導式設計頁 | capability-driven 問題與已驗證選項已接入 | 執行／結果展示仍保留合成標示；G6 尚未 accepted |
| `/progress` 施工進度中心 | 直接顯示 74 項正式工作佇列 | 只顯示控制面與證據，不產生工程製品 |
| Supported envelope | 機器可讀 `envelope.yaml`＋文件一致性與邊界測試 | 超界輸入回 `MEGIS-ENV-001`，不 silent clamp |
| Fixture／電子外殼核心 | 幾何、規則、驗證、Module、BOM、drawing、package 已通過 G2～G5 | 正式 UI-to-package E2E 尚未完成 |
| STEP/STL/DXF | G0 feasibility spike 可重建並重新載入 | classification 是 `FEASIBILITY_SPIKE`，`maturity: null`，不可當製造輸出 |
| 工程規則與 maturity | G3 accepted；規則治理、validator、benchmark、maturity evaluator 已驗證 | 不會自動升級為 `ENGINEERING_REVIEWED` 或 `RELEASED` |
| BOM、drawing、Prototype Package | G5 accepted；可重建且有 content hash | drawing 永久標示 draft／not for manufacturing |
| AI 輔助 | adapter、schema-bound Intent 萃取、54-case KPI 與 grounded explanation 已驗證；預設關閉，故障退回表單，未確認值隔離 | 尚未接真實 provider；G6 E2E 與人工驗收尚未完成 |
| Acoustic 產品線 | 僅有 schema-only golden case | G7 solver/thin slice 尚未施工 |
| Robot Car 產品線 | 僅有 schema-only golden case | G8 assembly/safety thin slice 尚未施工，maturity 上限受安全政策限制 |

也就是說，現在「產品少」不是遺漏，而是 MEGIS 的防誤導設計：只有具備 schema、negative tests、artifact 證據、review 與 Gate acceptance 的能力，才會從施工核心升級為使用者可見功能。

## 已驗證能力與尚未完成能力

| 層級 | 已驗證 | 尚未完成 |
|---|---|---|
| UI-0 | 中文進度中心、引導式 demo、桌面與窄螢幕驗收 | 真實工程資料、下載、multi-user、cloud |
| G0 | 鎖定工具鏈、CadQuery spike、FreeCAD fallback、Windows CI、fingerprint/classification/artifact policy、clean-checkout 審查與 `SO-0001` Gate 簽核 | 無（G0 11 項全 done） |
| G1 | Engineering primitives、IR schema、三種 golden inputs、migration/rollback、錯誤碼、機器可讀 envelope、review 與 sign-off | 無（Gate accepted） |
| G2 | Kernel-neutral geometry、fixture assembly、export/reload、negative corpus、review 與 sign-off | 無（Gate accepted） |
| G3 | 規則治理、validator、benchmark、maturity evaluator、review 與 sign-off | 無（Gate accepted） |
| G4 | Module capability、relationship、composition、safe import、review 與 sign-off | 無（Gate accepted） |
| G5 | Manifest、BOM、draft drawing、reproducibility、review 與 sign-off | 無（Gate accepted） |
| G6 | Guided flow、Question Engine、optional AI adapter、schema-bound Intent 萃取 | AI KPI、grounded explanation、a11y、usability、E2E、review、acceptance |
| G7～G9 | 藍圖與 acceptance criteria | Acoustic、Robot 與 hardening 尚未施工 |

- [UI-0 施工計畫](docs/UI0_PLAN.md)
- [UI-0 可行性紀錄](docs/UI0_FEASIBILITY.md)
- [UI-0 驗證報告](docs/UI0_VERIFICATION.md)
- [UI-0 使用者驗收紀錄](docs/UI0_ACCEPTANCE.md)
- [正式專案狀態](execution/PROJECT_STATE.md)
- [正式工作佇列](execution/WORK_QUEUE.yaml)
- [G0 工具鏈版本決策](docs/decisions/toolchain.md)
- [G0 CadQuery 可行性驗證](docs/G0_CAD_VERIFICATION.md)
- [G0 FreeCAD TechDraw fallback 決策](docs/G0_FREECAD_DECISION.md)
- [G0 COMSOL 可行性決策](docs/G0_COMSOL_DECISION.md)
- [G0 Baseline CI](docs/G0_BASELINE_CI.md)
- [G1 Engineering Primitives](docs/G1_PRIMITIVES.md)
- [G1 Engineering IR](docs/G1_ENGINEERING_IR.md)
- [G1 Golden Cases](docs/G1_GOLDEN_CASES.md)
- [G1 Schema Migration Contract](docs/G1_SCHEMA_MIGRATION.md)
- [G1 錯誤碼登錄](docs/ERROR_CODES.md)
- [G1 Supported Envelope](docs/SUPPORTED_ENVELOPE.md)
- [G2 Geometry Capability Contract](docs/G2_GEOMETRY_CONTRACT.md)
- [G2 Fixture Base](docs/G2_FIXTURE_BASE.md)
- [G2 Fixture Assembly](docs/G2_FIXTURE_ASSEMBLY.md)
- [G6 AI provider adapter 與離線 fallback](docs/G6_AI_PROVIDER_ADAPTER.md)
- [G6 AI Intent 到 Requirement 萃取](docs/G6_AI_REQUIREMENT_EXTRACTION.md)
- [V3 採用決策](docs/decisions/ADR-0001-adopt-v3-blueprint.md)
- [Classification 與 maturity 政策](docs/CLASSIFICATION_AND_MATURITY.md)
- [Artifact 儲存與 Git 大小預算政策](docs/ARTIFACT_POLICY.md)
- [ADR-0011：既有 G0 重型製品精確白名單](docs/decisions/ADR-0011-legacy-heavy-artifact-allowlist.md)
- [G1-ENV-001 完工進度報告](outputs/2026-09-19-G1-ENV-001-完工進度報告.md)
- [V3 最新施工進度盤點與 GitHub／網頁同步報告](outputs/2026-09-22-G6-AI-002-完工與V3盤點報告.md)
- [決策索引](docs/DECISIONS.md)

## 本機啟動

網站需求固定為 Node.js 24.17.0 與 npm 11.13.0。網站綁定於 `127.0.0.1`，不應公開至區域網路或網際網路。

```powershell
cd C:\0_JN1_MEGIS\apps\web
npm install
npm run dev
```

開啟：<http://127.0.0.1:4173/progress>

## 完整驗證

```powershell
cd C:\0_JN1_MEGIS
powershell -ExecutionPolicy Bypass -File scripts\run-baseline-ci.ps1
```

完整 baseline 會依序執行 control-plane、artifact policy 正／負向檢查、Python dependency/toolchain、126 個 Python tests、manifest maturity scan、13 筆 artifact smoke、前端 lint/typecheck、9 個 frontend tests 與 production build。

所有專案快取、暫存檔、測試輸出與建置結果都必須留在 `C:\0_JN1_MEGIS`。本專案不得修改、共用環境或依賴 `C:\0_JN1_AERIS` 與 `C:\0_JN1_Offline-Local-Voice-Agent`。

## 本機資料與 GitHub 同步

施工以本機 repository 為工作來源，每個通過驗證的單一工作項目先建立可回滾的 commit，再同步至 [GitHub `main`](https://github.com/Space653000/0_JN1_MEGIS)。同步前先執行 `git fetch origin` 與 `git status -sb` 確認沒有遠端分歧；同步後再次抓取遠端並核對 `HEAD` 與 `origin/main` 的 commit SHA。禁止使用 `git push --force`，任何推送都必須取得使用者明確授權。

藍圖、程式、schema、tests、文件、控制面與小型驗證證據會同步；`.venv`、cache、`.temp`、`node_modules`、`dist`、`.runs` 與新的 spike 重型製品不會上傳。這些排除項是可重建或本機執行資料，不是遺漏同步。

## 建設路線

```text
UI-0 使用者體驗原型與驗收
↓
G0 基礎建設與可行性
↓
G1 工程契約與黃金案例
↓
G2 治具幾何垂直切片
↓
G3 規則與驗證
↓
G4 模組與限制條件組合
↓
G5 原型套件與可重現性
↓
G6 引導式工程介面
├─ G7 聲學垂直切片
└─ G8 機器人垂直切片
↓
G9 強化與擴充
```

第一條完整工程路徑固定為小型 CNC 治具／電子外殼。MEGIS 自動化施工的最高成熟度為 `PROTOTYPE`；`ENGINEERING_REVIEWED` 與 `RELEASED` 必須經過合格工程師及適用的製造、品質與法規流程。
